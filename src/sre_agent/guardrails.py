import hmac

from .models import ProposedAction


class ApprovalGate:
    """No action reaches an executor without dry-run and explicit token checks."""

    def __init__(self, dry_run: bool, configured_token: str | None):
        self.dry_run = dry_run
        self.configured_token = configured_token

    def authorize(self, action: ProposedAction, supplied_token: str | None) -> None:
        if self.dry_run:
            raise PermissionError("Write actions are disabled while SRE_DRY_RUN=true")
        if action.requires_approval:
            if not self.configured_token or not supplied_token:
                raise PermissionError("A human approval token is required")
            if not hmac.compare_digest(self.configured_token, supplied_token):
                raise PermissionError("Approval token is invalid")
        if not action.command.startswith(("kubectl rollout undo", "kubectl rollout restart")):
            raise PermissionError("Action is not in the command allowlist")
