"""Plan storage using memory-keeper MCP protocol."""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Plan:
    """Represents a stored plan."""

    name: str
    content: str
    created_at: str
    updated_at: str
    status: str = "draft"  # draft, approved, completed


class PlanStore:
    """Store and retrieve plans using memory-keeper MCP.

    This class provides a Python interface for storing plans that can be
    used with the memory-keeper MCP server. In actual usage, the MCP tools
    are called directly by Claude. This class serves as:
    1. Documentation of the expected interface
    2. A testable abstraction for plan management
    3. A local fallback when MCP is not available
    """

    # Key prefix for all plans in memory-keeper
    KEY_PREFIX = "plan:"

    def __init__(self, storage_path: Optional[str] = None):
        """Initialize plan store.

        Args:
            storage_path: Optional local storage path for fallback.
                         If not provided, uses in-memory storage.
        """
        self.storage_path = storage_path
        self._local_store: dict[str, Plan] = {}

    def _make_key(self, name: str) -> str:
        """Create a storage key from plan name."""
        return f"{self.KEY_PREFIX}{name}"

    def _parse_key(self, key: str) -> str:
        """Extract plan name from storage key."""
        if key.startswith(self.KEY_PREFIX):
            return key[len(self.KEY_PREFIX):]
        return key

    def save_plan(self, name: str, content: str, status: str = "draft") -> Plan:
        """Save a plan to storage.

        Args:
            name: Unique plan name
            content: Plan content (typically markdown)
            status: Plan status (draft, approved, completed)

        Returns:
            Saved Plan object

        Note:
            In MCP context, this translates to:
            context_save(key="plan:{name}", value=content, category="decision")
        """
        now = datetime.utcnow().isoformat()

        # Check if plan exists for update
        existing = self._local_store.get(name)
        created_at = existing.created_at if existing else now

        plan = Plan(
            name=name,
            content=content,
            created_at=created_at,
            updated_at=now,
            status=status,
        )

        self._local_store[name] = plan
        return plan

    def load_plan(self, name: str) -> Optional[Plan]:
        """Load a plan from storage.

        Args:
            name: Plan name to load

        Returns:
            Plan object if found, None otherwise

        Note:
            In MCP context, this translates to:
            context_get(key="plan:{name}")
        """
        return self._local_store.get(name)

    def list_plans(self, status: Optional[str] = None) -> list[Plan]:
        """List all stored plans.

        Args:
            status: Optional filter by status

        Returns:
            List of Plan objects

        Note:
            In MCP context, this translates to:
            context_get(keyPattern="plan:*")
        """
        plans = list(self._local_store.values())

        if status:
            plans = [p for p in plans if p.status == status]

        return sorted(plans, key=lambda p: p.updated_at, reverse=True)

    def delete_plan(self, name: str) -> bool:
        """Delete a plan from storage.

        Args:
            name: Plan name to delete

        Returns:
            True if deleted, False if not found
        """
        if name in self._local_store:
            del self._local_store[name]
            return True
        return False

    def update_status(self, name: str, status: str) -> Optional[Plan]:
        """Update a plan's status.

        Args:
            name: Plan name
            status: New status (draft, approved, completed)

        Returns:
            Updated Plan object if found, None otherwise
        """
        plan = self._local_store.get(name)
        if plan:
            return self.save_plan(name, plan.content, status)
        return None

    def export_plan(self, name: str) -> Optional[dict]:
        """Export a plan as a dictionary for serialization.

        Args:
            name: Plan name to export

        Returns:
            Dictionary representation of plan, or None if not found
        """
        plan = self.load_plan(name)
        if plan:
            return {
                "name": plan.name,
                "content": plan.content,
                "created_at": plan.created_at,
                "updated_at": plan.updated_at,
                "status": plan.status,
            }
        return None

    def import_plan(self, data: dict) -> Plan:
        """Import a plan from a dictionary.

        Args:
            data: Dictionary with plan data

        Returns:
            Imported Plan object
        """
        plan = Plan(
            name=data["name"],
            content=data["content"],
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            updated_at=data.get("updated_at", datetime.utcnow().isoformat()),
            status=data.get("status", "draft"),
        )
        self._local_store[plan.name] = plan
        return plan

    def get_mcp_instructions(self) -> str:
        """Get instructions for using memory-keeper MCP.

        Returns:
            Markdown instructions for MCP usage
        """
        return """
## Memory-Keeper MCP Usage for Plans

### Save a plan:
```
context_save(
    key="plan:{plan-name}",
    value="{plan-content}",
    category="decision",
    priority="high"
)
```

### Load a plan:
```
context_get(key="plan:{plan-name}")
```

### List all plans:
```
context_get(keyPattern="plan:*")
```

### Create checkpoint:
```
context_checkpoint(name="before-implementation")
```
"""
