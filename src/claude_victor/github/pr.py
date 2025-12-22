"""Pull Request management using GitHub CLI."""

import json
from dataclasses import dataclass
from typing import Optional

from claude_victor.github.client import GitHubClient


@dataclass
class PullRequest:
    """Represents a GitHub Pull Request."""

    number: int
    title: str
    body: str
    state: str
    head: str
    base: str
    url: str
    draft: bool = False


class PullRequestManager:
    """Manage GitHub Pull Requests via gh CLI."""

    def __init__(self, client: Optional[GitHubClient] = None):
        """Initialize PR manager.

        Args:
            client: Optional GitHubClient instance. Creates new one if not provided.
        """
        self.client = client or GitHubClient()

    def create_pr(
        self,
        title: str,
        body: str,
        base: str = "main",
        head: Optional[str] = None,
        draft: bool = False,
    ) -> PullRequest:
        """Create a new pull request.

        Args:
            title: PR title
            body: PR description
            base: Base branch to merge into (default: main)
            head: Head branch with changes (default: current branch)
            draft: Whether to create as draft PR

        Returns:
            Created PullRequest object
        """
        args = [
            "pr", "create",
            "--title", title,
            "--body", body,
            "--base", base,
        ]

        if head:
            args.extend(["--head", head])

        if draft:
            args.append("--draft")

        args.extend(["--json", "number,title,body,state,headRefName,baseRefName,url,isDraft"])

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            head=data["headRefName"],
            base=data["baseRefName"],
            url=data["url"],
            draft=data.get("isDraft", False),
        )

    def update_pr(
        self,
        pr_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> PullRequest:
        """Update an existing pull request.

        Args:
            pr_number: PR number to update
            title: New title (optional)
            body: New body (optional)

        Returns:
            Updated PullRequest object
        """
        args = ["pr", "edit", str(pr_number)]

        if title:
            args.extend(["--title", title])

        if body:
            args.extend(["--body", body])

        self.client.run_command(args)

        # Fetch updated PR data
        return self.get_pr(pr_number)

    def get_pr(self, pr_number: int) -> PullRequest:
        """Get pull request details.

        Args:
            pr_number: PR number

        Returns:
            PullRequest object
        """
        args = [
            "pr", "view", str(pr_number),
            "--json", "number,title,body,state,headRefName,baseRefName,url,isDraft",
        ]

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return PullRequest(
            number=data["number"],
            title=data["title"],
            body=data["body"],
            state=data["state"],
            head=data["headRefName"],
            base=data["baseRefName"],
            url=data["url"],
            draft=data.get("isDraft", False),
        )

    def merge_pr(
        self,
        pr_number: int,
        method: str = "squash",
        delete_branch: bool = True,
    ) -> bool:
        """Merge a pull request.

        Args:
            pr_number: PR number to merge
            method: Merge method ('merge', 'squash', 'rebase')
            delete_branch: Whether to delete the head branch after merge

        Returns:
            True if merge successful
        """
        args = ["pr", "merge", str(pr_number), f"--{method}"]

        if delete_branch:
            args.append("--delete-branch")

        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def list_prs(self, state: str = "open", limit: int = 30) -> list[PullRequest]:
        """List pull requests.

        Args:
            state: Filter by state ('open', 'closed', 'merged', 'all')
            limit: Maximum number of PRs to return

        Returns:
            List of PullRequest objects
        """
        args = [
            "pr", "list",
            "--state", state,
            "--limit", str(limit),
            "--json", "number,title,body,state,headRefName,baseRefName,url,isDraft",
        ]

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return [
            PullRequest(
                number=pr["number"],
                title=pr["title"],
                body=pr["body"],
                state=pr["state"],
                head=pr["headRefName"],
                base=pr["baseRefName"],
                url=pr["url"],
                draft=pr.get("isDraft", False),
            )
            for pr in data
        ]

    def add_comment(self, pr_number: int, body: str) -> bool:
        """Add a comment to a pull request.

        Args:
            pr_number: PR number
            body: Comment body

        Returns:
            True if comment added successfully
        """
        args = ["pr", "comment", str(pr_number), "--body", body]
        result = self.client.run_command(args, check=False)
        return result.returncode == 0
