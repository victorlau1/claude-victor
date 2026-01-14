#!/usr/bin/env python3
"""Configure Claude-Victor plugin by adding local marketplace to Claude's known marketplaces."""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone


def main():
    # Get plugin path (directory containing this script's parent)
    plugin_path = str(Path(__file__).parent.parent.absolute())

    # Get Claude known_marketplaces file path
    known_marketplaces_file = Path.home() / ".claude" / "plugins" / "known_marketplaces.json"

    # Ensure .claude/plugins directory exists
    known_marketplaces_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing marketplaces or create empty
    if known_marketplaces_file.exists():
        with open(known_marketplaces_file, 'r') as f:
            try:
                marketplaces = json.load(f)
            except json.JSONDecodeError:
                marketplaces = {}
    else:
        marketplaces = {}

    # Add local marketplace
    marketplaces['local'] = {
        'source': {
            'source': 'directory',
            'path': plugin_path
        },
        'installLocation': plugin_path,
        'lastUpdated': datetime.now(timezone.utc).isoformat()
    }

    # Write marketplaces
    with open(known_marketplaces_file, 'w') as f:
        json.dump(marketplaces, f, indent=2)

    print(f"Local marketplace added to Claude known marketplaces")
    print(f"Plugin path: {plugin_path}")
    print(f"Marketplaces file: {known_marketplaces_file}")
    print()
    print("Next steps:")
    print("1. Restart Claude Code")
    print("2. Run '/plugin install claude-victor@local' to install the plugin")
    print("3. Use '/claude-victor:plan-victor' to invoke the planning workflow")


if __name__ == '__main__':
    main()
