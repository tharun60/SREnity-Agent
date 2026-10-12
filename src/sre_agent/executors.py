import subprocess

from .models import ProposedAction


class KubectlExecutor:
    """Tiny, injectable write boundary. The ApprovalGate must be called before this."""

    def execute(self, action: ProposedAction) -> str:
        parts = action.command.split()
        result = subprocess.run(parts, capture_output=True, text=True, check=True, timeout=60)
        return result.stdout.strip()

