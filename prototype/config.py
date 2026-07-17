from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5-coder:7b"

    database_path: str = "data/prototype.db"
    report_dir: str = "reports"

    max_agent_steps: int = 8
    tool_timeout: int = 300

    api_host: str = "127.0.0.1"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

Path(settings.database_path).parent.mkdir(
    parents=True,
    exist_ok=True,
)

Path(settings.report_dir).mkdir(
    parents=True,
    exist_ok=True,
)