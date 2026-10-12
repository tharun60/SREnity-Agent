from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SRE_", env_file=".env", extra="ignore")

    environment: str = "local"
    namespace: str = "default"
    incident_db: Path = Path("data/incidents.jsonl")
    mock_scenario: str = "crashloop"
    dry_run: bool = True
    approval_token: str | None = None
    prometheus_url: str = "http://localhost:9090"
    loki_url: str = "http://localhost:3100"
    slack_webhook_url: str | None = None
    llm_provider: str = "rules"
    llm_model: str | None = None
    llm_api_key: str | None = None
    agent_metrics_port: int = 9464

