"""
vjlive-switchboard — MCP Agent Communication & Lock Manager (FastMCP transport)

Exposes 6 tools via stdio MCP:
  checkout_file, checkin_file, get_locks, is_locked, post_message, get_messages

Run: python run_switchboard.py
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Resolve repo root regardless of CWD
_REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO))

os.environ.setdefault(
    "VJLIVE3_ROOT", str(_REPO)
)

from mcp.server.fastmcp import FastMCP  # noqa: E402

# Import business logic and set absolute repo root (fixes all 3 path globals)
from mcp_servers.vjlive_switchboard.server import VJLiveSwitchboard, set_repo_root  # noqa: E402
set_repo_root(_REPO)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
_logger = logging.getLogger("vjlive3.mcp.switchboard.fastmcp")

mcp = FastMCP(
    name="vjlive-switchboard",
    instructions=(
        "Inter-agent communication hub and file lock manager for VJLive3. "
        "Prevents file collisions. Enforces Manager → Worker information flow. "
        "Channels: general | decisions | dreamer | blockers"
    ),
)

_board = VJLiveSwitchboard()


@mcp.tool()
def checkout_file(file_path: str, agent_id: str, eta_mins: int = 30) -> dict:
    """Check out a file for exclusive editing. Returns {ok, message}."""
    success = _board.checkout_file(file_path, agent_id, eta_mins)
    return {
        "ok": success,
        "message": (
            f"Lock acquired: {file_path} → {agent_id} (ETA {eta_mins}m)"
            if success
            else f"DENIED: {file_path} is locked by another agent"
        ),
    }


@mcp.tool()
def checkin_file(file_path: str, agent_id: str) -> dict:
    """Release a file lock. Returns {ok, message}."""
    success = _board.checkin_file(file_path, agent_id)
    return {
        "ok": success,
        "message": (
            f"Released: {file_path}"
            if success
            else f"FAILED: {file_path} not locked or wrong agent"
        ),
    }


@mcp.tool()
def get_locks() -> list[dict]:
    """Return all currently active (non-expired) file locks."""
    locks = _board.get_locks()
    return [
        {
            "file_path": lock.file_path,
            "agent_id": lock.agent_id,
            "checked_out": lock.checked_out,
            "eta_mins": lock.eta_mins,
            "status": lock.status,
        }
        for lock in locks
    ]


@mcp.tool()
def is_locked(file_path: str) -> dict:
    """Check if a file is currently locked. Returns lock info or {locked: false}."""
    lock = _board.is_locked(file_path)
    if lock is None:
        return {"locked": False}
    return {
        "locked": True,
        "agent_id": lock.agent_id,
        "checked_out": lock.checked_out,
        "eta_mins": lock.eta_mins,
    }


@mcp.tool()
def post_message(agent_id: str, content: str, channel: str = "general") -> dict:
    """Post a message to an agent channel (general|decisions|dreamer|blockers)."""
    _board.post_message(agent_id, content, channel)
    return {"ok": True, "channel": channel, "agent_id": agent_id}


@mcp.tool()
def get_messages(channel: str = "general", limit: int = 20) -> list[dict]:
    """Retrieve recent messages from a channel (newest first)."""
    msgs = _board.get_messages(channel, limit)
    return [
        {
            "agent_id": m.agent_id,
            "channel": m.channel,
            "content": m.content,
            "timestamp": m.timestamp,
        }
        for m in msgs
    ]


@mcp.tool()
def queue_task(task_id: str, spec_path: str) -> dict:
    """Manager pushes a new task spec to the queue for a worker to pick up. Returns {ok, message}."""
    success = _board.queue_task(task_id, spec_path)
    return {
        "ok": success,
        "message": f"Task {task_id} added to the queue" if success else f"Failed to queue task {task_id}",
    }


@mcp.tool()
def request_work(worker_name: str) -> dict:
    """Worker pulls the highest priority available task from the queue. Returns {task_id, spec_path} or empty if no work."""
    task = _board.request_work(worker_name)
    if task is None:
        return {"has_work": False}
    return {
        "has_work": True,
        "task_id": task.task_id,
        "spec_path": task.spec_path,
        "status": task.status,
    }


@mcp.tool()
def complete_task(task_id: str) -> dict:
    """Worker marks a task as completed once tests pass. Returns {ok, message}."""
    success = _board.complete_task(task_id)
    return {
        "ok": success,
        "message": f"Task {task_id} marked complete" if success else f"Failed to mark task {task_id} complete",
    }


def main() -> None:
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "--test":
        _logger.info("Running switchboard smoke test...")
        ok = _board.smoke_test()
        _logger.info("Smoke test: %s", "PASS" if ok else "FAIL")
        _sys.exit(0 if ok else 1)

    port = 8000
    try:
        import uvicorn
        import starlette
    except ImportError:
        _logger.error("SSE transport requires 'uvicorn' and 'starlette'. Please run: pip install uvicorn starlette sse-starlette")
        _sys.exit(1)

    _logger.info(f"vjlive-switchboard MCP server starting (SSE transport on port {port})")
    mcp.settings.port = port
    mcp.settings.host = "127.0.0.1"
    mcp.run(transport="sse")


if __name__ == "__main__":
    main()
