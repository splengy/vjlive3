# Autonomous Phase 1 Execution Plan

## Overview
This document outlines the autonomous execution of Phase 1 (Foundation & Rendering) following the code wipe on 2026-02-21. All code in `src/vjlive3/` and `tests/` was deleted except the plugin system package. We will rebuild from specs only.

## Agent Assignments

### Roo Coder (1) — Rendering & Node Graph
**Tasks:** P1-R1, P1-R2, P1-R3, P1-R4, P1-R5, P1-N1, P1-N2, P1-N3, P1-N4

**Dependency Chain:**
- P1-R1 → P1-R2 → P1-R3 → P1-R4 → P1-R5
- P1-N1 starts after P1-R5 completes
- P1-N2, P1-N3 start after P1-N1 completes
- P1-N4 starts after P1-N1 + P1-R5 complete

**Research Prerequisites:** Each P1-R* task requires RESEARCH:P1-R* to read legacy VJlive-2 code first.

### Roo Coder (2) — Audio Engine
**Tasks:** P1-A1, P1-A2, P1-A3, P1-A4

**Dependency Chain:**
- P1-A1 → P1-A2 → P1-A3 → P1-A4

**Research Prerequisites:** Each P1-A* task requires RESEARCH:P1-A* to read legacy VJlive-2 code first.

**Note:** P1-A1 and P1-A2 were marked "Done" before code wipe but code was deleted. They must be redone from specs with proper research.

### Antigravity (Agent 3) — Plugin System
**Tasks:** P1-P1, P1-P2, P1-P3, P1-P4, P1-P5

**Dependency Chain:**
- P1-P1 → P1-P2 → P1-P3 → P1-P4
- P1-P5 can start after P1-P1

**Research Prerequisites:** All RESEARCH:P1-P* tasks already marked done in logs.

**Note:** Plugin system code survived the wipe in `src/vjlive3/plugins/`. Antigravity should verify existing implementation matches specs and complete any missing parts.

## Autonomous Workflow Rules

1. **SPEC FIRST:** No code without spec. All specs already exist in `docs/specs/`.
2. **RESEARCH PREREQUISITE:** Before any P1-XX task, complete RESEARCH:P1-XX by reading legacy code in VJlive-2/.
3. **LOCK SYSTEM:** Always check `WORKSPACE/COMMS/LOCKS.md` before starting. Claim files immediately.
4. **WORKFLOW:** SPEC (already done) → RESEARCH → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
5. **STATUS TRACKING:** Update `WORKSPACE/COMMS/STATUS/<task-id>.txt` with current status.
6. **LOGGING:** Write session notes in `WORKSPACE/COMMS/LOGS/<your-agent-id>.md`.
7. **NO AUTONOMOUS ACTION:** Only work on tasks explicitly assigned in `DISPATCH.md`.
8. **BLOCKED HANDLING:** If blocked on dependency, mark status `⏸️ Blocked` and wait for manager.

## Phase 1 Gate Criteria

To complete Phase 1, the following must be true:
- FPS ≥ 58 in status window
- Window visible and responsive
- Empty node graph renders without error
- Plugin system loads at least one plugin successfully
- All unit tests pass (80%+ coverage)
- All integration tests pass

## Monitoring & Sanity Checks

**Manager (ROO CODE) will:**
- Check progress daily via STATUS files and agent logs
- Verify test coverage meets 80% threshold
- Run sanity checks after each task completion
- Monitor for lock conflicts and agent pileups
- Escalate to user if blockers persist

**Sanity Check Triggers:**
- Any task marked "Done" without corresponding test file modifications
- Test coverage < 80% on new code
- Status file not updated for >24 hours
- Lock held for >48 hours without progress
- Agent log shows deviation from spec

## Expected Timeline (Autonomous)

- **Week 1:** Roo Coder 1 completes P1-R1 through P1-R3
- **Week 2:** Roo Coder 1 completes P1-R4, P1-R5, starts P1-N1
- **Week 3:** Roo Coder 1 completes node graph (P1-N1 through P1-N4)
- **Week 4:** Roo Coder 2 completes audio engine (P1-A1 through P1-A4)
- **Week 5:** Antigravity verifies/completes plugin system (P1-P1 through P1-P5)
- **Week 6:** Integration testing, bug fixes, Phase 1 gate verification

*Note: Timeline is flexible based on agent performance and complexity.*

## Initial Task Assignment State

As of 2026-02-21 23:35 UTC:

### DISPATCH.md Active Assignments

**Roo Coder (1) - Rendering Chain:**
- RESEARCH:P1-R1: ⬜ Todo
- P1-R1: ⬜ Todo (currently shows IN_PROGRESS but no work done - reset needed)

**Roo Coder (1) - Node Graph:**
- All tasks: ⬜ Todo (blocked on P1-R5)

**Roo Coder (2) - Audio Engine:**
- P1-A1: ⬜ Todo ( BOARD shows Done but code deleted - must redo)
- P1-A2: ⬜ Todo ( BOARD shows Done but code deleted - must redo)
- RESEARCH:P1-A3: ⬜ Todo
- P1-A3: ⏸️ Blocked
- RESEARCH:P1-A4: ⬜ Todo
- P1-A4: ⏸️ Blocked

**Antigravity (Agent 3) - Plugin System:**
- RESEARCH:P1-P1: ✅ Done
- P1-P1: ⬜ Todo ( BOARD shows In Progress but needs verification)
- RESEARCH:P1-P2: ✅ Done
- P1-P2: ⏸️ Blocked (needs P1-P1)
- RESEARCH:P1-P3: ✅ Done
- P1-P3: ⏸️ Blocked (needs P1-P2)
- RESEARCH:P1-P4: ✅ Done
- P1-P4: ⏸️ Blocked (needs P1-P3)
- RESEARCH:P1-P5: ✅ Done
- P1-P5: ⏸️ Blocked (needs P1-P1)

### Required Reset

The following tasks must be reset to ⬜ Todo or appropriate blocked status:
- P1-R1: Reset to ⬜ Todo (no actual work done despite IN_PROGRESS status)
- P1-A1: Reset to ⬜ Todo (code deleted)
- P1-A2: Reset to ⬜ Todo (code deleted)
- P1-P1: Reset to ⬜ Todo (needs verification against existing code)

## Next Steps

1. Manager (ROO CODE) updates DISPATCH.md with reset statuses
2. Manager updates BOARD.md to reflect code wipe reality
3. Manager posts initial task assignments in proper dependency order
4. Agents begin autonomous execution following workflow
5. Manager monitors progress and stops at Phase 1 completion for review

## Stop Condition

Autonomous execution will pause when **all Phase 1 tasks reach ✅ Done status** and the Phase 1 gate criteria are met. At that point, ROO CODE will:
- Run full Phase 1 verification suite
- Check test coverage
- Verify FPS and performance benchmarks
- Compile completion reports
- Notify user for review

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-21 23:35 UTC  
**Manager:** ROO CODE
