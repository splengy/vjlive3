# Implementation Tasks — Phase 6 AI/Neural

**Assigned By:** Manager-Gemini-3.1
**Date:** 2026-02-22
**Priority:** P0-P1 — Complete Phase 6 AI/Neural collection

---

## Context

Phase 6 requires porting 4 AI/Neural modules from the legacy VJlive-2 codebase. All specifications have been created and approved. These are advanced machine learning modules that provide neural style transfer, live coding, AI assistance, and dreamstate degradation.

---

## Task List

### P6-AI1: Neural Style Transfer (ML Effects)

**Spec:** `docs/specs/phase6_ai_neural/P6-AI1_Neural_Style_Transfer.md`
**Priority:** P0
**Dependencies:** torch, torchvision, opencv-python
**Test coverage:** ≥80%

### P6-AI2: Live Coding Engine (hot-reload Python + GLSL)

**Spec:** `docs/specs/phase6_ai_neural/P6-AI2_Live_Coding_Engine.md`
**Priority:** P0
**Dependencies:** moderngl, watchdog, importlib
**Test coverage:** ≥80%

### P6-AI3: AI Creative Assistant

**Spec:** `docs/specs/phase6_ai_neural/P6-AI3_AI_Creative_Assistant.md`
**Priority:** P1
**Dependencies:** openai, langchain, transformers
**Test coverage:** ≥80%

### P6-AI4: Dreamstate Degradation

**Spec:** `docs/specs/phase6_ai_neural/P6-AI4_Dreamstate_Degradation.md`
**Priority:** P1
**Dependencies:** torch, torchvision
**Test coverage:** ≥80%

---

## Instructions

1. Read each specification file thoroughly before starting implementation.
2. Implement modules in order: P6-AI1 through P6-AI4.
3. Follow the Definition of Done in each spec:
   - All tests pass
   - No file over 750 lines
   - No stubs
   - Git commit with proper message
   - Update BOARD.md
   - Write AGENT_SYNC.md handoff note
4. Use the pre-commit hooks to verify:
   - `scripts/check_stubs.py`
   - `scripts/check_file_size.py`
   - `scripts/check_performance_regression.py`
5. Respect all Safety Rails in `WORKSPACE/SAFETY_RAILS.md`.
6. Coordinate with other agents via `WORKSPACE/COMMS/AGENT_SYNC.md`.

---

## Critical Notes

- These are **AI/Neural** modules — GPU performance and model loading are critical.
- All modules must conform to the `PluginBase` interface in `src/vjlive3/plugins/api.py`.
- Parameter ranges and defaults must match the legacy manifest specifications exactly.
- Ensure proper handling of edge cases: model loading failures, GPU memory limits.

---

## Verification

After completing each module:
1. Run tests: `pytest tests/plugins/test_<plugin_name>.py`
2. Check coverage: `pytest --cov=src/vjlive3/plugins`
3. Update `BOARD.md` status to ✅ Done
4. Write completion note in `WORKSPACE/COMMS/STATUS/P6-<task-id>.txt`
5. Create `task_completion_P6-<task-id>.md` with summary

---

**Begin implementation. Report progress via AGENT_SYNC.md.**