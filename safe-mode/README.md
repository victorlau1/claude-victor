# Claude Code Safe Mode

Directory-specific safety settings that block dangerous bash commands.

## Quick Install

```bash
# Install to a specific directory
./install.sh /path/to/your/project

# Or install to current directory
./install.sh .
```

This creates `.claude/settings.json` and `.claude/hooks/` in the target directory. The safety rules only apply when running `claude` from that directory.

## What Gets Blocked

| Command | Reason |
|---------|--------|
| `rm -rf`, `rm -r` | Recursive deletion |
| `chmod 777`, `chmod -R` | Dangerous permission changes |
| `chown -R` | Recursive ownership changes |
| `killall`, `pkill -9` | Mass process killing |
| `mv /usr`, `rm /etc`, etc. | System directory operations |
| `curl \| bash`, `wget \| sh` | Remote code execution |
| `shutdown`, `reboot`, `halt` | System power commands |
| `dd`, `mkfs`, `fdisk` | Disk operations |

## What's Allowed

| Command | Notes |
|---------|-------|
| `sudo` | Allowed (Claude will still prompt for permission) |
| `rm file.txt` | Regular file deletion (non-recursive) |
| `chmod 644` | Normal permission changes |
| All other commands | Normal operation |

## How It Works

1. **Permission Deny Rules** (`settings.json`): Pattern-based blocking at the Claude permission layer
2. **PreToolUse Hook** (`safe-bash-validator.sh`): Regex-based validation before any Bash command executes

Both layers must pass for a command to run.

## Directory-Specific

These settings only apply to the directory where they're installed. Other directories are unaffected.

```
/my-project/           ← Safe mode active here
  .claude/
    settings.json
    hooks/
      safe-bash-validator.sh

/other-project/        ← Normal Claude behavior
```

## Manual Installation

If you prefer not to use the install script:

```bash
mkdir -p /your/project/.claude/hooks
cp settings.json /your/project/.claude/
cp hooks/safe-bash-validator.sh /your/project/.claude/hooks/
chmod +x /your/project/.claude/hooks/safe-bash-validator.sh
```

## Testing

```bash
# Install to test directory
./install.sh /tmp/safe-test

# Run Claude there
cd /tmp/safe-test && claude

# Ask Claude to run: rm -rf testfile.txt
# It should be blocked
```

## Customization

Edit `settings.json` to modify deny rules:

```json
{
  "permissions": {
    "deny": [
      "Bash(your-pattern *)"
    ]
  }
}
```

Edit `hooks/safe-bash-validator.sh` to add regex patterns:

```bash
DANGEROUS_PATTERNS=(
    'your-regex-here'
)
```
