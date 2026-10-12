from __future__ import annotations

from ..models import Signal, ToolCall
from .kubernetes import KubernetesClient
from .loki import LokiClient
from .prometheus import PrometheusClient


class ClusterTelemetryProvider:
    """Routes agent tool calls to real backends; every operation here is read-only."""

    def __init__(self, namespace: str, prometheus_url: str, loki_url: str):
        self.k8s = KubernetesClient(namespace)
        self.prom = PrometheusClient(prometheus_url)
        self.loki = LokiClient(loki_url)
        self.namespace = namespace

    def detect(self) -> list[Signal]:
        return self.k8s.events() + self.k8s.pods()

    def execute(self, call: ToolCall) -> list[Signal]:
        if call.tool == "get_kubernetes_events":
            return self.k8s.events()
        if call.tool == "get_pod_statuses":
            return self.k8s.pods()
        if call.tool == "query_prometheus":
            return self.prom.query(str(call.arguments["query"]))
        if call.tool == "query_logs":
            if "pod" in call.arguments:
                return self.k8s.logs(str(call.arguments["pod"]))
            return self.loki.query(str(call.arguments["query"]))
        raise ValueError(f"Unsupported read-only tool: {call.tool}")
