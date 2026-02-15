"""Pydantic schemas for API."""
from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, Field


class GrafanaSource(BaseModel):
    name: str
    url: str
    token: str


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    grafana_sources: Optional[List[dict]] = None
    k8s_config: Optional[dict] = None
    llm_type: str = "ollama"
    llm_model: str = "qwen2.5vl:7b"
    llm_api_key: Optional[str] = None


class ProjectRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    grafana_sources: Optional[List[dict]] = None
    k8s_config: Optional[dict] = None
    llm_type: str
    llm_model: str
    created_at: datetime

    class Config:
        from_attributes = True


class TestCreate(BaseModel):
    project_id: int
    test_type: str = Field(..., description="max_search | max_confirmation | reliability | destructive")
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    system_prompt: Optional[str] = None


class TestRead(BaseModel):
    id: int
    project_id: int
    test_type: str
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    system_prompt: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArtifactRead(BaseModel):
    id: int
    test_id: int
    kind: str
    display_name: Optional[str] = None
    file_path: Optional[str] = None
    metadata_: Optional[dict] = Field(None, serialization_alias="metadata")
    created_at: datetime

    class Config:
        from_attributes = True


class ReportRead(BaseModel):
    id: int
    test_id: int
    report_text: str
    pdf_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
