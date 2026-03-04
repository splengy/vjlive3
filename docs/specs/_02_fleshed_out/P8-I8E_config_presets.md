# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I8E_config_presets.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8E — Config Presets

**What This Module Does**

Implements a unified configuration preset system for VJLive3 that allows users to save, load, export, import, and manage complete application configurations including effect chain state, agent parameters, MIDI mappings, mood manifold settings, and plugin configurations. The system provides a hierarchical namespace approach, JSON-based persistence with versioning, validation, and migration support, and integrates with the agent plugin bus for collaborative preset management.

---

## Architecture Decisions

- **Pattern:** Repository + Factory + Versioned Serialization
- **Rationale:** Multiple configuration domains (effects, MIDI, mood, agents) need unified management while preserving type safety and validation. Versioning ensures backward compatibility as config schemas evolve.
- **Constraints:**
  - Must support multiple preset namespaces (effect_chain, midi_mapping, mood_manifold, agent_config)
  - Must handle schema versioning and migration
  - Must validate presets before saving/loading
  - Must not block the main thread during I/O
  - Must support export/import for sharing presets
  - Must integrate with agent plugin bus for distributed preset management

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-1 | `WORKSPACE IGNORE OLD /TASKS/DONE/PHASE-05_TASK-001_preset-system.md` | `PresetManager` | Port — general preset system |
| VJlive-1 | `core/core_plugins/midi_presets.py` | `MIDIPresetManager` | Port — MIDI preset manager |
| VJlive-1 | `core/mood_preset_manager.py` | `MoodPresetManager`, `MoodPreset` | Port — mood preset manager |
| VJlive-2 | `core/state/presets.py` | (planned) | Extend — unified system |
| VJlive-1 | `core/core_plugins/examples/use_preset_manager.py` | CLI example | Reference — usage patterns |

---

## Public Interface

```python
class ConfigPresetSystem:
    def __init__(self, config: PresetConfig) -> None:...
    def register_namespace(self, namespace: str, handler: PresetHandler) -> None:...
    def save_preset(self, namespace: str, name: str, data: dict, metadata: dict = None) -> str:...
    def load_preset(self, namespace: str, name: str, validate: bool = True) -> dict:...
    def list_presets(self, namespace: str = None) -> List[str]:...
    def delete_preset(self, namespace: str, name: str) -> bool:...
    def export_preset(self, namespace: str, name: str, format: str = 'json') -> bytes:...
    def import_preset(self, namespace: str, data: bytes, format: str = 'json', merge: bool = False) -> str:...
    def get_preset_metadata(self, namespace: str, name: str) -> dict:...
    def update_preset_metadata(self, namespace: str, name: str, metadata: dict) -> None:...
    def search_presets(self, query: str, namespace: str = None) -> List[PresetInfo]:...
    def validate_preset(self, namespace: str, data: dict) -> ValidationResult:...
    def migrate_preset(self, namespace: str, data: dict, from_version: int, to_version: int) -> dict:...
    def get_namespaces(self) -> List[str]:...
    def get_stats(self) -> dict:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `PresetConfig` | System configuration | Must include preset_dir |
| `namespace` | `str` | Preset namespace (e.g., 'effects', 'midi') | Must be registered |
| `name` | `str` | Preset name (unique within namespace) | No path separators |
| `data` | `dict` | Preset data payload | Must be JSON-serializable |
| `metadata` | `dict` | Preset metadata (tags, description, author) | Optional |
| `handler` | `PresetHandler` | Namespace-specific handler | Must implement interface |
| `format` | `str` | Export/import format ('json', 'yaml', 'msgpack') | Must be supported |
| `merge` | `bool` | Merge on import vs replace | — |
| `validate` | `bool` | Validate on load | — |
| `query` | `str` | Search query | — |
| **Output** | `str`, `dict`, `bytes`, `List` | Varies by method | See method docs |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `json` — serialization — fallback: pickle (security risk)
  - `yaml` (optional) — YAML format support — fallback: JSON only
  - `msgpack` (optional) — binary format — fallback: JSON only
  - `jsonschema` (optional) — validation — fallback: basic type checking
  - `pathlib` — path handling — fallback: os.path
  - `logging` — debug logging — fallback: print
- Internal modules this depends on:
  - `vjlive3.core.agent_plugin_bus` — distributed preset sharing
  - `vjlive3.core.telemetry_pipeline` — preset usage metrics
  - `vjlive3.plugins.manager` — plugin preset handlers
  - `vjlive3.core.unified_matrix` — matrix state serialization

---

## Error Cases

| Error Condition | Exception / Response | Recovery |
|-----------------|---------------------|----------|
| Namespace not registered | `KeyError("Namespace not registered")` | Register namespace first |
| Preset not found | `FileNotFoundError("Preset not found")` | Check name/path |
| Invalid preset data | `ValidationError` | Fix data or disable validation |
| I/O error | `IOError` | Check permissions/disk space |
| Schema version mismatch | `VersionMismatchError` | Run migration |
| Duplicate preset name | `ValueError("Preset already exists")` | Use different name or overwrite |
| Unsupported format | `ValueError("Unsupported format")` | Use supported format |
| Serialization error | `SerializationError` | Check data is JSON-serializable |

---

## Configuration Schema

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `preset_dir` | `str` | `"presets"` | — | Base directory for preset storage |
| `backup_enabled` | `bool` | `True` | — | Keep backup of overwritten presets |
| `backup_count` | `int` | `5` | `1 - 100` | Number of backups to retain |
| `validation_enabled` | `bool` | `True` | — | Validate presets on load |
| `auto_migrate` | `bool` | `True` | — | Auto-migrate old schemas |
| `export_default_format` | `str` | `"json"` | `json`, `yaml`, `msgpack` | Default export format |
| `sync_enabled` | `bool` | `False` | — | Sync presets via agent bus |
| `sync_channel` | `str` | `"preset.sync"` | — | Agent bus channel for sync |
| `max_presets_per_namespace` | `int` | `1000` | `10 - 10000` | Limit presets per namespace |
| `quota_enabled` | `bool` | `False` | — | Enable preset quota system |
| `quota_total_mb` | `int` | `100` | `1 - 10000` | Total preset storage quota (MB) |

---

## Namespace Handlers

Each namespace (effect_chain, midi_mapping, mood_manifold, agent_config) has a dedicated handler that knows how to:

1. **Validate** preset data for that namespace
2. **Migrate** old schema versions to current
3. **Normalize** data for consistent storage
4. **Provide defaults** for missing fields

### Handler Interface

```python
class PresetHandler(ABC):
    @abstractmethod
    def get_schema_version(self) -> int: ...
    
    @abstractmethod
    def get_default_data(self) -> dict: ...
    
    @abstractmethod
    def validate(self, data: dict) -> ValidationResult: ...
    
    @abstractmethod
    def migrate(self, data: dict, from_version: int) -> dict: ...
    
    @abstractmethod
    def normalize(self, data: dict) -> dict: ...
    
    @abstractmethod
    def denormalize(self, data: dict) -> dict: ...
```

### Built-in Handlers

1. **EffectChainHandler** — Effect chain configurations
   - Schema: effect list with parameters, routing, bypass states
   - Version: 1
   - Migration: Add missing effect defaults, update parameter ranges

2. **MIDIMappingHandler** — MIDI controller mappings
   - Schema: CC mappings, channel assignments, control types
   - Version: 1
   - Migration: Map old control numbers to new ones

3. **MoodManifoldHandler** — Mood manifold presets
   - Schema: Dimensions, anchors, interpolation, audio reactivity
   - Version: 2 (added audio_dimension_weights in v2)
   - Migration: v1 → v2: Add default audio weights

4. **AgentConfigHandler** — Agent configuration
   - Schema: Agent parameters, personality traits, decision weights
   - Version: 1
   - Migration: N/A

---

## Preset File Structure

```
presets/
├── effect_chain/
│   ├── ambient_textures.json
│   ├── bass_heavy.json
│   └── experimental.json
├── midi_mapping/
│   ├── launchpad_mk2.json
│   ├── novation_remote.json
│   └── ableton_push.json
├── mood_manifold/
│   ├── euphoric_ascension.json
│   ├── dark_abyss.json
│   └── neutral_ground.json
├── agent_config/
│   ├── julie_creative.json
│   ├── maxx_technical.json
│   └── desktop_stable.json
└── .metadata/
    ├── effect_chain/
    │   ├── ambient_textures.meta.json
    │   └── bass_heavy.meta.json
    └── midi_mapping/
        └── launchpad_mk2.meta.json
```

### Preset File Format (JSON)

```json
{
  "version": 2,
  "namespace": "mood_manifold",
  "name": "euphoric_ascension",
  "created_at": "2025-06-15T14:30:00Z",
  "modified_at": "2025-06-16T09:15:00Z",
  "author": "julie-roo",
  "description": "Uplifting mood for daytime performances",
  "tags": ["euphoric", "daytime", "uplifting"],
  "data": {
    "dimensions": 8,
    "mood_vector": [0.2, 0.8, 0.4, 0.6, 0.3, 0.9, 0.5, 0.7],
    "anchors": { ... },
    "interpolation_method": "spherical",
    "momentum_strength": 0.7,
    "velocity_damping": 0.3,
    "temporal_smoothing": 0.5,
    "oscillation_frequency": 1.2,
    "audio_mapping_mode": "follow",
    "audio_sensitivity": 0.8,
    "audio_dimension_weights": [1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.05, 0.02],
    "jitter_strength": 0.1,
    "jitter_radius": 0.05,
    "parameter_mappings": { ... }
  }
}
```

### Metadata File Format

```json
{
  "preset_name": "euphoric_ascension",
  "namespace": "mood_manifold",
  "file_size": 2048,
  "file_hash": "sha256:abc123...",
  "usage_count": 42,
  "last_used": "2025-06-20T16:45:00Z",
  "rating": 5,
  "favorite": true,
  "shared_with": ["maxx-roo", "julie-roo"],
  "imported_from": null
}
```

---

## Preset Lifecycle

1. **Creation**:
   - User or agent calls `save_preset(namespace, name, data)`
   - System validates data against namespace schema
   - System normalizes data (adds defaults, canonical format)
   - System generates preset file with metadata
   - System updates namespace index

2. **Loading**:
   - User or agent calls `load_preset(namespace, name)`
   - System reads preset file and metadata
   - If validation enabled, validate data
   - If schema version old, migrate to current version
   - System denormalizes data (remove defaults)
   - System updates usage stats in metadata
   - Return data to caller

3. **Export/Import**:
   - `export_preset()` returns bytes in specified format
   - `import_preset()` parses bytes, validates, saves
   - Import can merge with existing or replace
   - Metadata preserved on export/import

4. **Search**:
   - `search_presets(query)` searches names, descriptions, tags
   - Results include namespace and metadata
   - Supports fuzzy matching

5. **Sync** (optional):
   - If `sync_enabled`, presets shared via agent plugin bus
   - Presets broadcast on `preset.sync` channel
   - Other agents can import received presets
   - Conflict resolution: newest timestamp wins

---

## Thread Safety Model

- **File I/O:** Per-namespace locks to prevent concurrent writes to same namespace
- **In-memory cache:** Thread-safe LRU cache for preset metadata
- **Agent bus sync:** Async message handling, no blocking
- **Validation/migration:** Stateless, can run in parallel
- **Stats updates:** Atomic operations or per-namespace locks

---

## Performance Considerations

- **Caching:** Metadata cached in memory (LRU, 1000 entries)
- **Lazy loading:** Preset data only read on load, not on list
- **Indexing:** Namespace index files for fast listing
- **Batch operations:** Support batch import/export for efficiency
- **Async I/O:** File operations in thread pool to avoid blocking
- **Compression:** Optional gzip for large presets (> 1MB)

---

## Validation and Migration

### ValidationResult

```python
@dataclass
class ValidationResult:
    valid: bool
    errors: List[str]
    warnings: List[str]
    schema_version: int
    data_version: int
```

### Migration Strategy

- Each preset has `version` field in file
- Handler defines current `schema_version`
- If `data_version < schema_version`, run migration chain
- Migration functions: `migrate_v1_to_v2(data)`, `migrate_v2_to_v3(data)`, etc.
- Auto-migration if `auto_migrate=True`, else raise `VersionMismatchError`
- Preserve original file as backup during migration

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_creates_dirs` | Preset directories created on init |
| `test_register_namespace` | Namespace handlers can be registered |
| `test_save_load_roundtrip` | Save then load returns identical data |
| `test_list_presets` | Listing shows all presets in namespace |
| `test_delete_preset` | Delete removes preset and metadata |
| `test_export_import_json` | JSON export/import works correctly |
| `test_export_import_yaml` | YAML export/import works correctly |
| `test_export_import_msgpack` | MessagePack export/import works correctly |
| `test_validation_enabled` | Invalid presets rejected when validation on |
| `test_validation_disabled` | Invalid presets allowed when validation off |
| `test_migration_v1_to_v2` | Old schema migrates correctly |
| `test_metadata_preserved` | Metadata survives export/import |
| `test_search_by_name` | Search finds presets by name |
| `test_search_by_tags` | Search finds presets by tags |
| `test_duplicate_name_error` | Saving duplicate raises error |
| `test_namespace_isolation` | Presets isolated by namespace |
| `test_quota_enforcement` | Quota limits respected |
| `test_backup_creation` | Backups created on overwrite |
| `test_sync_via_agent_bus` | Presets sync across agents |
| `test_thread_safety` | Concurrent access safe |
| `test_large_preset_io` | Large presets (>1MB) handled correctly |
| `test_corrupted_file_handling` | Corrupted files detected and handled |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8E: Config Presets` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### WORKSPACE IGNORE OLD /TASKS/DONE/PHASE-05_TASK-001_preset-system.md (L1-20) [VJlive (Original)]
```markdown
# TASK: PHASE-05_TASK-001_preset-system

## Status
- [ ] BACKLOG
- [x] ACTIVE — Assigned to: Manager-Agent
- [ ] REVIEW
- [ ] DONE

## Objective
Implement a system to save and load the `UnifiedMatrix` state to/from JSON files. This allows users to save their VJ sets.

## Acceptance Criteria
- [ ] `core/state/presets.py` exists.
- [ ] `PresetManager` class implemented.
- [ ] `save_preset(name)`: Serializes `UnifiedMatrix.state` to `presets/{name}.json`.
- [ ] `load_preset(name)`: Reads JSON and updates `UnifiedMatrix` (handling missing/extra keys gracefully).
- [ ] `list_presets()`: Returns list of available preset names.
- [ ] Unit tests for saving/loading.
- [ ] Flask API endpoints added: `GET /presets`, `POST /presets`, `POST /presets/load`.
```

This shows the original preset system task with basic save/load requirements.

### core/core_plugins/midi_presets.py (L1-20) [VJlive (Original)]
```python
"""
MIDI presets manager

Save and load MIDI mapping presets (JSON) for quick recall.
"""

import os
import json
from typing import Dict, Any, Optional
from .plugin_api import register_plugin


class MIDIPresetManager:
    def __init__(self, preset_dir: str = None):
        if preset_dir is None:
            preset_dir = os.path.join(os.path.dirname(__file__), '..', 'presets')
        self.preset_dir = os.path.abspath(preset_dir)
        os.makedirs(self.preset_dir, exist_ok=True)
```

This demonstrates a simple preset manager with directory management and plugin registration.

### core/core_plugins/midi_presets.py (L17-34) [VJlive (Original)]
```python
        self.preset_dir = os.path.abspath(preset_dir)
        os.makedirs(self.preset_dir, exist_ok=True)

    def save_mapping(self, name: str, mapping: Dict[str, Any]) -> bool:
        path = os.path.join(self.preset_dir, name + '.midi.json')
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, indent=2)
        return True

    def load_mapping(self, name: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(self.preset_dir, name + '.midi.json')
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)


register_plugin('midi_preset_manager', MIDIPresetManager)
```

This shows the core save/load pattern with JSON serialization and plugin registration.

### core/mood_preset_manager.py (L1-20) [VJlive (Original)]
```python
from typing import List, Optional, Any, Dict, Tuple, Union, TypeVar
"""
Mood Manifold Preset Manager

Handles save/load/delete/export/import of mood presets with JSON persistence
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import hashlib

@dataclass
class MoodPreset:
    """Mood manifold preset definition"""

    id: str                           # Unique ID (hash-based)
    name: str                         # User-friendly name
```

This shows a more sophisticated preset with dataclass, metadata, and unique IDs.

### core/mood_preset_manager.py (L17-36) [VJlive (Original)]
```python
    """Mood manifold preset definition"""

    id: str                           # Unique ID (hash-based)
    name: str                         # User-friendly name
    description: str                  # Description
    tags: List[str]                   # Categorization tags
    created_at: str                   # ISO timestamp
    modified_at: str                  # ISO timestamp
    author: str                       # Creator name

    # Manifold state
    dimensions: int                   # 4-16
    mood_vector: List[float]          # Current position
    anchors: Dict[str, Dict]          # Anchor definitions
    interpolation_method: str         # linear, spherical, chaotic, etc.

    # Temporal settings
    momentum_strength: float
    velocity_damping: float
    temporal_smoothing: float
```

This demonstrates rich preset metadata and structured data with typed fields.

### core/mood_preset_manager.py (L33-52) [VJlive (Original)]
```python
    # Temporal settings
    momentum_strength: float
    velocity_damping: float
    temporal_smoothing: float
    oscillation_frequency: float

    # Audio reactivity
    audio_mapping_mode: str           # follow, contrast, enhance, modulate
    audio_sensitivity: float
    audio_dimension_weights: List[float]

    # Creative settings
    jitter_strength: float
    jitter_radius: float

    # Parameter mappings
    parameter_mappings: Dict[str, Any]
```

This shows how to organize complex preset data into logical sections.

### core/mood_preset_manager.py (L49-68) [VJlive (Original)]
```python
    parameter_mappings: Dict[str, Any]


class MoodPresetManager:
    """Manage mood manifold presets with JSON persistence"""

    def __init__(self, preset_dir: str = "presets/mood_manifold"):
        # Use absolute path if relative is provided to ensure it works from any CWD
        if not os.path.isabs(preset_dir):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            preset_dir = os.path.join(base_dir, preset_dir)
            
        self.preset_dir = preset_dir
        self.presets: Dict[str, MoodPreset] = {}

        # Create directory if needed
        os.makedirs(preset_dir, exist_ok=True)

        # Load all presets
        self.load_all_presets()
```

This demonstrates directory management with absolute path resolution and auto-loading.

### core/mood_preset_manager.py (L65-84) [VJlive (Original)]
```python
        os.makedirs(preset_dir, exist_ok=True)

        # Load all presets
        self.load_all_presets()

    def generate_preset_id(self, name: str, author: str) -> str:
        """Generate unique preset ID from name and author"""
        content = f"{name}_{author}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def create_preset(
        self,
        name: str,
        description: str,
        tags: List[str],
        mood_state: Dict[str, Any],
        author: str = "Anonymous"
    ) -> str:
        """
        Create new preset from current mood manifold state
```

This shows ID generation using hash and preset creation with metadata.

---

## Notes for Implementers

1. **Core Concept**: The Config Preset System is a unified manager for all configuration domains in VJLive3, providing save/load/export/import with validation, versioning, and agent collaboration.

2. **Namespace Pattern**: Each configuration domain (effects, MIDI, mood, agents) gets its own namespace and handler. This isolates schemas and allows domain-specific validation.

3. **Versioning**: Every preset has a version number. Handlers define migration paths between versions. Auto-migration ensures old presets work with new code.

4. **Validation**: Use JSON Schema or custom validators to ensure preset integrity. Validation can be strict or permissive based on config.

5. **Metadata Separation**: Store preset metadata (usage count, rating, tags) in separate `.meta.json` files to avoid loading heavy data for listings.

6. **Caching**: Cache preset metadata in memory (LRU) for fast listing and search. Invalidate cache on changes.

7. **Agent Sync**: Optional sync via agent plugin bus allows agents to share presets. Use channel `preset.sync` with message format:
   ```python
   {
     'type': 'preset.shared',
     'namespace': 'mood_manifold',
     'preset_name': 'euphoric_ascension',
     'data': { ... },
     'metadata': { ... },
     'sender': 'julie-roo',
     'timestamp': 1234567890.0
   }
   ```

8. **Quota Management**: If quota enabled, track total preset storage per namespace. Reject saves that exceed quota or delete oldest backups.

9. **Backup Strategy**: Keep N backups when overwriting presets. Rotate backups: `preset.json.bak1`, `preset.json.bak2`, etc.

10. **Search**: Implement search across name, description, tags. Use simple substring matching or full-text if needed. Return `PresetInfo` objects with namespace, name, metadata.

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import os
   import json
   import threading
   from pathlib import Path
   from typing import Dict, List, Optional, Any
   from dataclasses import dataclass, asdict
   from abc import ABC, abstractmethod
   from datetime import datetime
   import hashlib
   
   @dataclass
   class PresetConfig:
       preset_dir: str = "presets"
       backup_enabled: bool = True
       backup_count: int = 5
       validation_enabled: bool = True
       auto_migrate: bool = True
       export_default_format: str = "json"
       sync_enabled: bool = False
       sync_channel: str = "preset.sync"
       max_presets_per_namespace: int = 1000
       quota_enabled: bool = False
       quota_total_mb: int = 100
   
   @dataclass
   class ValidationResult:
       valid: bool
       errors: List[str]
       warnings: List[str]
       schema_version: int
       data_version: int
   
   @dataclass
   class PresetInfo:
       namespace: str
       name: str
       description: str
       author: str
       created_at: str
       modified_at: str
       tags: List[str]
       file_size: int
       usage_count: int
       rating: Optional[int] = None
       favorite: bool = False
   
   class PresetHandler(ABC):
       @abstractmethod
       def get_schema_version(self) -> int: ...
       
       @abstractmethod
       def get_default_data(self) -> dict: ...
       
       @abstractmethod
       def validate(self, data: dict) -> ValidationResult: ...
       
       @abstractmethod
       def migrate(self, data: dict, from_version: int) -> dict: ...
       
       @abstractmethod
       def normalize(self, data: dict) -> dict: ...
       
       @abstractmethod
       def denormalize(self, data: dict) -> dict: ...
   
   class ConfigPresetSystem:
       def __init__(self, config: PresetConfig):
           self.config = config
           self.preset_dir = Path(config.preset_dir)
           self.preset_dir.mkdir(parents=True, exist_ok=True)
           
           # Create namespace directories
           self.namespaces: Dict[str, Path] = {}
           
           # Handlers by namespace
           self.handlers: Dict[str, PresetHandler] = {}
           
           # Locks per namespace for thread safety
           self._locks: Dict[str, threading.RLock] = {}
           
           # Metadata cache (LRU)
           self._metadata_cache: Dict[str, dict] = {}
           self._cache_lock = threading.RLock()
           
           # Load existing namespaces
           self._scan_namespaces()
       
       def _scan_namespaces(self):
           """Scan preset_dir for namespace directories."""
           for ns_dir in self.preset_dir.iterdir():
               if ns_dir.is_dir() and not ns_dir.name.startswith('.'):
                   self.namespaces[ns_dir.name] = ns_dir
                   self._locks[ns_dir.name] = threading.RLock()
       
       def register_namespace(self, namespace: str, handler: PresetHandler):
           """Register a new namespace with its handler."""
           ns_dir = self.preset_dir / namespace
           ns_dir.mkdir(exist_ok=True)
           
           self.namespaces[namespace] = ns_dir
           self.handlers[namespace] = handler
           self._locks[namespace] = threading.RLock()
       
       def save_preset(self, namespace: str, name: str, data: dict, 
                      metadata: dict = None) -> str:
           """Save preset to namespace."""
           if namespace not in self.handlers:
               raise KeyError(f"Namespace '{namespace}' not registered")
           
           # Validate name
           if '/' in name or '\\' in name or '..' in name:
               raise ValueError("Invalid preset name")
           
           handler = self.handlers[namespace]
           
           # Validate data if enabled
           if self.config.validation_enabled:
               validation = handler.validate(data)
               if not validation.valid:
                   raise ValueError(f"Validation failed: {validation.errors}")
           
           # Normalize data (add defaults, canonical format)
           normalized = handler.normalize(data)
           
           # Build preset structure
           preset = {
               'version': handler.get_schema_version(),
               'namespace': namespace,
               'name': name,
               'created_at': datetime.utcnow().isoformat() + 'Z',
               'modified_at': datetime.utcnow().isoformat() + 'Z',
               'author': metadata.get('author', 'Anonymous') if metadata else 'Anonymous',
               'description': metadata.get('description', '') if metadata else '',
               'tags': metadata.get('tags', []) if metadata else [],
               'data': normalized
           }
           
           # Save with namespace lock
           lock = self._locks[namespace]
           with lock:
               ns_dir = self.namespaces[namespace]
               preset_path = ns_dir / f"{name}.json"
               
               # Backup if exists and backup enabled
               if preset_path.exists() and self.config.backup_enabled:
                   self._create_backup(preset_path)
               
               # Write preset
               with open(preset_path, 'w', encoding='utf-8') as f:
                   json.dump(preset, f, indent=2)
               
               # Create/update metadata
               self._update_metadata_cache(namespace, name, preset)
               
               # Check quota
               if self.config.quota_enabled:
                   self._check_quota()
               
               # Sync via agent bus if enabled
               if self.config.sync_enabled:
                   self._sync_preset(namespace, name, preset)
           
           return name
       
       def load_preset(self, namespace: str, name: str, validate: bool = True) -> dict:
           """Load preset from namespace."""
           if namespace not in self.namespaces:
               raise KeyError(f"Namespace '{namespace}' not found")
           
           lock = self._locks[namespace]
           with lock:
               ns_dir = self.namespaces[namespace]
               preset_path = ns_dir / f"{name}.json"
               
               if not preset_path.exists():
                   raise FileNotFoundError(f"Preset '{name}' not found in namespace '{namespace}'")
               
               with open(preset_path, 'r', encoding='utf-8') as f:
                   preset = json.load(f)
               
               # Get handler
               handler = self.handlers.get(namespace)
               if handler is None:
                   # No handler, return raw data
                   return preset['data']
               
               # Validate if requested
               if validate and self.config.validation_enabled:
                   validation = handler.validate(preset['data'])
                   if not validation.valid:
                       raise ValueError(f"Preset validation failed: {validation.errors}")
               
               # Migrate if version mismatch
               current_version = handler.get_schema_version()
               data_version = preset.get('version', 1)
               
               if data_version < current_version:
                   if self.config.auto_migrate:
                       migrated = preset['data']
                       for v in range(data_version, current_version):
                           migrated = handler.migrate(migrated, v)
                       preset['data'] = migrated
                       preset['version'] = current_version
                   else:
                       raise ValueError(f"Preset version {data_version} too old, auto_migrate disabled")
               
               # Denormalize (remove defaults)
               result = handler.denormalize(preset['data'])
               
               # Update usage stats
               self._increment_usage(namespace, name)
               
               return result
       
       def _create_backup(self, path: Path):
           """Create backup of existing preset."""
           for i in range(self.config.backup_count - 1, 0, -1):
               old_backup = path.with_name(f"{path.name}.bak{i}")
               new_backup = path.with_name(f"{path.name}.bak{i+1}")
               if old_backup.exists():
                   old_backup.rename(new_backup)
           first_backup = path.with_name(f"{path.name}.bak1")
           path.copy(first_backup)
       
       def _update_metadata_cache(self, namespace: str, name: str, preset: dict):
           """Update metadata cache for preset."""
           cache_key = f"{namespace}/{name}"
           meta = {
               'file_size': os.path.getsize(self.namespaces[namespace] / f"{name}.json"),
               'file_hash': hashlib.sha256(json.dumps(preset).encode()).hexdigest()[:16],
               'last_used': None,
               'usage_count': 0,
               'rating': None,
               'favorite': False,
               'tags': preset.get('tags', []),
               'description': preset.get('description', ''),
               'author': preset.get('author', ''),
               'created_at': preset.get('created_at'),
               'modified_at': preset.get('modified_at')
           }
           
           with self._cache_lock:
               self._metadata_cache[cache_key] = meta
       
       def _increment_usage(self, namespace: str, name: str):
           """Increment usage count for preset."""
           cache_key = f"{namespace}/{name}"
           with self._cache_lock:
               if cache_key in self._metadata_cache:
                   self._metadata_cache[cache_key]['usage_count'] += 1
                   self._metadata_cache[cache_key]['last_used'] = datetime.utcnow().isoformat() + 'Z'
       
       def _check_quota(self):
           """Check if total preset storage exceeds quota."""
           if not self.config.quota_enabled:
               return
           
           total_bytes = 0
           for ns_dir in self.namespaces.values():
               for preset_file in ns_dir.glob('*.json'):
                   total_bytes += preset_file.stat().st_size
           
           quota_bytes = self.config.quota_total_mb * 1024 * 1024
           if total_bytes > quota_bytes:
               # TODO: Implement cleanup strategy (delete oldest, least used)
               pass
       
       def _sync_preset(self, namespace: str, name: str, preset: dict):
           """Sync preset via agent plugin bus."""
           # This would use the agent plugin bus to broadcast preset
           # Implementation depends on agent bus integration
           pass
       
       def list_presets(self, namespace: str = None) -> List[str]:
           """List preset names, optionally filtered by namespace."""
           if namespace:
               if namespace not in self.namespaces:
                   return []
               ns_dir = self.namespaces[namespace]
               return [p.stem for p in ns_dir.glob('*.json') if not p.name.startswith('.')]
           else:
               all_presets = []
               for ns_name, ns_dir in self.namespaces.items():
                   all_presets.extend([f"{ns_name}/{p.stem}" for p in ns_dir.glob('*.json') if not p.name.startswith('.')])
               return all_presets
       
       def get_preset_metadata(self, namespace: str, name: str) -> dict:
           """Get metadata for a preset."""
           cache_key = f"{namespace}/{name}"
           with self._cache_lock:
               return self._metadata_cache.get(cache_key, {})
   ```

2. **EffectChainHandler Example**:
   ```python
   class EffectChainHandler(PresetHandler):
       def get_schema_version(self) -> int:
           return 1
       
       def get_default_data(self) -> dict:
           return {
               'effects': [],
               'routing': 'serial',
               'bypass_all': False,
               'master_fx': []
           }
       
       def validate(self, data: dict) -> ValidationResult:
           errors = []
           warnings = []
           
           if 'effects' not in data:
               errors.append("Missing 'effects' field")
           
           if not isinstance(data.get('effects', []), list):
               errors.append("'effects' must be a list")
           
           # Validate each effect
           for i, effect in enumerate(data.get('effects', [])):
               if 'type' not in effect:
                   errors.append(f"Effect {i} missing 'type'")
               if 'params' not in effect:
                   warnings.append(f"Effect {i} missing 'params', using defaults")
           
           return ValidationResult(
               valid=len(errors) == 0,
               errors=errors,
               warnings=warnings,
               schema_version=self.get_schema_version(),
               data_version=data.get('version', 1)
           )
       
       def migrate(self, data: dict, from_version: int) -> dict:
           # Migrate from old schema to new
           if from_version == 1:
               # No migration needed
               return data
           return data
       
       def normalize(self, data: dict) -> dict:
           # Add defaults for missing fields
           normalized = self.get_default_data()
           normalized.update(data)
           
           # Normalize each effect
           for effect in normalized['effects']:
               if 'params' not in effect:
                   effect['params'] = {}
               if 'bypassed' not in effect:
                   effect['bypassed'] = False
           
           return normalized
       
       def denormalize(self, data: dict) -> dict:
           # Remove default values to keep file size small
           # Keep only non-default values
           return data
   ```

3. **Export/Import**:
   ```python
   def export_preset(self, namespace: str, name: str, format: str = 'json') -> bytes:
       data = self.load_preset(namespace, name)
       preset = self._get_full_preset(namespace, name)  # includes metadata
       
       if format == 'json':
           return json.dumps(preset, indent=2).encode('utf-8')
       elif format == 'yaml':
           import yaml
           return yaml.dump(preset).encode('utf-8')
       elif format == 'msgpack':
           import msgpack
           return msgpack.packb(preset)
       else:
           raise ValueError(f"Unsupported format: {format}")
   
   def import_preset(self, namespace: str, data: bytes, format: str = 'json', 
                    merge: bool = False) -> str:
       # Parse data
       if format == 'json':
           preset = json.loads(data.decode('utf-8'))
       elif format == 'yaml':
           import yaml
           preset = yaml.safe_load(data.decode('utf-8'))
       elif format == 'msgpack':
           import msgpack
           preset = msgpack.unpackb(data)
       else:
           raise ValueError(f"Unsupported format: {format}")
       
       # Validate preset structure
       if 'name' not in preset or 'data' not in preset:
           raise ValueError("Invalid preset format")
       
       name = preset['name']
       
       # Check if exists and merge or replace
       if self.preset_exists(namespace, name):
           if merge:
               # Load existing and merge data
               existing = self.load_preset(namespace, name)
               existing.update(preset['data'])
               preset['data'] = existing
           else:
               # Backup before overwrite
               self._create_backup(self.namespaces[namespace] / f"{name}.json")
       
       # Save
       return self.save_preset(namespace, name, preset['data'], {
           'description': preset.get('description', ''),
           'tags': preset.get('tags', []),
           'author': preset.get('author', 'Imported')
       })
   ```

4. **Search**:
   ```python
   def search_presets(self, query: str, namespace: str = None) -> List[PresetInfo]:
       """Search presets by name, description, tags."""
       query = query.lower()
       results = []
       
       namespaces_to_search = [namespace] if namespace else self.namespaces.keys()
       
       for ns in namespaces_to_search:
           for name in self.list_presets(ns):
               meta = self.get_preset_metadata(ns, name)
               
               # Search in name, description, tags
               score = 0
               if query in name.lower():
                   score += 10
               if query in meta.get('description', '').lower():
                   score += 5
               if any(query in tag.lower() for tag in meta.get('tags', [])):
                   score += 3
               
               if score > 0:
                   results.append(PresetInfo(
                       namespace=ns,
                       name=name,
                       description=meta.get('description', ''),
                       author=meta.get('author', ''),
                       created_at=meta.get('created_at', ''),
                       modified_at=meta.get('modified_at', ''),
                       tags=meta.get('tags', []),
                       file_size=meta.get('file_size', 0),
                       usage_count=meta.get('usage_count', 0),
                       rating=meta.get('rating'),
                       favorite=meta.get('favorite', False)
                   ))
       
       # Sort by score (descending) then usage (descending)
       results.sort(key=lambda x: (x.usage_count or 0), reverse=True)
       return results
   ```

---
-

## References

- JSON Schema validation
- Data migration patterns
- Configuration management best practices
- Plugin architecture patterns
- VJLive-1 preset managers (MIDI, mood)
- VJLive-2 unified matrix state serialization
- LRU cache design
- File system watchers for real-time updates

---

## Conclusion

The Config Preset System provides a unified, robust, and extensible foundation for managing all configuration state in VJLive3. By supporting multiple namespaces with domain-specific handlers, versioned schemas with automatic migration, and agent collaboration via the plugin bus, it enables users to save, share, and recall complete performance setups with confidence. Its careful attention to validation, metadata, and performance ensures that preset management never interferes with the sacred 60 FPS experience, while its extensible architecture allows new configuration domains to be added without modifying core code.

---
