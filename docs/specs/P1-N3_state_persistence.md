# Spec: P1-N3 — Node Graph State Persistence (Save/Load)

**Phase:** Phase 1 / P1-N3
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Depends On:** P1-N1 (NodeGraph.serialize()), P1-N2 (core node types)

---

## What This Module Does

Provides `ProjectSerializer` — save and load the complete NodeGraph state to/from a JSON
project file (`*.vjl3`). Versioned schema with forward/backward compatibility handling.
Also provides auto-save (every 5 minutes to a `.autosave.vjl3` alongside the main file)
and crash recovery (loads the autosave on startup if newer than the main file).

---

## What It Does NOT Do

- Does NOT save GPU textures or audio buffers — only graph parameters and topology
- Does NOT implement cloud sync or network sharing
- Does NOT manage multiple project files simultaneously

---

## Public Interface

```python
# vjlive3/nodes/persistence.py

from pathlib import Path
from typing import Optional
from vjlive3.nodes.graph import NodeGraph
from vjlive3.nodes.registry import NodeRegistry


PROJECT_SCHEMA_VERSION = "3.0"

PROJECT_FILE_EXTENSION = ".vjl3"


class ProjectSerializer:
    """Save and load NodeGraph state from disk."""

    def __init__(self, registry: NodeRegistry) -> None:
        """
        Args:
            registry: Needed to reconstruct node instances from type IDs on load.
        """

    def save(self, graph: NodeGraph, path: Path) -> None:
        """
        Serialise graph to JSON and write to path.

        Writes atomically: write to temp file first, then rename.
        Raises IOError on write failure.
        Creates parent dirs if they don't exist.
        """

    def load(self, graph: NodeGraph, path: Path) -> None:
        """
        Read JSON from path and deserialise into graph.

        Clears graph before loading.
        Raises FileNotFoundError if path absent.
        Raises ValueError if schema version incompatible.
        Logs WARNING (does not crash) on unknown node types.
        """

    def autosave(self, graph: NodeGraph, project_path: Path) -> None:
        """
        Write autosave file alongside project_path.

        Autosave path: project_path.with_suffix('.autosave.vjl3')
        Called by engine every 5 minutes.
        """

    def check_recovery(self, project_path: Path) -> Optional[Path]:
        """
        Return autosave path if it is NEWER than the project file, else None.

        Used at startup to offer crash recovery.
        """
```

## Project File Format (JSON Schema)

```json
{
  "schema_version": "3.0",
  "metadata": {
    "name": "My Project",
    "created": "2026-02-21T03:00:00Z",
    "modified": "2026-02-21T03:05:00Z",
    "vjlive3_version": "3.0.0"
  },
  "graph": {
    "nodes": [
      {
        "id": "uuid-xxx",
        "type_id": "core.source",
        "parameters": {"width": 1920, "height": 1080},
        "position": {"x": 100, "y": 200},
        "active": true
      }
    ],
    "edges": [
      {
        "from_node": "uuid-xxx",
        "output": "out",
        "to_node": "uuid-yyy",
        "input": "in"
      }
    ]
  }
}
```

---

## Edge Cases

- **Incompatible schema version:** Raise `ValueError("Unsupported schema v{x}, expected v3.0")`
- **Atomic write failure:** Temp file left behind, original untouched
- **Partial autosave:** Skip if last autosave < 60s ago (rate limit)
- **recovery file not newer:** `check_recovery()` returns None

---

## Test Plan (8 tests, 80% coverage)

| Test ID | What |
|---------|------|
| `test_save_creates_file` | save() creates valid JSON file |
| `test_load_round_trips` | save then load → same node count, params, edges |
| `test_atomic_write` | partial write failure → original file intact |
| `test_load_missing_file_raises` | FileNotFoundError on absent path |
| `test_load_wrong_version_raises` | ValueError on wrong schema_version |
| `test_load_unknown_type_warns` | unknown type_id logs warning, skips |
| `test_autosave_creates_file` | autosave() creates .autosave.vjl3 |
| `test_check_recovery_newer` | newer autosave → path returned |

---

## Definition of Done

- [ ] All 8 tests pass
- [ ] File < 750 lines
- [ ] No stubs
- [ ] BOARD.md P1-N3 marked ✅
- [ ] Lock released; AGENT_SYNC.md updated
