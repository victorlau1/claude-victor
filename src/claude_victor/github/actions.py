"""GitHub Actions management using GitHub CLI."""

import json
from dataclasses import dataclass
from typing import Optional

from claude_victor.github.client import GitHubClient


@dataclass
class WorkflowRun:
    """Represents a GitHub Actions workflow run."""

    id: int
    name: str
    status: str
    conclusion: Optional[str]
    url: str
    head_branch: str
    event: str


class ActionsManager:
    """Manage GitHub Actions via gh CLI."""

    def __init__(self, client: Optional[GitHubClient] = None):
        """Initialize Actions manager.

        Args:
            client: Optional GitHubClient instance. Creates new one if not provided.
        """
        self.client = client or GitHubClient()

    def trigger_workflow(
        self,
        workflow: str,
        ref: str = "main",
        inputs: Optional[dict] = None,
    ) -> bool:
        """Trigger a workflow dispatch event.

        Args:
            workflow: Workflow file name or ID
            ref: Git ref (branch or tag) to run workflow on
            inputs: Optional workflow input parameters

        Returns:
            True if workflow triggered successfully
        """
        args = ["workflow", "run", workflow, "--ref", ref]

        if inputs:
            for key, value in inputs.items():
                args.extend(["-f", f"{key}={value}"])

        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def get_workflow_run(self, run_id: int) -> WorkflowRun:
        """Get details of a specific workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            WorkflowRun object
        """
        args = [
            "run", "view", str(run_id),
            "--json", "databaseId,name,status,conclusion,url,headBranch,event",
        ]

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return WorkflowRun(
            id=data["databaseId"],
            name=data["name"],
            status=data["status"],
            conclusion=data.get("conclusion"),
            url=data["url"],
            head_branch=data["headBranch"],
            event=data["event"],
        )

    def get_workflow_status(self, run_id: int) -> str:
        """Get the status of a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            Status string (e.g., 'completed', 'in_progress', 'queued')
        """
        run = self.get_workflow_run(run_id)
        return run.status

    def list_runs(
        self,
        workflow: Optional[str] = None,
        branch: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> list[WorkflowRun]:
        """List workflow runs.

        Args:
            workflow: Filter by workflow name/file
            branch: Filter by branch
            status: Filter by status ('completed', 'in_progress', 'queued')
            limit: Maximum number of runs to return

        Returns:
            List of WorkflowRun objects
        """
        args = [
            "run", "list",
            "--limit", str(limit),
            "--json", "databaseId,name,status,conclusion,url,headBranch,event",
        ]

        if workflow:
            args.extend(["--workflow", workflow])

        if branch:
            args.extend(["--branch", branch])

        if status:
            args.extend(["--status", status])

        result = self.client.run_command(args)
        data = json.loads(result.stdout)

        return [
            WorkflowRun(
                id=run["databaseId"],
                name=run["name"],
                status=run["status"],
                conclusion=run.get("conclusion"),
                url=run["url"],
                head_branch=run["headBranch"],
                event=run["event"],
            )
            for run in data
        ]

    def watch_run(self, run_id: int) -> WorkflowRun:
        """Watch a workflow run until completion.

        Args:
            run_id: Workflow run ID

        Returns:
            Final WorkflowRun object after completion
        """
        args = ["run", "watch", str(run_id)]
        self.client.run_command(args)
        return self.get_workflow_run(run_id)

    def cancel_run(self, run_id: int) -> bool:
        """Cancel a workflow run.

        Args:
            run_id: Workflow run ID

        Returns:
            True if cancelled successfully
        """
        args = ["run", "cancel", str(run_id)]
        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def rerun(self, run_id: int, failed_only: bool = False) -> bool:
        """Re-run a workflow.

        Args:
            run_id: Workflow run ID
            failed_only: Only re-run failed jobs

        Returns:
            True if re-run triggered successfully
        """
        args = ["run", "rerun", str(run_id)]

        if failed_only:
            args.append("--failed")

        result = self.client.run_command(args, check=False)
        return result.returncode == 0

    def list_workflows(self) -> list[dict]:
        """List all workflows in the repository.

        Returns:
            List of workflow dictionaries with 'name', 'id', 'state'
        """
        args = ["workflow", "list", "--json", "name,id,state"]

        result = self.client.run_command(args)
        return json.loads(result.stdout)
