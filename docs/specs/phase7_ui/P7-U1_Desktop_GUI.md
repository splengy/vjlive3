# Spec: P7-U1 — Desktop GUI + SentienceOverlay Easter Egg

**File naming:** `docs/specs/phase7_ui/P7-U1_Desktop_GUI.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P7-U1 — Desktop GUI

**Phase:** Phase 7 / P7-U1
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Desktop GUI provides the main application window and user interface for VJLive3. It includes the node graph editor, plugin controls, performance view, and the hidden SentienceOverlay easter egg. The GUI is built with a modern, responsive design that supports high-DPI displays and multi-monitor setups.

---

## What It Does NOT Do

- Does not handle node graph logic (delegates to P1-N4)
- Does not manage plugin loading (delegates to P1-P2)
- Does not provide web-based remote control (delegates to P7-U2)
- Does not include collaborative features (delegates to P7-U3)

---

## Public Interface

```python
class DesktopGUI:
    def __init__(self, render_engine: RenderEngine, node_graph: NodeGraphUI) -> None: ...
    
    def show(self) -> None: ...
    def hide(self) -> None: ...
    def is_visible(self) -> bool: ...
    
    def create_menu(self) -> None: ...
    def create_toolbar(self) -> None: ...
    def create_status_bar(self) -> None: ...
    
    def show_node_graph(self) -> None: ...
    def show_performance_view(self) -> None: ...
    def show_plugin_panel(self, plugin_id: str) -> None: ...
    
    def toggle_sentience_overlay(self) -> None: ...
    def is_sentience_overlay_active(self) -> bool: ...
    
    def handle_event(self, event: GUIEvent) -> None: ...
    def update(self, dt: float) -> None: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `render_engine` | `RenderEngine` | Rendering engine | Must be initialized |
| `node_graph` | `NodeGraphUI` | Node graph UI | Must be initialized |
| `event` | `GUIEvent` | User input event | Mouse, keyboard, etc. |
| `dt` | `float` | Delta time in seconds | > 0 |

**Output:** Manages main application window and all UI panels

---

## Edge Cases and Error Handling

- What happens if render engine not ready? → Show error, disable UI
- What happens if node graph fails? → Show fallback, log error
- What happens if display scaling is high? → Adjust UI scaling
- What happens if user triggers SentienceOverlay? → Toggle easter egg mode
- What happens on cleanup? → Close window, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `pygame` or `imgui` — for GUI framework — fallback: raise ImportError
  - `moderngl` — for rendering — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.render.opengl_context`
  - `vjlive3.render.chain`
  - `vjlive3.plugins.plugin_runtime`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_window_creation` | Creates main window correctly |
| `test_menu_toolbar` | Creates menus and toolbars |
| `test_node_graph_integration` | Integrates with node graph UI |
| `test_performance_view` | Shows performance metrics |
| `test_sentience_overlay` | Toggles easter egg mode |
| `test_event_handling` | Handles user input events |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-7] P7-U1: Desktop GUI + SentienceOverlay` message
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

*Specification based on VJlive-2 desktop GUI architecture.*