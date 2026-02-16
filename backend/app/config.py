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

    # Storage for artifacts and reports (привязка к каталогу backend, не к cwd)
    storage_path: Path = Path(__file__).resolve().parent.parent / "storage"
    artifacts_dir_name: str = "artifacts"
    reports_dir_name: str = "reports"
    grafana_snapshots_dir_name: str = "grafana_snapshots"

    # Default LLM (when not overridden by project). Для анализа логов — текстовая модель (qwen2.5:7b).
    # qwen2.5vl:7b — vision, тяжелее, может крашить runner (exit status 2).
    default_llm_type: str = "ollama"
    default_llm_model: str = "qwen2.5:7b"
    ollama_base_url: str = "http://localhost:11434"
    # Ограничение контекста для Ollama (500 при переполнении). ~32k токенов ≈ 35k символов.
    ollama_max_context_chars: int = 35_000

    def artifacts_path(self) -> Path:
        return self.storage_path / self.artifacts_dir_name

    def reports_path(self) -> Path:
        return self.storage_path / self.reports_dir_name

    def grafana_snapshots_path(self) -> Path:
        return self.storage_path / self.grafana_snapshots_dir_name


settings = Settings()
