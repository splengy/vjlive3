"""SQLite persistence layer for the vjlive-brain knowledge base."""
from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from mcp_servers.vjlive_brain.schema import (
    ConceptEntry,
    DreamerVerdict,
    LogicPurity,
    RoleAssignment,
)

_logger = logging.getLogger("vjlive3.mcp.brain.db")

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS concepts (
    concept_id       TEXT PRIMARY KEY,
    name             TEXT NOT NULL,
    description      TEXT NOT NULL,
    origin_ref       TEXT NOT NULL,
    source_files     TEXT NOT NULL DEFAULT '[]',
    dreamer_flag     INTEGER NOT NULL DEFAULT 0,
    dreamer_analysis TEXT NOT NULL DEFAULT '',
    dreamer_verdict  TEXT NOT NULL DEFAULT 'pending',
    logic_purity     TEXT NOT NULL DEFAULT 'unknown',
    role_assignment  TEXT NOT NULL,
    kitten_status    INTEGER NOT NULL DEFAULT 0,
    tags             TEXT NOT NULL DEFAULT '[]',
    category         TEXT NOT NULL,
    performance_impact TEXT NOT NULL DEFAULT 'unknown',
    ported_to        TEXT NOT NULL DEFAULT '',
    ported_date      TEXT
);
"""

_CREATE_FTS = """
CREATE VIRTUAL TABLE IF NOT EXISTS concepts_fts USING fts5(
    concept_id,
    name,
    description,
    tags,
    content='concepts',
    content_rowid='rowid'
);
"""


def _row_to_entry(row: dict[str, Any]) -> ConceptEntry:
    return ConceptEntry(
        concept_id=row["concept_id"],
        name=row["name"],
        description=row["description"],
        origin_ref=row["origin_ref"],
        source_files=json.loads(row["source_files"]),
        dreamer_flag=bool(row["dreamer_flag"]),
        dreamer_analysis=row["dreamer_analysis"],
        dreamer_verdict=DreamerVerdict(row["dreamer_verdict"]),
        logic_purity=LogicPurity(row["logic_purity"]),
        role_assignment=RoleAssignment(row["role_assignment"]),
        kitten_status=bool(row["kitten_status"]),
        tags=json.loads(row["tags"]),
        category=row["category"],
        performance_impact=row["performance_impact"],
        ported_to=row["ported_to"],
        ported_date=row["ported_date"],
    )


class ConceptDB:
    """SQLite-backed persistence for ConceptEntry objects."""

    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(str(self._path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.execute(_CREATE_TABLE)
            conn.execute(_CREATE_FTS)
        _logger.debug("Database initialized at %s", self._path)

    def upsert(self, entry: ConceptEntry) -> None:
        """Insert or update a concept."""
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO concepts VALUES (
                    :concept_id, :name, :description, :origin_ref,
                    :source_files, :dreamer_flag, :dreamer_analysis,
                    :dreamer_verdict, :logic_purity, :role_assignment,
                    :kitten_status, :tags, :category, :performance_impact,
                    :ported_to, :ported_date
                ) ON CONFLICT(concept_id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    origin_ref=excluded.origin_ref,
                    source_files=excluded.source_files,
                    dreamer_flag=excluded.dreamer_flag,
                    dreamer_analysis=excluded.dreamer_analysis,
                    dreamer_verdict=excluded.dreamer_verdict,
                    logic_purity=excluded.logic_purity,
                    role_assignment=excluded.role_assignment,
                    kitten_status=excluded.kitten_status,
                    tags=excluded.tags,
                    category=excluded.category,
                    performance_impact=excluded.performance_impact,
                    ported_to=excluded.ported_to,
                    ported_date=excluded.ported_date
                """,
                {
                    "concept_id": entry.concept_id,
                    "name": entry.name,
                    "description": entry.description,
                    "origin_ref": entry.origin_ref,
                    "source_files": json.dumps(entry.source_files),
                    "dreamer_flag": int(entry.dreamer_flag),
                    "dreamer_analysis": entry.dreamer_analysis,
                    "dreamer_verdict": entry.dreamer_verdict.value,
                    "logic_purity": entry.logic_purity.value,
                    "role_assignment": entry.role_assignment.value,
                    "kitten_status": int(entry.kitten_status),
                    "tags": json.dumps(entry.tags),
                    "category": entry.category,
                    "performance_impact": entry.performance_impact,
                    "ported_to": entry.ported_to,
                    "ported_date": entry.ported_date,
                },
            )

    def get(self, concept_id: str) -> ConceptEntry | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM concepts WHERE concept_id = ?", (concept_id,)
            ).fetchone()
        return _row_to_entry(dict(row)) if row else None

    def delete(self, concept_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM concepts WHERE concept_id = ?", (concept_id,)
            )

    def search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        role: str | None = None,
        category: str | None = None,
        origin: str | None = None,
        dreamer_only: bool = False,
    ) -> list[ConceptEntry]:
        clauses: list[str] = []
        params: list[Any] = []

        if query:
            clauses.append(
                "concept_id IN (SELECT concept_id FROM concepts_fts WHERE concepts_fts MATCH ?)"
            )
            params.append(query)
        if role:
            clauses.append("role_assignment = ?")
            params.append(role)
        if category:
            clauses.append("category = ?")
            params.append(category)
        if origin:
            clauses.append("origin_ref = ?")
            params.append(origin)
        if dreamer_only:
            clauses.append("dreamer_flag = 1")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM concepts {where} ORDER BY name"

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        results = [_row_to_entry(dict(r)) for r in rows]

        # Tag filtering (post-query since tags are stored as JSON)
        if tags:
            results = [
                r for r in results if all(t in r.tags for t in tags)
            ]
        return results

    def list_all(
        self,
        category: str | None = None,
        role: str | None = None,
        ported: bool | None = None,
    ) -> list[ConceptEntry]:
        clauses: list[str] = []
        params: list[Any] = []
        if category:
            clauses.append("category = ?")
            params.append(category)
        if role:
            clauses.append("role_assignment = ?")
            params.append(role)
        if ported is True:
            clauses.append("ported_to != ''")
        elif ported is False:
            clauses.append("ported_to = ''")
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT * FROM concepts {where} ORDER BY category, name", params
            ).fetchall()
        return [_row_to_entry(dict(r)) for r in rows]

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM concepts").fetchone()[0]
            ported = conn.execute(
                "SELECT COUNT(*) FROM concepts WHERE ported_to != ''"
            ).fetchone()[0]
            dreamer = conn.execute(
                "SELECT COUNT(*) FROM concepts WHERE dreamer_flag = 1"
            ).fetchone()[0]
        return {"total": total, "ported": ported, "unported": total - ported, "dreamer": dreamer}
