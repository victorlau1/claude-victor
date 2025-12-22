#!/usr/bin/env python3
"""Configure Claude-Victor plugin by adding local marketplace to Claude settings."""

import json
import os
import sys
from pathlib import Path


def main():
    # Get plugin path (directory containing this script's parent)
    plugin_path = str(Path(__file__).parent.parent.absolute())

    # Get Claude settings file path
    settings_file = Path.home() / ".claude" / "settings.json"

    # Ensure .claude directory exists
    settings_file.parent.mkdir(parents=True, exist_ok=True)

    # Load existing settings or create empty
    if settings_file.exists():
        with open(settings_file, 'r') as f:
            try:
                settings = json.load(f)
            except json.JSONDecodeError:
                settings = {}
    else:
        settings = {}

    # Add extraKnownMarketplaces if not present
    if 'extraKnownMarketplaces' not in settings:
        settings['extraKnownMarketplaces'] = {}

    # Add local marketplace
    settings['extraKnownMarketplaces']['local'] = {
        'source': {
            'source': 'directory',
            'path': plugin_path
        }
    }

    # Write settings
    with open(settings_file, 'w') as f:
        json.dump(settings, f, indent=4)

    print(f"Local marketplace added to Claude settings")
    print(f"Plugin path: {plugin_path}")
    print(f"Settings file: {settings_file}")
    print()
    print("Next step: Run '/plugin install claude-victor@local' in Claude Code")


if __name__ == '__main__':
    main()
