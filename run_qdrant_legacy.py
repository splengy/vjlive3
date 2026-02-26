#!/usr/bin/env python3
"""
run_qdrant_legacy.py — qdrant-legacy MCP server launcher (stdio for Roo and Antigravity)
"""
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO))
os.environ.setdefault("PYTHONPATH", str(_REPO))
os.environ.setdefault("VJLIVE3_ROOT", str(_REPO))

from mcp_servers.qdrant_legacy.server import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")
