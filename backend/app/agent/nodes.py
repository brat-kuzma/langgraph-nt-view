"""LangGraph nodes: analyze artifacts and produce report sections."""
import json
import re
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.agent.state import AgentState

logger = structlog.get_logger()

REPORT_SYSTEM = """Ты — эксперт по анализу результатов нагрузочного тестирования.

КРИТИЧЕСКИ ВАЖНО:
- Делай выводы ТОЛЬКО на основе данных, которые реально есть в переданных артефактах (файлах).
- Не придумывай факты, метрики, цифры и события — используй только то, что явно указано в тексте артефактов.
- Для каждого заключения обязательно укажи источник: из какого файла (артефакта) взяты данные. Используй точное имя файла из метки [АРТЕФАКТ: файл="..."].
- Если по какому-то вопросу в артефактах нет данных — так и напиши: "Данные не предоставлены" или "В переданных файлах сведений нет".
- В отчёте обязательны ВСЕ переданные артефакты (файлы). Не пропускай ни один: в SOURCES перечисли каждый файл, в выводах (GOOD/BAD/ERRORS/FULL_REPORT) упомяни каждый файл — либо вывод по нему, либо «по файлу X: данных для выводов недостаточно».

Артефакты помечены так: [АРТЕФАКТ: файл="имя_файла" kind=... id=...]. В выводах ссылайся на файл, например: «По данным из файла my-app-gc.log: ...» или «В артефакте pods_list.json указано: ...».

Формат ответа (строго придерживайся блоков):
## META
project: название тестируемого проекта
test_type: тип теста (поиск максимума / подтверждение максимума / надежность / деструктивный)
version: версия ПО (только если есть в артефактах)
time_range: время проведения теста

## PODS_TABLE
Таблица подов — ТОЛЬКО если в артефактах есть данные о подах (например из k8s_pods / pods_list.json). Иначе напиши: "Данные о подах не предоставлены."
Формат: Pod (группа) | Количество | Limits | Requests. Указывай источник: (данные из файла X).

## GOOD
Что работает хорошо — только по фактам из артефактов. Для каждого пункта укажи: (по данным из файла «имя»).

## BAD
Что работает плохо — только по фактам из артефактов. Укажи источник для каждого пункта.

## ERRORS
Ошибки и проблемы (логи, память, SLA) — только то, что явно есть в переданных файлах. Укажи файл-источник. Если явных проблем в данных нет: "По переданным артефактам явных проблем не выявлено."

## SOURCES
ОБЯЗАТЕЛЬНО перечисли ВСЕ артефакты из списка переданных файлов. Для каждого файла напиши, что из него взято (или «данных для выводов недостаточно»). Пропускать файлы нельзя.

## FULL_REPORT
Полное заключение: несколько абзацев. Каждое утверждение должно опираться на конкретный артефакт; в тексте указывай «по данным из файла …» или «в логе …».
"""


def _extract_section(text: str, tag: str) -> str:
    m = re.search(rf"## {tag}\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def analyze_artifacts(state: AgentState, llm: Any) -> AgentState:
    """Node: run LLM over artifact_contents + system_prompt and fill report_sections + report_text."""
    contents = state.get("artifact_contents") or ""
    max_chars = state.get("max_artifact_chars") or 120_000
    contents = contents[:max_chars]
    if max_chars < len(state.get("artifact_contents") or ""):
        logger.info("artifact_contents_truncated", max_chars=max_chars, original_len=len(state.get("artifact_contents") or ""))
    artifact_labels = state.get("artifact_labels") or []
    system_prompt = state.get("system_prompt") or ""
    test_meta = state.get("test_meta") or {}

    system = REPORT_SYSTEM
    if system_prompt:
        system += f"\n\nДополнительный контекст от инженера:\n{system_prompt}"

    labels_line = ""
    if artifact_labels:
        labels_line = f"\nОБЯЗАТЕЛЬНО: В отчёте должны быть учтены ВСЕ {len(artifact_labels)} артефактов. Список файлов (каждый должен быть упомянут в SOURCES и в выводах): {', '.join(repr(f) for f in artifact_labels)}.\n"

    user = f"""Метаданные теста: {json.dumps(test_meta, ensure_ascii=False)}
{labels_line}
Ниже — содержимое артефактов (файлов). Каждый блок начинается с метки [АРТЕФАКТ: файл="..." ...]. Строй отчёт только по этим данным и для каждого вывода указывай имя файла-источника. В разделах SOURCES, GOOD, BAD, ERRORS и в FULL_REPORT должны быть учтены ВСЕ переданные файлы.

--- НАЧАЛО АРТЕФАКТОВ ---

{contents}

--- КОНЕЦ АРТЕФАКТОВ ---

Составь отчёт по приведённым выше данным. Не используй информацию, которой нет в блоках артефактов. Для каждого файла из списка артефактов сделай вывод или укажи «по файлу X: данных для выводов недостаточно»."""
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    chain = llm | StrOutputParser()
    try:
        raw = chain.invoke(messages)
    except Exception as e:
        logger.exception("llm_invoke_failed", error=str(e))
        return {"error": str(e), "report_text": ""}

    report_sections = {
        "meta": _extract_section(raw, "META"),
        "pods_table": _extract_section(raw, "PODS_TABLE"),
        "good": _extract_section(raw, "GOOD"),
        "bad": _extract_section(raw, "BAD"),
        "errors": _extract_section(raw, "ERRORS"),
        "sources": _extract_section(raw, "SOURCES"),
        "full_report": _extract_section(raw, "FULL_REPORT"),
    }
    return {
        "analysis": raw,
        "report_sections": report_sections,
        "report_text": raw,
    }


def format_report_text(state: AgentState) -> AgentState:
    """Node: build final plain text report from report_sections. Если секции пустые — подставляем сырой ответ LLM."""
    sections = state.get("report_sections") or {}
    meta = sections.get("meta", "").strip()
    sources = sections.get("sources", "").strip()
    pods = sections.get("pods_table", "").strip()
    good = sections.get("good", "").strip()
    bad = sections.get("bad", "").strip()
    errors = sections.get("errors", "").strip()
    full = sections.get("full_report", "").strip()
    raw_analysis = (state.get("analysis") or "").strip()
    all_empty = not any([meta, sources, pods, good, bad, errors, full])
    if all_empty and raw_analysis:
        report_text = (
            "ОТЧЁТ ПО РЕЗУЛЬТАТАМ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ\n\n"
            "(Модель не вернула структурированные блоки ## META, ## GOOD и т.д. Ниже — сырой ответ.)\n\n"
            "---\n\n" + raw_analysis
        )
    else:
        lines = [
            "ОТЧЁТ ПО РЕЗУЛЬТАТАМ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ",
            "",
            meta or "—",
            "",
            "Источники данных (на основании каких файлов составлен отчёт):",
            sources or "—",
            "",
            "Таблица подов (Limits / Requests):",
            pods or "—",
            "",
            "Что работает хорошо:",
            good or "—",
            "",
            "Что работает плохо:",
            bad or "—",
            "",
            "Ошибки и проблемы (SLA, память, графики):",
            errors or "—",
            "",
            "Полное заключение:",
            full or "—",
        ]
        report_text = "\n".join(lines)
    return {"report_text": report_text}
