# Spec: P1-N2 — Core Node Types Collection

**Phase:** Phase 1 / P1-N2
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `VJlive-2/core/matrix/node_effect.py`, `VJlive-2/core/matrix/matrix_nodes.py`
**Depends On:** P1-N1 (NodeBase, NodeRegistry), P1-P2 (PluginLoader), P1-R3 (ShaderCompiler)

---

## What This Module Does

Implements the built-in set of Phase 1 node types that populate the node graph. These are
the core nodes every VJLive3 install ships with — not external plugins. Includes:
- **SourceNode**: Outputs a blank RGBA frame (1920×1080 or configured size) as a seed
- **EffectNode**: Wraps a loaded PluginBase instance; passes the frame through its `process()`
- **OutputNode**: Final node in the chain; pushes the frame to the render engine's output FBO
- **PassthroughNode**: Routes signal unchanged (useful for branching/debugging)
- **MixNode**: Blends two input frames by weight (lerp)
- **GainNode**: Multiplies pixel values by a scalar (brightness control)

No audio-reactive nodes here — those are Phase 2.

---

## What It Does NOT Do

- Does NOT render anything directly — nodes produce frame references, engine renders
- Does NOT implement hardware nodes (DMX, MIDI, OSC) — those are Phase 2
- Does NOT implement audio-reactive nodes — those are Phase 2
- Does NOT implement modulation nodes (LFO, envelopes) — those are Phase 2

---

## Public Interface per Node Type

All nodes inherit `NodeBase` from P1-N1. METADATA drives parameter UI.

### SourceNode

```python
class SourceNode(NodeBase):
    """Outputs a configurable blank or noise frame as graph seed."""
    METADATA = {
        "id": "core.source",
        "name": "Source",
        "description": "Outputs a blank RGBA frame of the configured resolution. Use as the first node in any signal chain. Supports solid colour or noise fill mode.",
        "inputs": [],
        "outputs": [{"name": "out", "type": "frame"}],
        "params": [
            {"id": "width",  "type": "int",  "min": 64,  "max": 4096, "default": 1920},
            {"id": "height", "type": "int",  "min": 64,  "max": 2160, "default": 1080},
            {"id": "r",      "type": "float","min": 0.0, "max": 1.0,  "default": 0.0},
            {"id": "g",      "type": "float","min": 0.0, "max": 1.0,  "default": 0.0},
            {"id": "b",      "type": "float","min": 0.0, "max": 1.0,  "default": 0.0},
            {"id": "a",      "type": "float","min": 0.0, "max": 1.0,  "default": 1.0},
        ]
    }
```

### EffectNode

```python
class EffectNode(NodeBase):
    """
    Wraps a loaded PluginBase effect.
    Parameters are dynamically added from the plugin's METADATA['parameters'].
    """
    METADATA = {
        "id": "core.effect",
        "name": "Effect",
        "description": "A visual effect processor node that applies a loaded plugin effect to an incoming video frame. Parameters are driven by the plugin's own manifest.",
        "inputs":  [{"name": "in",  "type": "frame"}],
        "outputs": [{"name": "out", "type": "frame"}],
        "params": []  # Dynamically extended from plugin METADATA['parameters']
    }

    def __init__(self, plugin_instance: 'EffectBase', **kwargs) -> None: ...
```

### OutputNode

```python
class OutputNode(NodeBase):
    """Terminal node — pushes processed frame to renderer."""
    METADATA = {
        "id": "core.output",
        "name": "Output",
        "description": "Terminal node that delivers the processed video frame to the active display output. Every graph must have exactly one OutputNode.",
        "inputs":  [{"name": "in",  "type": "frame"}],
        "outputs": [],
        "params": [
            {"id": "opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 1.0}
        ]
    }
```

### PassthroughNode

```python
class PassthroughNode(NodeBase):
    """Routes input to output unchanged — useful for signal routing and debugging."""
    METADATA = {
        "id": "core.passthrough",
        "name": "Passthrough",
        "description": "Routes an incoming frame to its output unchanged. Useful as a junction point in complex routing graphs or for inserting monitoring points.",
        "inputs":  [{"name": "in",  "type": "frame"}],
        "outputs": [{"name": "out", "type": "frame"}],
        "params": []
    }
```

### MixNode

```python
class MixNode(NodeBase):
    """Blends two frames by weight."""
    METADATA = {
        "id": "core.mix",
        "name": "Mix",
        "description": "Blends two incoming video frames together using a configurable mix weight. At 0.0 only the A input is visible; at 1.0 only B is visible; intermediate values produce a linear blend.",
        "inputs":  [{"name": "a", "type": "frame"}, {"name": "b", "type": "frame"}],
        "outputs": [{"name": "out", "type": "frame"}],
        "params": [
            {"id": "mix", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5}
        ]
    }
```

### GainNode

```python
class GainNode(NodeBase):
    """Multiplies pixel values by a scalar (brightness/contrast control)."""
    METADATA = {
        "id": "core.gain",
        "name": "Gain",
        "description": "Applies a brightness and contrast gain to the incoming frame by multiplying pixel values by the gain scalar. Values above 1.0 boost brightness; below 1.0 attenuate.",
        "inputs":  [{"name": "in",  "type": "frame"}],
        "outputs": [{"name": "out", "type": "frame"}],
        "params": [
            {"id": "gain", "type": "float", "min": 0.0, "max": 4.0, "default": 1.0}
        ]
    }
```

---

## Registration

```python
# vjlive3/nodes/__init__.py
from vjlive3.nodes.registry import NodeRegistry
from vjlive3.nodes.core import (
    SourceNode, EffectNode, OutputNode, PassthroughNode, MixNode, GainNode
)

def register_core_nodes(registry: NodeRegistry) -> None:
    """Register all built-in node types."""
    for cls in [SourceNode, EffectNode, OutputNode, PassthroughNode, MixNode, GainNode]:
        registry.register(cls)
```

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_source_node_metadata_valid` | SourceNode METADATA has all required fields |
| `test_source_node_process_returns_frame` | process() returns dict with 'out' key |
| `test_effect_node_calls_plugin` | EffectNode.process() invokes plugin.process() |
| `test_effect_node_plugin_error_handled` | plugin.process() raising → node quarantined |
| `test_output_node_stores_frame` | OutputNode stores 'in' for renderer to pick up |
| `test_passthrough_node_copies_input` | process(in=X) → {out: X} |
| `test_mix_node_at_zero` | mix=0.0 → output ≈ input A |
| `test_mix_node_at_one` | mix=1.0 → output ≈ input B |
| `test_gain_node_at_one` | gain=1.0 → output == input |
| `test_gain_node_at_zero` | gain=0.0 → output is all zeros |
| `test_register_core_nodes` | register_core_nodes → registry.count() == 6 |
| `test_all_descriptions_50_chars` | all METADATA descriptions ≥ 50 chars (Rail 3) |

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 12 tests pass
- [ ] All node descriptions ≥ 50 characters (Rail 3)
- [ ] No file > 750 lines
- [ ] No stubs
- [ ] BOARD.md P1-N2 marked ✅
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
