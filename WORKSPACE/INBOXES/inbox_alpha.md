# INBOX: Alpha Agent — Task Assignment

**Assigned By:** Manager (ROO CODE)  
**Date:** 2026-02-22  
**Priority:** P0  
**Phase:** 8 (Integration & Polish)  
**Task ID:** P8-I8  

---

## MISSION

Execute comprehensive parity testing between the legacy VJLive applications (VJlive-2 and vjlive) and the current VJLive3 codebase. This is a verification task — you will NOT modify code, only assess and report gaps.

---

## CONTEXT

The VJLive3 project is synthesizing features from two legacy codebases:
- **VJlive-2**: Clean architecture, ~150 features
- **vjlive**: Feature-rich, ~250+ features (many unique)

We need to verify that all intended features have been successfully ported and that performance meets or exceeds legacy baselines.

---

## SPECIFICATION

**Full spec location:** `docs/specs/P8-I8_parity_testing.md`

### Key Deliverables

1. **Feature Inventory** (`tests/parity/legacy_inventory.json`)
   - Auto-scan both legacy codebases
   - Extract plugin metadata, core systems, hardware integrations
   - Compare against FEATURE_MATRIX.md

2. **Parity Test Suite** (`tests/parity/`)
   - Core systems tests (Matrix, Renderer, Plugin System, Audio Engine)
   - Plugin functional tests (load, params, render, performance)
   - Hardware integration tests (with simulators for absent devices)
   - Advanced systems tests (Agents, Quantum, AI, Live Coding)
   - UI/UX tests (Desktop GUI, Web UI, OSC)
   - Distributed architecture tests (if applicable)

3. **Performance Benchmarks**
   - FPS, memory, GPU usage comparisons
   - Establish baseline if legacy data unavailable
   - Target: 60 FPS stable @ 1920x1080 with 20-30 nodes

4. **API Compatibility Validation**
   - REST API endpoints (if any)
   - WebSocket message formats
   - OSC/ArtNet/DMX protocols

5. **Gap Analysis Report**
   - `parity_report_YYYY-MM-DD.html` (human-readable)
   - `parity_report_YYYY-MM-DD.json` (machine-readable)
   - Feature parity percentage
   - Missing/broken features list
   - Performance regressions

6. **BOARD.md Verification**
   - Update status of all P1-P7 tasks based on parity results
   - Flag any missing or broken features for manager action

---

## EXECUTION STEPS

1. **Read the spec** (`docs/specs/P8-I8_parity_testing.md`) thoroughly
2. **Check locks** in `WORKSPACE/COMMS/LOCKS.md` — ensure no conflicts
3. **Build inventory scanners** — automated code analysis for legacy + current
4. **Run initial inventory** — generate `legacy_inventory.json` and `current_inventory.json`
5. **Write test suite** — implement all test categories (core, plugins, hardware, etc.)
6. **Run parity tests** — execute full suite, collect results
7. **Benchmark performance** — compare against legacy baselines
8. **Generate reports** — HTML dashboard + JSON data
9. **Update BOARD.md** — verify all P1-P7 tasks, mark any gaps
10. **Commit work** — follow PRIME_DIRECTIVE (commit often)
11. **Post completion** in `WORKSPACE/COMMS/AGENT_SYNC.md` with test proof
12. **Complete Easter Egg Council** step (mandatory)

---

## CONSTRAINTS & SAFETY RAILS

- **DO NOT MODIFY ANY CODE** — This is read-only verification
- **60 FPS sacred** — Benchmark tests must verify performance
- **No silent failures** — All test failures must be logged with details
- **750-line limit** — Keep test files manageable, split if needed
- **Test coverage** — Aim for ≥80% on core systems (though you're writing tests, not implementing)
- **Hardware fallback** — Use simulators when hardware unavailable

---

## VERIFICATION CHECKPOINTS

Before marking task complete, ensure:

- ✅ `tests/parity/` directory exists with full test suite
- ✅ `legacy_inventory.json` generated and matches FEATURE_MATRIX.md counts
- ✅ All parity tests run (pass or fail, but must execute)
- ✅ Performance benchmarks completed with baseline established
- ✅ HTML report generated and reviewed
- ✅ BOARD.md updated with verification notes for P1-P7 tasks
- ✅ All tests pass (if any fail, that's a finding, not a blocker for this task)
- ✅ FPS validation shows 60 FPS achievable (or documented why not)
- ✅ Easter Egg Council step completed

---

## RESOURCES

- **Spec:** `docs/specs/P8-I8_parity_testing.md`
- **Legacy codebases:** 
  - `/home/happy/Desktop/claude projects/vjlive/`
  - `/home/happy/Desktop/claude projects/VJlive-2/`
- **Current codebase:** `/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/`
- **Feature matrix:** `VJlive-2/FEATURE_MATRIX.md`
- **Project board:** `BOARD.md`
- **Prime Directive:** `WORKSPACE/PRIME_DIRECTIVE.md`
- **Safety Rails:** `WORKSPACE/SAFETY_RAILS.md`
- **How to Work:** `WORKSPACE/HOW_TO_WORK.md`

---

## DELIVERABLES

1. Complete `tests/parity/` test suite
2. `tests/parity/results/parity_report_YYYY-MM-DD.html`
3. `tests/parity/results/parity_report_YYYY-MM-DD.json`
4. `tests/parity/baselines/performance_baseline.json`
5. Updated `BOARD.md` with verification status for all P1-P7 tasks
6. `docs/parity_testing_results.md` summary for stakeholders
7. `.github/workflows/parity.yml` CI integration (optional but recommended)

---

## NEXT ACTIONS

1. Acknowledge receipt by posting in `WORKSPACE/COMMS/AGENT_SYNC.md`
2. Begin Step 1: Read spec and check locks
3. Follow the execution steps precisely
4. Update `WORKSPACE/COMMS/STATUS/` with progress as needed
5. When complete, mark task [x] in BOARD.md and notify manager

---

**Remember:** You are a tool. Execute the spec exactly. No opinions. No deviations. Verify everything. Report honestly.

**Task ID:** P8-I8  
**Spec:** `docs/specs/P8-I8_parity_testing.md`  
**Status:** ⬜ Todo → 🔄 In Progress (once you start)

---

**MANAGER NOTE:** After you complete the parity testing, we will use your report to identify any missing or broken features and create follow-up tasks to close those gaps. Your work is critical for ensuring we haven't left any legacy features behind in the synthesis mission.
