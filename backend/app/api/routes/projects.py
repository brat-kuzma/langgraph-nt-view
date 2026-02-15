from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.schemas import ProjectCreate, ProjectRead
from app.db import models

router = APIRouter()


@router.post("/", response_model=ProjectRead)
def create_project(p: ProjectCreate, db: Session = Depends(get_db)):
    proj = models.Project(
        name=p.name,
        description=p.description,
        grafana_sources=p.grafana_sources,
        k8s_config=p.k8s_config,
        llm_type=p.llm_type,
        llm_model=p.llm_model,
        llm_api_key=p.llm_api_key,
    )
    db.add(proj)
    db.commit()
    db.refresh(proj)
    return proj


@router.get("/", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).order_by(models.Project.id).all()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not p:
        raise HTTPException(404, "Project not found")
    return p


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, p: ProjectCreate, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    proj.name = p.name
    proj.description = p.description
    proj.grafana_sources = p.grafana_sources
    proj.k8s_config = p.k8s_config
    proj.llm_type = p.llm_type
    proj.llm_model = p.llm_model
    proj.llm_api_key = p.llm_api_key
    db.commit()
    db.refresh(proj)
    return proj


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    proj = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not proj:
        raise HTTPException(404, "Project not found")
    db.delete(proj)
    db.commit()
    return None
