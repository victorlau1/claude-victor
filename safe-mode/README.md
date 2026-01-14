# Claude Code Safe Mode

Safety settings to prevent dangerous bash commands from executing without explicit permission.

## What Gets Blocked

- `rm -rf` and recursive deletions
- `sudo` and privilege escalation
- Disk operations (`dd`, `mkfs`, `fdisk`)
- Fork bombs and resource exhaustion
- Remote code execution (`curl | sh`, `wget | bash`)
- System shutdown/reboot commands
- Mass process killing (`killall -9`, `pkill -9`)
- Dangerous permission changes (`chmod 777`, `chmod -R`)
- Operations on critical paths (`/`, `/usr`, `/etc`, `~/.ssh`, etc.)

## Installation

### Option 1: Copy to Project

Copy `settings.json` to your project's `.claude/settings.json`:

```bash
cp safe-mode/settings.json /path/to/project/.claude/settings.json
```

Make sure to also copy the hooks:

```bash
mkdir -p /path/to/project/.claude/hooks
cp safe-mode/hooks/safe-bash-validator.sh /path/to/project/.claude/hooks/
```

### Option 2: Use as User Settings

Copy to your global Claude settings:

```bash
# Backup existing settings first
cp ~/.claude/settings.json ~/.claude/settings.json.backup

# Merge or replace with safe mode settings
cp safe-mode/settings.json ~/.claude/settings.json
```

## Testing

Run Claude in a test directory and try a dangerous command:

```bash
cd /tmp/safe-mode-test
mkdir -p .claude/hooks
cp /path/to/claude-victor/safe-mode/settings.json .claude/
cp /path/to/claude-victor/safe-mode/hooks/safe-bash-validator.sh .claude/hooks/
chmod +x .claude/hooks/safe-bash-validator.sh

claude
```

Then ask Claude to run: `rm -rf /tmp/test`

The command should be blocked with an error message.

## How It Works

1. **Permission Deny Rules**: The `settings.json` contains deny patterns that block common dangerous command forms
2. **PreToolUse Hook**: The `safe-bash-validator.sh` script runs before every Bash command and uses regex matching to catch more sophisticated patterns

## Customization

Edit `settings.json` to add/remove deny rules:

```json
{
  "permissions": {
    "deny": [
      "Bash(your-pattern-here *)"
    ],
    "allow": [
      "Bash(safe-command-here)"
    ]
  }
}
```

Edit `safe-bash-validator.sh` to add regex patterns:

```bash
DANGEROUS_PATTERNS=(
    'your-regex-pattern'
)
```
