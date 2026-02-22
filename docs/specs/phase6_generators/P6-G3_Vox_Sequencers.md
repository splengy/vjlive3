# Spec: P6-G3 — Vox Sequencers (3D Sequencing)

**File naming:** `docs/specs/phase6_generators/P6-G3_Vox_Sequencers.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P6-G3 — Vox Sequencers

**Phase:** Phase 6 / P6-G3
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Vox Sequencers provide 3D spatial sequencing for visual elements and particles. They allow arranging and animating objects in 3D space with time-based control, enabling complex volumetric compositions, architectural visualizations, and immersive 3D scenes.

---

## What It Does NOT Do

- Does not handle 3D model loading (delegates to asset loader)
- Does not provide advanced 3D rendering (delegates to render engine)
- Does not include physics simulation (delegates to P6-AG2)
- Does not support external animation formats (procedural only)

---

## Public Interface

```python
class VoxSequencers:
    def __init__(self) -> None: ...
    
    def add_voxel(self, position: Tuple[float, float, float], color: Tuple[float, float, float], size: float = 1.0) -> str: ...
    def remove_voxel(self, voxel_id: str) -> bool: ...
    def move_voxel(self, voxel_id: str, position: Tuple[float, float, float]) -> None: ...
    
    def set_sequence(self, voxel_id: str, keyframes: List[Keyframe]) -> None: ...
    def get_sequence(self, voxel_id: str) -> List[Keyframe]: ...
    
    def set_playback_speed(self, speed: float) -> None: ...
    def get_playback_speed(self) -> float: ...
    
    def get_scene_state(self, time: float) -> SceneState: ...
    def render_frame(self, ctx: moderngl.Context, width: int, height: int, time: float) -> Texture: ...
    
    def clear_scene(self) -> None: ...
    def reset(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `position` | `Tuple[float, float, float]` | 3D position | Any valid floats |
| `color` | `Tuple[float, float, float]` | RGB color | 0.0 to 1.0 |
| `size` | `float` | Voxel size | > 0 |
| `keyframes` | `List[Keyframe]` | Animation keyframes | Valid keyframes |
| `speed` | `float` | Playback speed | 0.0 to 10.0 |
| `time` | `float` | Time in seconds | ≥ 0.0 |
| `ctx` | `moderngl.Context` | OpenGL context | Valid |
| `width, height` | `int` | Render dimensions | > 0 |

**Output:** `str`, `bool`, `List[Keyframe]`, `SceneState`, `Texture` — Various scene and rendering results

---

## Edge Cases and Error Handling

- What happens if voxel position is extreme? → May be clipped or culled
- What happens if keyframes are invalid? → Ignore, log warning
- What happens if playback speed is 0? → Static scene
- What happens if scene is empty? → Render black/empty frame
- What happens on cleanup? → Clear all voxels, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `moderngl` — for rendering — fallback: raise ImportError
  - `numpy` — for 3D math — fallback: raise ImportError
- Internal modules this depends on:
  - `vjlive3.render.opengl_context`
  - `vjlive3.plugins.PluginBase`

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_voxel_management` | Adds, removes, moves voxels correctly |
| `test_sequencing` | Keyframe sequences work |
| `test_playback_speed` | Speed affects animation rate |
| `test_scene_state` | Scene state queries work |
| `test_rendering` | Renders valid texture output |
| `test_clear_scene` | Clears all voxels correctly |
| `test_edge_cases` | Handles invalid inputs gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-6] P6-G3: Vox Sequencers (3D sequencing)` message
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

*Specification based on VJlive-2 Vox Sequencers module.*