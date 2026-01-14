---
description: Enter planning mode with memory-keeper persistence
arguments:
  - name: task
    description: The task name to plan for
    required: false
---

## Your Task

You are initiating the Plan Victor workflow for structured planning.

**Step 1: Acknowledge**

First, confirm to the user that you're starting the Plan Victor workflow. Say:

"Starting Plan Victor workflow. Let me check for existing plans and prepare for planning mode."

**Step 2: Check for Existing Plans**

Use the memory-keeper MCP to check for existing plans:

```
MCPSearch: select:mcp__memory-keeper__context_get
Then call: context_get with keyPattern="plan:*"
```

If plans exist, summarize them for the user.

**Step 3: Enter Planning Mode**

If this is an implementation task:

1. Use the EnterPlanMode tool to switch to planning mode
2. Explore the codebase to understand existing patterns
3. Create a detailed implementation plan
4. Save the plan to memory-keeper using context_save

**Step 4: Present Plan**

Present your plan to the user and wait for approval before proceeding with implementation.

## Memory-Keeper Commands

| Operation | Tool | Parameters |
|-----------|------|------------|
| Save plan | context_save | key="plan:{name}", value=content, category="decision" |
| Load plan | context_get | key="plan:{name}" |
| List plans | context_get | keyPattern="plan:*" |
| Checkpoint | context_checkpoint | name="before-{task}" |
