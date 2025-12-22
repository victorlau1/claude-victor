"""Integration tests for GitHub integration.

These tests verify the integration between components.
Some tests require actual GitHub CLI authentication and are marked with @pytest.mark.integration.
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from claude_victor.github.client import GitHubClient, GitHubClientError
from claude_victor.github.pr import PullRequestManager
from claude_victor.github.issues import IssueManager
from claude_victor.github.actions import ActionsManager


class TestGitHubClientIntegration:
    """Integration tests for GitHubClient."""

    def test_client_initialization_with_mock(self):
        """Test client initialization without actual gh CLI."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/gh"
            client = GitHubClient()
            assert client is not None

    @pytest.mark.integration
    def test_check_auth_status(self):
        """Test actual auth status check (requires gh to be installed)."""
        try:
            client = GitHubClient()
            # This will return True or False depending on auth status
            result = client.check_auth()
            assert isinstance(result, bool)
        except GitHubClientError:
            pytest.skip("GitHub CLI not installed")


class TestPRManagerIntegration:
    """Integration tests for PullRequestManager."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client for integration tests."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/gh"
            client = MagicMock(spec=GitHubClient)
            yield client

    def test_pr_manager_with_client(self, mock_client):
        """Test PR manager works with provided client."""
        manager = PullRequestManager(client=mock_client)
        assert manager.client is mock_client

    def test_full_pr_workflow_mock(self, mock_client):
        """Test complete PR workflow with mocked responses."""
        # Setup mock responses
        mock_client.run_command.side_effect = [
            # create_pr response
            MagicMock(stdout=json.dumps({
                "number": 1,
                "title": "Test PR",
                "body": "Test body",
                "state": "open",
                "headRefName": "feature",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/1",
                "isDraft": False,
            })),
            # add_comment response
            MagicMock(returncode=0),
            # merge response
            MagicMock(returncode=0),
        ]

        manager = PullRequestManager(client=mock_client)

        # Create PR
        pr = manager.create_pr(title="Test PR", body="Test body")
        assert pr.number == 1
        assert pr.title == "Test PR"

        # Add comment
        result = manager.add_comment(1, "LGTM!")
        assert result is True

        # Merge
        result = manager.merge_pr(1)
        assert result is True

    @pytest.mark.integration
    def test_list_prs_real(self):
        """Test listing PRs on a real repo (requires auth)."""
        try:
            client = GitHubClient()
            if not client.check_auth():
                pytest.skip("Not authenticated with GitHub")

            manager = PullRequestManager(client=client)
            # This might return empty list if no PRs exist
            prs = manager.list_prs(limit=5)
            assert isinstance(prs, list)
        except GitHubClientError:
            pytest.skip("GitHub CLI not installed or not in a repo")


class TestIssueManagerIntegration:
    """Integration tests for IssueManager."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/gh"
            client = MagicMock(spec=GitHubClient)
            yield client

    def test_issue_to_pr_workflow(self, mock_client):
        """Test creating issue and referencing in PR."""
        # Create issue
        mock_client.run_command.side_effect = [
            MagicMock(stdout=json.dumps({
                "number": 10,
                "title": "Bug: Something broken",
                "body": "Details here",
                "state": "open",
                "url": "https://github.com/owner/repo/issues/10",
                "labels": [{"name": "bug"}],
            })),
            # Close issue
            MagicMock(returncode=0),
        ]

        issue_manager = IssueManager(client=mock_client)

        # Create issue
        issue = issue_manager.create_issue(
            title="Bug: Something broken",
            body="Details here",
            labels=["bug"],
        )
        assert issue.number == 10

        # Close issue (simulating PR merge)
        result = issue_manager.close_issue(10)
        assert result is True


class TestActionsManagerIntegration:
    """Integration tests for ActionsManager."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/gh"
            client = MagicMock(spec=GitHubClient)
            yield client

    def test_workflow_trigger_and_watch(self, mock_client):
        """Test triggering and watching a workflow."""
        mock_client.run_command.side_effect = [
            # Trigger workflow
            MagicMock(returncode=0),
            # List runs to get run ID
            MagicMock(stdout=json.dumps([{
                "databaseId": 12345,
                "name": "CI",
                "status": "completed",
                "conclusion": "success",
                "url": "https://github.com/owner/repo/actions/runs/12345",
                "headBranch": "main",
                "event": "workflow_dispatch",
            }])),
        ]

        manager = ActionsManager(client=mock_client)

        # Trigger workflow
        result = manager.trigger_workflow("ci.yml")
        assert result is True

        # List runs
        runs = manager.list_runs(workflow="ci.yml", limit=1)
        assert len(runs) == 1
        assert runs[0].conclusion == "success"


class TestCrossComponentIntegration:
    """Integration tests across multiple components."""

    def test_client_shared_across_managers(self):
        """Test that managers can share a client instance."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/gh"

            client = MagicMock(spec=GitHubClient)
            client.run_command.return_value = MagicMock(stdout="[]")

            pr_manager = PullRequestManager(client=client)
            issue_manager = IssueManager(client=client)
            actions_manager = ActionsManager(client=client)

            # All managers should use the same client
            assert pr_manager.client is client
            assert issue_manager.client is client
            assert actions_manager.client is client

    def test_error_propagation(self):
        """Test that errors propagate correctly between components."""
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/local/bin/gh"

            client = MagicMock(spec=GitHubClient)
            client.run_command.side_effect = GitHubClientError("API rate limit exceeded")

            pr_manager = PullRequestManager(client=client)

            with pytest.raises(GitHubClientError) as exc_info:
                pr_manager.create_pr(title="Test", body="Body")

            assert "rate limit" in str(exc_info.value)
