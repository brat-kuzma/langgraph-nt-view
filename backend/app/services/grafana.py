"""Grafana API: export panels/snapshots for a time range and store structured."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime
import structlog

import requests

from app.config import settings

logger = structlog.get_logger()


class GrafanaService:
    """Access Grafana by API; export panel images/data for a time range and save."""

    def __init__(self, base_url: str, token: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.verify_ssl = verify_ssl
        self._session = requests.Session()
        self._session.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        url = f"{self.base_url}/api{path}"
        r = self._session.get(url, params=params, verify=self.verify_ssl, timeout=30)
        r.raise_for_status()
        return r.json() if r.content else None

    def list_dashboards(self) -> list[dict]:
        """List all dashboards (search)."""
        data = self._get("/search", params={"type": "dash-db"})
        return data or []

    def get_dashboard_uid(self, uid: str) -> dict:
        """Get dashboard by UID."""
        return self._get(f"/dashboards/uid/{uid}")

    def get_panels(self, dashboard_uid: str) -> list[dict]:
        """Get list of panels from dashboard."""
        dash = self.get_dashboard_uid(dashboard_uid)
        dash_data = dash.get("dashboard", {})
        return dash_data.get("panels", [])

    def render_panel_snapshot(
        self,
        dashboard_uid: str,
        panel_id: int,
        from_ts: datetime,
        to_ts: datetime,
        width: int = 1200,
        height: int = 400,
    ) -> bytes:
        """Render panel as image for given time range. Returns PNG bytes."""
        url = f"{self.base_url}/render/d-solo/{dashboard_uid}"
        params = {
            "panelId": panel_id,
            "from": int(from_ts.timestamp() * 1000),
            "to": int(to_ts.timestamp() * 1000),
            "width": width,
            "height": height,
        }
        r = self._session.get(url, params=params, verify=self.verify_ssl, timeout=60)
        r.raise_for_status()
        return r.content

    def export_panel_data(
        self,
        dashboard_uid: str,
        panel_id: int,
        from_ts: datetime,
        to_ts: datetime,
    ) -> dict:
        """Query panel data (if datasource supports) for time range. Returns JSON."""
        dash = self.get_dashboard_uid(dashboard_uid)
        # Grafana query API varies by datasource; here we use generic snapshot of panel config + time range
        return {
            "dashboard_uid": dashboard_uid,
            "panel_id": panel_id,
            "from": from_ts.isoformat(),
            "to": to_ts.isoformat(),
            "exported_at": datetime.utcnow().isoformat(),
        }

    def slice_and_save_dashboard(
        self,
        dashboard_uid: str,
        from_ts: datetime,
        to_ts: datetime,
        save_dir: Path,
        dashboard_title: Optional[str] = None,
    ) -> list[dict]:
        """
        For each panel in dashboard, render snapshot for [from_ts, to_ts] and save.
        Returns list of {panel_id, title, image_path, meta_path}.
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        panels = self.get_panels(dashboard_uid)
        if dashboard_title is None:
            dash = self.get_dashboard_uid(dashboard_uid)
            dashboard_title = dash.get("dashboard", {}).get("title", dashboard_uid)

        results = []
        for p in panels:
            if p.get("type") == "row":
                continue
            pid = p.get("id")
            title = p.get("title", f"panel_{pid}")
            if not pid:
                continue
            try:
                img_bytes = self.render_panel_snapshot(dashboard_uid, pid, from_ts, to_ts)
                safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in title)[:80]
                image_path = save_dir / f"{dashboard_uid}_{pid}_{safe_title}.png"
                image_path.write_bytes(img_bytes)
                meta = self.export_panel_data(dashboard_uid, pid, from_ts, to_ts)
                meta["panel_title"] = title
                meta_path = save_dir / f"{dashboard_uid}_{pid}_{safe_title}.json"
                meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
                results.append({
                    "panel_id": pid,
                    "title": title,
                    "image_path": str(image_path),
                    "meta_path": str(meta_path),
                })
            except Exception as e:
                logger.warning("grafana_panel_export_failed", panel_id=pid, error=str(e))
        return results
