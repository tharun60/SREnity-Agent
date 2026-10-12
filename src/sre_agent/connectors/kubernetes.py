from __future__ import annotations

from datetime import datetime, timezone

from ..models import Signal


class KubernetesClient:
    """Read-only Kubernetes evidence collector. Import is lazy so the MVP stays lightweight."""

    def __init__(self, namespace: str = "default"):
        from kubernetes import client, config

        try:
            config.load_incluster_config()
        except config.ConfigException:
            config.load_kube_config()
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()
        self.namespace = namespace

    def events(self) -> list[Signal]:
        events = self.core.list_namespaced_event(self.namespace).items
        return [
            Signal(
                source="kubernetes",
                kind="event",
                message=e.message or e.reason or "Kubernetes event",
                timestamp=e.last_timestamp or e.event_time or datetime.now(timezone.utc),
                labels={
                    "namespace": self.namespace,
                    "object": e.involved_object.name or "unknown",
                    "reason": e.reason or "unknown",
                },
            )
            for e in events
        ]

    def pods(self) -> list[Signal]:
        pods = self.core.list_namespaced_pod(self.namespace).items
        result: list[Signal] = []
        for pod in pods:
            restarts = sum(cs.restart_count for cs in (pod.status.container_statuses or []))
            result.append(
                Signal(
                    source="kubernetes",
                    kind="pod_status",
                    message=f"pod={pod.metadata.name} phase={pod.status.phase} restarts={restarts}",
                    labels={"namespace": self.namespace, "pod": pod.metadata.name},
                    value=float(restarts),
                )
            )
        return result

    def logs(self, pod: str, container: str | None = None, tail_lines: int = 200) -> list[Signal]:
        text = self.core.read_namespaced_pod_log(
            pod, self.namespace, container=container, tail_lines=tail_lines, timestamps=True
        )
        return [
            Signal(
                source="kubernetes",
                kind="log",
                message=line,
                labels={"namespace": self.namespace, "pod": pod},
            )
            for line in text.splitlines()
        ]

