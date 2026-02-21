# Spec: P1-R5 — Core Rendering Engine (60fps Loop)

**Phase:** Phase 1 / P1-R5
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Source References:** `VJlive-2/core/chain.py`, `VJlive-2/docs/specs/P1-R2_gpu_pipeline.md`
**Depends On:** P1-R1 (OpenGLContext), P1-R2 (GPU pipeline / EffectChain), P1-R3 (ShaderCompiler), P1-R4 (TextureManager), P1-N1 (NodeGraph)

---

## What This Module Does

Provides the core `RenderEngine` that drives the VJLive3 render loop. On each tick it:
1. Polls GLFW events and checks the window close flag
2. Reads the latest `AudioFrame` and `BeatState` from the audio bus
3. Calls `NodeGraph.tick()` with the current context
4. Executes the `EffectChain` (ping-pong FBOs through the active effect pipeline)
5. Blits the final framebuffer to the window backbuffer
6. Calls `swap_buffers()`
7. Reports FPS and enforces the 60 FPS gate (SAFETY_RAIL 1)

Also manages the `RenderContext` struct shared between all subsystems each frame.

---

## What It Does NOT Do

- Does NOT implement effects or generators (those are P1-N2 and plugin system)
- Does NOT manage windows or GL context lifecycle (P1-R1)
- Does NOT compile shaders (P1-R3)
- Does NOT manage audio capture (P1-A1)
- Does NOT implement the UI (P1-N4)

---

## Public Interface

```python
# vjlive3/render/engine.py

import moderngl
from dataclasses import dataclass
from typing import Optional, Callable
from vjlive3.render.context import OpenGLContext
from vjlive3.render.textures import TextureManager
from vjlive3.render.shader import ShaderCompiler
from vjlive3.nodes.graph import NodeGraph
from vjlive3.audio.analyzer import AudioAnalyzerBase, AudioFrame
from vjlive3.audio.beat_detector import BeatDetector, BeatState


@dataclass
class RenderContext:
    """
    Shared frame context passed to NodeGraph, EffectChain, and plugins each tick.
    Immutable per frame — a fresh instance is created at the start of each tick.
    """
    frame_count: int
    dt: float          # seconds since last frame
    fps: float         # measured FPS (EMA over 30 frames)
    width: int
    height: int
    time: float        # total elapsed seconds since start
    audio: AudioFrame  # latest audio analysis snapshot
    beat: BeatState    # latest beat detection state


class RenderEngine:
    """
    VJLive3 main render loop.

    Call run() to start the blocking render loop.
    Call stop() from another thread or from a node callback to exit.

    Performance guarantee:
        - Render loop must sustain ≥ 58 FPS at 1920×1080 with empty node graph
          (SAFETY_RAIL 1). FPS is measured and logged every 5 seconds.
        - If FPS drops below 58 for more than 3 consecutive seconds → log CRITICAL.
    """

    def __init__(
        self,
        gl_context: OpenGLContext,
        node_graph: NodeGraph,
        audio_analyzer: AudioAnalyzerBase,
        beat_detector: BeatDetector,
        *,
        on_frame: Optional[Callable[['RenderContext'], None]] = None,
    ) -> None:
        """
        Args:
            gl_context:    OpenGLContext from P1-R1.
            node_graph:    NodeGraph from P1-N1. Ticked each frame.
            audio_analyzer: From P1-A1.
            beat_detector:  From P1-A2.
            on_frame:       Optional callback called after each swap (for testing).
        """

    def run(self) -> None:
        """
        Start the render loop. Blocks until stop() is called or window is closed.

        Initialises all internal render resources on entry.
        Cleans up all render resources (TextureManager, ShaderCompiler) on exit.
        """

    def stop(self) -> None:
        """
        Signal the render loop to exit after the current frame.
        Thread-safe.
        """

    @property
    def is_running(self) -> bool:
        """True if render loop is active."""

    @property
    def fps(self) -> float:
        """Current measured FPS (EMA). Updated each frame."""

    @property
    def texture_manager(self) -> TextureManager:
        """Access the frame's TextureManager (valid after run() starts)."""

    @property
    def shader_compiler(self) -> ShaderCompiler:
        """Access the ShaderCompiler (valid after run() starts)."""
```

---

## Frame Timing

```python
TARGET_FPS = 60.0
TARGET_DT  = 1.0 / TARGET_FPS  # 16.667ms

# EMA for FPS smoothing
fps = 0.9 * fps + 0.1 * (1.0 / dt)
```

No artificial sleep — VSync (enabled in P1-R1) handles frame pacing.
If VSync disabled (e.g. headless), add `time.sleep(max(0, TARGET_DT - frame_time))`.

---

## Render Loop Pseudocode

```
frame_count = 0
last_time = time.monotonic()

while not should_stop and not gl_context.should_close():
    # 1. Timing
    now = time.monotonic()
    dt = now - last_time
    last_time = now

    # 2. Poll events
    gl_context.poll_events()

    # 3. Build frame context
    audio = analyzer.get_frame()
    beat  = beat_detector.get_state()
    ctx   = RenderContext(frame_count, dt, fps, width, height, total_time, audio, beat)

    # 4. Graph tick
    node_graph.tick(ctx)

    # 5. EffectChain render (from P1-R2 EffectChain.render())
    chain.render(ctx)

    # 6. Blit to window
    gl_context.ctx.screen.use()
    # blit final FBO → screen via quad shader

    # 7. Swap
    gl_context.swap_buffers()

    # 8. FPS accounting
    fps = 0.9 * fps + 0.1 * (1.0 / max(dt, 1e-6))
    frame_count += 1

    if on_frame: on_frame(ctx)
```

---

## Inputs and Outputs

| Item | Type | Description |
|------|------|-------------|
| `gl_context` | `OpenGLContext` | Window + GL context |
| `node_graph` | `NodeGraph` | Graph of effects to process |
| **Output** `RenderContext.fps` | `float` | Measured FPS |
| **Output** `on_frame(ctx)` | callback | Called post-swap for testing |

---

## Edge Cases and Error Handling

- **dt = 0:** Guard with `max(dt, 1e-6)` to avoid divide-by-zero.
- **Node crash in graph.tick():** NodeGraph handles internally (quarantine), render loop continues.
- **GL error in chain.render():** Catch, log CRITICAL, try to clear screen and swap.
- **FPS < 58 sustained:** Log CRITICAL (RAIL 1 violation). Do NOT crash — let it run.
- **stop() from another thread:** Uses `threading.Event`; loop checks it each frame.
- **on_frame exception:** Caught and logged; never propagates to render loop.

---

## Dependencies

### External
- `moderngl >= 5.0`

### Internal
- `vjlive3.render.context.OpenGLContext` (P1-R1)
- `vjlive3.render.pipeline.EffectChain` (P1-R2)
- `vjlive3.render.shader.ShaderCompiler` (P1-R3)
- `vjlive3.render.textures.TextureManager` (P1-R4)
- `vjlive3.nodes.graph.NodeGraph` (P1-N1)
- `vjlive3.audio.analyzer.AudioAnalyzerBase` (P1-A1)
- `vjlive3.audio.beat_detector.BeatDetector` (P1-A2)

---

## Test Plan

| Test ID | What It Verifies |
|---------|-----------------|
| `test_render_context_fields` | RenderContext is frozen and has all required fields |
| `test_engine_stop_exits_loop` | stop() causes run() to return |
| `test_fps_property_updates` | fps property returns > 0 after a few frames |
| `test_on_frame_callback_called` | on_frame called N times in N-frame run |
| `test_node_graph_ticked` | node_graph.tick() called each frame |
| `test_audio_frame_in_context` | RenderContext.audio contains AudioFrame |
| `test_fps_rail_1_log_on_slow` | Simulated slow loop triggers CRITICAL log |
| `test_gl_error_no_crash` | chain.render() raising does not crash engine |

Tests use headless context (NullOpenGLContext mock).

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 8 tests pass in headless mode
- [ ] FPS test passes: `≥ 58 FPS` at 1920×1080 with empty node graph (60s run)
- [ ] File < 750 lines
- [ ] No stubs
- [ ] BOARD.md P1-R5 marked ✅
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Command

```bash
# Unit tests (headless)
PYTHONPATH=src python3 -m pytest tests/unit/test_render_engine.py -v

# Phase Gate FPS test (requires display)
# Run for 30s with empty node graph, verify FPS ≥ 58
PYTHONPATH=src python3 scripts/profile_engine.py --duration 30 --resolution 1920x1080
# Expected: "Average FPS: XX.X" where XX.X ≥ 58
```
