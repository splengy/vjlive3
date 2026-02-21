#!/usr/bin/env python3
"""
Writes/merges the vjlive3brain entry into claude_desktop_config.json.
Safe to run from any directory.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CONFIG_PATH = Path.home() / ".config" / "claude" / "claude_desktop_config.json"
CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

# Load existing or start fresh
if CONFIG_PATH.exists():
    with open(CONFIG_PATH) as f:
        config = json.load(f)
    print(f"[config] Loaded existing: {CONFIG_PATH}")
else:
    config = {}
    print(f"[config] Creating new: {CONFIG_PATH}")

config.setdefault("mcpServers", {})

config["mcpServers"]["vjlive3brain"] = {
    "command": "python3",
    "args": [str(REPO / "run_brain.py")],
    "env": {
        "PYTHONPATH": str(REPO),
        "VJLIVE3_BRAIN_DB": str(REPO / "mcp_servers" / "vjlive3brain" / "brain.db"),
    },
}

with open(CONFIG_PATH, "w") as f:
    json.dump(config, f, indent=2)

print(f"[config] Written: {CONFIG_PATH}")
print(json.dumps(config["mcpServers"]["vjlive3brain"], indent=2))
