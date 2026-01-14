#!/bin/bash
# Install safe-mode settings to a specific directory
#
# Usage: ./install.sh /path/to/project
#
# This installs the safety settings to the target directory's .claude folder,
# making the restrictions apply ONLY to that directory when running Claude.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-.}"

if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: Directory '$TARGET_DIR' does not exist"
    exit 1
fi

# Create .claude directory structure
mkdir -p "$TARGET_DIR/.claude/hooks"

# Copy settings and hook
cp "$SCRIPT_DIR/settings.json" "$TARGET_DIR/.claude/settings.json"
cp "$SCRIPT_DIR/hooks/safe-bash-validator.sh" "$TARGET_DIR/.claude/hooks/"
chmod +x "$TARGET_DIR/.claude/hooks/safe-bash-validator.sh"

echo "✅ Safe mode installed to: $TARGET_DIR"
echo ""
echo "Blocked commands:"
echo "  • rm -rf, rm -r (recursive deletion)"
echo "  • chmod 777, chmod -R, chown -R"
echo "  • killall, pkill -9"
echo "  • mv/rm on system directories"
echo "  • curl/wget piped to shell"
echo "  • shutdown, reboot, halt"
echo ""
echo "Allowed:"
echo "  • sudo (with normal permission prompt)"
echo "  • Regular file operations"
echo ""
echo "Run 'claude' in $TARGET_DIR to use safe mode."
