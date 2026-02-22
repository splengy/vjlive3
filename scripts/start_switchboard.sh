#!/bin/bash
# start_switchboard.sh
# Boots the vjlive_switchboard MCP server as an SSE background service on port 8000.

# Resolve absolute path to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting VJLive3 Switchboard Orchestrator on port 8000..."
cd "$ROOT_DIR" || exit 1

# Activate venv and run via FastMCP's SSE transport
source .venv/bin/activate
export PYTHONPATH="$ROOT_DIR"
python mcp_servers/vjlive_switchboard/fastmcp_server.py &

PID=$!
echo "Switchboard running with PID $PID"
echo "To view logs: tail -f WORKSPACE/COMMS/AGENT_SYNC.md"
