"""Unit tests for Pull Request module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from claude_victor.github.pr import PullRequest, PullRequestManager


@pytest.fixture
def mock_client():
    """Create a mock GitHubClient."""
    with patch("claude_victor.github.pr.GitHubClient") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestPullRequest:
    """Tests for PullRequest dataclass."""

    def test_create_pull_request(self):
        """Verify PullRequest creation."""
        pr = PullRequest(
            number=1,
            title="Test PR",
            body="Description",
            state="open",
            head="feature",
            base="main",
            url="https://github.com/owner/repo/pull/1",
            draft=False,
        )

        assert pr.number == 1
        assert pr.title == "Test PR"
        assert pr.state == "open"


class TestPullRequestManager:
    """Tests for PullRequestManager class."""

    def test_create_pr_builds_correct_command(self, mock_client):
        """Verify gh pr create command is properly formed."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": "Test",
                "body": "Body",
                "state": "open",
                "headRefName": "feature",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/1",
                "isDraft": False,
            })
        )

        manager = PullRequestManager(client=mock_client)
        pr = manager.create_pr(title="Test", body="Body")

        call_args = mock_client.run_command.call_args[0][0]
        assert "pr" in call_args
        assert "create" in call_args
        assert "--title" in call_args
        assert "Test" in call_args
        assert "--body" in call_args
        assert pr.number == 1

    def test_create_pr_escapes_special_characters(self, mock_client):
        """Verify title/body with quotes are handled correctly."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": 'Test with "quotes"',
                "body": "Body with 'apostrophes'",
                "state": "open",
                "headRefName": "feature",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/1",
                "isDraft": False,
            })
        )

        manager = PullRequestManager(client=mock_client)
        pr = manager.create_pr(
            title='Test with "quotes"',
            body="Body with 'apostrophes'",
        )

        call_args = mock_client.run_command.call_args[0][0]
        assert 'Test with "quotes"' in call_args
        assert pr.title == 'Test with "quotes"'

    def test_create_pr_with_draft_flag(self, mock_client):
        """Verify draft PR creation."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": "Draft PR",
                "body": "WIP",
                "state": "open",
                "headRefName": "feature",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/1",
                "isDraft": True,
            })
        )

        manager = PullRequestManager(client=mock_client)
        pr = manager.create_pr(title="Draft PR", body="WIP", draft=True)

        call_args = mock_client.run_command.call_args[0][0]
        assert "--draft" in call_args
        assert pr.draft is True

    def test_create_pr_with_custom_base_and_head(self, mock_client):
        """Verify custom base and head branches."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps({
                "number": 1,
                "title": "Test",
                "body": "Body",
                "state": "open",
                "headRefName": "my-feature",
                "baseRefName": "develop",
                "url": "https://github.com/owner/repo/pull/1",
                "isDraft": False,
            })
        )

        manager = PullRequestManager(client=mock_client)
        pr = manager.create_pr(
            title="Test",
            body="Body",
            base="develop",
            head="my-feature",
        )

        call_args = mock_client.run_command.call_args[0][0]
        assert "--base" in call_args
        assert "develop" in call_args
        assert "--head" in call_args
        assert "my-feature" in call_args
        assert pr.base == "develop"
        assert pr.head == "my-feature"

    def test_merge_pr_uses_specified_method(self, mock_client):
        """Verify squash/merge/rebase methods work."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = PullRequestManager(client=mock_client)

        # Test squash (default)
        manager.merge_pr(1)
        call_args = mock_client.run_command.call_args[0][0]
        assert "--squash" in call_args

        # Test merge
        manager.merge_pr(2, method="merge")
        call_args = mock_client.run_command.call_args[0][0]
        assert "--merge" in call_args

        # Test rebase
        manager.merge_pr(3, method="rebase")
        call_args = mock_client.run_command.call_args[0][0]
        assert "--rebase" in call_args

    def test_merge_pr_delete_branch_option(self, mock_client):
        """Verify delete branch option."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = PullRequestManager(client=mock_client)

        # Default: delete branch
        manager.merge_pr(1)
        call_args = mock_client.run_command.call_args[0][0]
        assert "--delete-branch" in call_args

        # Explicitly don't delete
        manager.merge_pr(1, delete_branch=False)
        call_args = mock_client.run_command.call_args[0][0]
        assert "--delete-branch" not in call_args

    def test_update_pr(self, mock_client):
        """Verify PR update."""
        # Mock for edit command
        mock_client.run_command.side_effect = [
            MagicMock(returncode=0),  # edit command
            MagicMock(stdout=json.dumps({  # view command
                "number": 1,
                "title": "Updated Title",
                "body": "Updated Body",
                "state": "open",
                "headRefName": "feature",
                "baseRefName": "main",
                "url": "https://github.com/owner/repo/pull/1",
                "isDraft": False,
            })),
        ]

        manager = PullRequestManager(client=mock_client)
        pr = manager.update_pr(1, title="Updated Title", body="Updated Body")

        first_call = mock_client.run_command.call_args_list[0][0][0]
        assert "edit" in first_call
        assert "--title" in first_call
        assert "Updated Title" in first_call
        assert pr.title == "Updated Title"

    def test_list_prs(self, mock_client):
        """Verify listing PRs."""
        mock_client.run_command.return_value = MagicMock(
            stdout=json.dumps([
                {
                    "number": 1,
                    "title": "PR 1",
                    "body": "Body 1",
                    "state": "open",
                    "headRefName": "feature-1",
                    "baseRefName": "main",
                    "url": "https://github.com/owner/repo/pull/1",
                    "isDraft": False,
                },
                {
                    "number": 2,
                    "title": "PR 2",
                    "body": "Body 2",
                    "state": "open",
                    "headRefName": "feature-2",
                    "baseRefName": "main",
                    "url": "https://github.com/owner/repo/pull/2",
                    "isDraft": True,
                },
            ])
        )

        manager = PullRequestManager(client=mock_client)
        prs = manager.list_prs()

        assert len(prs) == 2
        assert prs[0].number == 1
        assert prs[1].draft is True

    def test_add_comment(self, mock_client):
        """Verify adding comment to PR."""
        mock_client.run_command.return_value = MagicMock(returncode=0)

        manager = PullRequestManager(client=mock_client)
        result = manager.add_comment(1, "Great work!")

        call_args = mock_client.run_command.call_args[0][0]
        assert "comment" in call_args
        assert "--body" in call_args
        assert "Great work!" in call_args
        assert result is True
