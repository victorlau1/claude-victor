"""Unit tests for Plan Store module."""

import pytest

from claude_victor.memory.plan_store import Plan, PlanStore


class TestPlan:
    """Tests for Plan dataclass."""

    def test_create_plan(self):
        """Verify Plan creation."""
        plan = Plan(
            name="test-plan",
            content="# Test Plan\n\nContent here",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
            status="draft",
        )

        assert plan.name == "test-plan"
        assert plan.status == "draft"

    def test_plan_default_status(self):
        """Verify default status is draft."""
        plan = Plan(
            name="test",
            content="content",
            created_at="2025-01-01T00:00:00",
            updated_at="2025-01-01T00:00:00",
        )

        assert plan.status == "draft"


class TestPlanStore:
    """Tests for PlanStore class."""

    @pytest.fixture
    def store(self):
        """Create a fresh PlanStore for each test."""
        return PlanStore()

    def test_save_plan_creates_new(self, store):
        """Verify saving a new plan."""
        plan = store.save_plan("my-plan", "# Plan Content")

        assert plan.name == "my-plan"
        assert plan.content == "# Plan Content"
        assert plan.status == "draft"
        assert plan.created_at is not None
        assert plan.updated_at is not None

    def test_save_plan_uses_correct_key_format(self, store):
        """Verify plan:{name} key pattern."""
        store.save_plan("test-feature", "content")

        # Internal key should use prefix
        key = store._make_key("test-feature")
        assert key == "plan:test-feature"

        # Parse should extract name
        name = store._parse_key("plan:test-feature")
        assert name == "test-feature"

    def test_load_plan_returns_saved(self, store):
        """Verify loading a saved plan."""
        store.save_plan("my-plan", "content")
        loaded = store.load_plan("my-plan")

        assert loaded is not None
        assert loaded.name == "my-plan"
        assert loaded.content == "content"

    def test_load_plan_returns_none_for_missing(self, store):
        """Verify graceful handling of missing plans."""
        result = store.load_plan("nonexistent")
        assert result is None

    def test_save_plan_updates_existing(self, store):
        """Verify updating an existing plan."""
        store.save_plan("my-plan", "original content")
        original = store.load_plan("my-plan")
        original_created = original.created_at

        # Update the plan
        updated = store.save_plan("my-plan", "updated content")

        assert updated.content == "updated content"
        assert updated.created_at == original_created  # Created time preserved
        assert updated.updated_at >= original.updated_at

    def test_save_plan_with_status(self, store):
        """Verify saving with custom status."""
        plan = store.save_plan("my-plan", "content", status="approved")
        assert plan.status == "approved"

    def test_list_plans_returns_all(self, store):
        """Verify listing all plans."""
        store.save_plan("plan-1", "content 1")
        store.save_plan("plan-2", "content 2")
        store.save_plan("plan-3", "content 3")

        plans = store.list_plans()

        assert len(plans) == 3
        names = [p.name for p in plans]
        assert "plan-1" in names
        assert "plan-2" in names
        assert "plan-3" in names

    def test_list_plans_filters_by_status(self, store):
        """Verify filtering plans by status."""
        store.save_plan("draft-plan", "content", status="draft")
        store.save_plan("approved-plan", "content", status="approved")
        store.save_plan("completed-plan", "content", status="completed")

        drafts = store.list_plans(status="draft")
        assert len(drafts) == 1
        assert drafts[0].name == "draft-plan"

        approved = store.list_plans(status="approved")
        assert len(approved) == 1
        assert approved[0].name == "approved-plan"

    def test_list_plans_sorted_by_updated(self, store):
        """Verify plans are sorted by updated time (newest first)."""
        store.save_plan("plan-1", "content")
        store.save_plan("plan-2", "content")
        store.save_plan("plan-1", "updated content")  # Update plan-1

        plans = store.list_plans()

        # plan-1 should be first (most recently updated)
        assert plans[0].name == "plan-1"

    def test_delete_plan(self, store):
        """Verify deleting a plan."""
        store.save_plan("my-plan", "content")
        result = store.delete_plan("my-plan")

        assert result is True
        assert store.load_plan("my-plan") is None

    def test_delete_plan_returns_false_for_missing(self, store):
        """Verify delete returns False for nonexistent plan."""
        result = store.delete_plan("nonexistent")
        assert result is False

    def test_update_status(self, store):
        """Verify updating plan status."""
        store.save_plan("my-plan", "content", status="draft")
        updated = store.update_status("my-plan", "approved")

        assert updated is not None
        assert updated.status == "approved"
        assert updated.content == "content"  # Content preserved

    def test_update_status_returns_none_for_missing(self, store):
        """Verify update_status returns None for missing plan."""
        result = store.update_status("nonexistent", "approved")
        assert result is None

    def test_export_plan(self, store):
        """Verify exporting plan to dictionary."""
        store.save_plan("my-plan", "content", status="approved")
        exported = store.export_plan("my-plan")

        assert exported is not None
        assert exported["name"] == "my-plan"
        assert exported["content"] == "content"
        assert exported["status"] == "approved"
        assert "created_at" in exported
        assert "updated_at" in exported

    def test_export_plan_returns_none_for_missing(self, store):
        """Verify export returns None for missing plan."""
        result = store.export_plan("nonexistent")
        assert result is None

    def test_import_plan(self, store):
        """Verify importing plan from dictionary."""
        data = {
            "name": "imported-plan",
            "content": "imported content",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00",
            "status": "completed",
        }

        plan = store.import_plan(data)

        assert plan.name == "imported-plan"
        assert plan.content == "imported content"
        assert plan.status == "completed"

        # Should be loadable
        loaded = store.load_plan("imported-plan")
        assert loaded is not None

    def test_import_plan_with_defaults(self, store):
        """Verify import with minimal data uses defaults."""
        data = {
            "name": "minimal-plan",
            "content": "content",
        }

        plan = store.import_plan(data)

        assert plan.status == "draft"
        assert plan.created_at is not None

    def test_get_mcp_instructions(self, store):
        """Verify MCP instructions are returned."""
        instructions = store.get_mcp_instructions()

        assert "context_save" in instructions
        assert "context_get" in instructions
        assert "plan:" in instructions
