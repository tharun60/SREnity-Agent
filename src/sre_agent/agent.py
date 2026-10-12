from __future__ import annotations

from datetime import datetime, timezone

from .interfaces import Notifier, Reasoner, TelemetryProvider
from .models import Incident, Severity, Signal
from .observability import INVESTIGATIONS, INVESTIGATION_SECONDS, TOOL_CALLS
from .state import IncidentStore


class SREAgent:
    """Observe -> plan a read tool -> gather -> repeat -> diagnose -> report."""

    def __init__(
        self,
        telemetry: TelemetryProvider,
        reasoner: Reasoner,
        notifier: Notifier,
        store: IncidentStore,
        environment: str,
        namespace: str,
        max_steps: int = 4,
    ):
        self.telemetry = telemetry
        self.reasoner = reasoner
        self.notifier = notifier
        self.store = store
        self.environment = environment
        self.namespace = namespace
        self.max_steps = max_steps

    @INVESTIGATION_SECONDS.time()
    def investigate(self) -> Incident | None:
        signals = self.telemetry.detect()
        if not signals:
            INVESTIGATIONS.labels(status="no_issue").inc()
            return None

        incident = Incident(
            environment=self.environment,
            namespace=self.namespace,
            severity=self._severity(signals),
            summary=signals[0].message,
            signals=signals,
            timeline=[self._event("Detection triggered")],
        )
        used_tools: set[str] = set()
        for _ in range(self.max_steps):
            call = self.reasoner.next_tool(incident.signals, used_tools)
            if call is None:
                break
            used_tools.add(call.tool)
            incident.timeline.append(self._event(f"Tool requested: {call.tool} — {call.rationale}"))
            try:
                evidence = self.telemetry.execute(call)
                incident.signals.extend(self._dedupe(incident.signals, evidence))
                TOOL_CALLS.labels(tool=call.tool, status="success").inc()
            except Exception as exc:  # One broken backend should not erase the investigation.
                incident.timeline.append(self._event(f"Tool failed: {call.tool}: {exc}"))
                TOOL_CALLS.labels(tool=call.tool, status="error").inc()

        incident.finding = self.reasoner.diagnose(incident.signals)
        incident.proposed_actions = self.reasoner.propose_actions(incident.finding, incident.signals)
        incident.timeline.append(self._event("Diagnosis and remediation drafted"))
        self.store.save(incident)
        self.notifier.send(incident)
        INVESTIGATIONS.labels(status="reported").inc()
        return incident

    @staticmethod
    def _event(message: str) -> str:
        return f"{datetime.now(timezone.utc).isoformat()} {message}"

    @staticmethod
    def _dedupe(existing: list[Signal], new: list[Signal]) -> list[Signal]:
        keys = {(s.source, s.kind, s.message) for s in existing}
        return [s for s in new if (s.source, s.kind, s.message) not in keys]

    @staticmethod
    def _severity(signals: list[Signal]) -> Severity:
        text = " ".join(s.message.lower() for s in signals)
        if any(token in text for token in ("critical", "crashloop", "oomkilled", "5xx")):
            return Severity.critical
        return Severity.warning

