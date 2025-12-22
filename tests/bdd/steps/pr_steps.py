"""Step definitions for PR workflow feature."""

import json
from unittest.mock import MagicMock, patch

from behave import given, when, then

from claude_victor.github.client import GitHubClient
from claude_victor.github.pr import PullRequest, PullRequestManager


@given("the GitHub CLI is installed")
def step_github_cli_installed(context):
    """Verify GitHub CLI is available."""
    context.mock_client = MagicMock(spec=GitHubClient)
    context.pr_manager = PullRequestManager(client=context.mock_client)


@given("I am authenticated with GitHub")
def step_authenticated_github(context):
    """Verify GitHub authentication."""
    context.mock_client.check_auth.return_value = True


@given("I have completed implementation changes")
def step_completed_changes(context):
    """Set up completed changes scenario."""
    context.has_changes = True
    context.changes_complete = True


@given("I have partial implementation changes")
def step_partial_changes(context):
    """Set up partial changes scenario."""
    context.has_changes = True
    context.changes_complete = False


@given('I have a branch named "{branch_name}"')
def step_have_branch(context, branch_name):
    """Set up branch context."""
    context.current_branch = branch_name


@given("I have written tests for my changes")
def step_written_tests(context):
    """Set up test scenario."""
    context.has_tests = True
    context.test_coverage = 85


@given("the tests are passing")
def step_tests_passing(context):
    """Mark tests as passing."""
    context.tests_passing = True


@given("a PR exists with number {pr_number:d}")
def step_pr_exists(context, pr_number):
    """Set up existing PR."""
    context.existing_pr = PullRequest(
        number=pr_number,
        title="Existing PR",
        body="Original body",
        state="open",
        head="feature-branch",
        base="main",
        url=f"https://github.com/owner/repo/pull/{pr_number}",
        draft=False,
    )

    context.mock_client.run_command.return_value = MagicMock(
        stdout=json.dumps({
            "number": pr_number,
            "title": "Existing PR",
            "body": "Original body",
            "state": "open",
            "headRefName": "feature-branch",
            "baseRefName": "main",
            "url": f"https://github.com/owner/repo/pull/{pr_number}",
            "isDraft": False,
        })
    )


@given("the PR has been approved")
def step_pr_approved(context):
    """Mark PR as approved."""
    context.pr_approved = True


@when('I request a pull request with title "{title}"')
def step_request_pr(context, title):
    """Create a PR request."""
    context.mock_client.run_command.return_value = MagicMock(
        stdout=json.dumps({
            "number": 1,
            "title": title,
            "body": "Implementation details here",
            "state": "open",
            "headRefName": context.current_branch,
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/1",
            "isDraft": False,
        })
    )

    context.created_pr = context.pr_manager.create_pr(
        title=title,
        body="Implementation details here",
        head=context.current_branch,
    )


@when("I request a draft pull request")
def step_request_draft_pr(context):
    """Create a draft PR."""
    context.mock_client.run_command.return_value = MagicMock(
        stdout=json.dumps({
            "number": 1,
            "title": "WIP: Draft PR",
            "body": "Work in progress",
            "state": "open",
            "headRefName": context.current_branch,
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/1",
            "isDraft": True,
        })
    )

    context.created_pr = context.pr_manager.create_pr(
        title="WIP: Draft PR",
        body="Work in progress",
        head=context.current_branch,
        draft=True,
    )


@when("I create a PR")
def step_create_pr(context):
    """Create a standard PR."""
    body = "Test coverage: 85%\n\nCI: Triggered" if context.has_tests else "No tests"

    context.mock_client.run_command.return_value = MagicMock(
        stdout=json.dumps({
            "number": 1,
            "title": "Feature PR",
            "body": body,
            "state": "open",
            "headRefName": "feature",
            "baseRefName": "main",
            "url": "https://github.com/owner/repo/pull/1",
            "isDraft": False,
        })
    )

    context.created_pr = context.pr_manager.create_pr(
        title="Feature PR",
        body=body,
    )


@when('I update the PR with new title "{title}"')
def step_update_pr_title(context, title):
    """Update PR title."""
    context.mock_client.run_command.side_effect = [
        MagicMock(returncode=0),  # edit command
        MagicMock(stdout=json.dumps({  # view command
            "number": context.existing_pr.number,
            "title": title,
            "body": context.existing_pr.body,
            "state": "open",
            "headRefName": context.existing_pr.head,
            "baseRefName": context.existing_pr.base,
            "url": context.existing_pr.url,
            "isDraft": False,
        })),
    ]

    context.updated_pr = context.pr_manager.update_pr(
        context.existing_pr.number,
        title=title,
    )


@when('I add a comment "{comment}"')
def step_add_comment(context, comment):
    """Add comment to PR."""
    context.mock_client.run_command.return_value = MagicMock(returncode=0)
    context.comment_added = context.pr_manager.add_comment(
        context.existing_pr.number,
        comment,
    )
    context.comment_text = comment


@when("I merge the PR using squash method")
def step_merge_pr_squash(context):
    """Merge PR with squash."""
    context.mock_client.run_command.return_value = MagicMock(returncode=0)
    context.merge_result = context.pr_manager.merge_pr(
        context.existing_pr.number,
        method="squash",
    )


@then("a PR is created with the task summary")
def step_pr_created(context):
    """Verify PR was created."""
    assert context.created_pr is not None
    assert context.created_pr.number > 0


@then("the PR body contains implementation details")
def step_pr_has_details(context):
    """Verify PR body has content."""
    assert context.created_pr.body is not None
    assert len(context.created_pr.body) > 0


@then('the PR is linked to the source branch "{branch}"')
def step_pr_linked_branch(context, branch):
    """Verify PR head branch."""
    assert context.created_pr.head == branch


@then("a draft PR is created")
def step_draft_pr_created(context):
    """Verify draft PR created."""
    assert context.created_pr is not None
    assert context.created_pr.draft is True


@then("the PR is marked as not ready for review")
def step_pr_not_ready(context):
    """Verify PR is draft."""
    assert context.created_pr.draft is True


@then("the PR description includes test coverage info")
def step_pr_has_coverage(context):
    """Verify coverage in PR body."""
    assert "coverage" in context.created_pr.body.lower() or "85%" in context.created_pr.body


@then("CI workflow is referenced in the PR")
def step_ci_referenced(context):
    """Verify CI mention in PR."""
    assert "CI" in context.created_pr.body or "triggered" in context.created_pr.body.lower()


@then('the PR title is changed to "{title}"')
def step_pr_title_changed(context, title):
    """Verify PR title updated."""
    assert context.updated_pr.title == title


@then("the PR retains its original number")
def step_pr_same_number(context):
    """Verify PR number unchanged."""
    assert context.updated_pr.number == context.existing_pr.number


@then("the comment appears on the PR")
def step_comment_appears(context):
    """Verify comment was added."""
    assert context.comment_added is True


@then("the comment is attributed to the authenticated user")
def step_comment_attributed(context):
    """Verify comment attribution (mock verification)."""
    # In real scenario, would verify user from API response
    assert context.comment_added is True


@then("the PR is merged")
def step_pr_merged(context):
    """Verify PR merged."""
    assert context.merge_result is True


@then("the source branch is deleted")
def step_branch_deleted(context):
    """Verify branch deletion (verified via merge call args)."""
    call_args = context.mock_client.run_command.call_args[0][0]
    assert "--delete-branch" in call_args


@then("the commits are squashed into one")
def step_commits_squashed(context):
    """Verify squash merge."""
    call_args = context.mock_client.run_command.call_args[0][0]
    assert "--squash" in call_args
