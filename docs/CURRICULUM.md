# Staged learning curriculum

Each phase has a runnable checkpoint and a question to answer before moving on.

## 1. Agent loop and mocked tools

Run `sre-agent investigate --scenario crashloop`. Trace `SREAgent.investigate`: an alert starts the loop, the reasoner selects bounded read tools, evidence accumulates, and a diagnosis is emitted. Swap fixture names to see how evidence changes the result.

**Exercise:** add `image_pull_failure.json` and a matching deterministic pattern. Why is deterministic reasoning valuable as an LLM fallback?

## 2. MCP tool server

Install `.[mcp]`, run `sre-mcp`, and inspect the tools using an MCP inspector/client. MCP standardizes discovery, schemas, invocation, and results; it does not replace authorization or domain guardrails.

**Exercise:** write a small MCP client that calls `detect_incidents`, then `query_logs`. Compare remote tool calling with the in-process connector.

## 3. Real connectors

Install `.[kubernetes]`, select a safe kube context, then run `sre-agent investigate --real`. Kubernetes RBAC should grant only get/list/watch for pods, events, deployments, replicasets, and logs. Prometheus and Loki endpoints come from environment variables.

**Exercise:** substitute a kubectl-based log adapter for Loki without changing the agent loop.

## 4. Correlation and root cause

Study `RuleReasoner`. Add time-window correlation, topology edges, revision metadata, and negative evidence. Keep the deterministic layer even when adding an LLM: let the model explain and prioritize structured evidence, not invent raw facts.

**Exercise:** score competing hypotheses and penalize evidence outside the incident window.

## 5. ChatOps

Set a Slack incoming webhook and use `--output slack`. The notifier is an interface: implement `TeamsNotifier.send` with the same incident model.

**Exercise:** add deduplication keys and update one incident thread instead of posting repeatedly.

## 6. Approval-gated remediation

The default is dry-run. `remediate` requires `SRE_DRY_RUN=false`, an exact human token, and an allowlisted command. In production, replace the shared token with an approval record tied to user identity, action hash, incident, and expiry.

**Exercise:** implement a two-person approval store and post the approval result back to ChatOps.

## 7. Evaluation and hardening

Use the fixture suite as a seed evaluation set. Measure detection recall, root-cause top-k accuracy, evidence citation coverage, unsafe-action rate, latency, and cost. Add replay tests, fault injection, rate limits, audit logs, secret redaction, tenant isolation, HA leadership, and SLOs for the agent.

**Capstone:** deploy into a lab cluster with read-only RBAC, inject failures, and compare the report to a human-written postmortem.

