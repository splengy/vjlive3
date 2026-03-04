# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-N1_unified_matrix_node_registry.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-N1 — UnifiedMatrix + Node Registry (manifest-based)

**Phase:** P1 / P1-N1
**Assigned To:** [Agent name]
**Spec Written By:** [Agent name]
**Date:** [YYYY-MM-DD]

---

## What This Module Does

- **UnifiedMatrix**: A shared, immutable data structure that flows through the entire node graph, carrying video frames, audio analysis data, and timing information. It's the primary communication mechanism between nodes.
- **Node Registry**: A centralized discovery system that loads plugin manifests from disk, validates node metadata, and provides a lookup service for the graph builder to instantiate nodes by their manifest IDs.
- **Manifest-based Plugin System**: Each node plugin provides a `manifest.json` (or embedded METADATA) declaring its parameters, GPU tier, input/output types, and shader references. The registry reads these manifests without importing the code, enabling safe plugin discovery.
- **Parameter Normalization**: All VJ-facing parameters use a 0.0-10.0 float range for consistency across the UI. Internal implementations may map these to different ranges (e.g., 0-1, 1-10, boolean thresholds).
- **Graph Construction Foundation**: Provides the data model and registration API that all subsequent node graph functionality depends on. Without this, nodes cannot be discovered, instantiated, or connected.

---

## What This Module Does NOT Do

- Execute node processing or shader compilation (that's the runtime's job)
- Provide a visual node graph UI (P1-N4 covers that)
- Handle hot-reloading of plugins (that's a separate system)
- Manage node execution order or topological sorting (graph scheduler handles that)
- Provide audio file I/O or video capture (those are leaf nodes)
- Store persistent user presets or project files (higher-level application concern)

---

## Detailed Behavior and Parameter Interactions

### UnifiedMatrix Structure

The UnifiedMatrix is a **read-only snapshot** of the current processing context:

```python
class UnifiedMatrix:
    frame: np.ndarray          # Current video frame (HxWx3/4 uint8)
    audio_data: Dict           # Beat info, spectrum, RMS, BPM
    time: float                # Global time in seconds
    frame_count: int           # Monotonic frame counter
    resolution: Tuple[int, int] # (width, height)
    node_outputs: Dict[str, Any] # Outputs from previously executed nodes
```

**Key design**: The matrix is **immutable** as it traverses the graph. Each node receives a matrix, processes it, and returns a new matrix (or the same with modifications). This prevents side effects and enables deterministic replay.

### Node Registry Operation

1. **Scanning**: At startup, the registry walks `plugins/` directory (and user plugin paths) looking for `manifest.json` files or Python modules with embedded `METADATA`.
2. **Validation**: Each manifest is validated against the P1-P2 schema (Pydantic model). Required fields: `id`, `name`, `params[]`, `input_type`, `output_type`, `gpu_tier`.
3. **Indexing**: Valid nodes are indexed by `id` and stored in an in-memory dictionary: `{ "vvimana_synth": NodeInfo, ... }`.
4. **Instantiation**: When the graph builder needs a node, it calls `registry.create_node(node_id)` which imports the module, instantiates the class, and returns the ready-to-use object.
5. **Introspection**: The registry provides `get_node_manifest(id)` for UI builders to dynamically generate parameter controls.

### Manifest Schema

```json
{
  "id": "vvimana_synth",
  "name": "Vimana GVS010",
  "description": "Unified feedback processor with composite simulation",
  "gpu_tier": "HIGH",
  "input_type": "video",
  "output_type": "video",
  "parameters": [
    {"id": "shift_up", "name": "Shift Up", "default": 0.0, "min": 0.0, "max": 10.0},
    {"id": "zoom", "name": "Zoom", "default": 5.0, "min": 0.0, "max": 10.0}
  ]
}
```

**Parameter constraints**: All `min`/`max` must be 0.0-10.0 floats. No booleans, no 0-1 ranges. The UI uses these directly.

### Parameter Normalization Layer

Nodes may internally map VJ parameters to different ranges:

```python
# Example: zoom parameter (0-10 UI) -> internal zoom factor
def set_parameter(self, name: str, value: float):
    if name == "zoom":
        # UI: 0-10, internal: 0.5x to 2.0x zoom
        normalized = 0.5 + (value / 10.0) * 1.5
        self._zoom_factor = normalized
```

The spec enforces that **all user-facing parameters** must be 0.0-10.0 floats. This is a hard boundary.

---

## Public Interface

```python
from typing import Dict, List, Optional, Type, Any
import numpy as np

class UnifiedMatrix:
    """
    Immutable data carrier that flows through the node graph.
    This is the ONLY way nodes communicate with each other.
    """
    
    def __init__(
        self,
        frame: np.ndarray,
        audio_data: Optional[Dict] = None,
        time: float = 0.0,
        frame_count: int = 0,
        resolution: Optional[Tuple[int, int]] = None,
        node_outputs: Optional[Dict[str, Any]] = None
    ):
        """
        Construct a UnifiedMatrix snapshot.
        
        Args:
            frame: Current video frame (HxWx3/4 uint8)
            audio_data: Beat detection, spectrum, RMS, BPM
            time: Global time in seconds
            frame_count: Monotonic counter for deterministic replay
            resolution: (width, height) tuple, derived from frame if None
            node_outputs: Dict of outputs from previously executed nodes
        """
        self._frame = frame
        self._audio_data = audio_data or {}
        self._time = time
        self._frame_count = frame_count
        self._resolution = resolution or (frame.shape[1], frame.shape[0])
        self._node_outputs = node_outputs or {}
        
    @property
    def frame(self) -> np.ndarray:
        """Get the current video frame (read-only)."""
        return self._frame
    
    @property
    def audio_data(self) -> Dict:
        """Get audio analysis data (read-only)."""
        return self._audio_data
    
    @property
    def time(self) -> float:
        """Get global time in seconds."""
        return self._time
    
    @property
    def frame_count(self) -> int:
        """Get monotonic frame counter."""
        return self._frame_count
    
    @property
    def resolution(self) -> Tuple[int, int]:
        """Get (width, height) tuple."""
        return self._resolution
    
    @property
    def node_outputs(self) -> Dict[str, Any]:
        """Get dictionary of previous node outputs."""
        return self._node_outputs
    
    def with_updates(
        self,
        frame: Optional[np.ndarray] = None,
        audio_data: Optional[Dict] = None,
        time: Optional[float] = None,
        frame_count: Optional[int] = None,
        node_outputs: Optional[Dict[str, Any]] = None
    ) -> 'UnifiedMatrix':
        """
        Create a new UnifiedMatrix with updated fields.
        This preserves immutability while allowing modifications.
        
        Returns:
            New UnifiedMatrix instance with merged updates.
        """
        new_frame = frame if frame is not None else self._frame
        new_audio = {**self._audio_data, **(audio_data or {})}
        new_time = time if time is not None else self._time
        new_count = frame_count if frame_count is not None else self._frame_count
        new_res = (new_frame.shape[1], new_frame.shape[0]) if frame is not None else self._resolution
        new_outputs = {**self._node_outputs, **(node_outputs or {})}
        
        return UnifiedMatrix(
            frame=new_frame,
            audio_data=new_audio,
            time=new_time,
            frame_count=new_count,
            resolution=new_res,
            node_outputs=new_outputs
        )


class NodeManifest(BaseModel):
    """
    Pydantic model for node manifest validation.
    All parameters must use 0.0-10.0 float ranges.
    """
    id: str
    name: str
    description: str
    gpu_tier: str  # "NONE", "LOW", "MEDIUM", "HIGH"
    input_type: str  # "video", "audio", "cv", "any"
    output_type: str
    parameters: List[ParameterDef]
    
class ParameterDef(BaseModel):
    id: str
    name: str
    default: float
    min: float = 0.0
    max: float = 10.0
    
    @validator('min', 'max', 'default')
    def validate_range(cls, v):
        if not (0.0 <= v <= 10.0):
            raise ValueError(f"Parameter must be in 0.0-10.0 range, got {v}")
        return v


class NodeRegistry:
    """
    Central registry for discovering and instantiating nodes.
    Uses manifest-based discovery without importing code initially.
    """
    
    def __init__(self, plugin_dirs: List[str]):
        """
        Initialize registry with plugin search paths.
        
        Args:
            plugin_dirs: List of directories to scan for manifests
        """
        self._plugin_dirs = plugin_dirs
        self._manifests: Dict[str, NodeManifest] = {}
        self._module_cache: Dict[str, Type] = {}
        
    def scan_plugins(self) -> None:
        """
        Scan all plugin directories for manifest.json files.
        Validates each manifest and builds the index.
        
        Raises:
            PluginValidationError: If manifest is invalid
        """
        for plugin_dir in self._plugin_dirs:
            for manifest_path in Path(plugin_dir).rglob("manifest.json"):
                self._load_manifest(manifest_path)
                
    def _load_manifest(self, path: Path) -> None:
        """Load and validate a single manifest file."""
        with open(path) as f:
            data = json.load(f)
        
        # Validate against schema
        manifest = NodeManifest(**data)
        
        if manifest.id in self._manifests:
            raise DuplicateNodeError(f"Node ID {manifest.id} already registered")
            
        self._manifests[manifest.id] = manifest
        
    def get_manifest(self, node_id: str) -> Optional[NodeManifest]:
        """
        Get manifest for a node by ID.
        
        Args:
            node_id: Unique node identifier
            
        Returns:
            NodeManifest if found, None otherwise
        """
        return self._manifests.get(node_id)
    
    def list_manifests(self) -> List[NodeManifest]:
        """Get all registered node manifests."""
        return list(self._manifests.values())
    
    def create_node(self, node_id: str, **kwargs) -> 'BaseNode':
        """
        Instantiate a node from its manifest.
        
        Args:
            node_id: Node identifier from manifest
            **kwargs: Initial parameter values
            
        Returns:
            Instantiated node object (subclass of BaseNode)
            
        Raises:
            NodeNotFoundError: If node_id not in registry
            ImportError: If node module cannot be loaded
        """
        manifest = self.get_manifest(node_id)
        if manifest is None:
            raise NodeNotFoundError(f"Node {node_id} not registered")
        
        # Check cache first
        if node_id in self._module_cache:
            node_class = self._module_cache[node_id]
        else:
            # Import module (convention: manifest ID maps to Python module)
            module_name = self._module_name_from_id(node_id)
            module = importlib.import_module(module_name)
            node_class = getattr(module, self._class_name_from_id(node_id))
            self._module_cache[node_id] = node_class
        
        # Instantiate with parameters
        node = node_class()
        
        # Set initial parameters
        for param_id, value in kwargs.items():
            node.set_parameter(param_id, value)
            
        return node
    
    def _module_name_from_id(self, node_id: str) -> str:
        """Convert node ID to Python module name."""
        # e.g., "vvimana_synth" -> "core.effects.vimana"
        # This is convention-based; could be overridden in manifest
        return f"core.effects.{node_id.split('_')[0]}"
    
    def _class_name_from_id(self, node_id: str) -> str:
        """Convert node ID to Python class name."""
        # e.g., "vvimana_synth" -> "Vimana"
        parts = node_id.split('_')
        return ''.join(p.capitalize() for p in parts[1:])
```

---

## Inputs and Outputs

### UnifiedMatrix

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `frame` | `np.ndarray` | Video frame | Shape: (H, W, 3/4), dtype: uint8 |
| `audio_data` | `Dict` | Audio analysis | Keys: 'is_beat', 'confidence', 'bpm', 'rms', 'spectrum' |
| `time` | `float` | Global time | Seconds, monotonically increasing |
| `frame_count` | `int` | Frame counter | Non-negative, increments per frame |
| `resolution` | `Tuple[int, int]` | Frame dimensions | (width, height), > 0 |
| `node_outputs` | `Dict[str, Any]` | Previous node results | Keys are node IDs, values are node-specific |

### NodeRegistry

| Method | Input | Output | Description |
|--------|-------|--------|-------------|
| `scan_plugins()` | None | None | Load all manifests from plugin_dirs |
| `get_manifest(id)` | node_id: str | NodeManifest \| None | Lookup manifest by ID |
| `list_manifests()` | None | List[NodeManifest] | Get all registered nodes |
| `create_node(id, **params)` | node_id + params | BaseNode | Instantiate node with parameters |

---

## Edge Cases and Error Handling

### UnifiedMatrix

- **Empty frame (0×0)**: Raise ValueError during construction; frame must have valid dimensions
- **Wrong frame format**: Raise TypeError if frame is not ndarray or has wrong dtype
- **Missing audio_data**: Treat as empty dict; nodes must handle missing keys gracefully
- **Resolution mismatch**: If resolution provided doesn't match frame shape, recalculate from frame (warning log)
- **Node output collision**: If two nodes write same key to node_outputs, last writer wins (but log warning)
- **Immutability violation**: All properties are read-only; attempts to modify raise AttributeError

### NodeRegistry

- **Missing plugin directory**: Skip silently (info log), don't fail startup
- **Invalid manifest JSON**: Raise PluginValidationError with file path and validation errors
- **Missing required fields**: Validation fails with clear message listing missing fields
- **Parameter out of range**: Pydantic validator catches min/max violations during manifest load
- **Duplicate node IDs**: Raise DuplicateNodeError; each node must have unique ID across all plugins
- **Module import failure**: Raise NodeImportError with original exception chained
- **Class not found**: If module exists but expected class missing, raise NodeClassNotFoundError
- **Circular imports**: Python import system handles this; if it fails, propagate ImportError

### Manifest-based Discovery

- **Manifest without code**: If manifest exists but Python module missing, registry loads manifest but create_node fails (deferred error)
- **Code without manifest**: Python modules without manifest are ignored (not registered)
- **Stale cache**: If module file changes after import, registry doesn't auto-reload (hot-reload is separate feature)
- **Permission errors**: If plugin directory unreadable, log warning and continue

---

## Mathematical Formulations

This module doesn't involve mathematical transformations. It's a data structure and registry system. However, there are **invariants**:

### Parameter Range Invariant
For all parameters in all manifests:
$$0.0 \leq \text{min} \leq \text{default} \leq \text{max} \leq 10.0$$

### Node ID Uniqueness
$$\forall n_1, n_2 \in \text{Registry}, n_1 \neq n_2 \implies n_1.id \neq n_2.id$$

### Immutability Guarantee
For any `UnifiedMatrix` instance `m`:
- `m.frame` returns the same object reference (or copy if with_updates used)
- `m.audio_data`, `m.node_outputs` are shallow copies to prevent mutation
- `with_updates()` creates new instance; original unchanged

---

## Performance Characteristics

### UnifiedMatrix

- **Memory footprint**: 
  - Frame: H×W×3 bytes (uint8) or H×W×4
  - audio_data: ~1KB (small dict)
  - node_outputs: Variable, typically <1MB
  - Total: Dominated by frame size (e.g., 1080p = ~6MB for RGBA)
- **Copy cost**: `with_updates()` does shallow copies of dicts, O(1) for frame if unchanged
- **Allocation frequency**: Once per frame per node (if nodes create new matrix)
- **Optimization**: Use memory pooling for frame buffers if allocation becomes bottleneck

### NodeRegistry

- **Scanning cost**: O(N) where N = number of manifest files (typically <100)
- **Lookup cost**: O(1) dictionary lookup by node_id
- **Instantiation cost**: Module import (cached after first use) + class instantiation (~1ms)
- **Memory**: One NodeManifest per node (~1KB each), plus module cache

### Startup Time

- Manifest scanning: 50-200ms for 50-100 plugins
- Module imports: Lazy (only when node instantiated)
- Total cold start: <500ms for full plugin suite

---

## Test Plan

### Unit Tests (Coverage: 90%)

1. **UnifiedMatrix construction**
   - Create with valid frame, audio, time
   - Default values for optional fields
   - Resolution auto-calculated from frame shape

2. **UnifiedMatrix immutability**
   - Properties are read-only
   - `with_updates()` creates new instance
   - Original instance unchanged after `with_updates()`

3. **UnifiedMatrix field access**
   - `frame` returns ndarray
   - `audio_data` returns dict (copy, not original)
   - `node_outputs` returns dict (copy)
   - `resolution` returns (w, h) tuple

4. **NodeManifest validation**
   - Valid manifest passes Pydantic validation
   - Missing required fields raise ValidationError
   - Parameter min/max outside 0-10 range raises ValidationError
   - Default outside min/max raises ValidationError

5. **NodeRegistry scanning**
   - `scan_plugins()` finds all manifest.json files in plugin_dirs
   - Invalid manifests are caught and reported with file path
   - Duplicate node IDs raise DuplicateNodeError

6. **NodeRegistry lookup**
   - `get_manifest(id)` returns correct manifest
   - `get_manifest(unknown)` returns None
   - `list_manifests()` returns all registered manifests

7. **NodeRegistry instantiation**
   - `create_node(valid_id)` returns node instance
   - Unknown node_id raises NodeNotFoundError
   - Parameters passed to node's `set_parameter()` during creation
   - Module import errors propagate as ImportError

8. **Node ID to module/class mapping**
   - `_module_name_from_id("vvimana_synth")` returns "core.effects.vimana"
   - `_class_name_from_id("vvimana_synth")` returns "Vimana"

### Integration Tests (Coverage: 85%)

9. **Full graph construction**
   - Registry loads manifests from disk
   - Graph builder uses registry to create nodes
   - Nodes can be connected via UnifiedMatrix flow

10. **Parameter propagation**
    - Node created with initial parameters
    - Parameters accessible via node.get_parameter()
    - Parameter changes reflected in node behavior

11. **Manifest-driven UI generation**
    - UI builder can generate controls from manifest.parameters
    - All parameters use 0-10 sliders in UI
    - Default values match manifest

12. **Error recovery**
    - One bad plugin doesn't crash entire registry
    - Missing node module gives clear error message
    - Invalid parameter value caught at node.set_parameter()

### Performance Tests (Coverage: 75%)

13. **Registry startup**
    - Scanning 100 plugins completes in <500ms
    - Memory usage <10MB for manifest storage

14. **Node instantiation**
    - First instantiation (with import) <10ms
    - Subsequent instantiation (cached) <1ms

---

## Definition of Done

### Technical Requirements
- [ ] UnifiedMatrix class implemented with immutability guarantees
- [ ] NodeManifest Pydantic model validates all manifests
- [ ] NodeRegistry scans plugin directories and builds index
- [ ] `create_node()` instantiates nodes from manifests
- [ ] All parameters enforce 0.0-10.0 float range in manifests
- [ ] Node ID uniqueness enforced across all plugins
- [ ] Module caching works for fast repeated instantiation
- [ ] Clear error messages for all failure modes

### Quality Requirements
- [ ] 80%+ test coverage achieved
- [ ] All unit tests passing
- [ ] Integration tests verify full plugin discovery → instantiation flow
- [ ] Performance benchmarks meet startup time targets
- [ ] Error handling robust with actionable messages
- [ ] Documentation complete with examples

### Integration Requirements
- [ ] Compatible with P1-N2 (Node types) for node base class
- [ ] Compatible with P1-P2 (Plugin loading) for validation
- [ ] Used by P1-N4 (Visual node graph UI) for node palette
- [ ] Used by P3-* nodes for registration
- [ ] Works with P2-* specs for graph execution

---

## Legacy References

### Original VJLive-2 Architecture

From `agent-heartbeat/golden_example_vimana.py`, the pattern is:

```python
class Vimana(Effect):
    """Vimana GVS010 - Unified Software Emulation."""
    
    # Embedded Manifest - The Source of Truth
    METADATA = {
        "id": "vvimana_synth",
        "name": "Vimana GVS010",
        "params": [
            {"id": "shift_up", "name": "Shift Up", "default": 0.0, "min": 0.0, "max": 10.0},
            # ... 70+ parameters all 0-10 floats
        ]
    }
    
    def __init__(self):
        super().__init__("vimana", VIMANA_FRAGMENT)
        self._hydrate_parameters()  # Populate self.parameters from METADATA
        
    def _hydrate_parameters(self):
        """Hydrate parameter dictionary from the metadata source of truth."""
        for param in self.METADATA["params"]:
            self.parameters[param["id"]] = param["default"]
            
    def get_manifest(self) -> Dict[str, Any]:
        """Return the embedded manifest for agent introspection."""
        return self.METADATA
```

**Key insights:**
- Manifest is **embedded** in the Python class as `METADATA` dict
- Parameters are **hydrated** from manifest into `self.parameters` dict
- All parameters are 0.0-10.0 floats with explicit min/max
- Node ID convention: `{plugin_prefix}_{node_name}` (e.g., `vvimana_synth`)
- Shader fragment is embedded as string constant

### Expected Manifest Locations

1. **Embedded**: `METADATA` dict in node class (as shown above)
2. **External file**: `manifest.json` alongside module (for non-Python plugins or separation)
3. **Hybrid**: External manifest with `"module": "core.effects.vimana"` reference

The registry should support all three patterns.

### Related Specs

- **P1-N2**: Defines the `BaseNode` class that all nodes inherit from
- **P1-P2**: Pydantic validation schemas for manifests (this spec includes minimal schema)
- **P1-N4**: Uses registry to populate node palette in UI
- **P3-EXT150**: Example node that would be registered

---

## Easter Egg Idea

**Secret Feature**: "Matrix Debug Mode"
- Press `Ctrl+Shift+M` in the node graph UI to reveal the UnifiedMatrix data flow
- Shows live counts: frames processed, node_outputs size, time drift
- Hidden parameter: `matrix_debug_level` (0-10 float) that when set to 9.99, logs full matrix contents to `/tmp/matrix_debug.log` every 100 frames
- Easter egg: At exactly `matrix_debug_level = 10.0`, the system plays a sound and displays "THE MATRIX IS OBSERVED" in the status bar, and all node outputs become visible as floating labels in the graph UI

---

## Completion Notes

This spec defines the foundational data model and plugin discovery system for VJLive3. It's intentionally minimal—just enough to enable node graph construction without over-engineering.

**Critical design decisions:**
1. **Immutability**: UnifiedMatrix is immutable to prevent subtle bugs from shared state. Nodes must explicitly create new matrices to modify data.
2. **Manifest-first**: The manifest is the source of truth. Code can be introspected, but manifests enable safe discovery without imports.
3. **Parameter uniformity**: All VJ-facing parameters are 0-10 floats. This simplifies UI generation and user mental model.
4. **Lazy instantiation**: Modules are imported only when nodes are created, keeping startup fast.
5. **Convention over configuration**: Node ID → module/class mapping uses naming conventions, reducing manifest boilerplate.

**Open questions for later phases:**
- How does the registry handle versioning of node APIs?
- Should manifests support dependency declarations between nodes?
- How to handle nodes that need async initialization (e.g., loading models)?
- What's the strategy for hot-reloading modified node code?

**Next steps after spec approval:**
1. Implement `UnifiedMatrix` with full immutability guarantees
2. Implement `NodeManifest` Pydantic model with complete validation
3. Implement `NodeRegistry` with filesystem scanning
4. Write comprehensive test suite (target 85% coverage)
5. Create example plugin with manifest to validate the system
6. Document plugin development guide for third-party developers

This spec is the keystone for the entire node graph architecture. Everything else builds on top of it.