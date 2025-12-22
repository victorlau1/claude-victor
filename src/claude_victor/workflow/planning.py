"""Planning workflow orchestration."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from claude_victor.memory.plan_store import Plan, PlanStore


class PlanningState(Enum):
    """States in the planning workflow."""

    INITIAL = "initial"
    EXPLORING = "exploring"
    DESIGNING = "designing"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    IMPLEMENTING = "implementing"
    COMPLETED = "completed"


@dataclass
class PlanningContext:
    """Context for a planning session."""

    task_name: str
    state: PlanningState
    plan: Optional[Plan] = None
    notes: list[str] = None

    def __post_init__(self):
        if self.notes is None:
            self.notes = []


class PlanningWorkflow:
    """Orchestrate the planning workflow.

    This class manages the planning state machine and integrates
    with memory-keeper for persistence.
    """

    def __init__(self, plan_store: Optional[PlanStore] = None):
        """Initialize planning workflow.

        Args:
            plan_store: Optional PlanStore instance. Creates new one if not provided.
        """
        self.plan_store = plan_store or PlanStore()
        self._context: Optional[PlanningContext] = None

    @property
    def context(self) -> Optional[PlanningContext]:
        """Get current planning context."""
        return self._context

    def start_planning(self, task_name: str) -> PlanningContext:
        """Start a new planning session.

        Args:
            task_name: Name/description of the task to plan

        Returns:
            New PlanningContext
        """
        # Check for existing plan
        existing_plan = self.plan_store.load_plan(task_name)

        if existing_plan:
            self._context = PlanningContext(
                task_name=task_name,
                state=PlanningState.REVIEWING,
                plan=existing_plan,
                notes=["Loaded existing plan from memory-keeper"],
            )
        else:
            self._context = PlanningContext(
                task_name=task_name,
                state=PlanningState.INITIAL,
                notes=["Started new planning session"],
            )

        return self._context

    def transition_to(self, new_state: PlanningState) -> PlanningContext:
        """Transition to a new planning state.

        Args:
            new_state: State to transition to

        Returns:
            Updated PlanningContext

        Raises:
            ValueError: If no active planning context
        """
        if not self._context:
            raise ValueError("No active planning context. Call start_planning first.")

        # Validate state transitions
        valid_transitions = {
            PlanningState.INITIAL: [PlanningState.EXPLORING],
            PlanningState.EXPLORING: [PlanningState.DESIGNING],
            PlanningState.DESIGNING: [PlanningState.REVIEWING, PlanningState.EXPLORING],
            PlanningState.REVIEWING: [PlanningState.APPROVED, PlanningState.DESIGNING],
            PlanningState.APPROVED: [PlanningState.IMPLEMENTING],
            PlanningState.IMPLEMENTING: [PlanningState.COMPLETED, PlanningState.REVIEWING],
            PlanningState.COMPLETED: [],
        }

        if new_state not in valid_transitions.get(self._context.state, []):
            raise ValueError(
                f"Invalid transition from {self._context.state.value} to {new_state.value}"
            )

        self._context.state = new_state
        self._context.notes.append(f"Transitioned to {new_state.value}")

        return self._context

    def save_plan(self, content: str) -> Plan:
        """Save the current plan.

        Args:
            content: Plan content

        Returns:
            Saved Plan object

        Raises:
            ValueError: If no active planning context
        """
        if not self._context:
            raise ValueError("No active planning context. Call start_planning first.")

        status = "draft"
        if self._context.state == PlanningState.APPROVED:
            status = "approved"
        elif self._context.state == PlanningState.COMPLETED:
            status = "completed"

        plan = self.plan_store.save_plan(
            name=self._context.task_name,
            content=content,
            status=status,
        )

        self._context.plan = plan
        self._context.notes.append(f"Saved plan with status: {status}")

        return plan

    def approve_plan(self) -> PlanningContext:
        """Approve the current plan.

        Returns:
            Updated PlanningContext

        Raises:
            ValueError: If not in reviewing state or no plan saved
        """
        if not self._context:
            raise ValueError("No active planning context.")

        if self._context.state != PlanningState.REVIEWING:
            raise ValueError("Can only approve plan in reviewing state")

        if not self._context.plan:
            raise ValueError("No plan to approve. Save a plan first.")

        # Update plan status
        self.plan_store.update_status(self._context.task_name, "approved")
        self._context.plan.status = "approved"

        # Transition state
        self._context.state = PlanningState.APPROVED
        self._context.notes.append("Plan approved")

        return self._context

    def complete_planning(self) -> PlanningContext:
        """Mark planning as complete.

        Returns:
            Updated PlanningContext

        Raises:
            ValueError: If not in implementing state
        """
        if not self._context:
            raise ValueError("No active planning context.")

        if self._context.state != PlanningState.IMPLEMENTING:
            raise ValueError("Can only complete from implementing state")

        self.plan_store.update_status(self._context.task_name, "completed")
        self._context.plan.status = "completed"

        self._context.state = PlanningState.COMPLETED
        self._context.notes.append("Planning completed")

        return self._context

    def get_workflow_prompt(self) -> str:
        """Get the prompt for the current workflow state.

        Returns:
            Markdown prompt for Claude
        """
        if not self._context:
            return "No active planning session. Use /plan-victor to start."

        prompts = {
            PlanningState.INITIAL: """
## Planning: Initial Phase

Starting planning for: **{task_name}**

Next steps:
1. Explore the codebase to understand existing patterns
2. Identify files that need to be modified
3. Transition to EXPLORING state
""",
            PlanningState.EXPLORING: """
## Planning: Exploring Phase

Task: **{task_name}**

Currently exploring the codebase. Actions:
- Use Glob/Grep to find relevant files
- Read key files to understand patterns
- Document findings in notes

When done, transition to DESIGNING state.
""",
            PlanningState.DESIGNING: """
## Planning: Designing Phase

Task: **{task_name}**

Design the implementation approach:
1. List files to modify/create
2. Define the implementation steps
3. Consider edge cases and trade-offs
4. Save the plan

When design is ready, transition to REVIEWING state.
""",
            PlanningState.REVIEWING: """
## Planning: Reviewing Phase

Task: **{task_name}**

Review the plan with the user:
- Present the plan for approval
- Address any questions or concerns
- Make adjustments if needed

Use approve_plan() when user approves.
""",
            PlanningState.APPROVED: """
## Planning: Approved

Task: **{task_name}**
Plan Status: **APPROVED**

Ready to implement. Transition to IMPLEMENTING state to begin.
""",
            PlanningState.IMPLEMENTING: """
## Planning: Implementing

Task: **{task_name}**

Implementation in progress. Track progress against the plan.

When complete, use complete_planning() to finish.
""",
            PlanningState.COMPLETED: """
## Planning: Completed

Task: **{task_name}**
Status: **COMPLETED**

The planning session is complete. Plan has been saved to memory-keeper.
""",
        }

        template = prompts.get(self._context.state, "Unknown state")
        return template.format(task_name=self._context.task_name)
