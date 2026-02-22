# Implementation Tasks — Phase 7 Business

**Assigned By:** Manager-Gemini-3.1
**Date:** 2026-02-22
**Priority:** P0-P1 — Complete Phase 7 Business collection

---

## Context

Phase 7 requires porting 4 business modules from the legacy VJlive-2 codebase. All specifications have been created and approved. These are business infrastructure modules for licensing, marketplace, analytics, and updates.

---

## Task List

### P7-B1: License Server (JWT + RBAC)

**Spec:** `docs/specs/phase7_business/P7-B1_License_Server.md`
**Priority:** P0
**Dependencies:** pyjwt, sqlite3/sqlalchemy
**Test coverage:** ≥80%

### P7-B2: Plugin Marketplace Integration

**Spec:** `docs/specs/phase7_business/P7-B2_Plugin_Marketplace.md`
**Priority:** P0
**Dependencies:** requests, aiohttp
**Test coverage:** ≥80%

### P7-B3: Analytics Dashboard

**Spec:** `docs/specs/phase7_business/P7-B3_Analytics_Dashboard.md`
**Priority:** P1
**Dependencies:** sqlite3/sqlalchemy, pandas
**Test coverage:** ≥80%

### P7-B4: Update Server (Delta Patches)

**Spec:** `docs/specs/phase7_business/P7-B4_Update_Server.md`
**Priority:** P1
**Dependencies:** requests, cryptography
**Test coverage:** ≥80%

---

## Instructions

1. Read each specification file thoroughly before starting implementation.
2. Implement modules in order: P7-B1 through P7-B4.
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

- These are **business** modules — security and reliability are critical.
- All modules must conform to the `PluginBase` interface in `src/vjlive3/plugins/api.py`.
- Parameter ranges and defaults must match the legacy manifest specifications exactly.
- Ensure proper handling of edge cases: security vulnerabilities, data corruption, network failures.

---

## Verification

After completing each module:
1. Run tests: `pytest tests/plugins/test_<plugin_name>.py`
2. Check coverage: `pytest --cov=src/vjlive3/plugins`
3. Update `BOARD.md` status to ✅ Done
4. Write completion note in `WORKSPACE/COMMS/STATUS/P7-<task-id>.txt`
5. Create `task_completion_P7-<task-id>.md` with summary

---

**Begin implementation. Report progress via AGENT_SYNC.md.**