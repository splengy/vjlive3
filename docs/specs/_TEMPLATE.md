# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: [TASK-ID] — [Module Name]

**What This Module Does**

*2–3 sentences. What problem does it solve? What does it produce?*

---

## Public Interface

```python
# Paste planned class/function signatures here before coding

class MyModule:
    def __init__(self, param: Type) -> None:...
    def method(self, arg: Type) -> ReturnType:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `param` | `type` | What it is | Range / valid values |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `library_name` — used for X — fallback: Y
- Internal modules this depends on:
  - `vjlive3.module.ClassName`

---

## Error Cases

*What can go wrong and how should the module respond? Be specific — coders will implement exactly what you write here.*

| Error Condition | Exception / Response | Recovery |
|----------------|---------------------|----------|
| Invalid parameter value | `ValueError("param must be 0.0-1.0")` | Clamp to valid range |
| Missing GPU context | `RuntimeError("No GL context")` | Fall back to CPU path or skip |
| Hardware disconnected | Log warning, continue | Auto-reconnect on next frame |

---

## Configuration Schema

*Pydantic model fields. Every tunable parameter must be listed with its type, default, and valid range. The coder will generate the Pydantic class directly from this table.*

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `intensity` | `float` | `0.5` | `0.0 - 1.0` | Overall effect strength |
| `enabled` | `bool` | `True` | — | Whether effect is active |

---

## State Management

*What persists between frames? What resets? A video effect that doesn't know what to keep will either leak or lose visual continuity.*

- **Per-frame state:** (cleared each frame)
  - Current input frame
- **Persistent state:** (survives across frames)
  - Previous frame buffer (for temporal effects)
  - Accumulated counters / phase values
- **Initialization state:** (set once at startup)
  - Shader programs, FBOs, textures
- **Cleanup required:** Yes/No — what `stop()` or `__del__` must release

---

## GPU Resources

*What OpenGL/GPU resources does this module allocate? Coders need this to write proper init/cleanup and hit 60fps.*

| Resource | Type | Size / Format | Lifecycle |
|----------|------|--------------|-----------|
| Main shader | GLSL program | vertex + fragment | Init once, reuse |
| Work FBO | Framebuffer | viewport-sized, RGBA8 | Init once, resize on window change |
| Lookup texture | Texture2D | 256x1, R32F | Init once |

*If this module does NOT use GPU resources, write "CPU-only — no GPU resources."*

---

## Test Plan

*List the tests that will verify this module before the task is marked done.*

| Test Name | What It Verifies |
|-----------|-----------------|
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