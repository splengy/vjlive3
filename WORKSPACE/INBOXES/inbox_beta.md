# Implementation Tasks — Phase 6 Quantum

**Assigned By:** Manager-Gemini-3.1
**Date:** 2026-02-22
**Priority:** P0-P1 — Complete Phase 6 Quantum collection

---

## Context

Phase 6 requires porting 4 quantum consciousness modules from the legacy VJlive-2 codebase. All specifications have been created and approved. These are advanced consciousness simulation modules that provide quantum-inspired visual effects.

---

## Task List

### P6-Q1: Quantum Nexus / Consciousness System

**Spec:** `docs/specs/phase6_quantum/P6-Q1_Quantum_Nexus.md`
**Priority:** P0
**Dependencies:** moderngl, numpy
**Test coverage:** ≥80%

### P6-Q2: Quantum Explorer

**Spec:** `docs/specs/phase6_quantum/P6-Q2_Quantum_Explorer.md`
**Priority:** P0
**Dependencies:** moderngl, numpy
**Test coverage:** ≥80%

### P6-Q3: Quantum Tunnel

**Spec:** `docs/specs/phase6_quantum/P6-Q3_Quantum_Tunnel.md`
**Priority:** P1
**Dependencies:** moderngl, numpy
**Test coverage:** ≥80%

### P6-Q4: Living Fractal Consciousness [DREAMER]

**Spec:** `docs/specs/phase6_quantum/P6-Q4_Living_Fractal_Consciousness.md`
**Priority:** P1
**Dependencies:** moderngl, numpy
**Test coverage:** ≥80%

---

## Instructions

1. Read each specification file thoroughly before starting implementation.
2. Implement modules in order: P6-Q1 through P6-Q4.
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

- These are **quantum consciousness** modules — GPU performance and visual quality are critical.
- All modules must conform to the `PluginBase` interface in `src/vjlive3/plugins/api.py`.
- Parameter ranges and defaults must match the legacy manifest specifications exactly.
- Ensure proper handling of edge cases: performance limits, memory usage.

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