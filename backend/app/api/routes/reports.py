from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import ReportRead
from app.db import models

router = APIRouter()


@router.get("/test/{test_id}", response_model=ReportRead)
def get_report_by_test(test_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Report).filter(models.Report.test_id == test_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    return r


@router.get("/test/{test_id}/text")
def get_report_text(test_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Report).filter(models.Report.test_id == test_id).first()
    if not r:
        raise HTTPException(404, "Report not found")
    return PlainTextResponse(r.report_text)


@router.get("/test/{test_id}/pdf")
def get_report_pdf(test_id: int, db: Session = Depends(get_db)):
    r = db.query(models.Report).filter(models.Report.test_id == test_id).first()
    if not r or not r.pdf_path:
        raise HTTPException(404, "Report PDF not found")
    p = Path(r.pdf_path)
    if not p.exists():
        raise HTTPException(404, "PDF file not found on disk")
    return FileResponse(p, media_type="application/pdf", filename=p.name)
