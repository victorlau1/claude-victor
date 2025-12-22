"""GitHub integration module using gh CLI."""

from claude_victor.github.client import GitHubClient
from claude_victor.github.pr import PullRequestManager
from claude_victor.github.issues import IssueManager
from claude_victor.github.actions import ActionsManager

__all__ = [
    "GitHubClient",
    "PullRequestManager",
    "IssueManager",
    "ActionsManager",
]
