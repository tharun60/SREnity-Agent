from prometheus_client import Counter, Histogram, start_http_server

INVESTIGATIONS = Counter("sre_agent_investigations_total", "Investigations", ["status"])
TOOL_CALLS = Counter("sre_agent_tool_calls_total", "Evidence tool calls", ["tool", "status"])
INVESTIGATION_SECONDS = Histogram("sre_agent_investigation_duration_seconds", "Investigation latency")


def serve_metrics(port: int) -> None:
    start_http_server(port)

