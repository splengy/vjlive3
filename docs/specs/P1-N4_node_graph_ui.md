# Spec: P1-N4 — Visual Node Graph UI

**Phase:** Phase 1 / P1-N4
**Assigned To:** TBD (awaiting Manager assignment)
**Spec Written By:** Antigravity (Agent 3)
**Date:** 2026-02-21
**Depends On:** P1-N1 (NodeGraph), P1-N2 (node types), P1-R1 (window / GLFW)
**Priority:** P1 — Phase Gate requires "empty node graph visible on screen"

---

## What This Module Does

Provides an **ImGui-based** visual node graph editor rendered directly in the GLFW window
alongside (or over) the render output. Allows the user to:
- See all nodes as draggable cards on a canvas
- See edges as bezier curves between ports
- Click a node to select it and edit its parameters in a side panel
- Right-click canvas to add a new node from a type picker
- Delete selected nodes/edges with the Delete key
- Pan the canvas (middle-mouse drag) and zoom (scroll wheel)

This is a Phase 1 **minimal viable** graph UI — polish and advanced features are Phase 3.

---

## What It Does NOT Do

- Does NOT render a browser or web-based UI (that's the future web-UI)
- Does NOT provide video preview compositing in the UI
- Does NOT support multi-select or group operations (Phase 3)
- Does NOT have undo/redo (Phase 3)

---

## Technology

Uses **PyImGui** (`imgui[glfw]`) rendered into the same GLFW window as ModernGL.
The `NodeGraphEditor` class owns the ImGui frame for the graph canvas each render tick.

## Public Interface

```python
# vjlive3/ui/node_editor.py

import imgui
from typing import Optional, Tuple
from vjlive3.nodes.graph import NodeGraph
from vjlive3.nodes.registry import NodeRegistry


class NodeGraphEditor:
    """
    ImGui-based visual node graph editor.

    Render order: call draw() inside an ImGui frame, after begin_frame().
    """

    def __init__(self, graph: NodeGraph, registry: NodeRegistry) -> None:
        """
        Args:
            graph:    Live NodeGraph to display and edit.
            registry: Used to populate the "Add Node" type picker.
        """

    def draw(self) -> None:
        """
        Render the complete node editor UI for this frame.

        Must be called between imgui.new_frame() and imgui.render().
        Mutates graph directly in response to user interactions.
        Thread-unsafe — call from render thread only.
        """

    @property
    def selected_node_id(self) -> Optional[str]:
        """ID of currently selected node, or None."""

    def pan_to(self, x: float, y: float) -> None:
        """Programmatically set canvas pan offset (e.g. centre on a node)."""

    def fit_all(self) -> None:
        """Pan and zoom to show all nodes within the canvas viewport."""
```

---

## UI Layout

```
┌──────────────────────────────────────────────────────┐
│ [Node Graph]    + Add Node     Zoom: 100%  Fit All   │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌──────────┐   bezier   ┌──────────────┐            │
│  │ Source   │ ─────────► │ Effect: Blur │ ──► [Out] │
│  └──────────┘            └──────────────┘            │
│               (canvas, pannable, zoomable)            │
├──────────────────────────────────────────────────────┤
│ PROPERTIES  [Blur effect node selected]              │
│  intensity: [slider 0.0 ──── 0.5 ──── 1.0]           │
│  radius:    [slider ...]                             │
└──────────────────────────────────────────────────────┘
```

---

## User Interactions

| Action | Result |
|--------|--------|
| Left-click node | Select node; show params in panel |
| Drag node | Move node on canvas |
| Drag from port → port | Create edge |
| Right-click canvas | "Add Node" popup with type picker |
| Delete key | Delete selected node/edge |
| Middle-mouse drag | Pan canvas |
| Scroll wheel | Zoom in/out |
| Double-click canvas | Deselect |

---

## Edge Cases

- **Cycle attempt:** Edge drag to an already-connected (would-cycle) port shows red highlight, drops on release.
- **Empty graph:** Canvas shows help text "Right-click to add your first node".
- **Node with no params:** Properties panel shows "No parameters".
- **Very long node name:** Truncate with ellipsis in card header.

---

## Dependencies

### External
- `imgui[glfw] >= 2.0` (PyImGui with GLFW backend)

### Internal
- `vjlive3.nodes.graph.NodeGraph` (P1-N1)
- `vjlive3.nodes.registry.NodeRegistry` (P1-N1)

---

## Test Plan

| Test ID | What |
|---------|------|
| `test_editor_initialises` | NodeGraphEditor(graph, registry) doesn't crash |
| `test_draw_empty_graph` | draw() with 0 nodes doesn't crash |
| `test_draw_two_nodes` | draw() with 2 connected nodes renders without error |
| `test_selected_node_none_initially` | selected_node_id is None at start |
| `test_fit_all_noop_on_empty` | fit_all() on empty graph doesn't crash |

Tests use headless ImGui mock (no display required).

**Minimum coverage:** 80%

---

## Definition of Done

- [ ] All 5 tests pass
- [ ] "Empty node graph visible on screen" (Phase Gate) verifiable with manual smoke test
- [ ] File < 750 lines
- [ ] No stubs
- [ ] BOARD.md P1-N4 marked ✅
- [ ] Lock released; AGENT_SYNC.md updated
