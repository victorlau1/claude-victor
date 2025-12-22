Feature: Plan Storage in Memory-Keeper
  As a Claude user
  I want plans stored in memory-keeper
  So that context persists across sessions

  Background:
    Given the memory-keeper MCP is configured
    And I have an active Claude session

  Scenario: Save plan for later retrieval
    Given I have an approved implementation plan
    And the plan is named "feature-authentication"
    When I save the plan to memory-keeper
    Then the plan is stored with key "plan:feature-authentication"
    And the plan has status "approved"
    And I can retrieve it by name

  Scenario: Resume planning from stored context
    Given a plan exists in memory-keeper with name "feature-auth"
    And the plan has status "draft"
    When I start a new Claude session
    And I invoke the planning workflow for "feature-auth"
    Then the existing plan is loaded
    And I can continue from where I left off
    And the planning state is "reviewing"

  Scenario: List all stored plans
    Given multiple plans exist in memory-keeper
      | name          | status    |
      | plan-alpha    | draft     |
      | plan-beta     | approved  |
      | plan-gamma    | completed |
    When I request a list of all plans
    Then I receive all 3 plans
    And they are sorted by most recently updated

  Scenario: Filter plans by status
    Given multiple plans exist with different statuses
    When I filter plans by status "approved"
    Then I only see plans with status "approved"
    And draft plans are not included

  Scenario: Update plan status
    Given a plan exists with name "my-plan" and status "draft"
    When I update the plan status to "approved"
    Then the plan status is changed to "approved"
    And the plan content is preserved
    And the updated timestamp is refreshed

  Scenario: Delete completed plan
    Given a plan exists with name "old-plan" and status "completed"
    When I delete the plan
    Then the plan is removed from storage
    And attempting to load "old-plan" returns nothing

  Scenario: Export and import plan
    Given a plan exists with name "exportable-plan"
    When I export the plan to JSON format
    Then I receive a valid JSON object with all plan fields
    And I can import the JSON to restore the plan
