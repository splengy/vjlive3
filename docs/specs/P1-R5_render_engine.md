# Spec: P1-R5 — Core Rendering Engine

**File naming:** `docs/specs/P1-R5_render_engine.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-R5 — Core Rendering Engine

**Phase:** Phase 1 / P1-R5
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The core rendering engine provides the main 60fps render loop that drives the entire VJLive3 application. It coordinates the GPU pipeline, manages framebuffers, executes shader programs, handles plugin processing chains, and ensures consistent timing and frame delivery for live visual performance.

---

## What It Does NOT Do

- Does not handle audio analysis (delegates to audio engine)
- Does not manage plugin loading or discovery (delegates to plugin system)
- Does not provide UI or user interaction (delegates to node graph UI)
- Does not handle hardware input directly (delegates to hardware modules)

---

## Public Interface

```python
class RenderEngine:
    def __init__(self, ctx: moderngl.Context, width: int, height: int) -> None: ...
    
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...
    
    def set_plugin_chain(self, plugins: List[PluginBase]) -> None: ...
    def add_plugin(self, plugin: PluginBase) -> None: ...
    def remove_plugin(self, plugin: PluginBase) -> None: ...
    
    def render_frame(self) -> None: ...
    def get_current_frame(self) -> Optional[Texture]: ...
    
    def get_fps(self) -> float: ...
    def get_frame_count(self) -> int: ...
    
    def on_resize(self, width: int, height: int) -> None: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `ctx` | `moderngl.Context` | ModernGL context | Must be valid |
| `width` | `int` | Framebuffer width | > 0, typically 1920+ |
| `height` | `int` | Framebuffer height | > 0, typically 1080+ |
| `plugins` | `List[PluginBase]` | Plugin processing chain | Ordered list |

**Output:** Renders to screen/framebuffer, provides current frame texture

---

## Edge Cases and Error Handling

- What happens if ModernGL context is lost? → Attempt recovery or graceful shutdown
- What happens if plugin crashes? → Disable plugin, continue rendering
- What happens if frame rate drops below 60? → Log warning, skip frames if needed
- What happens on window resize? → Recreate framebuffers, maintain aspect ratio
- What happens on cleanup? → Stop loop, release all resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `moderngl` — required for OpenGL rendering — fallback: raise ImportError
  - `glfw` or `pygame` — for window management — fallback: headless mode
- Internal modules this depends on:
  - `vjlive3.render.opengl_context`
  - `vjlive3.render.chain`
  - `vjlive3.render.framebuffer`
  - `vjlive3.render.program`
  - `vjlive3.plugins.PluginBase`
  - `vjlive3.plugins.plugin_runtime`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_start_stop` | Can start and stop render loop |
| `test_plugin_chain` | Processes plugins in order |
| `test_frame_output` | Produces valid framebuffer output |
| `test_fps_counter` | FPS calculation works |
| `test_resize` | Handles window resize correctly |
| `test_plugin_error` | Recovers from plugin crashes |
| `test_cleanup` | Releases all resources on cleanup |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-R5: Core rendering engine` message
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

*Specification based on VJlive-2 rendering engine architecture.*