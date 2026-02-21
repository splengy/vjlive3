"""
vjlive3brain — Legacy Codebase Seeder

Crawls vjlive (v1) and VJlive-2 (v2) to discover Python modules,
extracts basic metadata, and upserts them into the brain.db knowledgebase.

Also watches for file changes and re-seeds incrementally.

Usage:
    # One-shot seed:
    python -m mcp_servers.vjlive3brain.seeder --seed

    # Continuous watch + seed:
    python -m mcp_servers.vjlive3brain.seeder --watch
"""
from __future__ import annotations

import argparse
import ast
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

from mcp_servers.vjlive3brain.db import ConceptDB
from mcp_servers.vjlive3brain.schema import (
    ConceptEntry,
    DreamerVerdict,
    LogicPurity,
    RoleAssignment,
)

_logger = logging.getLogger("vjlive3.mcp.vjlive3brain.seeder")

# ─── Paths ────────────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_LEGACY_V1 = _REPO_ROOT.parent / "vjlive"
_LEGACY_V2 = _REPO_ROOT.parent / "VJlive-2"
_DB_PATH = _os_env = os.environ.get(
    "VJLIVE3_BRAIN_DB",
    str(_REPO_ROOT / "mcp_servers" / "vjlive3brain" / "brain.db"),
)

# ─── Patterns ─────────────────────────────────────────────────────────────────
_DREAMER_RE = re.compile(r"\[DREAMER_LOGIC\]", re.IGNORECASE)
_PLUGIN_RE  = re.compile(r"plugin|effect|generator|filter|fx", re.IGNORECASE)
_HW_RE      = re.compile(r"midi|osc|dmx|camera|depth|ndi", re.IGNORECASE)
_UI_RE      = re.compile(r"window|widget|panel|overlay|gui|ui", re.IGNORECASE)
_AUDIO_RE   = re.compile(r"audio|fft|beat|bpm|sound|waveform", re.IGNORECASE)

# files/dirs to ignore
_IGNORE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    "build", "dist", ".tox", ".mypy_cache", "migrations",
}
_IGNORE_SUFFIXES = {".pyc", ".pyo"}


def _classify_category(path: Path, src: str) -> str:
    name = path.stem + " " + str(path)
    if _PLUGIN_RE.search(name):
        return "plugin"
    if _HW_RE.search(name):
        return "hardware"
    if _UI_RE.search(name):
        return "ui"
    if _AUDIO_RE.search(name):
        return "engine"
    return "engine"


def _performance_impact(src: str) -> str:
    """Rough heuristic — shader / numpy heavy = high, else medium."""
    if "numpy" in src or "opengl" in src.lower() or "glsl" in src.lower():
        return "high"
    if len(src) > 3000:
        return "medium"
    return "low"


def _extract_docstring(src: str) -> str:
    """Pull module-level docstring via AST, or fall back to empty string."""
    try:
        tree = ast.parse(src)
        return ast.get_docstring(tree) or ""
    except SyntaxError:
        return ""


def _has_dreamer(src: str) -> bool:
    return bool(_DREAMER_RE.search(src))


def _make_concept_id(origin: str, path: Path) -> str:
    """Stable slug from origin tag + relative path."""
    rel = path.with_suffix("").as_posix().replace("/", "-").replace("_", "-")
    return f"{origin}--{rel}"[:120]


def _path_to_entry(
    path: Path,
    origin_ref: str,
    src: str,
) -> Optional[ConceptEntry]:
    """Convert a single Python file into a ConceptEntry."""
    doc = _extract_docstring(src)
    if not doc:
        # Use first non-empty line as a minimal description
        for line in src.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                doc = stripped[:200]
                break
    if not doc:
        doc = f"Module: {path.stem}"

    concept_id = _make_concept_id(origin_ref, path)
    category   = _classify_category(path, src)
    dreamer    = _has_dreamer(src)

    tags: list[str] = [origin_ref, category]
    if dreamer:
        tags.append("dreamer")

    return ConceptEntry(
        concept_id=concept_id,
        name=path.stem.replace("_", " ").title(),
        description=doc[:500],
        origin_ref=origin_ref,
        source_files=[str(path)],
        dreamer_flag=dreamer,
        dreamer_analysis="" if not dreamer else "[DREAMER_LOGIC] detected — analysis pending",
        dreamer_verdict=DreamerVerdict.PENDING,
        logic_purity=LogicPurity.UNKNOWN,
        role_assignment=(
            RoleAssignment.MANAGER
            if any(kw in path.stem for kw in ("manager", "orchestrat", "dispatch", "server"))
            else RoleAssignment.WORKER
        ),
        kitten_status=False,
        tags=tags,
        category=category,
        performance_impact=_performance_impact(src),
        ported_to="",
    )


def seed_directory(db: ConceptDB, root: Path, origin_ref: str) -> int:
    """
    Walk `root`, parse each .py file, upsert into DB.

    Returns:
        Number of concepts upserted.
    """
    if not root.exists():
        _logger.warning("Legacy path does not exist, skipping: %s", root)
        return 0

    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune ignored dirs in-place
        dirnames[:] = [d for d in dirnames if d not in _IGNORE_DIRS]

        for fname in filenames:
            fpath = Path(dirpath) / fname
            if fpath.suffix in _IGNORE_SUFFIXES or fpath.suffix != ".py":
                continue
            try:
                src = fpath.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                _logger.debug("Cannot read %s: %s", fpath, exc)
                continue

            entry = _path_to_entry(fpath, origin_ref, src)
            if entry:
                db.upsert(entry)
                count += 1

    _logger.info("Seeded %d concepts from %s [%s]", count, root, origin_ref)
    return count


def run_full_seed(db: ConceptDB) -> None:
    """Seed both legacy codebases."""
    total = 0
    total += seed_directory(db, _LEGACY_V1, "vjlive-v1")
    total += seed_directory(db, _LEGACY_V2, "vjlive-v2")
    stats = db.stats()
    _logger.info(
        "Full seed complete. Total DB: %d concepts (%d ported, %d dreamer)",
        stats["total"], stats["ported"], stats["dreamer"],
    )


def run_watch(db: ConceptDB) -> None:
    """
    Watch legacy directories for changes and re-seed modified files.

    Uses watchdog if available, otherwise falls back to polling.
    """
    try:
        from watchdog.events import FileSystemEvent, FileSystemEventHandler  # type: ignore[import]
        from watchdog.observers import Observer  # type: ignore[import]

        class _Handler(FileSystemEventHandler):  # type: ignore[misc]
            def __init__(self, origin: str) -> None:
                self._origin = origin

            def on_modified(self, event: FileSystemEvent) -> None:
                path = Path(str(event.src_path))
                if path.suffix != ".py":
                    return
                try:
                    src = path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    return
                entry = _path_to_entry(path, self._origin, src)
                if entry:
                    db.upsert(entry)
                    _logger.info("Hot-updated concept: %s", entry.concept_id)

            on_created = on_modified  # type: ignore[assignment]

        observer = Observer()
        if _LEGACY_V1.exists():
            observer.schedule(_Handler("vjlive-v1"), str(_LEGACY_V1), recursive=True)
        if _LEGACY_V2.exists():
            observer.schedule(_Handler("vjlive-v2"), str(_LEGACY_V2), recursive=True)

        observer.start()
        _logger.info("Watcher active. Monitoring legacy sources for changes...")
        try:
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()

    except ImportError:
        _logger.warning(
            "watchdog not installed — falling back to 60s polling. "
            "Install with: pip install watchdog"
        )
        while True:
            try:
                run_full_seed(db)
                time.sleep(60)
            except KeyboardInterrupt:
                break


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="vjlive3brain seeder")
    parser.add_argument("--seed",  action="store_true", help="One-shot seed of both legacy codebases")
    parser.add_argument("--watch", action="store_true", help="Seed then watch for changes")
    parser.add_argument("--db",    default=_DB_PATH,    help="Override DB path")
    args = parser.parse_args()

    db = ConceptDB(args.db)
    db.initialize()

    if args.watch:
        run_full_seed(db)
        run_watch(db)
    elif args.seed:
        run_full_seed(db)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
