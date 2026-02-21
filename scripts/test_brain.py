#!/usr/bin/env python3
"""
Standalone smoke-test for vjlive3brain.
Run from any directory:
    python scripts/test_brain.py
"""
import sys
import os
from pathlib import Path

# Always resolve to repo root regardless of cwd
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from mcp_servers.vjlive3brain.db import ConceptDB  # noqa: E402
from mcp_servers.vjlive3brain.schema import (  # noqa: E402
    ConceptEntry, DreamerVerdict, LogicPurity, RoleAssignment,
)

DB_PATH = "/tmp/vjlive3brain_smoketest.db"


def main() -> None:
    print(f"[vjlive3brain smoke-test] repo={REPO}")

    db = ConceptDB(DB_PATH)
    db.initialize()
    print("  ✓ DB initialized")

    entry = ConceptEntry(
        concept_id="__smoke__",
        name="Smoke Test",
        description="Temporary health-check entry.",
        origin_ref="none",
        source_files=[],
        dreamer_flag=False,
        dreamer_analysis="",
        dreamer_verdict=DreamerVerdict.PENDING,
        logic_purity=LogicPurity.CLEAN,
        role_assignment=RoleAssignment.WORKER,
        kitten_status=False,
        tags=["test"],
        category="test",
        performance_impact="low",
        ported_to="",
    )
    db.upsert(entry)
    print("  ✓ Concept upserted")

    retrieved = db.get("__smoke__")
    assert retrieved is not None, "Retrieved entry is None!"
    assert retrieved.name == "Smoke Test", f"Wrong name: {retrieved.name}"
    print(f"  ✓ Concept retrieved: {retrieved.concept_id}")

    results = db.search(query="Smoke")
    assert any(r.concept_id == "__smoke__" for r in results), "FTS search failed!"
    print(f"  ✓ FTS search returned {len(results)} result(s)")

    stats = db.stats()
    print(f"  ✓ Stats: {stats}")

    db.delete("__smoke__")
    assert db.get("__smoke__") is None
    print("  ✓ Entry deleted")

    os.unlink(DB_PATH)
    print("\n  ✅ vjlive3brain smoke test: PASS")


if __name__ == "__main__":
    main()
