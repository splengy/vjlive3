#!/usr/bin/env python3
"""
Standalone seeder script — safe to run from any directory.
Sets sys.path from the script's own location.

Usage:
    python3 scripts/seed_brain.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import logging  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from mcp_servers.vjlive3brain.db import ConceptDB  # noqa: E402
from mcp_servers.vjlive3brain.seeder import run_full_seed  # noqa: E402

DB_PATH = str(REPO / "mcp_servers" / "vjlive3brain" / "brain.db")

print(f"[seed_brain] repo={REPO}")
print(f"[seed_brain] db={DB_PATH}")

db = ConceptDB(DB_PATH)
db.initialize()
run_full_seed(db)

stats = db.stats()
print(f"\n[seed_brain] DONE — {stats}")
