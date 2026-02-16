"""PostgreSQL models for projects, tests, artifacts, reports."""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import enum


class Base(DeclarativeBase):
    pass


class TestType(str, enum.Enum):
    max_search = "max_search"           # поиск максимума
    max_confirmation = "max_confirmation"  # подтверждение максимума
    reliability = "reliability"         # надежность
    destructive = "destructive"          # деструктивный тест


class LLMType(str, enum.Enum):
    ollama = "ollama"
    gigachat = "gigachat"
    openai = "openai"


class ArtifactKind(str, enum.Enum):
    grafana_slice = "grafana_slice"
    k8s_pods = "k8s_pods"
    k8s_logs = "k8s_logs"
    custom_java_log = "custom_java_log"
    custom_gc = "custom_gc"
    custom_thread_dump = "custom_thread_dump"
    custom_heap_dump = "custom_heap_dump"
    custom_jvm_opts = "custom_jvm_opts"
    custom_jfr = "custom_jfr"
    custom_other = "custom_other"


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Grafana: список источников (url + token) в JSON
    # [{"name": "business", "url": "https://grafana.example.com", "token": "..."}, ...]
    grafana_sources: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=list)

    # Kubernetes: kubeconfig base64 или token + server
    k8s_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # {"kubeconfig_base64": "..."} или {"server": "https://...", "token": "..."}

    # LLM для агента
    llm_type: Mapped[str] = mapped_column(String(32), default=LLMType.ollama.value)
    llm_model: Mapped[str] = mapped_column(String(128), default="qwen2.5:7b")
    llm_api_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tests: Mapped[list["Test"]] = relationship("Test", back_populates="project", cascade="all, delete-orphan")


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)

    test_type: Mapped[str] = mapped_column(String(32), nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(32), default="pending")
    # pending | collecting | analyzing | done | failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="tests")
    artifacts: Mapped[list["Artifact"]] = relationship("Artifact", back_populates="test", cascade="all, delete-orphan")
    report: Mapped[Optional["Report"]] = relationship("Report", back_populates="test", uselist=False, cascade="all, delete-orphan")


class Artifact(Base):
    __tablename__ = "artifacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)

    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    test: Mapped["Test"] = relationship("Test", back_populates="artifacts")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, unique=True)

    report_text: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    # Снимок списка артефактов на момент формирования отчёта (id, kind, display_name, file_path)
    artifacts_used_snapshot: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    test: Mapped["Test"] = relationship("Test", back_populates="report")
