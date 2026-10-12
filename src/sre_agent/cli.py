from __future__ import annotations

from pathlib import Path

import typer

from .agent import SREAgent
from .config import Settings
from .connectors.mock import MockTelemetryProvider
from .connectors.real import ClusterTelemetryProvider
from .executors import KubectlExecutor
from .guardrails import ApprovalGate
from .observability import serve_metrics
from .providers.notifiers import ConsoleNotifier, JsonNotifier, SlackWebhookNotifier
from .providers.rules import RuleReasoner
from .state import IncidentStore

app = typer.Typer(help="Investigate SRE incidents with safe, swappable tools.")


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _reasoner(settings: Settings):
    if settings.llm_provider == "rules":
        return RuleReasoner()
    if settings.llm_provider == "openai":
        if not settings.llm_model or not settings.llm_api_key:
            raise typer.BadParameter("SRE_LLM_MODEL and SRE_LLM_API_KEY are required")
        from .providers.openai_reasoner import OpenAIReasoner

        return OpenAIReasoner(settings.llm_model, settings.llm_api_key)
    raise typer.BadParameter(f"Unsupported SRE_LLM_PROVIDER: {settings.llm_provider}")


@app.command()
def investigate(
    scenario: str = typer.Option("crashloop", help="Fixture name for mock mode."),
    real: bool = typer.Option(False, "--real", help="Read from the current Kubernetes context."),
    output: str = typer.Option("console", help="console, json, or slack"),
    metrics: bool = typer.Option(False, help="Expose Prometheus metrics during the run."),
) -> None:
    settings = Settings()
    if metrics:
        serve_metrics(settings.agent_metrics_port)
    telemetry = (
        ClusterTelemetryProvider(settings.namespace, settings.prometheus_url, settings.loki_url)
        if real
        else MockTelemetryProvider(scenario, _root() / "examples" / "incidents")
    )
    if output == "slack":
        if not settings.slack_webhook_url:
            raise typer.BadParameter("SRE_SLACK_WEBHOOK_URL is required for Slack output")
        notifier = SlackWebhookNotifier(settings.slack_webhook_url)
    elif output == "json":
        notifier = JsonNotifier()
    else:
        notifier = ConsoleNotifier()
    agent = SREAgent(
        telemetry,
        _reasoner(settings),
        notifier,
        IncidentStore(settings.incident_db),
        settings.environment,
        settings.namespace,
    )
    if agent.investigate() is None:
        typer.echo("No incident detected.")


@app.command("history")
def history(limit: int = 10) -> None:
    for incident in IncidentStore(Settings().incident_db).list(limit):
        typer.echo(f"{incident.id} {incident.created_at.isoformat()} {incident.summary}")


@app.command()
def remediate(
    incident_id: str,
    action_index: int = typer.Option(0),
    approve: str | None = typer.Option(None, help="Human-provided approval token."),
) -> None:
    settings = Settings()
    store = IncidentStore(settings.incident_db)
    incident = store.get(incident_id)
    if not incident:
        raise typer.BadParameter(f"Incident not found: {incident_id}")
    try:
        action = incident.proposed_actions[action_index]
    except IndexError as exc:
        raise typer.BadParameter("Proposed action does not exist") from exc
    ApprovalGate(settings.dry_run, settings.approval_token).authorize(action, approve)
    result = KubectlExecutor().execute(action)
    typer.echo(result or "Action completed")


if __name__ == "__main__":
    app()
