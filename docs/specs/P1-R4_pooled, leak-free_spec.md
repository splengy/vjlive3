# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P1-R4_pooled, leak-free.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-R4 — pooled, leak-free

**What This Module Does**

**What This Module Does NOT Do**
- Does NOT hardcode `moderngl.Texture` or `moderngl.Buffer` assumptions. Must abstract all textures via the generic `BackendContext` (e.g., `wgpu-py` resource pooling).

---

## Detailed Behavior and Parameter Interactions

- All texture resources must be strictly renderer agnostic. The Texture Manager must provide a unified interface that translates engine texture requests into the active backend's native format (e.g., `wgpu.GPUTexture` vs fallback `moderngl.Texture`).

---

## Public Interface

---

## Inputs and Outputs

---

## Edge Cases and Error Handling

---

## Mathematical Formulations

---

## Performance Characteristics

---

## Test Plan

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P1-R4: pooled, leak-free` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  
