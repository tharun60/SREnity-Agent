from __future__ import annotations

from typing import Protocol

from .models import Finding, Incident, ProposedAction, Signal, ToolCall


class TelemetryProvider(Protocol):
    def detect(self) -> list[Signal]: ...
    def execute(self, call: ToolCall) -> list[Signal]: ...


class Reasoner(Protocol):
    def next_tool(self, signals: list[Signal], used_tools: set[str]) -> ToolCall | None: ...
    def diagnose(self, signals: list[Signal]) -> Finding: ...
    def propose_actions(self, finding: Finding, signals: list[Signal]) -> list[ProposedAction]: ...


class Notifier(Protocol):
    def send(self, incident: Incident) -> None: ...


class ActionExecutor(Protocol):
    def execute(self, action: ProposedAction) -> str: ...
