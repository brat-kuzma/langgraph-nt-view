"""Orchestrate artifact collection and LangGraph analysis for a test."""
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import json
import structlog

from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import Project, Test, Artifact, Report, ArtifactKind
from app.services.grafana import GrafanaService
from app.services.kubernetes import KubernetesService
from app.services.artifacts import ArtifactsService
from app.services.report_generator import ReportGeneratorService
from app.agent.graph import run_analysis

logger = structlog.get_logger()


def _parse_pods_table(text: str) -> list[list[str]]:
    """Convert PODS_TABLE section (markdown-like) to rows for PDF table."""
    rows = [["Pod / группа", "Количество", "Limits", "Requests"]]
    for line in (text or "").strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Split by | or tabs
        cells = [c.strip() for c in line.replace("|", "\t").split("\t") if c.strip()]
        if len(cells) >= 4:
            rows.append(cells[:4])
        elif len(cells) == 1 and "—" in line:
            continue
        elif cells:
            rows.append(cells + [""] * (4 - len(cells)))
    return rows


def build_artifact_contents(db: Session, test_id: int) -> str:
    """Load all artifacts for test from DB and storage into one text for the agent."""
    artifacts = db.query(Artifact).filter(Artifact.test_id == test_id).order_by(Artifact.id).all()
    parts = []
    art_service = ArtifactsService()
    base = Path(art_service.base).resolve()
    logger.info("artifact_load_start", test_id=test_id, artifacts_base=str(base), db_paths=[a.file_path for a in artifacts if a.file_path])
    for a in artifacts:
        if not a.file_path:
            continue
        try:
            full_path = base / a.file_path
            raw = art_service.read_artifact(a.file_path)
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = raw.decode("latin-1", errors="replace")
            if len(text) > 50000:
                text = text[:50000] + "\n... [обрезано]"
            label = a.display_name or Path(a.file_path).name or f"{a.kind}_{a.id}"
            parts.append(f"[АРТЕФАКТ: файл=\"{label}\" kind={a.kind} id={a.id}]\n{text}")
            logger.info("artifact_loaded", artifact_id=a.id, path=a.file_path, size=len(raw))
        except Exception as e:
            logger.warning("artifact_read_failed", artifact_id=a.id, path=a.file_path, full_path=str(base / a.file_path), error=str(e))
    out = "\n\n".join(parts)
    if not out and artifacts:
        logger.warning("no_artifact_content_loaded", test_id=test_id, artifact_ids=[a.id for a in artifacts])
    return out


def run_analysis_for_test(db: Session, test_id: int) -> Tuple[Report, List[dict]]:
    """
    Load test and project, build artifact_contents from DB artifacts,
    run LangGraph agent, save report text + PDF, create Report row.
    """
    test = db.query(Test).filter(Test.id == test_id).first()
    if not test:
        raise ValueError(f"Test {test_id} not found")
    project = db.query(Project).filter(Project.id == test.project_id).first()
    if not project:
        raise ValueError("Project not found")

    test.status = "analyzing"
    db.commit()

    try:
        artifacts = db.query(Artifact).filter(Artifact.test_id == test_id).order_by(Artifact.id).all()
        artifacts_used = [
            {"id": a.id, "kind": a.kind, "display_name": a.display_name, "file_path": a.file_path}
            for a in artifacts if a.file_path
        ]
        artifact_contents = build_artifact_contents(db, test_id)
        if not artifact_contents.strip():
            raise ValueError(
                "Не удалось прочитать ни один артефакт. Проверьте, что файлы существуют в storage/artifacts/ (пути в БД: "
                + ", ".join(a.file_path for a in artifacts if a.file_path) + ")."
            )
        test_meta = {
            "project_name": project.name,
            "test_type": test.test_type,
            "version": getattr(project, "version", "") or "—",
            "time_range": f"{test.started_at} — {test.ended_at}" if test.started_at and test.ended_at else "—",
        }
        artifact_labels = [a.get("display_name") or Path(a.get("file_path") or "").name for a in artifacts_used]
        max_chars = settings.ollama_max_context_chars if project.llm_type == "ollama" else None
        llm_model = project.llm_model or settings.default_llm_model
        if project.llm_type == "ollama" and llm_model and "qwen2.5vl" in llm_model.lower():
            logger.warning(
                "ollama_qwen2vl_unsafe",
                requested=llm_model,
                using="qwen2.5:7b",
                reason="qwen2.5vl крашит runner (RoPE/exit 2); для анализа логов достаточно текстовой модели",
            )
            llm_model = "qwen2.5:7b"
        result = run_analysis(
            test_meta=test_meta,
            artifact_contents=artifact_contents,
            artifact_labels=artifact_labels,
            system_prompt=test.system_prompt,
            max_artifact_chars=max_chars,
            llm_type=project.llm_type,
            llm_model=llm_model,
            llm_api_key=project.llm_api_key,
            llm_base_url=settings.ollama_base_url if project.llm_type == "ollama" else None,
        )
        if result.get("error"):
            test.status = "failed"
            test.error_message = result["error"]
            db.commit()
            raise RuntimeError(result["error"])

        report_text = result.get("report_text") or ""
        sections = result.get("report_sections") or {}
        gen = ReportGeneratorService()
        txt_path = gen.save_text_report(test_id, report_text)

        meta = {
            "project_name": test_meta["project_name"],
            "test_type": test_meta["test_type"],
            "version": test_meta["version"],
            "time_range": test_meta["time_range"],
        }
        table_rows = _parse_pods_table(sections.get("pods_table", ""))
        pdf_path = gen.build_pdf(
            test_id=test_id,
            title="Отчёт по результатам НТ",
            meta=meta,
            sources=sections.get("sources", ""),
            table_rows=table_rows,
            good_points=sections.get("good", ""),
            bad_points=sections.get("bad", ""),
            errors_focus=sections.get("errors", ""),
            full_text=sections.get("full_report", report_text),
        )

        # Один отчёт на тест: обновляем существующий или создаём новый
        report = db.query(Report).filter(Report.test_id == test_id).first()
        if report:
            report.report_text = report_text
            report.pdf_path = str(pdf_path)
            report.artifacts_used_snapshot = artifacts_used
        else:
            report = Report(
                test_id=test_id,
                report_text=report_text,
                pdf_path=str(pdf_path),
                artifacts_used_snapshot=artifacts_used,
            )
            db.add(report)
        test.status = "done"
        test.error_message = None
        db.commit()
        db.refresh(report)
        return report, artifacts_used
    except Exception as e:
        db.rollback()
        test.status = "failed"
        test.error_message = str(e)
        db.commit()
        raise
