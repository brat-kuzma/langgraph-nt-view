"""Configuration from environment."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    app_name: str = "langgraph-nt-view-backend"
    debug: bool = False

    # DB: по умолчанию SQLite (без установки PostgreSQL). Для прода — задать DATABASE_URL (postgresql+psycopg2://...)
    database_url: str = "sqlite:///./ntview.db"

    # Storage for artifacts and reports (local filesystem)
    storage_path: Path = Path("storage")
    artifacts_dir_name: str = "artifacts"
    reports_dir_name: str = "reports"
    grafana_snapshots_dir_name: str = "grafana_snapshots"

    # Default LLM (when not overridden by project)
    default_llm_type: str = "ollama"
    default_llm_model: str = "qwen2.5vl:7b"
    ollama_base_url: str = "http://localhost:11434"

    def artifacts_path(self) -> Path:
        return self.storage_path / self.artifacts_dir_name

    def reports_path(self) -> Path:
        return self.storage_path / self.reports_dir_name

    def grafana_snapshots_path(self) -> Path:
        return self.storage_path / self.grafana_snapshots_dir_name


settings = Settings()
