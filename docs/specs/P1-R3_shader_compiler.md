# Spec: P1-R3 — Shader Compilation System

**File naming:** `docs/specs/P1-R3_shader_compiler.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-R3 — Shader Compilation System

**Phase:** Phase 1 / P1-R3
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The shader compilation system provides a unified interface for compiling and managing GLSL shaders and Milkdrop presets. It handles shader preprocessing, error reporting, caching, and hot-reloading, enabling real-time shader development and deployment in the VJLive3 rendering pipeline.

---

## What It Does NOT Do

- Does not provide shader editing or IDE features
- Does not handle shader optimization or performance tuning
- Does not manage shader uniforms or parameters
- Does not provide shader debugging tools

---

## Public Interface

```python
class ShaderCompiler:
    def __init__(self, shader_dir: str = "shaders") -> None: ...
    
    def compile_glsl(self, source: str, shader_type: str) -> ShaderProgram: ...
    def compile_milkdrop(self, preset: str) -> ShaderProgram: ...
    
    def get_shader(self, shader_name: str) -> Optional[ShaderProgram]: ...
    def reload_shader(self, shader_name: str) -> bool: ...
    
    def list_shaders(self) -> List[str]: ...
    def get_shader_info(self, shader_name: str) -> ShaderInfo: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `source` | `str` | GLSL source code | Valid GLSL syntax |
| `shader_type` | `str` | Shader type (vertex, fragment, compute) | 'vertex', 'fragment', 'compute' |
| `preset` | `str` | Milkdrop preset text | Valid Milkdrop format |
| `shader_name` | `str` | Shader identifier | Valid filename/path |

**Output:** `ShaderProgram` — Compiled shader program with error info

---

## Edge Cases and Error Handling

- What happens if shader compilation fails? → Returns error info with line numbers
- What happens if shader file is missing? → Returns None with error message
- What happens if shader is modified? → Hot-reloads automatically
- What happens on cleanup? → Releases all shader resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `moderngl` — for OpenGL shader compilation — fallback: raise ImportError
  - `watchdog` — for hot-reloading — fallback: manual reload only
- Internal modules this depends on:
  - `vjlive3.render.opengl_context`
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_glsl_compilation` | Compiles valid GLSL shaders |
| `test_milkdrop_compilation` | Compiles Milkdrop presets |
| `test_error_handling` | Reports compilation errors correctly |
| `test_hot_reloading` | Reloads modified shaders |
| `test_shader_caching` | Caches compiled shaders efficiently |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-R3: Shader compilation system` message
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

*Specification based on VJlive-2 shader compilation system.*