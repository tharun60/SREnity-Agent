from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from ..connectors.mock import MockTelemetryProvider

mcp = FastMCP("sre-evidence")
FIXTURES = Path(__file__).resolve().parents[3] / "examples" / "incidents"


def _read(scenario: str, key: str) -> list[dict]:
    provider = MockTelemetryProvider(scenario, FIXTURES)
    return [item.model_dump(mode="json") for item in provider._signals(key)]


@mcp.tool()
def detect_incidents(scenario: str = "crashloop") -> list[dict]:
    """Return alert signals for a training scenario."""
    return _read(scenario, "detection")


@mcp.tool()
def get_kubernetes_events(scenario: str = "crashloop") -> list[dict]:
    """Return Kubernetes events. This tool is read-only."""
    return _read(scenario, "get_kubernetes_events")


@mcp.tool()
def get_pod_statuses(scenario: str = "crashloop") -> list[dict]:
    """Return pod and container status. This tool is read-only."""
    return _read(scenario, "get_pod_statuses")


@mcp.tool()
def query_prometheus(scenario: str = "crashloop") -> list[dict]:
    """Return metric evidence for a training scenario."""
    return _read(scenario, "query_prometheus")


@mcp.tool()
def query_logs(scenario: str = "crashloop") -> list[dict]:
    """Return bounded log evidence for a training scenario."""
    return _read(scenario, "query_logs")


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

