from __future__ import annotations

from dataclasses import dataclass

from ..models import Finding, ProposedAction, Signal, ToolCall


@dataclass(frozen=True)
class Pattern:
    title: str
    needles: tuple[str, ...]
    explanation: str
    remediation: tuple[str, ...]
    verification: tuple[str, ...]
    action: tuple[str, str, str] | None = None


PATTERNS = (
    Pattern(
        "Container is repeatedly crashing",
        ("crashloopbackoff", "back-off restarting", "exit code 1"),
        "The workload cannot remain healthy. Correlated restart events and application logs usually "
        "point to a bad configuration, missing dependency, or startup regression.",
        ("Inspect the first fatal log from the previous container instance.", "Compare the active deployment configuration with the last known-good revision.", "Fix the configuration or roll back after approval."),
        ("Pod becomes Ready.", "Restart count stops increasing.", "Error-rate alert clears."),
        ("rollback", "deployment/api", "kubectl rollout undo deployment/api -n {namespace}"),
    ),
    Pattern(
        "Container was OOMKilled",
        ("oomkilled", "out of memory", "memory limit"),
        "The container exceeded its memory limit or the node experienced memory pressure.",
        ("Compare working-set memory to the configured limit.", "Check for a deployment-related memory regression.", "Right-size the limit only after confirming normal demand."),
        ("No new OOMKilled events.", "Memory stays below the limit with headroom."),
        ("restart", "deployment/api", "kubectl rollout restart deployment/api -n {namespace}"),
    ),
    Pattern(
        "Service 5xx spike after deployment",
        ("5xx", "http 500", "new replica", "deployment"),
        "The error increase overlaps a workload change, making a deployment regression likely.",
        ("Compare errors by pod and revision.", "Review the deployment diff and failing request logs.", "Roll back the affected revision after approval."),
        ("5xx rate returns to baseline.", "Synthetic checks pass."),
        ("rollback", "deployment/api", "kubectl rollout undo deployment/api -n {namespace}"),
    ),
    Pattern(
        "DNS resolution failures",
        ("dns", "nxdomain", "temporary failure in name resolution"),
        "Multiple failures resolve to the DNS path rather than the application itself.",
        ("Check CoreDNS health and saturation.", "Verify the queried service name and namespace.", "Inspect NetworkPolicy changes."),
        ("DNS queries succeed from an affected pod.", "Dependency errors clear."),
    ),
    Pattern(
        "CPU saturation",
        ("high cpu", "cpu thrott", "cpu >"),
        "CPU demand or throttling is degrading the workload.",
        ("Compare usage, limits, and throttling by container.", "Profile hot paths or scale replicas.", "Validate HPA behavior before changing limits."),
        ("CPU and throttling return to baseline.", "Latency SLO recovers."),
    ),
    Pattern(
        "Upstream dependency latency",
        ("dependency", "upstream", "timeout", "latency"),
        "Latency and timeout evidence points to an upstream dependency as the initiating fault.",
        ("Break latency down by dependency and route.", "Check the upstream service's saturation and recent changes.", "Use bounded retries or failover if already designed."),
        ("Dependency latency returns to baseline.", "Timeout and retry rates recover."),
    ),
)


class RuleReasoner:
    """Deterministic baseline: auditable, testable, and useful without an LLM."""

    TOOL_ORDER = ("get_kubernetes_events", "get_pod_statuses", "query_prometheus", "query_logs")

    def next_tool(self, signals: list[Signal], used_tools: set[str]) -> ToolCall | None:
        for tool in self.TOOL_ORDER:
            if tool not in used_tools:
                args = {}
                if tool == "query_prometheus":
                    args = {"query": 'sum(rate(http_requests_total{status=~"5.."}[5m]))'}
                elif tool == "query_logs":
                    args = {"query": '{namespace="default"} |~ "error|fatal|timeout"'}
                return ToolCall(tool=tool, arguments=args, rationale="Collect independent evidence")
        return None

    def _score(self, pattern: Pattern, text: str) -> tuple[int, list[str]]:
        matched = [needle for needle in pattern.needles if needle in text]
        return len(matched), matched

    def diagnose(self, signals: list[Signal]) -> Finding:
        text = "\n".join(signal.message.lower() for signal in signals)
        ranked = sorted(((self._score(p, text)[0], p) for p in PATTERNS), key=lambda x: x[0], reverse=True)
        score, pattern = ranked[0]
        confidence = min(0.95, 0.45 + 0.12 * score)
        evidence = [s.message for s in signals if any(n in s.message.lower() for n in pattern.needles)][:6]
        if score == 0:
            return Finding(
                title="Insufficient evidence for a specific root cause",
                confidence=0.25,
                explanation="The collected signals do not match a known baseline pattern.",
                evidence=[s.message for s in signals[:5]],
                remediation=["Inspect the raw evidence and expand data collection."],
                verification=["Confirm the triggering symptom has recovered."],
            )
        return Finding(
            title=pattern.title,
            confidence=confidence,
            explanation=pattern.explanation,
            evidence=evidence,
            remediation=list(pattern.remediation),
            verification=list(pattern.verification),
        )

    def propose_actions(self, finding: Finding, signals: list[Signal]) -> list[ProposedAction]:
        pattern = next((p for p in PATTERNS if p.title == finding.title), None)
        if not pattern or not pattern.action:
            return []
        action, target, command = pattern.action
        namespace = next((s.labels.get("namespace") for s in signals if s.labels.get("namespace")), "default")
        return [ProposedAction(action=action, target=target, command=command.format(namespace=namespace))]

