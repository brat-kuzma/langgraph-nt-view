"""Collect artifacts from Grafana and Kubernetes for a test (time range)."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import settings
from app.db import models
from app.services.grafana import GrafanaService
from app.services.kubernetes import KubernetesService

router = APIRouter()


def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


@router.post("/test/{test_id}/grafana")
def collect_grafana(
    test_id: int,
    from_ts: str = Query(..., description="Start ISO datetime, e.g. 2025-02-15T10:00:00"),
    to_ts: str = Query(..., description="End ISO datetime"),
    dashboard_uid: str = Query(..., description="Grafana dashboard UID"),
    grafana_source_index: int = Query(0, description="Index in project.grafana_sources"),
    db: Session = Depends(get_db),
):
    """Slice dashboard panels for [from_ts, to_ts] and save as artifacts."""
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    proj = db.query(models.Project).filter(models.Project.id == t.project_id).first()
    if not proj or not proj.grafana_sources:
        raise HTTPException(400, "Project has no Grafana sources")
    sources = proj.grafana_sources
    if grafana_source_index >= len(sources):
        raise HTTPException(400, "Invalid grafana_source_index")
    src = sources[grafana_source_index]
    url = src.get("url") or src.get("base_url")
    token = src.get("token") or src.get("api_key")
    if not url or not token:
        raise HTTPException(400, "Grafana url and token required")
    save_dir = settings.grafana_snapshots_path() / str(test_id)
    save_dir.mkdir(parents=True, exist_ok=True)
    svc = GrafanaService(base_url=url, token=token)
    results = svc.slice_and_save_dashboard(dashboard_uid, _parse_ts(from_ts), _parse_ts(to_ts), save_dir)
    for r in results:
        art = models.Artifact(
            test_id=test_id,
            kind="grafana_slice",
            display_name=r.get("title"),
            file_path=r.get("image_path"),
            metadata_={"meta_path": r.get("meta_path"), "panel_id": r.get("panel_id")},
        )
        db.add(art)
    db.commit()
    return {"collected": len(results), "artifacts": results}


@router.post("/test/{test_id}/kubernetes")
def collect_kubernetes(
    test_id: int,
    from_ts: str = Query(..., description="Start ISO datetime"),
    to_ts: str = Query(..., description="End ISO datetime"),
    namespace: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Save pods list and pod/container logs for time range as artifacts."""
    t = db.query(models.Test).filter(models.Test.id == test_id).first()
    if not t:
        raise HTTPException(404, "Test not found")
    proj = db.query(models.Project).filter(models.Project.id == t.project_id).first()
    if not proj or not proj.k8s_config:
        raise HTTPException(400, "Project has no Kubernetes config")
    save_dir = settings.artifacts_path() / str(test_id) / "k8s"
    save_dir.mkdir(parents=True, exist_ok=True)
    svc = KubernetesService(proj.k8s_config)
    out = svc.collect_and_save(_parse_ts(from_ts), _parse_ts(to_ts), save_dir, namespace=namespace)
    # Register artifacts in DB
    pods_art = models.Artifact(
        test_id=test_id,
        kind="k8s_pods",
        display_name="pods_list.json",
        file_path=out["pods_file"],
        metadata_={"pods_count": out["pods_count"]},
    )
    db.add(pods_art)
    for log_entry in out.get("logs", []):
        art = models.Artifact(
            test_id=test_id,
            kind="k8s_logs",
            display_name=f"{log_entry['pod']}/{log_entry['container']}",
            file_path=log_entry["log_file"],
            metadata_=log_entry,
        )
        db.add(art)
    db.commit()
    return {"pods_file": out["pods_file"], "logs_count": len(out.get("logs", []))}
