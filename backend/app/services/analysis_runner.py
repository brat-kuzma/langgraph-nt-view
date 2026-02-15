"""Orchestrate artifact collection and LangGraph analysis for a test."""
from pathlib import Path
from datetime import datetime
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
    for a in artifacts:
        if not a.file_path:
            continue
        try:
            raw = art_service.read_artifact(a.file_path)
            try:
                text = raw.decode("utf-8", errors="replace")
            except Exception:
                text = raw.decode("latin-1", errors="replace")
            if len(text) > 50000:
                text = text[:50000] + "\n... [обрезано]"
            parts.append(f"--- {a.kind}: {a.display_name or a.file_path} ---\n{text}")
        except Exception as e:
            logger.warning("artifact_read_failed", artifact_id=a.id, path=a.file_path, error=str(e))
    return "\n\n".join(parts)


def run_analysis_for_test(db: Session, test_id: int) -> Report:
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
        artifact_contents = build_artifact_contents(db, test_id)
        test_meta = {
            "project_name": project.name,
            "test_type": test.test_type,
            "version": getattr(project, "version", "") or "—",
            "time_range": f"{test.started_at} — {test.ended_at}" if test.started_at and test.ended_at else "—",
        }
        result = run_analysis(
            test_meta=test_meta,
            artifact_contents=artifact_contents,
            system_prompt=test.system_prompt,
            llm_type=project.llm_type,
            llm_model=project.llm_model,
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
            table_rows=table_rows,
            good_points=sections.get("good", ""),
            bad_points=sections.get("bad", ""),
            errors_focus=sections.get("errors", ""),
            full_text=sections.get("full_report", report_text),
        )

        report = Report(
            test_id=test_id,
            report_text=report_text,
            pdf_path=str(pdf_path),
        )
        db.add(report)
        test.status = "done"
        test.error_message = None
        db.commit()
        db.refresh(report)
        return report
    except Exception as e:
        test.status = "failed"
        test.error_message = str(e)
        db.commit()
        raise
