# VJLive3 — Plugin API Reference

> Module: `vjlive3.plugins.api` | 249 plugins in `src/vjlive3/plugins/` | Tests: 1,091 ✅

---

## Plugin Base Classes

### `EffectPlugin`

All VJLive3 effect plugins extend `EffectPlugin` from `vjlive3.plugins.api`.

```python
from vjlive3.plugins.api import EffectPlugin, PluginContext

class MyPlugin(EffectPlugin):
    def get_metadata(self) -> dict: ...
    def initialize(self, context: PluginContext) -> bool: ...
    def process_frame(self, input_texture: int, params: dict, context: PluginContext) -> int: ...
    def cleanup(self) -> None: ...
```

### Lifecycle

```
initialize(ctx) → True
    ↓   (per frame, ≤ 16.67ms)
process_frame(tex, params, ctx) → output_texture
    ↓
cleanup()
```

### `PluginContext`

Available fields inside `process_frame`:

| Field | Type | Description |
|-------|------|-------------|
| `width` | `int` | Frame width (px) |
| `height` | `int` | Frame height (px) |
| `time` | `float` | Engine clock (seconds) |
| `inputs` | `dict` | `"audio_data"` → `{bass, mid, treble, beat}` |
| `outputs` | `dict` | Write `"video_out"` here |
| `agent_state` | `dict` | Populated by `AgentBridge.step()` |

---

## Metadata Schema

`get_metadata()` must return a dict with these keys:

```python
{
    "name": str,          # Human-readable name
    "description": str,   # One-line description
    "version": str,       # Semver "1.0.0"
    "plugin_type": str,   # "effect" | "generator" | "audio"
    "category": str,      # "vfx" | "visualizer" | "audio" | ...
    "tags": List[str],    # Searchable tags
    "priority": int,      # 1 = normal, 0 = low, 2 = high
    "inputs": List[str],  # ["video_in"] or []
    "outputs": List[str], # ["video_out"]
    "parameters": [
        {
            "name": str,
            "type": "float",    # All VJLive3 params are float 0–10
            "default": float,
            "min": float,
            "max": float,
        }
    ]
}
```

---

## Standard Parameter Convention

All plugin parameters use a **0–10 scale** (not 0–1 or raw physical units).  
Map to shader uniforms using the `_map()` helper:

```python
def _map(val, lo, hi):
    return lo + (max(0., min(10., float(val))) / 10.) * (hi - lo)
```

Special parameter `mix` (default 8.0) controls output blend: 0 = input passthrough, 10 = full effect.

---

## GL Pattern

Every plugin follows the same GLSL FSQ pattern:

```python
VERTEX_SHADER = """
#version 330 core
const vec2 verts[4] = vec2[4](vec2(-1,-1), vec2(1,-1), vec2(-1,1), vec2(1,1));
out vec2 uv;
void main() { gl_Position = vec4(verts[gl_VertexID], 0.0, 1.0); uv = verts[gl_VertexID]*0.5+0.5; }
"""
```

The trail FBO (`trail_fbo` + `trail_tex`) stores the previous frame for temporal effects.

---

## Reading Agent State in Plugins

Plugins can modulate their behavior using the agent system:

```python
def process_frame(self, input_texture, params, context):
    state = getattr(context, "agent_state", {})
    positions = state.get("screen_positions", [])
    influences = state.get("param_influences")  # ndarray (N, 8)

    if positions:
        # e.g. modulate intensity based on first agent's X position
        ax, ay = positions[0]
        params = dict(params)
        params["intensity"] = ax * 10.0

    # ... rest of render
```

---

## Plugin Categories by Phase

| Phase | Count | Category |
|-------|-------|----------|
| P4-AU | 7 | Audio Reactive |
| P5-DM | 35 | Datamosh |
| P5-MO/VE | 2 | Modulate / Analog |
| P6-QC | 9 | VFX / AI |
| P6-GE | 14 | Generators |
| P6-P3 | 4 | Particles |
| P7-VE | 82 | Visual FX (all types) |
| P7-VE81-82 | 2 | Audio Visualizers |
| **Total** | **249** | |

---

## Mock Mode (Headless / CI)

If `OpenGL` is unavailable, plugins automatically enter **mock mode**:
- `initialize()` returns `True` immediately
- `process_frame()` returns `input_texture` unchanged
- `cleanup()` is a no-op

No special config is needed — this is detected at import time via `HAS_GL`.

---

## Writing a New Plugin

1. Copy any existing plugin as a template
2. Update `METADATA`, `FRAGMENT_SHADER`, `_PARAM_NAMES`, `_PARAM_DEFAULTS`
3. Rename the class (e.g. `class MyEffectPlugin(EffectPlugin)`)
4. Add `tests/plugins/test_my_effect.py` with ≥ 7 tests (see existing test files)
5. Register in `BOARD.md` under the appropriate phase

Minimum test checklist:
- `test_plugin_metadata_valid`
- `test_initialize_returns_true`
- `test_process_frame_zero_input`
- `test_process_frame_valid_input`
- `test_process_frame_all_params`
- `test_cleanup_no_error`
- `test_context_output_set`
