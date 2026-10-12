from __future__ import annotations

import json

import httpx

from ..models import Incident


def format_report(incident: Incident) -> str:
    finding = incident.finding
    lines = [
        f"[{incident.severity.value.upper()}] {incident.summary}",
        f"Incident: {incident.id} | {incident.environment}/{incident.namespace}",
    ]
    if finding:
        lines.extend(
            [
                f"Likely cause ({finding.confidence:.0%}): {finding.title}",
                finding.explanation,
                "Evidence:",
                *[f"- {item}" for item in finding.evidence],
                "Recommended remediation:",
                *[f"{i}. {item}" for i, item in enumerate(finding.remediation, 1)],
                "Verify:",
                *[f"- {item}" for item in finding.verification],
            ]
        )
    if incident.proposed_actions:
        lines.append("Approval required before write action:")
        lines.extend(f"- {a.command}" for a in incident.proposed_actions)
    return "\n".join(lines)


class ConsoleNotifier:
    def send(self, incident: Incident) -> None:
        print(format_report(incident))


class SlackWebhookNotifier:
    """Uses an incoming webhook; a Teams adapter can implement the same send method."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send(self, incident: Incident) -> None:
        response = httpx.post(self.webhook_url, json={"text": format_report(incident)}, timeout=10)
        response.raise_for_status()


class JsonNotifier:
    def send(self, incident: Incident) -> None:
        print(json.dumps(incident.model_dump(mode="json"), indent=2))

