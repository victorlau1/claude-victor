---
name: plan-victor
description: Enter planning mode and store plan in memory-keeper for persistence across sessions
arguments:
  - name: task
    description: The task name to plan for
    required: false
---

# Plan Victor Workflow

This command initiates a structured planning workflow that:
1. Checks memory-keeper for existing plan context
2. Enters plan mode for implementation tasks
3. Designs approach with user approval
4. Saves approved plan to memory-keeper
5. Exits plan mode ready for implementation

## Usage

```
/plan-victor [task-name]
```

## Workflow Steps

### Step 1: Check for Existing Context

First, check if there's an existing plan in memory-keeper:

```
Use memory-keeper MCP:
context_get(keyPattern="plan:*")
```

If a plan exists for the task, load it and resume from the saved state.

### Step 2: Enter Plan Mode

For new tasks or significant implementation work:

1. Use EnterPlanMode to switch to planning mode
2. Explore the codebase to understand existing patterns
3. Identify files that need modification

### Step 3: Design the Implementation

Create a detailed plan including:

- Files to create/modify
- Implementation steps in order
- Test cases to write
- Potential risks or edge cases

### Step 4: Save Plan to Memory-Keeper

Save the plan for persistence:

```
Use memory-keeper MCP:
context_save(
    key="plan:{task-name}",
    value="{plan-content-as-markdown}",
    category="decision",
    priority="high"
)
```

### Step 5: Get User Approval

Present the plan to the user and wait for approval before proceeding.

### Step 6: Exit Plan Mode

Once approved:

```
Use memory-keeper MCP:
context_save(
    key="plan:{task-name}",
    value="{approved-plan}",
    category="decision"
)
```

Then use ExitPlanMode to begin implementation.

## Memory-Keeper Integration

All plans are stored with the prefix `plan:` for easy retrieval:

| Operation | MCP Call |
|-----------|----------|
| Save plan | `context_save(key="plan:{name}", value=content)` |
| Load plan | `context_get(key="plan:{name}")` |
| List plans | `context_get(keyPattern="plan:*")` |
| Checkpoint | `context_checkpoint(name="before-{task}")` |

## Best Practices

1. **Always plan before implementing** - Use this command for any non-trivial task
2. **Save frequently** - Update the plan in memory-keeper as it evolves
3. **Create checkpoints** - Before major changes, create a checkpoint
4. **Review existing plans** - Check for related plans before starting new work
