"""Unit tests for Issues module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from claude_victor.github.issues import Issue, IssueManager


@pytest.fixture
def mock_client():
    """Create a mock GitHubClient."""
    with patch("claude_victor.github.issues.GitHubClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestIssue:
    """Tests for Issue dataclass."""

    def test_create_issue(self):
        """Verify Issue creation."""
        issue = Issue(
            number=1,
            title="Bug report",
            body="Description",
            state="open",
            url="https://github.com/owner/repo/issues/1",
            labels=["bug", "high-priority"],
        )

        assert issue.number == 1
        assert issue.title == "Bug report"
        assert "bug" in issue.labels


class TestIssueManager:
    """Tests for IssueManager class."""

    def test_create_issue_basic(self, mock_client):
        """Verify basic issue creation."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": "New Issue",
                "body": "Issue body",
                "state": "open",
                "url": "https://github.com/owner/repo/issues/1",
                "labels": [],
            })
        )

        manager = IssueManager(client=mock_client)
        issue = manager.create_issue(title="New Issue", body="Issue body")

        call_args = mock_client.run_command.call_args[0][0]
        assert "issue" in call_args
        assert "create" in call_args
        assert "--title" in call_args
        assert issue.number == 1

    def test_create_issue_with_labels(self, mock_client):
        """Verify issue creation with labels."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": "Bug",
                "body": "Body",
                "state": "open",
                "url": "https://github.com/owner/repo/issues/1",
                "labels": [{"name": "bug"}, {"name": "urgent"}],
            })
        )

        manager = IssueManager(client=mock_client)
        issue = manager.create_issue(
            title="Bug",
            body="Body",
            labels=["bug", "urgent"],
        )

        call_args = mock_client.run_command.call_args[0][0]
        assert "--label" in call_args
        assert "bug" in issue.labels
        assert "urgent" in issue.labels

    def test_create_issue_with_assignees(self, mock_client):
        """Verify issue creation with assignees."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": "Task",
                "body": "Body",
                "state": "open",
                "url": "https://github.com/owner/repo/issues/1",
                "labels": [],
            })
        )

        manager = IssueManager(client=mock_client)
        manager.create_issue(
            title="Task",
            body="Body",
            assignees=["user1", "user2"],
        )

        call_args = mock_client.run_command.call_args[0][0]
        assert "--assignee" in call_args
        assert "user1" in call_args
        assert "user2" in call_args

    def test_close_issue(self, mock_client):
        """Verify closing an issue."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = IssueManager(client=mock_client)
        result = manager.close_issue(1)

        call_args = mock_client.run_command.call_args[0][0]
        assert "close" in call_args
        assert "1" in call_args
        assert "--reason" in call_args
        assert result is True

    def test_close_issue_not_planned(self, mock_client):
        """Verify closing issue as not planned."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = IssueManager(client=mock_client)
        manager.close_issue(1, reason="not_planned")

        call_args = mock_client.run_command.call_args[0][0]
        assert "not_planned" in call_args

    def test_reopen_issue(self, mock_client):
        """Verify reopening an issue."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = IssueManager(client=mock_client)
        result = manager.reopen_issue(1)

        call_args = mock_client.run_command.call_args[0][0]
        assert "reopen" in call_args
        assert result is True

    def test_add_comment(self, mock_client):
        """Verify adding comment to issue."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = IssueManager(client=mock_client)
        result = manager.add_comment(1, "Comment text")

        call_args = mock_client.run_command.call_args[0][0]
        assert "comment" in call_args
        assert "--body" in call_args
        assert "Comment text" in call_args
        assert result is True

    def test_list_issues(self, mock_client):
        """Verify listing issues."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps([
                {
                    "number": 1,
                    "title": "Issue 1",
                    "body": "Body 1",
                    "state": "open",
                    "url": "https://github.com/owner/repo/issues/1",
                    "labels": [{"name": "bug"}],
                },
                {
                    "number": 2,
                    "title": "Issue 2",
                    "body": "Body 2",
                    "state": "open",
                    "url": "https://github.com/owner/repo/issues/2",
                    "labels": [],
                },
            ])
        )

        manager = IssueManager(client=mock_client)
        issues = manager.list_issues()

        assert len(issues) == 2
        assert issues[0].number == 1
        assert "bug" in issues[0].labels

    def test_list_issues_with_filters(self, mock_client):
        """Verify listing issues with filters."""
        mock_client.run_command.return_value = MagicMock(stdout="[]")

        manager = IssueManager(client=mock_client)
        manager.list_issues(state="closed", labels=["bug"], limit=10)

        call_args = mock_client.run_command.call_args[0][0]
        assert "--state" in call_args
        assert "closed" in call_args
        assert "--label" in call_args
        assert "bug" in call_args
        assert "--limit" in call_args
        assert "10" in call_args

    def test_add_labels(self, mock_client):
        """Verify adding labels to issue."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = IssueManager(client=mock_client)
        result = manager.add_labels(1, ["new-label", "another"])

        call_args = mock_client.run_command.call_args[0][0]
        assert "edit" in call_args
        assert "--add-label" in call_args
        assert result is True

    def test_get_issue(self, mock_client):
        """Verify getting issue details."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 42,
                "title": "Specific Issue",
                "body": "Details",
                "state": "closed",
                "url": "https://github.com/owner/repo/issues/42",
                "labels": [{"name": "fixed"}],
            })
        )

        manager = IssueManager(client=mock_client)
        issue = manager.get_issue(42)

        call_args = mock_client.run_command.call_args[0][0]
        assert "view" in call_args
        assert "42" in call_args
        assert issue.number == 42
        assert issue.state == "closed"
