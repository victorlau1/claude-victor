"""Step definitions for plan storage feature."""

from behave import given, when, then
from behave.runner import Context

from claude_victor.memory.plan_store import Plan, PlanStore
from claude_victor.workflow.planning import PlanningWorkflow, PlanningState


@given("the memory-keeper MCP is configured")
def step_mcp_configured(context: Context):
    """Initialize plan store (simulating MCP)."""
    context.plan_store = PlanStore()
    context.workflow = PlanningWorkflow(plan_store=context.plan_store)


@given("I have an active Claude session")
def step_active_session(context: Context):
    """Mark session as active."""
    context.session_active = True


@given("I have an approved implementation plan")
def step_approved_plan(context: Context):
    """Create an approved plan."""
    context.plan_content = "# Implementation Plan\n\n## Steps\n1. Step one\n2. Step two"
    context.plan_status = "approved"


@given('the plan is named "{plan_name}"')
def step_plan_named(context: Context, plan_name: str):
    """Set plan name."""
    context.plan_name = plan_name


@given('a plan exists in memory-keeper with name "{plan_name}"')
def step_plan_exists(context: Context, plan_name: str):
    """Create existing plan in store."""
    context.plan_store.save_plan(
        name=plan_name,
        content="# Existing Plan\n\nContent here",
        status="draft",
    )
    context.plan_name = plan_name


@given('the plan has status "{status}"')
def step_plan_has_status(context: Context, status: str):
    """Update plan status."""
    if hasattr(context, "plan_name"):
        context.plan_store.update_status(context.plan_name, status)


@given("multiple plans exist in memory-keeper")
def step_multiple_plans(context: Context):
    """Create multiple plans from table."""
    for row in context.table:
        context.plan_store.save_plan(
            name=row["name"],
            content=f"Content for {row['name']}",
            status=row["status"],
        )


@given("multiple plans exist with different statuses")
def step_plans_different_statuses(context: Context):
    """Create plans with various statuses."""
    context.plan_store.save_plan("draft-plan", "Draft content", status="draft")
    context.plan_store.save_plan("approved-plan", "Approved content", status="approved")
    context.plan_store.save_plan("completed-plan", "Completed content", status="completed")


@given('a plan exists with name "{name}" and status "{status}"')
def step_plan_exists_with_status(context: Context, name: str, status: str):
    """Create plan with specific status."""
    context.plan_store.save_plan(name, f"Content for {name}", status=status)
    context.plan_name = name


@given('a plan exists with name "{name}"')
def step_plan_exists_by_name(context: Context, name: str):
    """Create plan by name."""
    context.plan_store.save_plan(name, f"Content for {name}", status="draft")
    context.plan_name = name


@when("I save the plan to memory-keeper")
def step_save_plan(context: Context):
    """Save plan to store."""
    context.saved_plan = context.plan_store.save_plan(
        name=context.plan_name,
        content=context.plan_content,
        status=context.plan_status,
    )


@when("I start a new Claude session")
def step_new_session(context: Context):
    """Simulate new session."""
    context.new_session = True


@when('I invoke the planning workflow for "{task_name}"')
def step_invoke_planning(context: Context, task_name: str):
    """Start planning workflow."""
    context.planning_context = context.workflow.start_planning(task_name)


@when("I request a list of all plans")
def step_list_all_plans(context: Context):
    """List all plans."""
    context.plan_list = context.plan_store.list_plans()


@when('I filter plans by status "{status}"')
def step_filter_by_status(context: Context, status: str):
    """Filter plans by status."""
    context.filtered_plans = context.plan_store.list_plans(status=status)


@when('I update the plan status to "{status}"')
def step_update_status(context: Context, status: str):
    """Update plan status."""
    context.updated_plan = context.plan_store.update_status(context.plan_name, status)


@when("I delete the plan")
def step_delete_plan(context: Context):
    """Delete the plan."""
    context.delete_result = context.plan_store.delete_plan(context.plan_name)


@when("I export the plan to JSON format")
def step_export_plan(context: Context):
    """Export plan to JSON."""
    context.exported_data = context.plan_store.export_plan(context.plan_name)


@then('the plan is stored with key "{key}"')
def step_plan_stored_with_key(context: Context, key: str):
    """Verify plan storage key."""
    expected_name = key.replace("plan:", "")
    loaded = context.plan_store.load_plan(expected_name)
    assert loaded is not None, f"Plan not found with key {key}"


@then('the plan has status "{status}"')
def step_verify_plan_status(context: Context, status: str):
    """Verify plan status."""
    assert context.saved_plan.status == status


@then("I can retrieve it by name")
def step_retrieve_by_name(context: Context):
    """Verify plan retrieval."""
    loaded = context.plan_store.load_plan(context.plan_name)
    assert loaded is not None
    assert loaded.content == context.plan_content


@then("the existing plan is loaded")
def step_existing_plan_loaded(context: Context):
    """Verify existing plan was loaded."""
    assert context.planning_context is not None
    assert context.planning_context.plan is not None


@then("I can continue from where I left off")
def step_continue_planning(context: Context):
    """Verify can continue planning."""
    assert context.planning_context.state in [
        PlanningState.REVIEWING,
        PlanningState.DESIGNING,
    ]


@then('the planning state is "{state}"')
def step_verify_planning_state(context: Context, state: str):
    """Verify planning state."""
    assert context.planning_context.state.value == state


@then("I receive all {count:d} plans")
def step_receive_plans(context: Context, count: int):
    """Verify plan count."""
    assert len(context.plan_list) == count


@then("they are sorted by most recently updated")
def step_sorted_by_updated(context: Context):
    """Verify sort order."""
    if len(context.plan_list) > 1:
        for i in range(len(context.plan_list) - 1):
            assert context.plan_list[i].updated_at >= context.plan_list[i + 1].updated_at


@then('I only see plans with status "{status}"')
def step_only_status_plans(context: Context, status: str):
    """Verify filtered plans."""
    for plan in context.filtered_plans:
        assert plan.status == status


@then("draft plans are not included")
def step_no_draft_plans(context: Context):
    """Verify no drafts in filtered list."""
    for plan in context.filtered_plans:
        assert plan.status != "draft"


@then('the plan status is changed to "{status}"')
def step_status_changed(context: Context, status: str):
    """Verify status change."""
    assert context.updated_plan.status == status


@then("the plan content is preserved")
def step_content_preserved(context: Context):
    """Verify content unchanged."""
    loaded = context.plan_store.load_plan(context.plan_name)
    assert loaded.content == context.updated_plan.content


@then("the updated timestamp is refreshed")
def step_timestamp_refreshed(context: Context):
    """Verify timestamp updated."""
    assert context.updated_plan.updated_at is not None


@then("the plan is removed from storage")
def step_plan_removed(context: Context):
    """Verify plan deleted."""
    assert context.delete_result is True


@then('attempting to load "{name}" returns nothing')
def step_load_returns_nothing(context: Context, name: str):
    """Verify plan not found."""
    loaded = context.plan_store.load_plan(name)
    assert loaded is None


@then("I receive a valid JSON object with all plan fields")
def step_valid_json(context: Context):
    """Verify JSON export."""
    assert context.exported_data is not None
    assert "name" in context.exported_data
    assert "content" in context.exported_data
    assert "status" in context.exported_data
    assert "created_at" in context.exported_data
    assert "updated_at" in context.exported_data


@then("I can import the JSON to restore the plan")
def step_import_json(context: Context):
    """Verify JSON import."""
    # Modify name to avoid conflict
    context.exported_data["name"] = "imported-copy"
    imported = context.plan_store.import_plan(context.exported_data)
    assert imported is not None
    assert imported.name == "imported-copy"
