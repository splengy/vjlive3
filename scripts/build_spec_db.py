#!/usr/bin/env python3
"""
build_spec_db.py — Seed / refresh WORKSPACE/spec_tracker.db

Scans docs/specs/_02_fleshed_out/ for all fleshed-out spec files and
populates a small SQLite database used by Antigravity to track implementation
status. Deliberately kept SEPARATE from vjlive3brain (21K legacy entries)
so pre-implementation noise does not contaminate the current-state picture.

Usage:
    python scripts/build_spec_db.py           # seed/refresh (idempotent)
    python scripts/build_spec_db.py --status  # print summary table
    python scripts/build_spec_db.py --pending # list specs awaiting implementation

Schema:
    specs(spec_id, name, spec_file, phase, category, status,
          impl_files, test_file, coverage_pct, as_built_date,
          implementing_agent, qdrant_ingested, notes,
          created_at, updated_at)
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (all relative to repo root, resolved at runtime)
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent.parent
SPECS_DIR = REPO_ROOT / "docs" / "specs" / "_02_fleshed_out"
DB_PATH   = REPO_ROOT / "WORKSPACE" / "spec_tracker.db"

# Marker that tells us a spec has been implemented + corrected
AS_BUILT_MARKER = "## As-Built Implementation Notes"

# ---- Schema ---------------------------------------------------------------
DDL = """
CREATE TABLE IF NOT EXISTS specs (
    spec_id             TEXT PRIMARY KEY,
    name                TEXT NOT NULL,
    spec_file           TEXT NOT NULL,
    phase               TEXT,
    category            TEXT,
    status              TEXT NOT NULL DEFAULT 'pending',
    impl_files          TEXT,          -- JSON array, e.g. ["src/vjlive3/audio/analyzer.py"]
    test_file           TEXT,
    coverage_pct        REAL,
    as_built_date       TEXT,
    implementing_agent  TEXT,
    qdrant_ingested     INTEGER NOT NULL DEFAULT 0,
    notes               TEXT,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY
);
"""

CURRENT_SCHEMA_VERSION = 1

# ---- Filename parser -------------------------------------------------------
# Matches:  P1-A1_audio_analyzer.md
#           P3-EXT013_bad_trip_datamosh.md
#           P1-AI2_agent_manager.md
_SPEC_RE = re.compile(
    r"^([A-Z][0-9]+-[A-Z]+[0-9]*(?:-[A-Z0-9]+)*)_(.+)\.md$",
    re.IGNORECASE,
)
_PHASE_RE = re.compile(r"^([A-Z]?[0-9]+)")
_CAT_RE   = re.compile(r"^[A-Z][0-9]+-([A-Z]+)")


def parse_spec_filename(path: Path) -> tuple[str, str, str, str] | None:
    """
    Return (spec_id, name, phase, category) or None if filename doesn't match.
    e.g. 'P1-A1_audio_analyzer.md' → ('P1-A1', 'audio_analyzer', 'P1', 'A')
    """
    m = _SPEC_RE.match(path.name)
    if not m:
        return None
    spec_id = m.group(1).upper()
    name    = m.group(2).lower().replace(" ", "_")
    phase_m = _PHASE_RE.match(spec_id)
    phase   = phase_m.group(0) if phase_m else ""
    cat_m   = _CAT_RE.match(spec_id)
    category = cat_m.group(1) if cat_m else ""
    return spec_id, name, phase, category


def detect_status(text: str) -> tuple[str, str | None, float | None]:
    """
    Return (status, as_built_date, coverage_pct) by scanning spec text.
    """
    if AS_BUILT_MARKER not in text:
        return "pending", None, None

    # Try to extract date and coverage from the as-built block
    date_m = re.search(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    cov_m  = re.search(r"\*\*Coverage:\*\*\s*(\d+(?:\.\d+)?)\s*%", text)
    date   = date_m.group(1) if date_m else None
    cov    = float(cov_m.group(1)) if cov_m else None
    return "done", date, cov


def detect_agent(text: str) -> str | None:
    m = re.search(r"\*\*Agent:\*\*\s*([^\s|]+)", text)
    return m.group(1) if m else None


# ---- Database helpers ------------------------------------------------------

def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.executescript(DDL)
    # Ensure schema version
    if not con.execute("SELECT 1 FROM schema_version").fetchone():
        con.execute("INSERT INTO schema_version VALUES (?)", (CURRENT_SCHEMA_VERSION,))
        con.commit()
    return con


def upsert_spec(con: sqlite3.Connection, row: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    existing = con.execute(
        "SELECT created_at FROM specs WHERE spec_id = ?", (row["spec_id"],)
    ).fetchone()
    if existing:
        con.execute(
            """UPDATE specs SET
                name=:name, spec_file=:spec_file, phase=:phase, category=:category,
                status=:status, impl_files=:impl_files, test_file=:test_file,
                coverage_pct=:coverage_pct, as_built_date=:as_built_date,
                implementing_agent=:implementing_agent, notes=:notes,
                updated_at=:updated_at
               WHERE spec_id=:spec_id""",
            {**row, "updated_at": now},
        )
    else:
        con.execute(
            """INSERT INTO specs
               (spec_id, name, spec_file, phase, category, status,
                impl_files, test_file, coverage_pct, as_built_date,
                implementing_agent, qdrant_ingested, notes, created_at, updated_at)
               VALUES
               (:spec_id,:name,:spec_file,:phase,:category,:status,
                :impl_files,:test_file,:coverage_pct,:as_built_date,
                :implementing_agent,0,:notes,:created_at,:updated_at)""",
            {**row, "created_at": now, "updated_at": now},
        )


# ---- Main seeder ----------------------------------------------------------

def seed(con: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {"inserted": 0, "updated": 0, "skipped": 0}

    for md_path in sorted(SPECS_DIR.glob("*.md")):
        parsed = parse_spec_filename(md_path)
        if not parsed:
            counts["skipped"] += 1
            continue
        spec_id, name, phase, category = parsed

        text = md_path.read_text(encoding="utf-8")
        status, as_built_date, coverage_pct = detect_status(text)
        agent = detect_agent(text) if status == "done" else None

        row = {
            "spec_id":            spec_id,
            "name":               name,
            "spec_file":          str(md_path.relative_to(REPO_ROOT)),
            "phase":              phase,
            "category":           category,
            "status":             status,
            "impl_files":         None,
            "test_file":          None,
            "coverage_pct":       coverage_pct,
            "as_built_date":      as_built_date,
            "implementing_agent": agent,
            "notes":              None,
        }

        existing = con.execute(
            "SELECT spec_id FROM specs WHERE spec_id=?", (spec_id,)
        ).fetchone()
        upsert_spec(con, row)
        if existing:
            counts["updated"] += 1
        else:
            counts["inserted"] += 1

    con.commit()
    return counts


# ---- CLI reporting --------------------------------------------------------

def print_summary(con: sqlite3.Connection) -> None:
    rows = con.execute(
        """SELECT status, COUNT(*) as n FROM specs GROUP BY status ORDER BY n DESC"""
    ).fetchall()
    total = con.execute("SELECT COUNT(*) FROM specs").fetchone()[0]
    print(f"\n{'='*50}")
    print(f"  spec_tracker.db — {total} fleshed-out specs")
    print(f"{'='*50}")
    for r in rows:
        bar = "█" * (r["n"] // 5 + 1)
        print(f"  {r['status']:15s} {r['n']:4d}  {bar}")
    done = con.execute("SELECT COUNT(*) FROM specs WHERE status='done'").fetchone()[0]
    if total:
        pct = done / total * 100
        print(f"\n  Progress: {done}/{total} ({pct:.1f}%)")
    print()


def print_pending(con: sqlite3.Connection) -> None:
    rows = con.execute(
        """SELECT spec_id, name, phase, category
           FROM specs WHERE status='pending'
           ORDER BY phase, category, spec_id"""
    ).fetchall()
    print(f"\n{'='*60}")
    print(f"  PENDING specs ({len(rows)} total)")
    print(f"{'='*60}")
    for r in rows:
        print(f"  [{r['phase']:3s}] {r['spec_id']:20s}  {r['name']}")
    print()


# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Build / query spec_tracker.db")
    parser.add_argument("--status",  action="store_true", help="Print status summary")
    parser.add_argument("--pending", action="store_true", help="List pending specs")
    args = parser.parse_args()

    con = open_db(DB_PATH)
    counts = seed(con)
    print(f"Seeded: +{counts['inserted']} new, ~{counts['updated']} updated, "
          f"{counts['skipped']} skipped (filename mismatch)")

    if args.status or not any(vars(args).values()):
        print_summary(con)
    if args.pending:
        print_pending(con)


if __name__ == "__main__":
    main()
