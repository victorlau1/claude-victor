"""Integration tests for memory-keeper integration.

These tests verify the integration between plan storage and workflow components.
"""

import pytest

from claude_victor.memory.plan_store import Plan, PlanStore
from claude_victor.workflow.planning import PlanningWorkflow, PlanningState, PlanningContext


class TestPlanStoreIntegration:
    """Integration tests for PlanStore."""

    @pytest.fixture
    def store(self):
        """Create a fresh store for each test."""
        return PlanStore()

    def test_full_plan_lifecycle(self, store):
        """Test complete plan lifecycle: create, update, complete."""
        # Create draft plan
        plan = store.save_plan(
            name="feature-auth",
            content="# Auth Implementation\n\n1. Add login\n2. Add logout",
            status="draft",
        )
        assert plan.status == "draft"

        # Update to approved
        plan = store.update_status("feature-auth", "approved")
        assert plan.status == "approved"

        # Update content
        plan = store.save_plan(
            name="feature-auth",
            content="# Auth Implementation (Updated)\n\n1. Add login\n2. Add logout\n3. Add session",
            status="approved",
        )
        assert "Updated" in plan.content

        # Complete
        plan = store.update_status("feature-auth", "completed")
        assert plan.status == "completed"

    def test_multiple_plans_management(self, store):
        """Test managing multiple plans simultaneously."""
        plans_data = [
            ("auth", "Auth plan", "draft"),
            ("api", "API plan", "approved"),
            ("ui", "UI plan", "completed"),
            ("tests", "Test plan", "draft"),
        ]

        for name, content, status in plans_data:
            store.save_plan(name, content, status)

        # List all
        all_plans = store.list_plans()
        assert len(all_plans) == 4

        # Filter by status
        drafts = store.list_plans(status="draft")
        assert len(drafts) == 2

        approved = store.list_plans(status="approved")
        assert len(approved) == 1
        assert approved[0].name == "api"

    def test_export_import_roundtrip(self, store):
        """Test exporting and importing plans."""
        # Create original plan
        original = store.save_plan(
            name="exportable",
            content="# Original Content\n\nWith details",
            status="approved",
        )

        # Export
        exported = store.export_plan("exportable")
        assert exported is not None

        # Create new store and import
        new_store = PlanStore()
        imported = new_store.import_plan(exported)

        # Verify content matches
        assert imported.name == original.name
        assert imported.content == original.content
        assert imported.status == original.status


class TestPlanningWorkflowIntegration:
    """Integration tests for PlanningWorkflow."""

    @pytest.fixture
    def workflow(self):
        """Create workflow with fresh store."""
        store = PlanStore()
        return PlanningWorkflow(plan_store=store)

    def test_complete_planning_workflow(self, workflow):
        """Test complete planning workflow from start to finish."""
        # Start planning
        context = workflow.start_planning("new-feature")
        assert context.state == PlanningState.INITIAL

        # Transition through states
        context = workflow.transition_to(PlanningState.EXPLORING)
        assert context.state == PlanningState.EXPLORING

        context = workflow.transition_to(PlanningState.DESIGNING)
        assert context.state == PlanningState.DESIGNING

        # Save plan
        plan = workflow.save_plan("# Plan\n\n1. Step one\n2. Step two")
        assert plan.status == "draft"

        # Move to review
        context = workflow.transition_to(PlanningState.REVIEWING)
        assert context.state == PlanningState.REVIEWING

        # Approve
        context = workflow.approve_plan()
        assert context.state == PlanningState.APPROVED
        assert context.plan.status == "approved"

        # Start implementing
        context = workflow.transition_to(PlanningState.IMPLEMENTING)
        assert context.state == PlanningState.IMPLEMENTING

        # Complete
        context = workflow.complete_planning()
        assert context.state == PlanningState.COMPLETED
        assert context.plan.status == "completed"

    def test_resume_existing_plan(self, workflow):
        """Test resuming an existing plan from storage."""
        # Create and save a plan
        workflow.start_planning("existing-task")
        workflow.transition_to(PlanningState.EXPLORING)
        workflow.transition_to(PlanningState.DESIGNING)
        workflow.save_plan("# Saved Plan\n\nContent here")

        # Create new workflow with same store
        new_workflow = PlanningWorkflow(plan_store=workflow.plan_store)

        # Start planning - should load existing
        context = new_workflow.start_planning("existing-task")
        assert context.plan is not None
        assert context.state == PlanningState.REVIEWING
        assert "existing plan" in context.notes[0].lower()

    def test_workflow_state_validation(self, workflow):
        """Test that invalid state transitions are rejected."""
        workflow.start_planning("task")

        # Can't go directly to DESIGNING from INITIAL
        with pytest.raises(ValueError) as exc_info:
            workflow.transition_to(PlanningState.DESIGNING)
        assert "Invalid transition" in str(exc_info.value)

        # Can't approve without being in REVIEWING state
        with pytest.raises(ValueError):
            workflow.approve_plan()

    def test_workflow_prompt_generation(self, workflow):
        """Test that workflow generates appropriate prompts."""
        context = workflow.start_planning("my-task")

        # Check prompt for initial state
        prompt = workflow.get_workflow_prompt()
        assert "my-task" in prompt
        assert "Initial" in prompt or "initial" in prompt

        # Transition and check prompt updates
        workflow.transition_to(PlanningState.EXPLORING)
        prompt = workflow.get_workflow_prompt()
        assert "Exploring" in prompt or "exploring" in prompt


class TestStoreWorkflowIntegration:
    """Integration tests between store and workflow."""

    def test_plan_persistence_across_workflows(self):
        """Test that plans persist across workflow instances."""
        # Shared store
        store = PlanStore()

        # First workflow creates plan
        workflow1 = PlanningWorkflow(plan_store=store)
        workflow1.start_planning("shared-task")
        workflow1.transition_to(PlanningState.EXPLORING)
        workflow1.transition_to(PlanningState.DESIGNING)
        workflow1.save_plan("# Shared Plan")
        workflow1.transition_to(PlanningState.REVIEWING)
        workflow1.approve_plan()

        # Second workflow should find the approved plan
        workflow2 = PlanningWorkflow(plan_store=store)
        context = workflow2.start_planning("shared-task")

        assert context.plan is not None
        assert context.plan.status == "approved"

    def test_multiple_concurrent_tasks(self):
        """Test managing multiple tasks in the same store."""
        store = PlanStore()

        # Create plans for different tasks
        for task_name in ["task-a", "task-b", "task-c"]:
            store.save_plan(task_name, f"Plan for {task_name}", "draft")

        # Each workflow can work on different tasks
        workflow_a = PlanningWorkflow(plan_store=store)
        workflow_b = PlanningWorkflow(plan_store=store)

        context_a = workflow_a.start_planning("task-a")
        context_b = workflow_b.start_planning("task-b")

        assert context_a.task_name != context_b.task_name
        assert context_a.plan.name == "task-a"
        assert context_b.plan.name == "task-b"

    def test_plan_updates_reflect_in_workflow(self):
        """Test that store updates are reflected in workflow."""
        store = PlanStore()
        workflow = PlanningWorkflow(plan_store=store)

        # Start and save initial plan
        workflow.start_planning("evolving-task")
        workflow.transition_to(PlanningState.EXPLORING)
        workflow.transition_to(PlanningState.DESIGNING)
        workflow.save_plan("# Initial Plan")

        # Update directly via store
        store.save_plan("evolving-task", "# Updated Plan", "draft")

        # Reload via workflow
        new_workflow = PlanningWorkflow(plan_store=store)
        context = new_workflow.start_planning("evolving-task")

        assert "Updated" in context.plan.content
