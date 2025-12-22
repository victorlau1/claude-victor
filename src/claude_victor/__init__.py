"""Claude-Victor: Claude Code workflow system with GitHub integration and enforced planning."""

__version__ = "1.0.0"

from claude_victor.github import client, pr, issues, actions
from claude_victor.memory import plan_store
from claude_victor.workflow import planning

__all__ = [
    "__version__",
    "client",
    "pr",
    "issues",
    "actions",
    "plan_store",
    "planning",
]
