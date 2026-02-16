from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, Response, StreamingResponse
from sqlalchemy.orm import Session
from pathlib import Path
import zipfile
import io

from app.api.deps import get_db
from app.api.schemas import ArtifactRead
from app.db import models
from app.services.artifacts import ArtifactsService

router = APIRouter()


@router.get("/test/{test_id}", response_model=List[ArtifactRead])
def list_artifacts(test_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    arts = db.query(models.Artifact).filter(models.Artifact.test_id == test_id).all()
    return arts


@router.post("/test/{test_id}/upload", response_model=ArtifactRead)
async def upload_artifact(
    test_id: int,
    kind: str = Form(...),
    display_name: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    content = await file.read()
    svc = ArtifactsService()
    path_for_db, meta = svc.save_custom_artifact(
        test_id=test_id,
        kind=kind,
        content=content,
        display_name=display_name or file.filename,
        metadata={"original_filename": file.filename},
    )
    art = models.Artifact(
        test_id=test_id,
        kind=kind,
        display_name=display_name or file.filename,
        file_path=str(path_for_db),
        metadata_=meta,
    )
    db.add(art)
    db.commit()
    db.refresh(art)
    return art


@router.get("/download-all/{test_id}")
def download_all_artifacts(test_id: int, db: Session = Depends(get_db)):
    """Return ZIP of all artifact files for the test."""
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    arts = db.query(models.Artifact).filter(models.Artifact.test_id == test_id).all()
    svc = ArtifactsService()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for a in arts:
            if not a.file_path:
                continue
            try:
                data = svc.read_artifact(a.file_path)
                name = Path(a.file_path).name
                zf.writestr(name, data)
            except Exception:
                pass
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=test_{test_id}_artifacts.zip"},
    )


@router.delete("/test/{test_id}/artifacts", status_code=204)
def delete_test_artifacts(test_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    arts = db.query(models.Artifact).filter(models.Artifact.test_id == test_id).all()
    for a in arts:
        db.delete(a)
    svc = ArtifactsService()
    svc.delete_test_artifacts(test_id)
    db.commit()
    return Response(status_code=204)
