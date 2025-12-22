"""Issue management using GitHub CLI."""

import json
from dataclasses import dataclass
from typing import Optional

from claude_victor.github.client import GitHubClient


@dataclass
class Issue:
    """Represents a GitHub Issue."""

    number: int
    title: str
    body: str
    state: str
    url: str
    labels: list[str]


class IssueManager:
    """Manage GitHub Issues via gh CLI."""

    def __init__(self, client: Optional[GitHubClient] = None):
        """Initialize Issue manager.

        Args:
            client: Optional GitHubClient instance. Creates new one if not provided.
        """
        self.client = client or GitHubClient()

    def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[list[str]] = None,
        assignees: Optional[list[str]] = None,
    ) -> Issue:
        """Create a new issue.

        Args:
            title: Issue title
            body: Issue description
            labels: Optional list of labels
            assignees: Optional list of assignees

        Returns:
            Created Issue object
        """
        args = [
            "issue", "create",
            "--title", title,
            "--body", body,
        ]

        if labels:
            for label in labels:
                args.extend(["--label", label])

        if assignees:
            for assignee in assignees:
                args.extend(["--assignee", assignee])

        args.extend(["--json", "number,title,body,state,url,labels"])

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return Issue(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            url=data["url"],
            labels=[label["name"] for label in data.get("labels", [])],
        )

    def get_issue(self, issue_number: int) -> Issue:
        """Get issue details.

        Args:
            issue_number: Issue number

        Returns:
            Issue object
        """
        args = [
            "issue", "view", str(issue_number),
            "--json", "number,title,body,state,url,labels",
        ]

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return Issue(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            url=data["url"],
            labels=[label["name"] for label in data.get("labels", [])],
        )

    def close_issue(self, issue_number: int, reason: str = "completed") -> bool:
        """Close an issue.

        Args:
            issue_number: Issue number to close
            reason: Close reason ('completed' or 'not_planned')

        Returns:
            True if closed successfully
        """
        args = ["issue", "close", str(issue_number), "--reason", reason]
        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def reopen_issue(self, issue_number: int) -> bool:
        """Reopen a closed issue.

        Args:
            issue_number: Issue number to reopen

        Returns:
            True if reopened successfully
        """
        args = ["issue", "reopen", str(issue_number)]
        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def add_comment(self, issue_number: int, body: str) -> bool:
        """Add a comment to an issue.

        Args:
            issue_number: Issue number
            body: Comment body

        Returns:
            True if comment added successfully
        """
        args = ["issue", "comment", str(issue_number), "--body", body]
        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def list_issues(
        self,
        state: str = "open",
        labels: Optional[list[str]] = None,
        limit: int = 30,
    ) -> list[Issue]:
        """List issues.

        Args:
            state: Filter by state ('open', 'closed', 'all')
            labels: Filter by labels
            limit: Maximum number of issues to return

        Returns:
            List of Issue objects
        """
        args = [
            "issue", "list",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,body,state,url,labels",
        ]

        if labels:
            for label in labels:
                args.extend(["--label", label])

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return [
            Issue(
                number=issue["number"],
                title=issue["title"],
                body=issue["body"],
                state=issue["state"],
                url=issue["url"],
                labels=[label["name"] for label in issue.get("labels", [])],
            )
            for issue in data
        ]

    def add_labels(self, issue_number: int, labels: list[str]) -> bool:
        """Add labels to an issue.

        Args:
            issue_number: Issue number
            labels: Labels to add

        Returns:
            True if labels added successfully
        """
        args = ["issue", "edit", str(issue_number)]
        for label in labels:
            args.extend(["--add-label", label])

        result = self.client.run_command(args, check=False)
        return result.returncode == 0
