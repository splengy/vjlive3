# P1-C2: StatePersistenceManager — Comprehensive Save/Load System

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3 requires a robust state persistence system that:
- Saves and loads complete application state (projects, presets, configurations)
- Handles multiple state types (projects, snapshots, preferences)
- Ensures data integrity and crash recovery
- Supports version migration for state format changes
- Integrates with ApplicationStateManager for seamless state capture/restore
- Provides atomic save operations to prevent corruption

The legacy codebases have fragmented persistence approaches that need unification.

---

## Proposed Solution

Implement `StatePersistenceManager` as a comprehensive persistence layer with:

1. **Atomic Save Operations** — write to temp file, then atomic rename
2. **Versioned State Format** — JSON with schema version for migration
3. **Multiple State Types** — projects, snapshots, preferences, cache
4. **Compression** — optional compression for large state blobs
5. **Backup & Recovery** — automatic backups, crash recovery
6. **Validation** — schema validation before/after load
7. **Integration** — seamless with ApplicationStateManager snapshots

---

## API/Interface Definition

```python
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import zlib
import tempfile
import shutil

class StateType(Enum):
    """Types of state that can be persisted."""
    PROJECT = "project"          # Full project with all compositions
    SNAPSHOT = "snapshot"        # Quick state capture (8 slots)
    PRESET = "preset"            # Effect/parameter preset
    PREFERENCES = "preferences"  # User preferences
    CACHE = "cache"              # Temporary cache (can be cleared)

@dataclass
class StateMetadata:
    """Metadata for a persisted state."""
    state_type: StateType
    version: str
    timestamp: float
    application_version: str
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)

class StatePersistenceManager:
    """
    Comprehensive state persistence manager.

    Usage:
        persistence = StatePersistenceManager(base_path="/path/to/data")
        # Save project
        persistence.save_state(
            state_type=StateType.PROJECT,
            state_data=state_mgr.get_snapshot(),
            filepath="my_project.vjlive"
        )
        # Load project
        loaded_state = persistence.load_state("my_project.vjlive")
        state_mgr.restore_snapshot(loaded_state)
    """

    def __init__(
        self,
        base_path: Union[str, Path],
        backup_retention_count: int = 10,
        enable_compression: bool = True
    ):
        """
        Initialize persistence manager.

        Args:
            base_path: Base directory for all persisted state
            backup_retention_count: Number of backup files to keep
            enable_compression: Whether to compress state files
        """
        self.base_path = Path(base_path)
        self.backup_retention_count = backup_retention_count
        self.enable_compression = enable_compression
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directory structure."""
        directories = [
            self.base_path / "projects",
            self.base_path / "snapshots",
            self.base_path / "presets",
            self.base_path / "preferences",
            self.base_path / "cache",
            self.base_path / "backups",
            self.base_path / ".tmp"
        ]
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)

    def save_state(
        self,
        state_type: StateType,
        state_data: Union[Dict, 'StateSnapshot'],
        filepath: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Path:
        """
        Save state to disk atomically.

        Args:
            state_type: Type of state being saved
            state_data: State data (dict or StateSnapshot)
            filepath: Optional custom filepath relative to type directory
            description: Optional human-readable description
            tags: Optional tags for organization

        Returns:
            Path to saved file
        """
        import time
        import json

        # Determine target directory
        type_dir = self.base_path / state_type.value

        # Generate filename if not provided
        if filepath is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filepath = f"state_{timestamp}.vjlive"

        full_path = type_dir / filepath

        # Prepare state payload
        if hasattr(state_data, 'get_snapshot'):
            # It's a StateSnapshot or similar
            payload = {
                "snapshot": state_data.data if hasattr(state_data, 'data') else state_data,
                "metadata": StateMetadata(
                    state_type=state_type,
                    version="1.0",
                    timestamp=time.time(),
                    application_version="VJLive3-alpha",
                    description=description,
                    tags=tags or []
                ).__dict__
            }
        else:
            # It's a plain dict
            payload = {
                "state": state_data,
                "metadata": StateMetadata(
                    state_type=state_type,
                    version="1.0",
                    timestamp=time.time(),
                    application_version="VJLive3-alpha",
                    description=description,
                    tags=tags or []
                ).__dict__
            }

        # Serialize to JSON
        json_data = json.dumps(payload, indent=2)

        # Compress if enabled
        if self.enable_compression:
            json_data = zlib.compress(json_data.encode('utf-8'), level=6)
            filepath = full_path.with_suffix('.vjlivec')
        else:
            json_data = json_data.encode('utf-8')
            filepath = full_path

        # Atomic write: write to temp, then rename
        temp_path = self.base_path / ".tmp" / f"temp_{time.time()}.tmp"
        try:
            with open(temp_path, 'wb') as f:
                f.write(json_data)

            # Create backup if file exists
            if filepath.exists():
                self._create_backup(filepath)

            # Atomic move
            shutil.move(str(temp_path), str(filepath))

            return filepath

        except Exception:
            # Cleanup temp file on error
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load_state(
        self,
        filepath: Union[str, Path],
        validate: bool = True
    ) -> Dict[str, Any]:
        """
        Load state from disk.

        Args:
            filepath: Path to state file (relative to base_path or absolute)
            validate: Whether to validate state structure

        Returns:
            Dict containing state data and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails
        """
        full_path = Path(filepath)
        if not full_path.is_absolute():
            full_path = self.base_path / filepath

        if not full_path.exists():
            raise FileNotFoundError(f"State file not found: {full_path}")

        # Read file
        with open(full_path, 'rb') as f:
            data = f.read()

        # Decompress if compressed
        if full_path.suffix == '.vjlivec':
            data = zlib.decompress(data)
            data = data.decode('utf-8')
        else:
            data = data.decode('utf-8')

        # Parse JSON
        payload = json.loads(data)

        # Validate structure
        if validate:
            self._validate_payload(payload)

        return payload

    def _validate_payload(self, payload: Dict[str, Any]) -> None:
        """
        Validate state payload structure.

        Args:
            payload: Loaded state payload

        Raises:
            ValueError: If validation fails
        """
        if "state" not in payload and "snapshot" not in payload:
            raise ValueError("Invalid state file: missing 'state' or 'snapshot'")

        if "metadata" not in payload:
            raise ValueError("Invalid state file: missing 'metadata'")

        metadata = payload["metadata"]
        required_fields = ["state_type", "version", "timestamp", "application_version"]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Invalid metadata: missing '{field}'")

    def _create_backup(self, filepath: Path) -> None:
        """
        Create backup of existing file.

        Args:
            filepath: Path to file to backup
        """
        import time
        backup_dir = self.base_path / "backups"
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"{filepath.stem}_{timestamp}{filepath.suffix}"

        shutil.copy2(filepath, backup_path)

        # Prune old backups
        backups = sorted(backup_dir.glob(f"{filepath.stem}_*{filepath.suffix}"))
        if len(backups) > self.backup_retention_count:
            for old_backup in backups[:-self.backup_retention_count]:
                old_backup.unlink()

    def list_states(
        self,
        state_type: Optional[StateType] = None
    ) -> List[Dict[str, Any]]:
        """
        List available saved states.

        Args:
            state_type: Optional filter by state type

        Returns:
            List of state info dicts with metadata
        """
        if state_type:
            search_dir = self.base_path / state_type.value
        else:
            search_dir = self.base_path

        states = []
        for filepath in search_dir.rglob("*.vjlive*"):
            try:
                metadata = self._extract_metadata(filepath)
                states.append({
                    "filepath": str(filepath.relative_to(self.base_path)),
                    "metadata": metadata
                })
            except Exception:
                # Skip corrupted files
                continue

        return sorted(states, key=lambda x: x["metadata"]["timestamp"], reverse=True)

    def _extract_metadata(self, filepath: Path) -> Dict[str, Any]:
        """Extract metadata without full load."""
        with open(filepath, 'rb') as f:
            data = f.read()

        if filepath.suffix == '.vjlivec':
            data = zlib.decompress(data)

        payload = json.loads(data.decode('utf-8'))
        return payload.get("metadata", {})

    def delete_state(self, filepath: Union[str, Path]) -> None:
        """
        Delete a saved state.

        Args:
            filepath: Path to state file to delete
        """
        full_path = Path(filepath)
        if not full_path.is_absolute():
            full_path = self.base_path / filepath

        if full_path.exists():
            full_path.unlink()

    def migrate_state(
        self,
        old_filepath: Union[str, Path],
        target_version: str
    ) -> Dict[str, Any]:
        """
        Migrate state to new version format.

        Args:
            old_filepath: Path to old state file
            target_version: Target schema version

        Returns:
            Migrated state data
        """
        # Load old state
        old_state = self.load_state(old_filepath, validate=False)

        # Migration logic would go here
        # For now, just update version number
        if "metadata" in old_state:
            old_state["metadata"]["version"] = target_version

        return old_state
```

---

## Implementation Plan

### Day 1: Core Structure
- Create `src/vjlive3/state/persistence_manager.py`
- Implement `StatePersistenceManager` with basic save/load
- Add atomic write with temp file + rename
- Add compression support (zlib)
- Write unit tests for file I/O

### Day 2: Metadata & Validation
- Implement `StateMetadata` dataclass
- Add state schema validation
- Implement backup/restore functionality
- Add error handling and recovery
- Write tests for validation and backup

### Day 3: Integration
- Integrate with `ApplicationStateManager` snapshots
- Add state type directories (projects, snapshots, etc.)
- Implement state listing and browsing
- Add delete operation
- Write integration tests

### Day 4: Advanced Features
- Add state migration framework
- Implement version tracking and auto-migration
- Add preferences management
- Implement cache cleanup utilities
- Write migration tests

### Day 5: Testing & Polish
- Comprehensive test suite (≥80% coverage)
- Performance benchmarking
- Error scenario testing (corrupted files, disk full)
- Documentation and usage examples

---

## Test Strategy

**Unit Tests:**
- Atomic save/load round-trip
- Compression/decompression
- Backup creation and pruning
- Metadata extraction
- Validation logic (valid/invalid payloads)
- Error handling (missing files, corrupted data)
- State listing and filtering

**Integration Tests:**
- Full save → load → restore cycle with ApplicationStateManager
- Multi-state type handling
- Version migration scenarios
- Backup recovery simulation

**Performance Tests:**
- Save/load latency for various state sizes
- Compression ratio benchmarks
- Memory usage during large state operations

---

## Performance Requirements

- **Save Latency:** <100ms for typical project (10MB uncompressed)
- **Load Latency:** <200ms for typical project
- **Compression:** 50-70% size reduction for typical state
- **Atomicity:** Zero corruption even on crash/power loss during save
- **Scalability:** Handle state files up to 100MB

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** All I/O errors raised with context
- **Rail 8 (Resource Leak Prevention):** Temp files cleaned up; file handles closed
- **Rail 10 (Security):** JSON parsing safe; no arbitrary code execution

---

## Dependencies

- **P1-C1:** ApplicationStateManager — provides snapshot format
- **Blocking:** None — can implement independently
- **Blocked By:** None

---

## Open Questions

1. Should we use a database (SQLite) instead of JSON files for large states?
2. How to handle binary data (images, textures) in state? (Probably separate files)
3. Do we need cloud sync integration? (Future phase)
4. Should snapshots be auto-saved periodically? (Probably yes)

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md`
- `WORKSPACE/SAFETY_RAILS.md`
- Legacy: `vjlive/project_manager.py`, `VJlive-2/state_persistence.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*