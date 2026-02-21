# Spec: P1-R3 — Shader Compilation System (GLSL + Milkdrop)

**Phase:** Phase 1 / P1-R3
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `VJlive-2/shaders/`, `VJlive-2/glfw_shader_test.py`
**Depends On:** P1-R1 (OpenGLContext / ModernGL)

---

## What This Module Does

Provides a `ShaderCompiler` that compiles GLSL vertex/fragment shader source code into
ModernGL `Program` objects, caches them by source hash, and provides clear error messages
on compilation failure. Also provides a `MilkdropShader` preprocessor that translates the
subset of Milkdrop GLSL extensions used by legacy presets into standard GLSL 3.30 core
(uniform names, `sampler2D` declarations, `gl_FragCoord` equivalents). Compiled programs
are ref-counted so they are only destroyed when all consumers release them.

---

## What It Does NOT Do

- Does NOT manage framebuffers or textures (P1-R4)
- Does NOT run the render loop (P1-R5)
- Does NOT compile SPIR-V or Vulkan shaders
- Does NOT auto-watch shader files for changes (hot-reload is P1-P3 scope)

---

## Public Interface

```python
# vjlive3/render/shader.py

import moderngl
from pathlib import Path
from typing import Optional, Dict, Tuple


class ShaderError(Exception):
    """Raised when shader compilation or linking fails."""


class ShaderProgram:
    """
    Ref-counted wrapper around a moderngl.Program.

    Obtained via ShaderCompiler.compile() — do not construct directly.
    """

    @property
    def mgl(self) -> moderngl.Program:
        """Access the underlying ModernGL program."""

    def __enter__(self) -> 'ShaderProgram': ...
    def __exit__(self, *args) -> None:
        """Release reference. Program destroyed when count = 0."""

    def set_uniform(self, name: str, value) -> None:
        """
        Set a uniform value. No-op (with DEBUG log) if name not in program.
        Supports: float, int, tuple[float], numpy arrays for matrices.
        """

    def use(self) -> None:
        """Bind this program (calls mgl.use())."""


class ShaderCompiler:
    """
    GLSL shader compiler with source-hash cache.

    One instance per OpenGL context. Not thread-safe — must be used on
    the thread that owns the OpenGL context.
    """

    def __init__(self, ctx: moderngl.Context) -> None:
        """
        Args:
            ctx: Active ModernGL context (from P1-R1 OpenGLContext.ctx).
        """

    def compile(
        self,
        vertex_src: str,
        fragment_src: str,
    ) -> ShaderProgram:
        """
        Compile and link a vertex + fragment shader pair.

        Cache key: SHA-256 of (vertex_src + fragment_src).
        Returns cached ShaderProgram if source unchanged.

        Raises:
            ShaderError: With GLSL compile/link error log if compilation fails.
        """

    def compile_from_files(
        self,
        vertex_path: Path,
        fragment_path: Path,
    ) -> ShaderProgram:
        """
        Read shader files and compile them.

        Raises:
            FileNotFoundError: If either file not found.
            ShaderError: On compilation failure.
        """

    def clear_cache(self) -> None:
        """Release all cached programs (calls cleanup on each)."""

    @property
    def cache_size(self) -> int:
        """Number of currently cached programs."""


class MilkdropPreprocessor:
    """
    Translates Milkdrop GLSL dialect → standard GLSL 3.30 core.

    Handles:
      - `uniform sampler2D tex_main;` → `uniform sampler2D tex_main;` (passthrough)
      - `uniform float time;` → `uniform float time;` (passthrough)
      - `q1..q32` compat vars → float uniforms
      - `#define PI 3.14159...` → passthrough
      - `bass`, `mid`, `treb` → float uniforms (injected into preamble)
      - `shader_body {}` wrapper → `void main() {}`

    Returns transformed GLSL string ready to pass to ShaderCompiler.
    """

    PREAMBLE: str  # Standard version + precision header

    def process(self, milkdrop_src: str) -> str:
        """
        Apply all transformations to Milkdrop GLSL source.

        Returns valid GLSL 3.30 fragment shader source.
        Does NOT raise — on unrecognised syntax, passes through untouched.
        """

    def get_required_uniforms(self, milkdrop_src: str) -> Dict[str, str]:
        """
        Return {uniform_name: glsl_type} dict of uniforms referenced in the source.

        Used by the render engine to know which uniforms to set per-frame.
        """
```

---

## GLSL Standard Preamble (injected by MilkdropPreprocessor)

```glsl
#version 330 core
precision highp float;

uniform float time;
uniform float bass;
uniform float mid;
uniform float treb;
uniform float beat;
uniform float beat_phase;
uniform vec2  resolution;
uniform sampler2D tex_main;

out vec4 fragColor;
```

---

## Inputs and Outputs

| Item | Type | Description |
|------|------|-------------|
| `vertex_src` | `str` | GLSL vertex source |
| `fragment_src` | `str` | GLSL fragment source |
| `milkdrop_src` | `str` | Raw Milkdrop shader body |
| **Output** `compile()` | `ShaderProgram` | Compiled, cached program |
| **Output** `process()` | `str` | Valid GLSL 3.30 fragment source |
| **Output** `get_required_uniforms()` | `Dict[str, str]` | {name: type} |

---

## Edge Cases and Error Handling

- **Compilation error:** Raise `ShaderError(f"Fragment shader error:\n{error_log}")` with full GLSL error log.
- **Linker error:** Raise `ShaderError(f"Shader link error:\n{error_log}")`.
- **Cache hit:** Return existing `ShaderProgram` without recompiling.
- **set_uniform on missing name:** Log DEBUG, silently ignore (not all presets use all uniforms).
- **`compile_from_files` file not found:** Raise `FileNotFoundError` before attempting compile.
- **Milkdrop syntax errors:** Pass through untransformed — ShaderCompiler will catch GLSL errors.

---

## Dependencies

### External
- `moderngl >= 5.0` (from P1-R1)

### Internal
- `vjlive3.render.context.OpenGLContext` (P1-R1)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_compile_passthrough_vert_frag` | Minimal vert+frag compiles without error |
| `test_compile_cache_hit` | Compiling same source twice returns same program |
| `test_compile_syntax_error_raises` | Bad GLSL → ShaderError with error log |
| `test_compile_from_files_not_found` | Missing file → FileNotFoundError |
| `test_set_uniform_float` | set_uniform('time', 1.0) sets value without crash |
| `test_set_uniform_missing_noop` | set_uniform on missing name → no exception |
| `test_clear_cache` | clear_cache → cache_size == 0 |
| `test_milkdrop_preamble_injected` | process() output starts with #version 330 |
| `test_milkdrop_shader_body_wrap` | shader_body{} → void main() {} |
| `test_milkdrop_bass_uniform` | 'bass' in get_required_uniforms output |
| `test_milkdrop_compile_roundtrip` | milkdrop src → preprocessor → compiler → ShaderProgram |

Tests run in headless OpenGL context (NullContext or mesa software renderer in CI).

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 11 tests pass (headless CI compatible)
- [ ] File < 750 lines (split `_cache.py` if needed)
- [ ] No stubs
- [ ] BOARD.md P1-R3 marked ✅
- [ ] Lock released in LOCKS.md
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Command

```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_shader_compiler.py -v

# Smoke test (requires display / mesa)
PYTHONPATH=src python3 -c "
from vjlive3.render.context import OpenGLContext
from vjlive3.render.shader import ShaderCompiler

VERT = '''
#version 330 core
in vec2 in_position;
void main() { gl_Position = vec4(in_position, 0.0, 1.0); }
'''
FRAG = '''
#version 330 core
out vec4 fragColor;
void main() { fragColor = vec4(1.0, 0.0, 0.5, 1.0); }
'''

with OpenGLContext(640, 480, debug=True) as ctx:
    compiler = ShaderCompiler(ctx.ctx)
    prog = compiler.compile(VERT, FRAG)
    prog.set_uniform('time', 1.5)
    print('Compiled OK. Cache size:', compiler.cache_size)
"
```
