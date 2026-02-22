# Spec: P5-V01 — V-Shadertoy Extra

**File naming:** `docs/specs/phase5_v_effects/P5-V01_V-Shadertoy_Extra.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P5-V01 — V-Shadertoy Extra

**Phase:** Phase 5 / P5-V01
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

V-Shadertoy Extra is an advanced shader playground that provides access to Shadertoy-style GLSL shaders with additional VJLive3-specific features. It includes real-time shader compilation, uniform parameter controls, and integration with the audio-reactive system, making it a powerful tool for creating custom visual effects.

---

## What It Does NOT Do

- Does not provide shader editing or IDE features
- Does not include built-in shader library management
- Does not handle shader optimization or performance tuning
- Does not provide shader debugging tools

---

## Public Interface

```python
class VShadertoyExtra:
    def __init__(self) -> None: ...
    
    def load_shader(self, shader_code: str) -> bool: ...
    def get_shader_code(self) -> str: ...
    
    def set_uniform(self, name: str, value: Any) -> None: ...
    def get_uniform(self, name: str) -> Any: ...
    
    def set_audio_reactive(self, enabled: bool) -> None: ...
    def is_audio_reactive(self) -> bool: ...
    
    def process(self, input_texture: Texture, time: float) -> Texture: ...
    
    def get_available_uniforms(self) -> List[str]: ...
    def get_uniform_info(self, name: str) -> UniformInfo: ...
    
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `shader_code` | `str` | GLSL shader source code | Valid GLSL syntax |
| `name` | `str` | Uniform parameter name | Valid uniform name |
| `value` | `Any` | Uniform value | Valid for uniform type |
| `enabled` | `bool` | Audio-reactive mode | True/False |
| `input_texture` | `Texture` | Input texture | Valid texture |
| `time` | `float` | Current time in seconds | > 0 |

**Output:** `Texture` — Processed output texture

---

## Edge Cases and Error Handling

- What happens if shader compilation fails? → Keep old shader, log error
- What happens if uniform doesn't exist? → Ignore, log warning
- What happens if audio-reactive mode enabled but no audio? → Use default values
- What happens if input texture is invalid? → Return black texture
- What happens on cleanup? → Release shader resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `moderngl` — for shader compilation — fallback: raise ImportError
  - `numpy` — for uniform data — fallback: use basic types
- Internal modules this depends on:
  - `vjlive3.render.opengl_context`
  - `vjlive3.audio.audio_analyzer` (for audio-reactive mode)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_shader_loading` | Loads and compiles shaders correctly |
| `test_uniform_control` | Sets and gets uniform values |
| `test_audio_reactive` | Audio-reactive mode works |
| `test_shader_error` | Handles shader compilation errors |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-5] P5-V01: V-Shadertoy Extra shader playground` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 V-Shadertoy Extra module.*