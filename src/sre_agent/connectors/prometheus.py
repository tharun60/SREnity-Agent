from __future__ import annotations

import httpx

from ..models import Signal


class PrometheusClient:
    def __init__(self, base_url: str, timeout: float = 10):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def query(self, promql: str, kind: str = "metric") -> list[Signal]:
        response = httpx.get(
            f"{self.base_url}/api/v1/query", params={"query": promql}, timeout=self.timeout
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "success":
            raise RuntimeError(f"Prometheus query failed: {payload}")
        signals = []
        for row in payload["data"]["result"]:
            timestamp, value = row["value"]
            signals.append(
                Signal(
                    source="prometheus",
                    kind=kind,
                    message=f"{promql} = {value}",
                    timestamp=timestamp,
                    labels=row.get("metric", {}),
                    value=float(value),
                    raw={"query": promql},
                )
            )
        return signals

