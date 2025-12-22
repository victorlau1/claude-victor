"""Unit tests for GitHub client module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from claude_victor.github.client import GitHubClient, GitHubClientError


class TestGitHubClient:
    """Tests for GitHubClient class."""

    @patch("shutil.which")
    def test_init_verifies_gh_installed(self, mock_which):
        """Verify that initialization checks for gh CLI."""
        mock_which.return_value = "/usr/local/bin/gh"
        client = GitHubClient()
        mock_which.assert_called_with("gh")
        assert client.repo is None

    @patch("shutil.which")
    def test_init_with_repo(self, mock_which):
        """Verify initialization with explicit repo."""
        mock_which.return_value = "/usr/local/bin/gh"
        client = GitHubClient(repo="owner/repo")
        assert client.repo == "owner/repo"

    @patch("shutil.which")
    def test_init_raises_when_gh_not_installed(self, mock_which):
        """Verify error when gh CLI is not installed."""
        mock_which.return_value = None
        with pytest.raises(GitHubClientError) as exc_info:
            GitHubClient()
        assert "not installed" in str(exc_info.value)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_command_basic(self, mock_run, mock_which):
        """Verify basic command execution."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr="",
        )

        client = GitHubClient()
        result = client.run_command(["pr", "list"])

        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args[0][0] == ["gh", "pr", "list"]
        assert result.stdout == "output"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_command_with_repo(self, mock_run, mock_which):
        """Verify command includes repo when specified."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        client = GitHubClient(repo="owner/repo")
        client.run_command(["pr", "list"])

        call_args = mock_run.call_args[0][0]
        assert "--repo" in call_args
        assert "owner/repo" in call_args

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_command_raises_on_failure(self, mock_run, mock_which):
        """Verify error raised on command failure."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message",
        )

        client = GitHubClient()
        with pytest.raises(GitHubClientError) as exc_info:
            client.run_command(["pr", "list"])

        assert exc_info.value.returncode == 1
        assert exc_info.value.stderr == "error message"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_run_command_no_check(self, mock_run, mock_which):
        """Verify command with check=False doesn't raise."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error")

        client = GitHubClient()
        result = client.run_command(["pr", "list"], check=False)

        assert result.returncode == 1

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_check_auth_returns_true_when_authenticated(self, mock_run, mock_which):
        """Verify check_auth returns True when authenticated."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        client = GitHubClient()
        assert client.check_auth() is True

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_check_auth_returns_false_when_not_authenticated(self, mock_run, mock_which):
        """Verify check_auth returns False when not authenticated."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        client = GitHubClient()
        assert client.check_auth() is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_get_repo_returns_name(self, mock_run, mock_which):
        """Verify get_repo returns repository name."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="owner/repo\n",
            stderr="",
        )

        client = GitHubClient()
        result = client.get_repo()

        assert result == "owner/repo"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_get_repo_returns_none_when_not_in_repo(self, mock_run, mock_which):
        """Verify get_repo returns None when not in a repository."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="")

        client = GitHubClient()
        result = client.get_repo()

        assert result is None

    @patch("shutil.which")
    def test_get_repo_returns_explicit_repo(self, mock_which):
        """Verify get_repo returns explicit repo when set."""
        mock_which.return_value = "/usr/local/bin/gh"
        client = GitHubClient(repo="explicit/repo")
        assert client.get_repo() == "explicit/repo"

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_api_get_request(self, mock_run, mock_which):
        """Verify API GET request."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"data": "value"}',
            stderr="",
        )

        client = GitHubClient()
        result = client.api("/repos/owner/repo")

        call_args = mock_run.call_args[0][0]
        assert "api" in call_args
        assert "-X" in call_args
        assert "GET" in call_args
        assert result == '{"data": "value"}'

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_api_post_with_fields(self, mock_run, mock_which):
        """Verify API POST request with fields."""
        mock_which.return_value = "/usr/local/bin/gh"
        mock_run.return_value = MagicMock(returncode=0, stdout="{}", stderr="")

        client = GitHubClient()
        client.api("/repos/owner/repo", method="POST", fields={"key": "value"})

        call_args = mock_run.call_args[0][0]
        assert "POST" in call_args
        assert "-f" in call_args
        assert "key=value" in call_args
