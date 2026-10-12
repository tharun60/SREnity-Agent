from __future__ import annotations

import json
from pathlib import Path

from ..models import Signal, ToolCall


class MockTelemetryProvider:
    """Fixture-backed connector used to learn the agent loop without infrastructure."""

    def __init__(self, scenario: str, fixture_dir: Path):
        path = fixture_dir / f"{scenario}.json"
        if not path.exists():
            available = ", ".join(sorted(p.stem for p in fixture_dir.glob("*.json")))
            raise ValueError(f"Unknown scenario {scenario!r}. Available: {available}")
        self.payload = json.loads(path.read_text())

    def _signals(self, key: str) -> list[Signal]:
        return [Signal.model_validate(item) for item in self.payload.get(key, [])]

    def detect(self) -> list[Signal]:
        return self._signals("detection")

    def execute(self, call: ToolCall) -> list[Signal]:
        return self._signals(call.tool)

