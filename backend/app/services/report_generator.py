"""Generate report as PDF and text file from structured report content."""
from pathlib import Path
from datetime import datetime
import structlog

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

from app.config import settings

logger = structlog.get_logger()


class ReportGeneratorService:
    """Build PDF and save text report from agent output."""

    def __init__(self):
        self.reports_path = settings.reports_path()
        self.reports_path.mkdir(parents=True, exist_ok=True)

    def save_text_report(self, test_id: int, content: str) -> Path:
        path = self.reports_path / f"test_{test_id}_report.txt"
        path.write_text(content, encoding="utf-8")
        return path

    def build_pdf(
        self,
        test_id: int,
        title: str,
        meta: dict,
        sources: str,
        table_rows: list[list[str]],
        good_points: str,
        bad_points: str,
        errors_focus: str,
        full_text: str,
    ) -> Path:
        """
        meta: project_name, test_type, version, time_range
        sources: какие файлы использованы для отчёта
        table_rows: [["Pod", "Count", "Limits", "Requests"], ...]
        """
        path = self.reports_path / f"test_{test_id}_report.pdf"
        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
        )
        styles = getSampleStyleSheet()
        style_h = ParagraphStyle(name="Heading", parent=styles["Heading1"], fontSize=14, spaceAfter=6)
        style_b = ParagraphStyle(name="Body", parent=styles["Normal"], fontSize=10, spaceAfter=4)

        story = []
        story.append(Paragraph(title, style_h))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph(f"Проект: {meta.get('project_name', '—')}", style_b))
        story.append(Paragraph(f"Тип теста: {meta.get('test_type', '—')}", style_b))
        story.append(Paragraph(f"Версия ПО: {meta.get('version', '—')}", style_b))
        story.append(Paragraph(f"Время тестирования: {meta.get('time_range', '—')}", style_b))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Источники данных (файлы, на которых основан отчёт)", style_h))
        story.append(Paragraph(sources or "—", style_b))
        story.append(Spacer(1, 0.5 * cm))

        if table_rows:
            t = Table(table_rows)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5 * cm))

        story.append(Paragraph("Что работает хорошо", style_h))
        story.append(Paragraph(good_points or "—", style_b))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Что работает плохо", style_h))
        story.append(Paragraph(bad_points or "—", style_b))
        story.append(Spacer(1, 0.3 * cm))
        story.append(Paragraph("Ошибки и проблемы (SLA, память, графики)", style_h))
        story.append(Paragraph(errors_focus or "—", style_b))
        story.append(Spacer(1, 0.5 * cm))
        story.append(Paragraph("Полный отчёт", style_h))
        for block in full_text.split("\n\n"):
            if block.strip():
                story.append(Paragraph(block.replace("\n", "<br/>"), style_b))

        doc.build(story)
        return path
