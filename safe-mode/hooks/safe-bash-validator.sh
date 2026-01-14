#!/bin/bash
# Safe Bash Validator Hook for Claude-Victor
#
# This hook validates bash commands before execution and blocks
# dangerous operations that could harm the system.
#
# Exit codes:
#   0 - Allow command
#   2 - Block command (shows stderr as error message)

set -e

# Read the tool input from stdin
INPUT=$(cat)

# Extract the command from JSON input
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Handle nested structure from hook input
    if 'tool_input' in data:
        print(data['tool_input'].get('command', ''))
    else:
        print(data.get('command', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
    # No command found, allow (might be malformed input)
    exit 0
fi

# =============================================================================
# DANGEROUS COMMAND PATTERNS
# =============================================================================

declare -a DANGEROUS_PATTERNS=(
    # Recursive deletion
    'rm\s+(-[a-zA-Z]*r[a-zA-Z]*\s+|--recursive)'
    'rm\s+-[a-zA-Z]*f[a-zA-Z]*\s+-[a-zA-Z]*r'
    'rm\s+-rf'
    'rm\s+-fr'

    # Root/system directory operations (rm)
    'rm\s+/($|\s)'
    'rm\s+/usr'
    'rm\s+/bin'
    'rm\s+/etc'
    'rm\s+/var'
    'rm\s+/System'
    'rm\s+/Library'
    'rm\s+/Applications'
    'rm\s+~/Library'
    'rm\s+~/.ssh'
    'rm\s+~/.gnupg'

    # Root/system directory operations (mv)
    'mv\s+/\s'
    'mv\s+/usr'
    'mv\s+/bin'
    'mv\s+/etc'
    'mv\s+/var'
    'mv\s+/home'
    'mv\s+/System'
    'mv\s+/Library'

    # Destructive disk operations
    'mkfs'
    'dd\s+if='
    'dd\s+of=/dev'
    'wipefs'
    'fdisk'
    'parted'

    # Fork bombs and resource exhaustion
    ':\(\)\s*{\s*:\|:&\s*};'
    'while\s+true.*fork'

    # Remote code execution
    'curl.*\|\s*(ba)?sh'
    'wget.*\|\s*(ba)?sh'
    'curl.*\|\s*python'
    'wget.*\|\s*python'

    # System shutdown/reboot
    'shutdown'
    'reboot'
    'halt'
    'init\s+[06]'
    'systemctl\s+(poweroff|reboot|halt)'

    # Mass process killing
    'killall'
    'pkill\s+-9'
    'kill\s+-9\s+-1'

    # Dangerous permission changes
    'chmod\s+777'
    'chmod\s+-R'
    'chown\s+-R'

    # Dangerous redirects
    '>\s*/dev/(sda|hd|nvme)'
    'cat\s+/dev/zero\s*>'
    'cat\s+/dev/urandom\s*>'

    # History/credential destruction
    'rm\s+.*\.bash_history'
    'rm\s+.*\.zsh_history'
    'rm\s+.*\.gitconfig'
    'rm\s+.*\.npmrc'
    'rm\s+.*\.pypirc'

    # Network attacks
    'iptables\s+-F'
    'iptables\s+--flush'
)

# =============================================================================
# VALIDATION LOGIC
# =============================================================================

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
    if echo "$COMMAND" | grep -qEi "$pattern"; then
        echo "🛑 BLOCKED: Dangerous command detected" >&2
        echo "" >&2
        echo "Command: $COMMAND" >&2
        echo "Matched pattern: $pattern" >&2
        echo "" >&2
        echo "This command has been blocked for safety. If you need to run" >&2
        echo "this command, please execute it manually in your terminal." >&2
        exit 2
    fi
done

# =============================================================================
# PATH SAFETY CHECK
# =============================================================================

CRITICAL_PATHS=(
    "^/"
    "/usr"
    "/bin"
    "/sbin"
    "/etc"
    "/var"
    "/System"
    "/Library"
    "/Applications"
    "~/.ssh"
    "~/.gnupg"
)

# Check for rm commands targeting critical paths
if echo "$COMMAND" | grep -qE "^rm\s+" ; then
    for path in "${CRITICAL_PATHS[@]}"; do
        if echo "$COMMAND" | grep -qE "rm\s+[^|;]*$path"; then
            echo "🛑 BLOCKED: Cannot delete critical system path" >&2
            echo "" >&2
            echo "Command: $COMMAND" >&2
            echo "Protected path: $path" >&2
            exit 2
        fi
    done
fi

# =============================================================================
# ALLOW COMMAND
# =============================================================================

exit 0
