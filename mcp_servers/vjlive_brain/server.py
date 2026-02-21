"""
vjlive_brain — MCP Knowledge Base Server

The Repository of Truth for VJLive3.
Indexes legacy codebase concepts and provides lookup for all agents.

Tools exposed:
  - get_concept(concept_id) → ConceptEntry
  - search_concepts(query, tags, role, category) → list[ConceptEntry]
  - add_concept(entry) → concept_id
  - update_concept(concept_id, **fields) → None
  - flag_dreamer(concept_id, analysis, verdict) → None
  - list_concepts(category, role, status) → list[ConceptEntry]

Only the Manager Agent (Antigravity) may call add_concept / flag_dreamer
to maintain the integrity of the Repository of Truth.

Run: python -m mcp_servers.vjlive_brain.server
"""
from __future__ import annotations

import json
import logging
import sys
from typing import Any

from mcp_servers.vjlive_brain.db import ConceptDB
from mcp_servers.vjlive_brain.schema import ConceptEntry, DreamerVerdict, LogicPurity, RoleAssignment

_logger = logging.getLogger("vjlive3.mcp.brain")


class VJLiveBrainServer:
    """
    The Repository of Truth.

    Manages the concept knowledge base that maps legacy VJLive logic
    to its VJLive3 implementation target. Agents query this before
    writing any code — 'Knowledge First' (PRIME_DIRECTIVE Rule 1).
    """

    def __init__(self, db_path: str = "mcp_servers/vjlive_brain/brain.db") -> None:
        self._db = ConceptDB(db_path)
        self._db.initialize()
        _logger.info("VJLive Brain server initialized. Repository of Truth is open.")

    # ─────────────────────────────────────────────────────────────────────────
    #  READ tools — available to all agents
    # ─────────────────────────────────────────────────────────────────────────

    def get_concept(self, concept_id: str) -> ConceptEntry | None:
        """
        Retrieve a single concept by its ID.

        Args:
            concept_id: The unique concept identifier (e.g. 'vimana-depth-mosh')

        Returns:
            ConceptEntry if found, None otherwise.
        """
        return self._db.get(concept_id)

    def search_concepts(
        self,
        query: str = "",
        tags: list[str] | None = None,
        role: str | None = None,
        category: str | None = None,
        origin: str | None = None,
        dreamer_only: bool = False,
    ) -> list[ConceptEntry]:
        """
        Search concepts by text, tags, role, or category.

        Args:
            query: Text to match against name and description
            tags: Filter to concepts having ALL specified tags
            role: 'manager' | 'worker' — filter by role_assignment
            category: 'engine' | 'plugin' | 'ui' | 'hardware' | 'dreamer'
            origin: 'vjlive-v1' | 'vjlive-v2' | 'none'
            dreamer_only: If True, only return concepts with dreamer_flag=True

        Returns:
            List of matching ConceptEntry objects, ordered by relevance.
        """
        return self._db.search(
            query=query,
            tags=tags or [],
            role=role,
            category=category,
            origin=origin,
            dreamer_only=dreamer_only,
        )

    def list_concepts(
        self,
        category: str | None = None,
        role: str | None = None,
        ported: bool | None = None,
    ) -> list[ConceptEntry]:
        """
        List all concepts, optionally filtered.

        Args:
            category: Filter by category
            role: Filter by role_assignment
            ported: True = only ported, False = only unported, None = all

        Returns:
            List of ConceptEntry objects.
        """
        return self._db.list_all(category=category, role=role, ported=ported)

    # ─────────────────────────────────────────────────────────────────────────
    #  WRITE tools — Manager Agent only
    # ─────────────────────────────────────────────────────────────────────────

    def add_concept(self, entry: ConceptEntry) -> str:
        """
        Add a new concept to the knowledge base.
        Manager Agent only — workers do not modify the Repository of Truth.

        Args:
            entry: Fully populated ConceptEntry

        Returns:
            The concept_id of the newly created entry.
        """
        self._db.upsert(entry)
        _logger.info("Concept added: %s (%s)", entry.concept_id, entry.name)
        return entry.concept_id

    def update_concept(self, concept_id: str, **fields: Any) -> None:
        """
        Update fields on an existing concept.
        Manager Agent only.

        Args:
            concept_id: Concept to update
            **fields: Fields to update (e.g. ported_to='src/vjlive3/effects/...')
        """
        existing = self._db.get(concept_id)
        if existing is None:
            _logger.warning("update_concept: concept not found: %s", concept_id)
            return
        updated = existing.model_copy(update=fields)
        self._db.upsert(updated)
        _logger.info("Concept updated: %s — fields: %s", concept_id, list(fields.keys()))

    def flag_dreamer(
        self,
        concept_id: str,
        analysis: str,
        verdict: str,
    ) -> None:
        """
        Update the Dreamer analysis on a concept.
        Verdicts: 'genius' | 'dead_end' | 'sandbox' | 'pending'

        Args:
            concept_id: Concept to flag
            analysis: Human-readable analysis of the Dreamer logic
            verdict: One of DreamerVerdict values
        """
        existing = self._db.get(concept_id)
        if existing is None:
            _logger.warning("flag_dreamer: concept not found: %s", concept_id)
            return
        updated = existing.model_copy(update={
            "dreamer_flag": True,
            "dreamer_analysis": analysis,
            "logic_purity": LogicPurity.GENIUS if verdict == "genius"
                            else LogicPurity.UNKNOWN,
        })
        self._db.upsert(updated)
        _logger.info(
            "Dreamer flag set on %s — verdict: %s", concept_id, verdict
        )

    def get_stats(self) -> dict[str, int]:
        """Return summary statistics about the knowledge base."""
        return self._db.stats()

    # ─────────────────────────────────────────────────────────────────────────
    #  Smoke test — called by server.py --test
    # ─────────────────────────────────────────────────────────────────────────

    def smoke_test(self) -> bool:
        """Verify the server is operational. Used in pre-flight checks."""
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
        self.add_concept(test_entry)
        retrieved = self.get_concept("__smoke_test__")
        assert retrieved is not None
        assert retrieved.name == "Smoke Test Concept"
        self._db.delete("__smoke_test__")
        _logger.info("Brain server smoke test: PASS")
        return True


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    server = VJLiveBrainServer()

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ok = server.smoke_test()
        sys.exit(0 if ok else 1)

    stats = server.get_stats()
    _logger.info("VJLive Brain ready. Stats: %s", json.dumps(stats))
    # In production: register with MCP framework and serve
    # For now: keep alive for direct import by agents
    print("VJLive Brain server ready. Import VJLiveBrainServer for direct use.")
    print(f"Knowledge base stats: {stats}")


if __name__ == "__main__":
    main()
