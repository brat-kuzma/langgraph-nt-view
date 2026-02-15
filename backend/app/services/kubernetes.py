"""Kubernetes: list pods (count, limits, requests, versions), fetch logs and store."""
from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import structlog

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from app.config import settings

logger = structlog.get_logger()


def _load_k8s_client(k8s_config: dict) -> tuple[client.CoreV1Api, client.AppsV1Api]:
    """Build K8s API from project config: kubeconfig base64 or token+server."""
    if "kubeconfig_base64" in k8s_config:
        import tempfile
        kc = base64.b64decode(k8s_config["kubeconfig_base64"]).decode()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(kc)
            f.flush()
            config.load_kube_config(config_file=f.name)
    elif "token" in k8s_config and "server" in k8s_config:
        configuration = client.Configuration()
        configuration.host = k8s_config["server"]
        configuration.api_key = {"authorization": "Bearer " + k8s_config["token"]}
        configuration.verify_ssl = k8s_config.get("verify_ssl", True)
        client.Configuration.set_default(configuration)
    else:
        raise ValueError("k8s_config must contain kubeconfig_base64 or (token, server)")
    return client.CoreV1Api(), client.AppsV1Api()


class KubernetesService:
    """List pods, get limits/requests/versions, save logs for time range."""

    def __init__(self, k8s_config: dict):
        self._core, self._apps = _load_k8s_client(k8s_config)
        self._config = k8s_config

    def list_pods(
        self,
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
    ) -> list[dict]:
        """List pods with count, limits, requests, container images (versions)."""
        namespaces = [namespace] if namespace else self._get_namespaces()
        result = []
        for ns in namespaces:
            try:
                pods = self._core.list_namespaced_pod(
                    namespace=ns,
                    label_selector=label_selector,
                )
                for p in pods.items:
                    result.append(self._pod_to_dict(p, ns))
            except ApiException as e:
                logger.warning("k8s_list_pods_failed", namespace=ns, error=str(e))
        return result

    def _get_namespaces(self) -> list[str]:
        if "namespace" in self._config:
            return [self._config["namespace"]]
        try:
            ns_list = self._core.list_namespace()
            return [n.metadata.name for n in ns_list.items]
        except ApiException:
            return ["default"]

    def _pod_to_dict(self, p: Any, namespace: str) -> dict:
        containers = []
        for c in p.spec.containers:
            limits = {}
            requests = {}
            if c.resources:
                if c.resources.limits:
                    limits = {k: str(v) for k, v in c.resources.limits.to_dict().items()}
                if c.resources.requests:
                    requests = {k: str(v) for k, v in c.resources.requests.to_dict().items()}
            containers.append({
                "name": c.name,
                "image": c.image,
                "limits": limits,
                "requests": requests,
            })
        return {
            "namespace": namespace,
            "name": p.metadata.name,
            "phase": p.status.phase if p.status else None,
            "containers": containers,
            "created_at": p.metadata.creation_timestamp.isoformat() if p.metadata.creation_timestamp else None,
        }

    def get_pod_logs(
        self,
        namespace: str,
        pod_name: str,
        container: Optional[str] = None,
        tail_lines: Optional[int] = 1000,
        since_seconds: Optional[int] = None,
    ) -> str:
        """Get logs of a pod (optionally one container)."""
        return self._core.read_namespaced_pod_log(
            name=pod_name,
            namespace=namespace,
            container=container,
            tail_lines=tail_lines,
            since_seconds=since_seconds,
        )

    def collect_and_save(
        self,
        from_ts: datetime,
        to_ts: datetime,
        save_dir: Path,
        namespace: Optional[str] = None,
    ) -> dict:
        """
        List pods, save pods JSON; for each pod save container logs for time range.
        Returns {pods_file, logs: [{pod, container, log_file}]}.
        """
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        since_sec = max(1, int((to_ts - from_ts).total_seconds()))

        pods = self.list_pods(namespace=namespace)
        pods_file = save_dir / "pods_list.json"
        pods_file.write_text(json.dumps(pods, ensure_ascii=False, indent=2), encoding="utf-8")

        log_entries = []
        for pod_info in pods:
            ns = pod_info["namespace"]
            name = pod_info["name"]
            for c in pod_info.get("containers", []):
                cname = c["name"]
                try:
                    log_text = self.get_pod_logs(ns, name, container=cname, tail_lines=5000, since_seconds=since_sec)
                    safe = "".join(x if x.isalnum() or x in ".-_" else "_" for x in f"{ns}_{name}_{cname}")[:120]
                    log_path = save_dir / f"logs_{safe}.txt"
                    log_path.write_text(log_text, encoding="utf-8", errors="replace")
                    log_entries.append({"pod": name, "container": cname, "namespace": ns, "log_file": str(log_path)})
                except ApiException as e:
                    logger.warning("k8s_log_failed", pod=name, container=cname, error=str(e))

        return {
            "pods_file": str(pods_file),
            "pods_count": len(pods),
            "logs": log_entries,
        }
