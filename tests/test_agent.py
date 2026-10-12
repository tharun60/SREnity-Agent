from pathlib import Path

from sre_agent.agent import SREAgent
from sre_agent.connectors.mock import MockTelemetryProvider
from sre_agent.providers.rules import RuleReasoner
from sre_agent.state import IncidentStore


class CaptureNotifier:
    def __init__(self):
        self.incident = None

    def send(self, incident):
        self.incident = incident


def fixture_dir() -> Path:
    return Path(__file__).parents[1] / "examples" / "incidents"


def test_crashloop_investigation_persists_and_reports(tmp_path):
    notifier = CaptureNotifier()
    store = IncidentStore(tmp_path / "incidents.jsonl")
    agent = SREAgent(
        MockTelemetryProvider("crashloop", fixture_dir()),
        RuleReasoner(),
        notifier,
        store,
        "test",
        "default",
    )

    incident = agent.investigate()

    assert incident is not None
    assert incident.finding.title == "Container is repeatedly crashing"
    assert incident.finding.confidence >= 0.8
    assert any("DATABASE_URL" in item for item in incident.finding.evidence)
    assert incident.proposed_actions[0].requires_approval is True
    assert notifier.incident.id == incident.id
    assert store.get(incident.id).id == incident.id


def test_all_fixtures_are_diagnosable(tmp_path):
    for path in fixture_dir().glob("*.json"):
        agent = SREAgent(
            MockTelemetryProvider(path.stem, fixture_dir()),
            RuleReasoner(),
            CaptureNotifier(),
            IncidentStore(tmp_path / f"{path.stem}.jsonl"),
            "test",
            "default",
        )
        incident = agent.investigate()
        assert incident and incident.finding.confidence > 0.4, path.name

