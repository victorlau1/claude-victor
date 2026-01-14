#!/bin/bash
# Enforce Planning Hook for Claude-Victor
#
# This hook runs on UserPromptSubmit to remind about planning.
# It's optional and can be disabled by removing from plugin.json.
#
# Note: This is a soft enforcement - it outputs a reminder but
# doesn't block execution. For strict enforcement, exit with
# non-zero code.

# Get the user prompt from stdin or first argument
PROMPT="${1:-$(cat)}"

# Keywords that suggest implementation work
IMPLEMENTATION_KEYWORDS=(
    "implement"
    "create"
    "add"
    "build"
    "fix"
    "refactor"
    "update"
    "modify"
    "change"
    "write"
)

# Keywords that suggest planning is not needed
SKIP_KEYWORDS=(
    "plan"
    "what"
    "how"
    "why"
    "explain"
    "show"
    "list"
    "?"
)

# Convert prompt to lowercase for comparison
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# Check if this looks like a planning or question prompt
for keyword in "${SKIP_KEYWORDS[@]}"; do
    if [[ "$PROMPT_LOWER" == *"$keyword"* ]]; then
        # This is a question or planning prompt, no reminder needed
        exit 0
    fi
done

# Check if this looks like implementation work
for keyword in "${IMPLEMENTATION_KEYWORDS[@]}"; do
    if [[ "$PROMPT_LOWER" == *"$keyword"* ]]; then
        # This looks like implementation work
        echo "---"
        echo "PLANNING REMINDER: Consider using /plan-victor before implementing."
        echo "This ensures your work is saved to memory-keeper for session persistence."
        echo "---"
        exit 0
    fi
done

# Default: no action needed
exit 0
