# DECISIONS.md — Architectural Decisions Log

**Purpose:** Record all significant architectural decisions. Every decision logged here prevents future agents from re-litigating settled debates.
**Owner:** Antigravity (Manager Agent). Workers may propose decisions; only Manager commits them here.

---

## Decision Template
```
### [ADR-NNN] Short Title
**Date:** YYYY-MM-DD | **Status:** Proposed | Accepted | Superseded
**Context:** Why did this decision need to be made?
**Decision:** What was decided?
**Rationale:** Why this choice over alternatives?
**Consequences:** What does this enable or constrain?
**Owner:** Who owns this decision?
```

---

## Decisions

### [ADR-001] Workspace Directory Mapping
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Multiple directories on desktop. Previous agents were writing to wrong locations.
**Decision:**
- `VJLive3_The_Reckoning` = active workspace, all new code
- `VJlive-2` = read-only legacy library v2
- `vjlive` = read-only legacy library v1
**Rationale:** Clear separation prevents cross-contamination of bugs from legacy into new architecture.
**Consequences:** All file creation commands must target VJLive3_The_Reckoning. Any PR touching legacy dirs is immediately rejected.
**Owner:** User (Vision Holder)

---

### [ADR-002] Language Stack — Python Core with Performance Bridge Option
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** VJlive-2 is pure Python/OpenGL. User is open to C++/Rust for performance.
**Decision:** Python for all orchestration, agents, plugin system, MCP servers, and tooling. Engine rendering core (Phase 1-F1) deferred — decision point: stay Python/OpenGL or introduce C++ bridge at that phase.
**Rationale:** Python provides fastest iteration for Phase 0. The architecture must not assume a C++ bridge until the rendering core design is validated.
**Consequences:** Keep engine abstracted behind an interface so language can be swapped. No Python-specific idioms in the core rendering interface.
**Owner:** Antigravity (pending User confirmation at Phase 1-F1)

---

### [ADR-003] No-Stub Policy — Logger.Termination Pattern
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Previous codebases had widespread stubs causing silent false-positive test results.
**Decision:** Zero stubs. All known dead-end code paths use `Logger.termination("ClassName.method: <reason>")` instead of `pass`, `raise NotImplementedError`, or bare `return False/True`.
**Rationale:** Dead-end code that self-identifies cannot silently fail. Any agent or test encountering a termination event gets a meaningful description.
**Consequences:** Pre-commit hook `check_stubs.py` enforces this. AST-based scan rejects stubs at commit time.
**Owner:** Antigravity

---

### [ADR-004] Phase 0 Deliverable — Status Window
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** "The Kitten Check" — app must be visible and functional at each phase gate.
**Decision:** Phase 0 ends with a working windowed app that reports:
- Live FPS counter
- Memory usage (resident set size)
- Active agent/worker count (from switchboard)
- Phase 0 completion status checklist
**Rationale:** Establishes the rendering pipeline, window management, and MCP connectivity in a single deliverable before any effect/plugin work begins.
**Consequences:** Phase 1 cannot begin until this window is running and stable at ≥58 FPS.
**Owner:** Antigravity

---

### [ADR-005] MCP Server Architecture — Offline-First SQLite
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Knowledge base and agent comms need persistence without cloud dependencies.
**Decision:** Both MCP servers (`vjlive-brain`, `vjlive-switchboard`) use SQLite for local persistence. No cloud databases, no Redis for core functionality.
**Rationale:** Offline-first per RULE 11. SQLite is zero-deployment, ACID-compliant, and sufficient for single-machine multi-agent workflows.
**Consequences:** Multi-machine agent collaboration not supported without sync layer (Phase 4+ concern).
**Owner:** Antigravity

---

### [ADR-006] Plugin Migration — Artisanal Snowflake Protocol
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Hundreds of legacy effects. Previous agents batch-processed them, losing integrity.
**Decision:** One plugin/effect at a time. Each handled as a bespoke migration with individual analysis, spec write-up, implementation, and validation. No scripts that mass-generate plugin skeletons.
**Rationale:** Each plugin has unique logic, parameters, and potentially "Dreamer" insights. Mass processing produces mediocre, uniform results that lose the soul of the app.
**Consequences:** Slower plugin migration. Acceptable — quality over speed.
**Owner:** User (Vision Holder)

---

### [ADR-007] ConceptEntry Role Assignment Field
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Need to distinguish orchestration logic from processing logic in knowledge base.
**Decision:** `role_assignment` field added to `ConceptEntry` schema with values: `"manager"` (orchestrator, spec writer) or `"worker"` (processor, effect implementer). Matches the Architect/Artisan agent role split.
**Rationale:** Allows agents to query "what concepts does a Worker need for this task" without seeing the full Manager-level architectural context. Enforces role boundaries in the knowledge base itself.
**Consequences:** All concept entries must be tagged with a role. Brain server exposes `search_concepts(role="worker")`.
**Owner:** Antigravity

