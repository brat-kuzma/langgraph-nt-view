"""Store and retrieve custom artifacts (Java logs, GC, thread-dump, heapdump, JVM opts, JFR)."""
from pathlib import Path
from typing import Optional
from uuid import uuid4
import structlog

from app.config import settings
from app.db.models import ArtifactKind

logger = structlog.get_logger()


class ArtifactsService:
    """Save engineer-provided artifacts with a structured path and metadata."""

    def __init__(self):
        self.base = settings.artifacts_path()

    def save_custom_artifact(
        self,
        test_id: int,
        kind: str,
        content: bytes,
        display_name: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> tuple[Path, dict]:
        """
        Save raw bytes to storage. Kind should be one of ArtifactKind (custom_*).
        Returns (file_path, metadata to store in DB).
        """
        self.base.mkdir(parents=True, exist_ok=True)
        test_dir = self.base / str(test_id)
        test_dir.mkdir(parents=True, exist_ok=True)
        ext = self._extension_for_kind(kind)
        name = display_name or f"{kind}_{uuid4().hex[:8]}"
        safe_name = "".join(c if c.isalnum() or c in ".-_" else "_" for c in name)[:200]
        path = test_dir / f"{safe_name}{ext}"
        path.write_bytes(content)
        meta = metadata or {}
        meta["kind"] = kind
        meta["original_name"] = display_name
        return path, meta

    def _extension_for_kind(self, kind: str) -> str:
        m = {
            "custom_java_log": ".log",
            "custom_gc": ".log",
            "custom_thread_dump": ".txt",
            "custom_heap_dump": ".hprof",
            "custom_jvm_opts": ".txt",
            "custom_jfr": ".jfr",
            "custom_other": ".bin",
        }
        return m.get(kind, ".bin")

    def read_artifact(self, file_path: str) -> bytes:
        """Read artifact bytes by path (relative to storage or absolute)."""
        p = Path(file_path)
        if not p.is_absolute():
            p = self.base / file_path
        return p.read_bytes()

    def list_test_artifacts(self, test_id: int) -> list[Path]:
        """List all files under test's artifact directory."""
        test_dir = self.base / str(test_id)
        if not test_dir.exists():
            return []
        return list(test_dir.rglob("*"))

    def delete_test_artifacts(self, test_id: int) -> None:
        """Remove test artifact directory and all contents."""
        test_dir = self.base / str(test_id)
        if test_dir.exists():
            for f in test_dir.rglob("*"):
                if f.is_file():
                    f.unlink()
            test_dir.rmdir()
