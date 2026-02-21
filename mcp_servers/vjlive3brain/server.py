"""
vjlive3brain — MCP Knowledge Base Server

The Repository of Truth for VJLive3.
Indexes legacy codebase concepts and provides lookup for all agents.

Tools exposed:
  - get_concept(concept_id)               → ConceptEntry JSON
  - search_concepts(query, tags, ...)     → list[ConceptEntry JSON]
  - list_concepts(category, role, ported) → list[ConceptEntry JSON]
  - add_concept(entry_json)               → concept_id
  - update_concept(concept_id, **fields)  → status
  - flag_dreamer(concept_id, analysis, verdict) → status
  - get_stats()                           → dict

Run (stdio — for Claude Desktop / Roo):
  python -m mcp_servers.vjlive3brain.server

Run (smoke-test):
  python -m mcp_servers.vjlive3brain.server --test
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp.server.fastmcp import FastMCP

from mcp_servers.vjlive3brain.db import ConceptDB
from mcp_servers.vjlive3brain.schema import (
    ConceptEntry,
    DreamerVerdict,
    LogicPurity,
    RoleAssignment,
)

_logger = logging.getLogger("vjlive3.mcp.vjlive3brain")

# ─── Default DB path (relative to repo root, or override via env) ─────────────
import os as _os

_DB_PATH = _os.environ.get(
    "VJLIVE3_BRAIN_DB",
    _os.path.join(
        _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))),
        "mcp_servers", "vjlive3brain", "brain.db",
    ),
)

# ─── Initialise DB once at import time ────────────────────────────────────────
_db = ConceptDB(_DB_PATH)
_db.initialize()

# ─── FastMCP server ───────────────────────────────────────────────────────────
mcp = FastMCP(
    name="vjlive3brain",
    instructions=(
        "The Repository of Truth for VJLive3. "
        "Query this BEFORE writing any code (PRIME_DIRECTIVE Rule 1). "
        "search_concepts() and get_concept() are read-only and safe for all agents. "
        "add_concept/update_concept/flag_dreamer are Manager-only write tools."
    ),
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _entry_to_dict(entry: ConceptEntry) -> dict[str, Any]:
    """Serialize a ConceptEntry to a plain dict for JSON transport."""
    return entry.model_dump()


# ─── READ tools (all agents) ─────────────────────────────────────────────────

@mcp.tool()
def get_concept(concept_id: str) -> str:
    """
    Retrieve a single concept by its unique ID.

    Args:
        concept_id: Slug, e.g. 'vimana-depth-mosh'

    Returns:
        JSON-serialised ConceptEntry, or '{}' if not found.
    """
    entry = _db.get(concept_id)
    if entry is None:
        return "{}"
    return json.dumps(_entry_to_dict(entry), indent=2)


@mcp.tool()
def search_concepts(
    query: str = "",
    tags: str = "",
    role: str = "",
    category: str = "",
    origin: str = "",
    dreamer_only: bool = False,
) -> str:
    """
    Search the knowledge base for concepts.

    Args:
        query:       Text to match against name / description (FTS5).
        tags:        Comma-separated tags; concept must have ALL of them.
        role:        'manager' | 'worker'
        category:    'engine' | 'plugin' | 'ui' | 'hardware' | 'dreamer'
        origin:      'vjlive-v1' | 'vjlive-v2' | 'both' | 'none'
        dreamer_only: If true, only Dreamer-flagged entries.

    Returns:
        JSON array of matching ConceptEntry objects.
    """
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    results = _db.search(
        query=query,
        tags=tag_list,
        role=role or None,
        category=category or None,
        origin=origin or None,
        dreamer_only=dreamer_only,
    )
    return json.dumps([_entry_to_dict(r) for r in results], indent=2)


@mcp.tool()
def list_concepts(
    category: str = "",
    role: str = "",
    ported: str = "",
) -> str:
    """
    List all concepts, optionally filtered.

    Args:
        category: Filter by category string.
        role:     'manager' | 'worker'
        ported:   'yes' | 'no' | '' (all)

    Returns:
        JSON array of ConceptEntry objects.
    """
    ported_bool: bool | None = None
    if ported.lower() == "yes":
        ported_bool = True
    elif ported.lower() == "no":
        ported_bool = False

    results = _db.list_all(
        category=category or None,
        role=role or None,
        ported=ported_bool,
    )
    return json.dumps([_entry_to_dict(r) for r in results], indent=2)


@mcp.tool()
def get_stats() -> str:
    """
    Return summary statistics about the knowledge base.

    Returns:
        JSON with keys: total, ported, unported, dreamer.
    """
    return json.dumps(_db.stats(), indent=2)


@mcp.tool()
def reseed_brain(mode: str = "docs") -> str:
    """
    Re-populate the brain database without restarting the server.
    MANAGER AGENT ONLY.

    Args:
        mode: What to re-seed:
              'docs'   — re-index all markdown docs (WORKSPACE, specs, legacy) [fast ~5s]
              'enrich' — re-run porting maps, nav guides, plugin manifests [fast ~5s]
              'full'   — full Python + docs + enrichment [slow ~60s]

    Returns:
        JSON with status and new stats.
    """
    try:
        if mode == "docs":
            from mcp_servers.vjlive3brain.seeder import run_doc_seed
            run_doc_seed(_db)
        elif mode == "enrich":
            from mcp_servers.vjlive3brain.enricher import run_enrichment
            run_enrichment(_db)
        elif mode == "full":
            from mcp_servers.vjlive3brain.seeder import run_full_seed
            run_full_seed(_db)
        else:
            return json.dumps({"status": "error", "message": f"Unknown mode '{mode}'. Use: docs | enrich | full"})
        stats = _db.stats()
        return json.dumps({"status": "ok", "mode": mode, "stats": stats})
    except Exception as exc:  # noqa: BLE001
        _logger.warning("reseed_brain failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})


# ─── WRITE tools (Manager Agent only) ────────────────────────────────────────

@mcp.tool()
def add_concept(entry_json: str) -> str:
    """
    Add or overwrite a concept in the Repository of Truth.
    MANAGER AGENT ONLY.

    Args:
        entry_json: JSON string matching the ConceptEntry schema.
                    Required fields: concept_id, name, description,
                    origin_ref, role_assignment, category.

    Returns:
        concept_id of the stored entry, or an error message.
    """
    try:
        data = json.loads(entry_json)
        entry = ConceptEntry(**data)
        _db.upsert(entry)
        _logger.info("Concept added/updated: %s", entry.concept_id)
        return json.dumps({"status": "ok", "concept_id": entry.concept_id})
    except Exception as exc:  # noqa: BLE001
        _logger.warning("add_concept failed: %s", exc)
        return json.dumps({"status": "error", "message": str(exc)})


@mcp.tool()
def update_concept(concept_id: str, fields_json: str) -> str:
    """
    Update specific fields on an existing concept.
    MANAGER AGENT ONLY.

    Args:
        concept_id:  Concept to update.
        fields_json: JSON object of fields to update,
                     e.g. '{"ported_to": "src/vjlive3/effects/vimana.py"}'

    Returns:
        Status JSON.
    """
    existing = _db.get(concept_id)
    if existing is None:
        return json.dumps({"status": "error", "message": f"Not found: {concept_id}"})
    try:
        fields = json.loads(fields_json)
        updated = existing.model_copy(update=fields)
        _db.upsert(updated)
        _logger.info("Concept %s updated: %s", concept_id, list(fields.keys()))
        return json.dumps({"status": "ok", "concept_id": concept_id})
    except Exception as exc:  # noqa: BLE001
        return json.dumps({"status": "error", "message": str(exc)})


@mcp.tool()
def flag_dreamer(
    concept_id: str,
    analysis: str,
    verdict: str,
) -> str:
    """
    Mark a concept with a Dreamer analysis result.
    MANAGER AGENT ONLY.

    Args:
        concept_id: Concept to flag.
        analysis:   Human-readable analysis of the [DREAMER_LOGIC] block.
        verdict:    'genius' | 'sandbox' | 'dead_end' | 'pending'

    Returns:
        Status JSON.
    """
    existing = _db.get(concept_id)
    if existing is None:
        return json.dumps({"status": "error", "message": f"Not found: {concept_id}"})

    purity = LogicPurity.GENIUS if verdict == "genius" else LogicPurity.UNKNOWN
    try:
        dv = DreamerVerdict(verdict)
    except ValueError:
        dv = DreamerVerdict.PENDING

    updated = existing.model_copy(update={
        "dreamer_flag": True,
        "dreamer_analysis": analysis,
        "dreamer_verdict": dv,
        "logic_purity": purity,
    })
    _db.upsert(updated)
    _logger.info("Dreamer flag set on %s — verdict: %s", concept_id, verdict)
    return json.dumps({"status": "ok", "concept_id": concept_id, "verdict": verdict})


# ─── Smoke test ───────────────────────────────────────────────────────────────

def _smoke_test() -> bool:
    """Quick round-trip to verify DB and serialisation are functional."""
    test_entry = ConceptEntry(
        concept_id="__smoke_test__",
        name="Smoke Test Concept",
        description="Temporary entry for server health check.",
        origin_ref="none",
        source_files=[],
        dreamer_flag=False,
        dreamer_analysis="",
        logic_purity=LogicPurity.CLEAN,
        role_assignment=RoleAssignment.WORKER,
        kitten_status=False,
        tags=["test"],
        category="test",
        ported_to="",
    )
    _db.upsert(test_entry)
    retrieved = _db.get("__smoke_test__")
    assert retrieved is not None, "Retrieved entry is None"
    assert retrieved.name == "Smoke Test Concept"
    _db.delete("__smoke_test__")
    _logger.info("vjlive3brain smoke test: PASS")
    return True


# ─── Entrypoint ───────────────────────────────────────────────────────────────

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = _smoke_test()
        sys.exit(0 if ok else 1)

    # Serve via stdio (Claude Desktop / Roo MCP protocol)
    _logger.info(
        "vjlive3brain starting — DB: %s — Stats: %s",
        _DB_PATH,
        json.dumps(_db.stats()),
    )
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
