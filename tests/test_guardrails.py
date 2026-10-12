import pytest

from sre_agent.guardrails import ApprovalGate
from sre_agent.models import ProposedAction


ACTION = ProposedAction(
    action="rollback",
    target="deployment/api",
    command="kubectl rollout undo deployment/api -n default",
)


def test_dry_run_always_blocks():
    with pytest.raises(PermissionError, match="disabled"):
        ApprovalGate(True, "secret").authorize(ACTION, "secret")


def test_token_is_required_and_checked():
    gate = ApprovalGate(False, "secret")
    with pytest.raises(PermissionError, match="invalid"):
        gate.authorize(ACTION, "wrong")
    gate.authorize(ACTION, "secret")


def test_allowlist_blocks_arbitrary_commands():
    unsafe = ACTION.model_copy(update={"command": "kubectl delete namespace production"})
    with pytest.raises(PermissionError, match="allowlist"):
        ApprovalGate(False, "secret").authorize(unsafe, "secret")

