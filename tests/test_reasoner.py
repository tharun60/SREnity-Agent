from sre_agent.models import Signal
from sre_agent.providers.rules import RuleReasoner


def test_unknown_signal_has_low_confidence():
    finding = RuleReasoner().diagnose([Signal(source="x", kind="x", message="unfamiliar")])
    assert finding.confidence == 0.25
    assert "Insufficient" in finding.title

