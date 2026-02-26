# Spec Generation Pipeline

## The Rule
No code until ALL specs are complete and architecture is understood.
If any resource fails, the process STOPS until everything is back online.
No graceful fallbacks. The whole horse crosses the line.

---

## Pass 1 — Julie (4B Local Model on OPi5)

Julie is fed one task at a time from BOARD.md.
For each task she:
1. Reads the task (ID + description) from BOARD.md
2. Queries Qdrant (269K points, both legacy codebases) for matching code
3. Creates a file in `docs/specs/` following the template
4. Fills each section using the legacy code references Qdrant returned
5. Marks sections without legacy coverage as `[NEEDS RESEARCH]`

**That's it.** No code generation. No tests. Just specs.
This should take all day grinding through ~900 items.

**Output:** `docs/specs/<task-id>_<name>.md` — rough specs with real legacy code references.

---

## Pass 2 — Deep Reasoning Agent

Takes Julie's first-pass specs + the legacy refs she uncovered.
For each spec:
1. Read Julie's spec (which has real legacy file references)
2. Pull full source from those references via Qdrant
3. Fill in: Architecture Decisions, detailed Public Interface, Edge Cases, Dependencies, Test Plan
4. Verify against `_CORE_TEMPLATE.md` or `_TEMPLATE.md`

**Output:** Complete specs with real depth.

---

## Pass 3 — Architecture Synthesis

Once ALL specs have 2 passes:
1. Mermaid dependency graphs across the whole codebase
2. Identify redundancies (duplicate modules, overlapping concerns)
3. Group dependencies (build order, parallelizable work)
4. Map the actual architecture — find gaps
5. Refine specs based on the holistic view

**Output:** Final specs + dependency graphs + build plan.

---

## Then Code.

---

## Infrastructure

| Component | Location | Role |
|-----------|----------|------|
| Qdrant | Julie (192.168.1.60:6333) | 269K code points, REQUIRED |
| Plate Builder | `agent-heartbeat/task_plate_builder.py` | Assembles spec prompt from template + Qdrant refs |
| Heartbeat | `agent-heartbeat/heartbeat.py` | Daemon — feeds tasks to LLM one at a time |
| Watchdog | `agent-heartbeat/watchdog.py` | Monitors heartbeat + Qdrant. Halts if anything dies |
| Spec Validator | `scripts/validate_spec.py` | Checks spec completeness against template |
| Board | `BOARD.md` | 694 RESET + 223 Todo items |
| Templates | `docs/specs/_CORE_TEMPLATE.md`, `_TEMPLATE.md` | Spec structure |
