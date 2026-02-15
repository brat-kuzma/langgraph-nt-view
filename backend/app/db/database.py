"""Database session and initialization."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import settings
from app.db.models import Base

_connect_args = {}
_engine_kw = {"echo": settings.debug}
if settings.database_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
else:
    _engine_kw["pool_pre_ping"] = True

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args if _connect_args else None,
    **_engine_kw,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables and ensure storage directories exist."""
    Base.metadata.create_all(bind=engine)
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    settings.artifacts_path().mkdir(parents=True, exist_ok=True)
    settings.reports_path().mkdir(parents=True, exist_ok=True)
    settings.grafana_snapshots_path().mkdir(parents=True, exist_ok=True)
