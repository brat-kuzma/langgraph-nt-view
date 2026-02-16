from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import TestCreate, TestRead
from app.db import models

router = APIRouter()


@router.post("/", response_model=TestRead)
def create_test(t: TestCreate, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == t.project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    test = models.Test(
        project_id=t.project_id,
        test_type=t.test_type,
        started_at=t.started_at,
        ended_at=t.ended_at,
        system_prompt=t.system_prompt,
    )
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("/", response_model=List[TestRead])
def list_tests(project_id: Optional[int] = None, db: Session = Depends(get_db)):
    q = db.query(models.Test).order_by(models.Test.id.desc())
    if project_id is not None:
        q = q.filter(models.Test.project_id == project_id)
    return q.all()


@router.get("/{test_id}", response_model=TestRead)
def get_test(test_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    return t


@router.post("/{test_id}/run-analysis")
def run_test_analysis(test_id: int, db: Session = Depends(get_db)):
    from app.services.analysis_runner import run_analysis_for_test
    try:
        report, artifacts_used = run_analysis_for_test(db, test_id)
        return {"status": "done", "report_id": report.id, "artifacts_used": artifacts_used}
    except ValueError as e:
        raise HTTPException(404, str(e))
    except RuntimeError as e:
        raise HTTPException(500, str(e))


@router.delete("/{test_id}", status_code=204)
def delete_test(test_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    db.delete(t)
    db.commit()
    return None
