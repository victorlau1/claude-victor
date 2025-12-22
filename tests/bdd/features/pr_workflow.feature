Feature: Automated PR Workflow
  As a developer using Claude
  I want PRs created from conversations
  So that my work is tracked in GitHub

  Background:
    Given the GitHub CLI is installed
    And I am authenticated with GitHub

  Scenario: Create PR from completed task
    Given I have completed implementation changes
    And I have a branch named "feature/new-feature"
    When I request a pull request with title "Add new feature"
    Then a PR is created with the task summary
    And the PR body contains implementation details
    And the PR is linked to the source branch "feature/new-feature"

  Scenario: Create draft PR for work in progress
    Given I have partial implementation changes
    And I have a branch named "wip/experimental"
    When I request a draft pull request
    Then a draft PR is created
    And the PR is marked as not ready for review

  Scenario: PR includes test artifacts
    Given I have written tests for my changes
    And the tests are passing
    When I create a PR
    Then the PR description includes test coverage info
    And CI workflow is referenced in the PR

  Scenario: Update existing PR
    Given a PR exists with number 42
    When I update the PR with new title "Updated feature"
    Then the PR title is changed to "Updated feature"
    And the PR retains its original number

  Scenario: Add comment to PR
    Given a PR exists with number 42
    When I add a comment "Implementation complete"
    Then the comment appears on the PR
    And the comment is attributed to the authenticated user

  Scenario: Merge PR with squash
    Given a PR exists with number 42
    And the PR has been approved
    When I merge the PR using squash method
    Then the PR is merged
    And the source branch is deleted
    And the commits are squashed into one
