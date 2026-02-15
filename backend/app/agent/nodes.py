"""LangGraph nodes: analyze artifacts and produce report sections."""
import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser

from app.agent.state import AgentState

REPORT_SYSTEM = """Ты — эксперт по анализу результатов нагрузочного тестирования.
Тебе переданы артефакты теста: метрики Grafana, логи и список подов Kubernetes, логи JVM/GC и т.д.
Твоя задача — составить структурированный отчёт на русском языке.

Формат ответа (строго придерживайся блоков):
## META
project: название тестируемого проекта
test_type: тип теста (поиск максимума / подтверждение максимума / надежность / деструктивный)
version: версия ПО
time_range: время проведения теста

## PODS_TABLE
Таблица: Pod (или группа подов) | Количество | Limits | Requests
(по одной строке на под или группу по имени префикса)

## GOOD
Кратко: что работает хорошо (метрики в норме, стабильность, SLA соблюдены).

## BAD
Кратко: что работает плохо.

## ERRORS
Акцент на: ошибки в логах, провалы на графиках, исчерпание памяти, выход за SLA.
Если явных проблем нет — напиши "Явных проблем не выявлено."

## FULL_REPORT
Полный текст заключения в свободной форме (несколько абзацев).
"""


def _extract_section(text: str, tag: str) -> str:
    m = re.search(rf"## {tag}\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def analyze_artifacts(state: AgentState, llm: Any) -> AgentState:
    """Node: run LLM over artifact_contents + system_prompt and fill report_sections + report_text."""
    contents = state.get("artifact_contents") or ""
    system_prompt = state.get("system_prompt") or ""
    test_meta = state.get("test_meta") or {}

    system = REPORT_SYSTEM
    if system_prompt:
        system += f"\n\nДополнительный контекст от инженера:\n{system_prompt}"

    user = f"""Метаданные теста: {json.dumps(test_meta, ensure_ascii=False)}

Артефакты (графики описаны по файлам, логи и данные ниже):

{contents[:120000]}
"""
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    chain = llm | StrOutputParser()
    try:
        raw = chain.invoke(messages)
    except Exception as e:
        return {"error": str(e), "report_text": ""}

    report_sections = {
        "meta": _extract_section(raw, "META"),
        "pods_table": _extract_section(raw, "PODS_TABLE"),
        "good": _extract_section(raw, "GOOD"),
        "bad": _extract_section(raw, "BAD"),
        "errors": _extract_section(raw, "ERRORS"),
        "full_report": _extract_section(raw, "FULL_REPORT"),
    }
    return {
        "analysis": raw,
        "report_sections": report_sections,
        "report_text": raw,
    }


def format_report_text(state: AgentState) -> AgentState:
    """Node: build final plain text report from report_sections."""
    sections = state.get("report_sections") or {}
    lines = [
        "ОТЧЁТ ПО РЕЗУЛЬТАТАМ НАГРУЗОЧНОГО ТЕСТИРОВАНИЯ",
        "",
        sections.get("meta", ""),
        "",
        "Таблица подов (Limits / Requests):",
        sections.get("pods_table", "—"),
        "",
        "Что работает хорошо:",
        sections.get("good", "—"),
        "",
        "Что работает плохо:",
        sections.get("bad", "—"),
        "",
        "Ошибки и проблемы (SLA, память, графики):",
        sections.get("errors", "—"),
        "",
        "Полное заключение:",
        sections.get("full_report", "—"),
    ]
    return {"report_text": "\n".join(lines)}
