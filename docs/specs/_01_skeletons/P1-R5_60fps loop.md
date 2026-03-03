# Spec: P1-R5 — 60 FPS Render Engine (Main Loop)

**Phase:** Phase 1 / P1-R5
**Assigned To:** TBD
**Spec Written By:** Antigravity (Manager Agent) — 2026-03-03
**Date:** 2026-03-03
**Source:**
- `vjlive/core/app/app.py` → `VJLiveApp.run()` (lines 2682–2876) — **the real working render loop**
- `vjlive/core/app/app.py` → `VJLiveApp.render_frame()` (lines 2363–2571) — per-frame render pass
- `vjlive/core/app/app.py` → `VJLiveApp.update_fps()` (lines 2344–2360) — FPS tracking
- `vjlive/core/frame_budget.py` → `FrameBudgetAllocator` (lines 1–120) — per-effect budget tracking

---

## What This Module Does

Implements VJLive3's main 60 FPS render loop. It is the heartbeat of the application: it drives the window, polls input, times each frame, calls the effect chain, and sleeps precisely enough to hit the target frame rate.

Three responsibilities:

1. **`RenderEngine`** — The main loop class. Holds target FPS, runs `while not closed`, drives `poll_events → render_frame → swap_buffers → sleep`.
2. **`FrameProfiler`** — Lightweight per-named-stage timing using `time.perf_counter()`. Records `'graph'`, `'effects'`, `'screen'`, `'total'` per frame. Emits warnings when any stage exceeds 5 ms or total exceeds 16.67 ms.
3. **`FrameBudgetAllocator`** — Ported verbatim from legacy. Registers per-effect CPU budgets (ms). After each effect, records actual duration and decides whether to skip or reduce LOD scale next frame. Max 2 consecutive skips.

> **Note on PRIME_DIRECTIVE Rule 9 (60fps is sacred):** FPS must be verified at every phase completion via the smoke test command in this spec. Non-negotiable.

---

## What This Module Does NOT Do

- Does NOT use OpenGL or GLFW directly. All window calls go through `RenderContext` (P1-R1).
- Does NOT compile shaders (P1-R3)
- Does NOT manage render targets (P1-R2)
- Does NOT drive audio analysis (P1-A1) — but accepts `audio_reactor` and passes it to `EffectChain`
- Does NOT manage plugins or node graphs — those feed into the EffectChain externally

---

## Public Interface

```python
# src/vjlive3/render/engine.py
import time
from typing import Callable, Optional

class FrameProfiler:
    """Per-frame stage timing. Named stages via context manager."""

    def time(self, stage: str) -> "FrameProfilerContext":
        """Context manager: times the block and records to stage."""

    def record(self, stage: str, duration_ms: float) -> None:
        """Manually record a duration for a stage."""

    def tick(self) -> None:
        """Advance frame counter. Call once per frame after all stages."""

    def get_metrics(self) -> dict:
        """Return {stage: {'last_ms': float, 'avg_ms': float}} for all stages."""

    @property
    def frame_count(self) -> int: ...


class FrameBudgetAllocator:
    """
    Adaptive skip / LOD controller for CPU-bound effects.
    Ported from vjlive/core/frame_budget.py (120 lines, fully functional).
    """

    def __init__(self, target_fps: int = 60) -> None: ...

    def register(self, name: str, budget_ms: float = 4.0) -> None:
        """Register an effect with its per-frame time budget."""

    def unregister(self, name: str) -> None: ...

    def should_skip(self, name: str) -> bool:
        """True if effect overran budget last frame. Never skips >2 frames in a row."""

    def get_lod_scale(self, name: str) -> float:
        """Current downscale factor for the effect (0.1–1.0)."""

    def record_duration(self, name: str, duration_ms: float) -> None:
        """Record actual time taken. Updates skip flag and LOD scale."""

    def get_status(self) -> dict:
        """Return full budget status dict for debug overlay."""


class RenderEngine:
    """Main 60 FPS render loop. Drives window, effects, and timing."""

    METADATA: dict  # required — PRIME_DIRECTIVE Rule 2

    def __init__(
        self,
        context: "RenderContext",           # P1-R1
        effect_chain: "EffectChain",         # P1-R2
        target_fps: float = 60.0,
        audio_reactor: Optional[object] = None,
    ) -> None:
        """
        Args:
            context:        Active RenderContext (window + wgpu device).
            effect_chain:   Configured EffectChain.
            target_fps:     Target frame rate. Default 60.
            audio_reactor:  Optional audio analysis object (duck-typed).
        """

    def run(self) -> None:
        """Enter the main render loop. Blocks until window close or stop() called."""

    def stop(self) -> None:
        """Request clean loop exit. Safe to call from any thread."""

    def set_frame_callback(self, cb: Callable[["RenderEngine"], None]) -> None:
        """
        Register a per-frame callback invoked before EffectChain.render().
        Used by the node graph, MIDI, OSC, agent bridge, etc.
        Callback receives the RenderEngine instance for access to frame_time, fps, etc.
        """

    def set_input_texture_callback(
        self, cb: Callable[[], Optional[object]]
    ) -> None:
        """
        Register a callback that returns the current input texture view (or None).
        Called each frame. If None, EffectChain receives a black texture.
        """

    # Read-only runtime properties
    @property
    def frame_time(self) -> float:
        """Delta time of the previous frame in seconds. Clamped to 0.1s max."""

    @property
    def fps(self) -> float:
        """Measured FPS, averaged over the last 1 second."""

    @property
    def total_frames(self) -> int:
        """Total frames rendered since run() was called."""

    @property
    def profiler(self) -> FrameProfiler: ...
    @property
    def budget(self) -> FrameBudgetAllocator: ...
```

---

## Loop Structure (Pseudocode)

Derived from `vjlive/core/app/app.py` lines 2799–2874:

```python
target_frame_time = 1.0 / target_fps   # 16.67ms for 60fps
last_loop_time = time.time()

while not context.should_close() and running:
    frame_start = time.time()

    # 1. Delta time (clamped — prevents jumps after hangs)
    frame_time = min(frame_start - last_loop_time, 0.1)
    last_loop_time = frame_start

    # 2. Window events
    context.poll_events()

    # 3. Per-frame callbacks (MIDI sync, agent bridge, node graph, etc.)
    for cb in frame_callbacks:
        cb(self)

    # 4. Get input texture
    input_tex = input_texture_callback() or black_texture

    # 5. Render effect chain
    with profiler.time('effects'):
        output_tex = effect_chain.render(input_tex, audio_reactor=audio_reactor)

    # 6. Blit to screen
    with profiler.time('screen'):
        effect_chain.render_to_screen(output_tex, (0, 0, width, height))
        context.swap_buffers()

    # 7. Profiler tick + FPS update
    profiler.tick()
    _update_fps(frame_start)

    # 8. FPS cap — sleep only the remainder
    elapsed = time.time() - frame_start
    sleep_time = target_frame_time - elapsed
    if sleep_time > 0:
        time.sleep(sleep_time)

context.terminate()
```

---

## Inputs and Outputs

| Name | Type | Description |
|------|------|-------------|
| `context` | `RenderContext` | Window + wgpu device from P1-R1 |
| `effect_chain` | `EffectChain` | Effect pipeline from P1-R2 |
| `target_fps` | `float` | Target frame rate. Default 60. |
| `audio_reactor` | `Any` | Duck-typed audio analysis. Optional. |
| `frame_callback` | `Callable` | Per-frame hook for external systems |
| `input_texture_callback` | `Callable → texture view` | Source of input texture per frame |

---

## Edge Cases and Error Handling

| Scenario | Required Behaviour |
|----------|--------------------|
| Frame takes longer than 16.67 ms | No sleep; log `DEBUG` warning; do NOT drop the frame |
| `frame_time` spike > 100 ms | Clamp to 100 ms (prevents physics jumps after hangs) |
| Effect chain raises exception | Log `ERROR`, continue loop — never crash the loop |
| `should_close()` returns True | Exit loop gracefully, call `context.terminate()` |
| `stop()` called from another thread | Set `self._running = False`; loop exits at top-of-iteration |
| No input texture available | Pass black texture to effect chain; log `DEBUG` |
| FPS drops below 30 for 10 frames | Log `WARNING: sustained FPS below 30` |

---

## Dependencies

- `vjlive3.render.render_context` (P1-R1) — `RenderContext`
- `vjlive3.render.chain` (P1-R2) — `EffectChain`
- `vjlive3.render.texture_pool` (P1-R4) — black texture allocation
- `threading` — `_running` flag stop signal
- `time` — `perf_counter()` for profiler, `time()` for frame budget and FPS

---

## File Layout

```
src/vjlive3/render/
    engine.py       — RenderEngine + FrameProfiler + FrameBudgetAllocator  (~250 lines)
```

> The `FrameBudgetAllocator` moves here from the legacy `core/frame_budget.py` (120 lines). It is pure Python with no GPU dependency — no changes needed except removing the legacy import.

---

## Test Plan

| Test | File | What It Verifies |
|------|------|-----------------|
| `test_engine_runs_headless` | `test_engine.py` | `RenderEngine` with mocked context + chain runs 10 frames, exits cleanly |
| `test_fps_cap` | `test_engine.py` | With instant render, loop sleeps to hit ~60fps (±5fps tolerance) |
| `test_frame_time_clamped` | `test_engine.py` | Injected 1s spike → `frame_time` ≤ 0.1 |
| `test_stop_from_thread` | `test_engine.py` | `stop()` from background thread exits within 2 frames |
| `test_callback_called` | `test_engine.py` | Frame callback invoked exactly once per frame |
| `test_effect_exception_survives` | `test_engine.py` | Effect raising exception → loop continues |
| `test_profiler_records` | `test_engine.py` | `profiler.get_metrics()` returns values after 5 frames |
| `test_budget_skip` | `test_engine.py` | Effect reporting 2× its budget is skipped next frame |
| `test_budget_max_consecutive_skips` | `test_engine.py` | Effect skipped only 2 frames max before forced compute |
| `test_fps_measurement` | `test_engine.py` | `fps` property reads ≥ 50 after 60-frame headless run |

**Minimum coverage:** 80%.

> All tests use mocked `RenderContext` and `EffectChain` — no GPU required.

---

## Definition of Done

- [ ] Spec reviewed and approved
- [ ] All 10 tests pass
- [ ] `engine.py` under 250 lines
- [ ] Zero stubs — all dead paths raise `RuntimeError` per ADR-003
- [ ] `METADATA` constant on `RenderEngine`
- [ ] `fps` measured ≥ 58 in smoke test below
- [ ] Git commit: `[Phase-1] P1-R5: 60fps render engine (loop, profiler, frame budget)`
- [ ] BOARD.md P1-R5 marked ✅
- [ ] Lock released from LOCKS.md

---

## Verification Smoke Test (60 FPS Gate)

```bash
VJ_HEADLESS=true PYTHONPATH=src python3 -c "
import time, threading, numpy as np
from unittest.mock import MagicMock, patch
from vjlive3.render.engine import RenderEngine

ctx = MagicMock()
ctx.should_close.return_value = False
chain = MagicMock()
chain.render.return_value = MagicMock()
chain.render_to_screen.return_value = None

engine = RenderEngine(ctx, chain, target_fps=60.0)
threading.Timer(3.0, engine.stop).start()
engine.run()
print(f'FPS: {engine.fps:.1f} (must be >= 58)')
assert engine.fps >= 58, f'FAILED: FPS={engine.fps:.1f}'
print('PASS')
"
# Expected: FPS >= 58
```

---

## LEGACY CODE REFERENCES

### Main loop — `vjlive/core/app/app.py` lines 2799–2874

The working legacy loop. Key patterns ported:
- `self.frame_time = min(frame_start - self.last_loop_time, 0.1)` → frame time clamping (line 2807)
- `glfw.poll_events()` → `context.poll_events()` (line 2809)
- `glfw.swap_buffers(self.window)` → `context.swap_buffers()` (line 2858)
- `elapsed = time.time() - frame_start; sleep_time = target_frame_time - elapsed` → FPS cap (lines 2871–2874)
- `self.update_fps()` → 1-second rolling FPS average (line 2868; see `update_fps()` at lines 2344–2360)

### Per-frame render — `vjlive/core/app/app.py` lines 2363–2474

- `frame_start = time.perf_counter()` → high-res timing within frame
- `graph_renderer.render()` → in VJLive3, this is `input_texture_callback()`
- `effect_chain.render(graph_texture, [], audio_reactor, semantic_layer)` → direct port
- `effect_chain.render_to_screen(output_texture, (0, 0, w, h))` → direct port
- `frame_profiler.record('total', ...)` + `frame_profiler.tick()` → ported to `FrameProfiler`

### Frame budget — `vjlive/core/frame_budget.py` lines 1–120

Port verbatim. Zero changes needed. Pure Python. The `% 3` throttle and `scale=0.25` hack it replaces are in the legacy depth effects — VJLive3 effects should use `budget.should_skip()` and `budget.get_lod_scale()` instead.
