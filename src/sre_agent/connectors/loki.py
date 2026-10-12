from __future__ import annotations

from datetime import datetime, timezone

import httpx

from ..models import Signal


class LokiClient:
    def __init__(self, base_url: str, timeout: float = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def query(self, logql: str, limit: int = 100) -> list[Signal]:
        response = httpx.get(
            f"{self.base_url}/loki/api/v1/query_range",
            params={"query": logql, "limit": limit, "direction": "backward"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        streams = response.json().get("data", {}).get("result", [])
        return [
            Signal(
                source="loki",
                kind="log",
                message=line,
                timestamp=datetime.fromtimestamp(int(ns) / 1e9, tz=timezone.utc),
                labels=stream.get("stream", {}),
            )
            for stream in streams
            for ns, line in stream.get("values", [])
        ]

