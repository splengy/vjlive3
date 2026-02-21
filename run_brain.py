#!/usr/bin/env python3
"""
run_brain.py — vjlive3brain MCP server launcher

Usage:
    # Start MCP server (stdio, for Claude Desktop / Roo):
    python run_brain.py

    # Seed the knowledge base from legacy sources then start:
    python run_brain.py --seed

    # Smoke test:
    python run_brain.py --test

    # Seed + watch for changes (background process):
    python run_brain.py --watch
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent


def _run(module: str, extra_args: list[str] | None = None) -> int:
    cmd = [sys.executable, "-m", module] + (extra_args or [])
    try:
        result = subprocess.run(cmd, cwd=str(_REPO_ROOT))
        return result.returncode
    except KeyboardInterrupt:
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description="vjlive3brain — VJLive3 Knowledge Base MCP Server"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed the knowledge base from all legacy sources, then exit",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Seed then watch for file changes (keeps running)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run smoke test and exit",
    )
    args = parser.parse_args()

    if args.test:
        sys.exit(_run("mcp_servers.vjlive3brain.server", ["--test"]))

    if args.seed:
        rc = _run("mcp_servers.vjlive3brain.seeder", ["--seed"])
        if rc != 0:
            sys.exit(rc)
        print("Seed complete. Start MCP server with: python run_brain.py")
        sys.exit(0)

    if args.watch:
        # Run watcher in background via subprocess, then start MCP server
        import multiprocessing

        def _watch_target() -> None:
            _run("mcp_servers.vjlive3brain.seeder", ["--watch"])

        watcher = multiprocessing.Process(target=_watch_target, daemon=True)
        watcher.start()
        print(f"Watcher started (PID {watcher.pid}). Launching MCP server…")

    # Default: run the MCP stdio server
    sys.exit(_run("mcp_servers.vjlive3brain.server"))


if __name__ == "__main__":
    main()
