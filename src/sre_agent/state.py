import json
from pathlib import Path

from .models import Incident


class IncidentStore:
    def __init__(self, path: Path):
        self.path = path

    def save(self, incident: Incident) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a") as stream:
            stream.write(incident.model_dump_json() + "\n")

    def list(self, limit: int = 20) -> list[Incident]:
        if not self.path.exists():
            return []
        rows = self.path.read_text().splitlines()[-limit:]
        return [Incident.model_validate(json.loads(row)) for row in rows]

    def get(self, incident_id: str) -> Incident | None:
        return next((item for item in reversed(self.list(10_000)) if item.id == incident_id), None)

