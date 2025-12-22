"""Unit tests for GitHub Actions module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from claude_victor.github.actions import ActionsManager, WorkflowRun


@pytest.fixture
def mock_client():
    """Create a mock GitHubClient."""
    with patch("claude_victor.github.actions.GitHubClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestWorkflowRun:
    """Tests for WorkflowRun dataclass."""

    def test_create_workflow_run(self):
        """Verify WorkflowRun creation."""
        run = WorkflowRun(
            id=12345,
            name="CI",
            status="completed",
            conclusion="success",
            url="https://github.com/owner/repo/actions/runs/12345",
            head_branch="main",
            event="push",
        )

        assert run.id == 12345
        assert run.status == "completed"
        assert run.conclusion == "success"


class TestActionsManager:
    """Tests for ActionsManager class."""

    def test_trigger_workflow(self, mock_client):
        """Verify triggering a workflow."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = ActionsManager(client=mock_client)
        result = manager.trigger_workflow("ci.yml")

        call_args = mock_client.run_command.call_args[0][0]
        assert "workflow" in call_args
        assert "run" in call_args
        assert "ci.yml" in call_args
        assert result is True

    def test_trigger_workflow_with_ref(self, mock_client):
        """Verify triggering workflow on specific ref."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = ActionsManager(client=mock_client)
        manager.trigger_workflow("ci.yml", ref="develop")

        call_args = mock_client.run_command.call_args[0][0]
        assert "--ref" in call_args
        assert "develop" in call_args

    def test_trigger_workflow_with_inputs(self, mock_client):
        """Verify triggering workflow with inputs."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = ActionsManager(client=mock_client)
        manager.trigger_workflow(
            "deploy.yml",
            inputs={"environment": "staging", "version": "1.0.0"},
        )

        call_args = mock_client.run_command.call_args[0][0]
        assert "-f" in call_args
        assert "environment=staging" in call_args
        assert "version=1.0.0" in call_args

    def test_get_workflow_run(self, mock_client):
        """Verify getting workflow run details."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "databaseId": 12345,
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "url": "https://github.com/owner/repo/actions/runs/12345",
                "headBranch": "main",
                "event": "push",
            })
        )

        manager = ActionsManager(client=mock_client)
        run = manager.get_workflow_run(12345)

        call_args = mock_client.run_command.call_args[0][0]
        assert "run" in call_args
        assert "view" in call_args
        assert "12345" in call_args
        assert run.id == 12345
        assert run.status == "completed"

    def test_get_workflow_status(self, mock_client):
        """Verify getting workflow status."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "databaseId": 12345,
                "name": "CI",
                "status": "in_progress",
                "conclusion": None,
                "url": "https://github.com/owner/repo/actions/runs/12345",
                "headBranch": "feature",
                "event": "pull_request",
            })
        )

        manager = ActionsManager(client=mock_client)
        status = manager.get_workflow_status(12345)

        assert status == "in_progress"

    def test_list_runs(self, mock_client):
        """Verify listing workflow runs."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps([
                {
                    "databaseId": 1,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "success",
                    "url": "https://github.com/owner/repo/actions/runs/1",
                    "headBranch": "main",
                    "event": "push",
                },
                {
                    "databaseId": 2,
                    "name": "CI",
                    "status": "completed",
                    "conclusion": "failure",
                    "url": "https://github.com/owner/repo/actions/runs/2",
                    "headBranch": "feature",
                    "event": "pull_request",
                },
            ])
        )

        manager = ActionsManager(client=mock_client)
        runs = manager.list_runs()

        assert len(runs) == 2
        assert runs[0].conclusion == "success"
        assert runs[1].conclusion == "failure"

    def test_list_runs_with_filters(self, mock_client):
        """Verify listing runs with filters."""
        mock_client.run_command.return_value = MagicMock(stdout="[]")

        manager = ActionsManager(client=mock_client)
        manager.list_runs(
            workflow="ci.yml",
            branch="main",
            status="completed",
            limit=5,
        )

        call_args = mock_client.run_command.call_args[0][0]
        assert "--workflow" in call_args
        assert "ci.yml" in call_args
        assert "--branch" in call_args
        assert "main" in call_args
        assert "--status" in call_args
        assert "completed" in call_args
        assert "--limit" in call_args
        assert "5" in call_args

    def test_cancel_run(self, mock_client):
        """Verify cancelling a run."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = ActionsManager(client=mock_client)
        result = manager.cancel_run(12345)

        call_args = mock_client.run_command.call_args[0][0]
        assert "cancel" in call_args
        assert "12345" in call_args
        assert result is True

    def test_rerun(self, mock_client):
        """Verify re-running a workflow."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = ActionsManager(client=mock_client)
        result = manager.rerun(12345)

        call_args = mock_client.run_command.call_args[0][0]
        assert "rerun" in call_args
        assert "12345" in call_args
        assert result is True

    def test_rerun_failed_only(self, mock_client):
        """Verify re-running only failed jobs."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = ActionsManager(client=mock_client)
        manager.rerun(12345, failed_only=True)

        call_args = mock_client.run_command.call_args[0][0]
        assert "--failed" in call_args

    def test_list_workflows(self, mock_client):
        """Verify listing workflows."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps([
                {"name": "CI", "id": 1, "state": "active"},
                {"name": "Deploy", "id": 2, "state": "active"},
            ])
        )

        manager = ActionsManager(client=mock_client)
        workflows = manager.list_workflows()

        assert len(workflows) == 2
        assert workflows[0]["name"] == "CI"
