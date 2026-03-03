# Spec: P1-R3 — WGSL Shader Hot-Reload

**Phase:** Phase 1 / P1-R3
**Assigned To:** TBD
**Spec Written By:** Antigravity (Manager Agent) — revised 2026-03-03
**Date:** 2026-03-03
**Source:** `vjlive/core/effects/shader_base.py` → `Effect.reload_fragment()` (lines 596–612), `ShaderProgram._compile()` (lines 388–428)

---

## What This Module Does

Provides runtime WGSL shader compilation and hot-reload for VJLive3 effects. An effect's fragment shader can be replaced at runtime — without restarting the render loop or dropping frames — by calling `reload_shader()`.

Three responsibilities:
1. **`ShaderCache`** — Compile-once, reuse-many. Caches compiled `RenderPipeline` objects by content hash. Cache hit avoids GPU recompile cost.
2. **`reload_shader(effect, wgsl_source)`** — Swap the pipeline on a live `Effect` instance. Old pipeline is deleted after the new one is confirmed valid.
3. **`watch_shader_file(path, effect)`** — Optional filesystem watcher. Polls `path` for changes; calls `reload_shader` on modification. Useful for development.

> **Milkdrop note:** Milkdrop preset support is explicitly NOT in scope here. Milkdrop is a standalone renderer. If Milkdrop integration is ever added to VJLive3, it will be a subprocess-to-texture effect (`P3-ML*`), not a shader compilation concern.

---

## What This Module Does NOT Do

- Does NOT compile GLSL (all shaders in VJLive3 are WGSL)
- Does NOT integrate Milkdrop or translate Milkdrop presets
- Does NOT manage render targets or effect chains (P1-R2)
- Does NOT provide the base WGSL shader strings (P1-R6)
- Does NOT block the render thread during reload — old pipeline stays active until new one is proven valid

---

## Public Interface

```python
# src/vjlive3/render/hot_reload.py
import hashlib
from typing import Optional
from pathlib import Path

class ShaderCache:
    """Compile-once shader cache keyed by WGSL content hash."""

    def get_or_compile(
        self,
        wgsl_source: str,
        name: str = "unnamed",
    ) -> "RenderPipeline":  # from P1-R2
        """Return cached pipeline for wgsl_source, or compile and cache it.

        Raises:
            RuntimeError: If WGSL compilation fails.
        """

    def invalidate(self, wgsl_source: str) -> None:
        """Remove a cached entry by source string. No-op if not cached."""

    def clear(self) -> None:
        """Flush entire cache. All pipelines deleted."""

    @property
    def size(self) -> int:
        """Number of cached pipelines."""


def reload_shader(effect: "Effect", wgsl_source: str) -> bool:
    """Hot-swap the fragment shader on a live Effect.

    Compiles new pipeline. On success, deletes old pipeline and installs new.
    On failure, logs ERROR and leaves old pipeline intact.

    Returns:
        True if reload succeeded, False if compilation failed.
    """


def watch_shader_file(
    path: str | Path,
    effect: "Effect",
    poll_interval: float = 0.5,
) -> "ShaderWatcher":
    """Start a background watcher that calls reload_shader on file changes.

    Returns a ShaderWatcher with .stop() method.
    """


class ShaderWatcher:
    def stop(self) -> None:
        """Stop the background watcher thread."""
    def is_running(self) -> bool: ...
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `wgsl_source` | `str` | Valid WGSL fragment shader source |
| `effect` | `Effect` | Live effect instance (from P1-R2) |
| `path` | `str \| Path` | Filesystem path to `.wgsl` file |
| `poll_interval` | `float` | File-check interval in seconds. Default 0.5s. |
| **returns (reload_shader)** | `bool` | `True` = success, `False` = compile error |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|--------------------|
| Invalid WGSL | Logs `ERROR` with compile message; old pipeline stays active |
| Reload during active render | Lock acquisition; swap happens between frames |
| File deleted mid-watch | Logs `WARNING`; watcher continues polling |
| `clear()` with active effects | Pipelines deleted from cache; live effects retain their own reference |
| `invalidate()` on missing key | Silent no-op |

---

## Dependencies

- `vjlive3.render.pipeline` (P1-R2) — `RenderPipeline`, `Effect`
- `threading` — background watcher
- `hashlib` — cache keying
- `pathlib` — file watching
- `logging` — error reporting

---

## File Layout

```
src/vjlive3/render/
    hot_reload.py    — ShaderCache, reload_shader, watch_shader_file, ShaderWatcher  (~150 lines)
```

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_cache_compiles_once` | `test_hot_reload.py` | Same source → same pipeline object returned |
| `test_cache_different_source` | `test_hot_reload.py` | Different source → different pipeline compiled |
| `test_cache_invalidate` | `test_hot_reload.py` | `invalidate()` removes entry; next call recompiles |
| `test_cache_clear` | `test_hot_reload.py` | `clear()` empties cache, size == 0 |
| `test_reload_success` | `test_hot_reload.py` | Valid WGSL swaps pipeline, returns `True` |
| `test_reload_bad_wgsl` | `test_hot_reload.py` | Invalid WGSL returns `False`, old pipeline intact |
| `test_watch_detects_change` | `test_hot_reload.py` | File write triggers `reload_shader` within 1s |
| `test_watcher_stop` | `test_hot_reload.py` | `stop()` terminates background thread |

**Minimum coverage:** 80%.

> Note: `test_watch_detects_change` writes a temp `.wgsl` file. No GPU context required if `Effect` is mocked.

---

## Definition of Done

- [ ] Spec reviewed and approved
- [ ] All 8 tests pass
- [ ] `hot_reload.py` under 150 lines
- [ ] Zero stubs — dead-end paths raise `RuntimeError` per ADR-003
- [ ] Reload is non-blocking (old pipeline serves frames during compile)
- [ ] Git commit: `[Phase-1] P1-R3: WGSL shader hot-reload (cache, live swap, file watcher)`
- [ ] BOARD.md P1-R3 marked ✅
- [ ] Lock released from LOCKS.md

---

## LEGACY CODE REFERENCES

**`vjlive/core/effects/shader_base.py` — `Effect.reload_fragment()` (lines 596–612):**

```python
def reload_fragment(self, fragment_source: str):
    try:
        if hasattr(self, 'shader') and self.shader:
            self.shader.delete()
    except Exception:
        pass
    self.shader = ShaderProgram(BASE_VERTEX_SHADER, fragment_source, self.name)
```

This deletes the old shader before confirming the new one compiles — that's the bug to fix. VJLive3 must compile first, then swap.
