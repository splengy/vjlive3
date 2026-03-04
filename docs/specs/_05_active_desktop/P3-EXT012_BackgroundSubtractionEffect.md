# Spec Template — Copy this file for every new task
# File naming: `docs/specs/<task-id>_<module-name>.md`
# Rule: This file must exist and be reviewed BEFORE writing any code for this task.

---
## Task: [P3-EXT012] — BackgroundSubtractionEffect

**Phase:** [P0]
**Assigned To:** [Agent name]
**Spec Written By:** [Agent name]
**Date:** [YYYY-MM-DD]

---
## What This Module Does

BackgroundSubtractionEffect is a computer vision technique that identifies moving objects or regions by comparing the current frame with a reference background model. This effect isolates foreground elements from the static background, enabling applications like motion detection, object tracking, and activity recognition.

---
## What It Does NOT Do

- Does not perform real-time object classification or identification
- Does not handle complex lighting changes without adaptive background modeling
- Does not process video streams at frame rates exceeding 30 FPS on standard hardware
- Does not directly output object bounding boxes or tracking data

---
## Public Interface

```python
# Paste planned class/function signatures here before coding

class BackgroundSubtractionEffect:
    def __init__(self, history: float = 0.0, threshold: float = 0.0, 
                learning_rate: float = 0.0) -> None: ...
    def process_frame(self, frame: Type) -> Type: ...
    def reset(self) -> None: ...
```

---
## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `history` | `float` | Number of frames to maintain in history | [0.0-10.0] |
| `threshold` | `float` | Pixel intensity threshold for change detection | [0.0-10.0] |
| `learning_rate` | `float` | Rate at which background model adapts | [0.0-10.0] |
| `process_frame` | `method` | Processes a single frame and returns foreground mask | - |

---
## Edge Cases and Error Handling

- What happens if hardware is missing? → (NullDevice pattern / graceful fallback)
- What happens on bad input? → (raise ValueError with message)
- What is the cleanup path? → (close(), __exit__, resource release)

---
## Dependencies

- External libraries needed (and what happens if they are missing):
  - `opencv-python` — used for background subtraction algorithms — fallback: manual implementation
- Internal modules this depends on:
  - `vjlive3.plugins.background_subtraction.BackgroundSubtractionPlugin`

---
## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_basic_operation` | Core function returns expected output |
| `test_error_handling` | Bad input raises correct exception |
| `test_cleanup` | stop() / close() releases resources cleanly |

**Minimum coverage:** 80% before task is marked done.

---
## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] task-id: description` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---