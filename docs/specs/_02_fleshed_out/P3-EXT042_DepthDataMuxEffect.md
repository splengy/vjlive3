# DepthDataMuxEffect — Depth Data Multiplexer

**Task ID:** P3-EXT042  
**Module:** `DepthDataMuxEffect`  
**Phase:** Pass 2 Fleshing Out  
**Status:** Ready for Phase 3 Review  

---

## Overview

The [`DepthDataMuxEffect`](docs/specs/_02_fleshed_out/P3-EXT042_DepthDataMuxEffect.md:32) class is a depth data multiplexer that takes a single depth input and fans it out to N identical outputs. It starts with 3 outputs by default, and additional outputs can be added dynamically at runtime via `add_output()`. The effect performs zero processing — it simply copies the depth data from the source to all output buffers. This is a utility node for routing depth data to multiple consumers in the graph.

**What This Module Does**

- Accepts a single depth data source (via `set_depth_source`)
- Maintains multiple output buffers (`depth_out_1`, `depth_out_2`, ...) all containing identical copies of the latest depth frame
- Updates all outputs automatically each frame via `update_depth_data()`
- Allows dynamic expansion of outputs with `add_output()` (returns new output ID)
- Allows removal of outputs with `remove_output()` (removes last or specific output)
- Provides read access to any output via `get_depth_output(output_id)`
- Uses a trivial passthrough shader (samples `tex0` and outputs unchanged)
- Supports audio reactivity infrastructure (unused)

**What This Module Does NOT Do**

- Does not perform any depth processing, filtering, or transformation
- Does not combine multiple depth sources (only one source)
- Does not support different data per output (all outputs are identical)
- Does not provide any visual effects or rendering (it's a data router)
- Does not include audio reactivity (infrastructure present but unused)
- Does not manage OpenGL textures directly (operates on CPU-side numpy arrays)

---

## Detailed Behavior and Parameter Interactions

### Core Concept: Data Fan-Out

The effect is a pure data multiplexer. It receives depth data from a `depth_source` object (which must implement `get_filtered_depth_frame()` returning a numpy array). Each frame, it calls `update_depth_data()` to fetch the latest depth frame and copies the reference to all output buffers. The shader is a simple passthrough that would render whatever texture is bound to `tex0`, but the effect's primary purpose is to manage the CPU-side data distribution, not to render.

### Texture Unit Layout

The effect uses the standard texture layout:

| Unit | Name | Type | Purpose |
|------|------|------|---------|
| 0 | `tex0` | `sampler2D` | Input depth data (when rendered) |

The shader is a trivial passthrough:

```glsl
void main() {
    fragColor = texture(tex0, uv);
}
```

This means if the effect is rendered, it will output exactly the input texture. However, the effect's real utility is in the Python-managed output buffers, not the shader output.

### Output Management

The effect maintains a dictionary `self._outputs` mapping output IDs (`depth_out_1`, `depth_out_2`, ...) to depth frame data (numpy arrays). Initially, `num_outputs` outputs are created (default 3). The `depth_frame` is fetched from `depth_source` and then copied (by reference) to all outputs:

```python
def update_depth_data(self):
    if self.depth_source:
        self.depth_frame = self.depth_source.get_filtered_depth_frame()
        if self.depth_frame is not None:
            for key in self._outputs:
                self._outputs[key] = self.depth_frame
```

All outputs point to the same numpy array object (shallow copy). This is efficient but means if one output is modified externally, all will reflect the change. This is acceptable because depth data is typically read-only.

### Dynamic Output Expansion

- `add_output()`: Adds a new output with the next sequential number. Returns the new output ID (e.g., `depth_out_4`). The new output is immediately populated with the current `depth_frame` if available.
- `remove_output(output_id=None)`: Removes an output. If `output_id` is provided, that specific output is removed. If `None`, the highest-numbered output is removed. Will not reduce below 1 output.

### Parameter Space

The effect has **no parameters** (`self.parameters = {}`). It is a pure passthrough with no user controls.

### Audio Reactivity

The class has an `audio_reactor` attribute and `set_audio_analyzer()` method inherited from base, but does not use them. No audio reactivity.

---

## Public Interface

### Class: `DepthDataMuxEffect`

**Inheritance:** [`Effect`](docs/specs/_02_fleshed_out/P3-EXT042_DepthDataMuxEffect.md:32) (from `core.effects.shader_base`)

**Constructor:** `__init__(self, num_outputs=3)`

Initializes the effect with a specified number of outputs (default 3):

```python
self.depth_source = None
self.depth_frame = None
self._outputs = {}
self.parameters = {}  # No parameters

for i in range(1, num_outputs + 1):
    self._outputs[f'depth_out_{i}'] = None
```

**Properties:**

- `name = "depth_data_mux"`
- `fragment_shader = DEPTH_MUX_FRAGMENT` — trivial passthrough shader
- `effect_category` — Not explicitly set; likely `"depth"` or `"utility"`
- `effect_tags` — Not explicitly set; based on description: `["depth", "mux", "router", "utility"]`
- `_outputs` — Dictionary of output IDs to depth data (numpy arrays or None)
- `depth_frame` — The most recent depth frame (numpy array or None)

**Methods:**

- `set_depth_source(source)`: Set the depth source object. Must implement `get_filtered_depth_frame()` returning a numpy array of shape (H, W) with float32 values 0-1.
- `add_output() -> str`: Add a new output. Returns the new output ID (e.g., `depth_out_4`). The new output is immediately set to the current `depth_frame` if available.
- `remove_output(output_id=None)`: Remove an output. If `output_id` is given, remove that specific output. If `None`, remove the highest-numbered output. Will not remove the last remaining output (minimum 1).
- `num_outputs` (property): Returns the number of outputs currently available.
- `output_ids` (property): Returns a sorted list of output IDs (strings).
- `update_depth_data()`: Fetch the latest depth frame from `depth_source` and copy it to all outputs. Should be called from `apply_uniforms` (which does this automatically).
- `get_depth_output(output_id='depth_out_1')`: Return the depth data (numpy array or None) for the specified output ID.
- `apply_uniforms(time_val, resolution, audio_reactor=None, semantic_layer=None)`: Overrides base to call `update_depth_data()`. Also calls `super().apply_uniforms(...)` to set standard uniforms.

**Class Attributes:**

- `DEPTH_MUX_FRAGMENT` — The passthrough GLSL shader (lines 16-28 in legacy file).
- `BASE_VERTEX_SHADER` — Inherited from `Effect`.

---

## Inputs and Outputs

### Inputs

| Pin | Type | Description |
|-----|------|-------------|
| `tex0` | `sampler2D` | Input depth data (when the effect is rendered) |
| `time` | `float` | Shader time (unused) |
| `resolution` | `vec2` | Viewport resolution (unused) |
| `u_mix` | `float` | Blend factor (unused) |

The effect does not actually use any uniforms meaningfully; the shader just samples `tex0`.

### Outputs

The effect does **not** have multiple output pins in the traditional sense. Instead, it provides **data outputs** via the Python API:

| Output ID | Type | Description |
|-----------|------|-------------|
| `depth_out_1` | `numpy.ndarray` (H, W) float32 | First depth output (identical to source) |
| `depth_out_2` | `numpy.ndarray` (H, W) float32 | Second depth output (identical) |
| `depth_out_3` | `numpy.ndarray` (H, W) float32 | Third depth output (identical) |
| `depth_out_N` | `numpy.ndarray` (H, W) float32 | Additional outputs as added |

All outputs contain the same depth data (the latest frame from the source). The host can query any output using `get_depth_output(output_id)`.

---

## Edge Cases and Error Handling

### Edge Cases

1. **No depth source**: If `depth_source` is `None`, `update_depth_data()` does nothing. All outputs remain `None` or hold stale data. The host should set a valid source before expecting data.

2. **Depth source returns None**: If `depth_source.get_filtered_depth_frame()` returns `None`, the outputs are not updated (they keep previous values). This is safe.

3. **Depth frame shape changes**: If the depth source changes resolution between frames, the numpy array shape may change. All outputs will be updated to the new array, but any consumer expecting a fixed shape must handle this. The effect itself does not enforce consistency.

4. **Zero outputs**: The constructor ensures at least 1 output (default 3). `remove_output()` prevents reducing below 1. So there is always at least one output.

5. **Adding outputs dynamically**: `add_output()` can be called at any time, even before a depth source is set. The new output will be populated on the next `update_depth_data()` call (or immediately if `depth_frame` already exists).

6. **Removing non-existent output**: `remove_output(output_id)` will silently do nothing if the ID doesn't exist. This is safe.

7. **Shader rendering**: If the effect is rendered (e.g., as part of an `EffectChain`), it will output the input texture `tex0` unchanged. This is harmless but pointless; the effect is not meant for visual rendering.

8. **Audio reactivity**: Not implemented; no effect.

### Error Handling

- **No parameter validation needed**: There are no parameters.
- **Depth source interface**: The code assumes `depth_source.get_filtered_depth_frame()` exists and returns a numpy array or None. If it raises an exception, it will propagate. The host should ensure the source is valid.
- **No OpenGL operations**: The effect does not create textures or perform GL calls, so no GL errors.

---

## Mathematical Formulations

None. This effect performs no mathematical transformations. It is a pure data copy operation.

---

## Performance Characteristics

### Computational Complexity

- **Base cost**: Minimal. The shader is a single texture sample and output. The Python side does:
  - One call to `depth_source.get_filtered_depth_frame()` per frame
  - A loop over `self._outputs` to assign references (O(N) where N = number of outputs, typically small)
- **No GPU load**: The shader is trivial; if rendered, it's the cheapest possible.
- **CPU overhead**: Negligible. The main cost is the depth source fetching data (which would happen anyway).

### Memory Usage

- **Python objects**: A dictionary of N references to the same numpy array. The array itself is stored once (shared). Overhead is O(N) for dictionary entries (small).
- **No extra GPU memory**: The effect does not allocate textures or framebuffers.

### Optimization Notes

- The effect is essentially free. The only consideration is that if many outputs are added (e.g., 100), the dictionary grows linearly, but that's still tiny.
- The design uses shallow copies (references) to avoid duplicating large numpy arrays. This is efficient but means consumers should not modify the data.

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

### Unit Tests (Python)

1. **Constructor defaults**: Verify `num_outputs=3` creates exactly 3 outputs with IDs `depth_out_1`, `depth_out_2`, `depth_out_3` and all values `None`.
2. **Custom num_outputs**: Verify `DepthDataMuxEffect(5)` creates 5 outputs.
3. **Set depth source**: Test `set_depth_source()` sets `depth_source`.
4. **Update depth data with source**: Mock a depth source that returns a known numpy array. Call `update_depth_data()` and verify all outputs contain that array (same object reference).
5. **Update depth data without source**: Verify `update_depth_data()` does nothing and outputs remain unchanged when `depth_source` is `None`.
6. **Update depth data with None return**: Mock source returning `None`; verify outputs are not updated.
7. **Add output**: Call `add_output()` and verify a new output ID appears in `output_ids` and `num_outputs` increases. Verify the new output contains current `depth_frame` (if set).
8. **Add multiple outputs**: Call `add_output()` multiple times and verify sequential numbering.
9. **Remove last output**: Call `remove_output()` with no args and verify the highest-numbered output is removed and count decreases.
10. **Remove specific output**: Call `remove_output('depth_out_2')` and verify that output is removed.
11. **Remove non-existent**: Call `remove_output('nonexistent')` and verify no error and no change.
12. **Prevent removing last output**: With 1 output, call `remove_output()` and verify still 1 output.
13. **Get depth output**: Call `get_depth_output('depth_out_1')` and verify returns the correct array (or None).
14. **Get non-existent output**: Call `get_depth_output('nonexistent')` and verify returns `None`.
15. **Output IDs order**: Verify `output_ids` returns sorted list (numerical order, not string lexicographic? Actually sorted strings: `['depth_out_1', 'depth_out_10', 'depth_out_2']` would be lexicographic. The code uses `sorted(self._outputs.keys())` which gives lexicographic order. This may be unexpected if there are >9 outputs. Should verify behavior. [NEEDS RESEARCH: is lexicographic order intended?]
16. **Apply uniforms**: Verify `apply_uniforms` calls `update_depth_data` and calls `super().apply_uniforms`.
17. **Parameters empty**: Verify `parameters` is an empty dict.
18. **Shader code**: Verify `fragment_shader` equals the expected passthrough string.

### Integration Tests

19. **Full workflow**: Set a mock depth source, call `apply_uniforms`, then query all outputs and verify they all reference the same numpy array object (shallow copy).
20. **Dynamic expansion**: Start with 3 outputs, add 2 more, verify 5 outputs, all get updated when source changes.
21. **Dynamic removal**: Add outputs, then remove some, verify remaining outputs still get updates.
22. **Multiple frames**: Simulate multiple frames with different depth arrays, verify all outputs are updated each frame and always match the current source.

### Performance Tests

23. **Memory overhead**: Create with 100 outputs and verify memory usage is negligible (just dictionary overhead).
24. **Update speed**: Time `update_depth_data()` with many outputs; should be microseconds.

---

## Definition of Done

- [x] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass (80% coverage minimum)
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-EXT042: DepthDataMuxEffect` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

This spec is derived from the following legacy implementations:

- [`plugins/vdepth/depth_data_mux.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdepth/depth_data_mux.py:1) (VJlive Original) — Full implementation with shader code (lines 16-28) and class (lines 32-96).
- [`plugins/vdepth/__init__.py`](home/happy/Desktop/claude projects/VJlive-2/plugins/vdepth/__init__.py:1) — Registration of the effect in the depth plugin module.

The legacy code validates the simple passthrough architecture and dynamic output management. The effect is a lightweight utility for routing depth data to multiple consumers without duplication overhead.

---

## Open Questions / [NEEDS RESEARCH]

- **Output ID ordering**: The `output_ids` property returns `sorted(self._outputs.keys())`, which sorts strings lexicographically. With outputs `depth_out_1` through `depth_out_10`, lexicographic order yields: `['depth_out_1', 'depth_out_10', 'depth_out_2', 'depth_out_3', ...]`. This is likely not the intended numerical order. Should the sorting be numerical? The code could parse the number and sort by int. However, the effect may not rely on ordering; consumers should request specific IDs. [NEEDS RESEARCH — decide if sorting should be numerical]
- **Shallow copy risk**: The `add_output()` method sets `self._outputs[key] = self.depth_frame` (reference). If a consumer modifies the returned numpy array, it will affect all outputs. Should we return a copy? The current design prioritizes performance. The spec should document that depth data is read-only and should not be modified by consumers. [NEEDS RESEARCH — confirm intended mutability]
- **Thread safety**: The effect is not thread-safe. If `update_depth_data()` is called concurrently with `get_depth_output()`, there could be race conditions. In a typical single-threaded effect chain, this is fine. [NEEDS RESEARCH — is multithreading expected?]
- **Audio reactivity**: The infrastructure exists but is unused. Should audio modulate anything? Probably not; this is a data router. [NEEDS RESEARCH — confirm no audio needed]
- **Shader utility**: The shader is a passthrough. Is there any scenario where this effect would be rendered? Possibly if the host wants to visualize the depth data directly, but then a dedicated depth visualization effect would be used. The shader seems vestigial. Could it be removed? The base `Effect` class expects a shader. So it's needed for compatibility. [NEEDS RESEARCH — confirm shader is required by base class]
- **Depth source interface**: The effect expects `depth_source.get_filtered_depth_frame()`. What is the exact return type? Likely `numpy.ndarray` of shape (height, width) with `dtype=np.float32` or `np.uint8`? The code does not check or convert. Should we enforce a specific dtype? [NEEDS RESEARCH — define expected interface]
- **Missing `u_mix`**: The shader includes `uniform float u_mix;` but does not use it. This is likely inherited from base class conventions. Should it be removed? Probably keep for consistency. [NEEDS RESEARCH]

---

*— desktop-roo, 2026-03-03*