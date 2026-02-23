#!/usr/bin/env python3
"""
run_switchboard_stdio.py — vjlive-switchboard MCP server launcher (stdio for clients like Roo and Antigravity)
"""
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent
sys.path.insert(0, str(_REPO))
os.environ.setdefault("PYTHONPATH", str(_REPO))
os.environ.setdefault("VJLIVE3_ROOT", str(_REPO))

# Import the server mcp instance
from mcp_servers.vjlive_switchboard.fastmcp_server import mcp

if __name__ == "__main__":
    import asyncio
    
    # FastMCP uses the underlying MCP server. To force stdio, we can either
    # use the mcp.run() without transport specified (default is stdio)
    mcp.run(transport="stdio")
