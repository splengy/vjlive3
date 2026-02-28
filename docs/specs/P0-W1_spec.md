# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-W1 — Manager Job Workflow Specification

**Phase:** Phase 0 / P0  
**Assigned To:** [Agent name]  
**Spec Written By:** [Agent name]  
**Date:** 2025-04-05

---

## What This Module Does

This module defines the operational and architectural rules governing how agents interact with the VJLive Reborn project. It establishes the foundational workflow for task creation, review, execution, and coordination across all team members. The specification ensures consistency in development practices, enforces quality gates (e.g., architecture-first design, testing, and running app), and provides a clear governance structure to prevent duplication or misalignment.

---

## What It Does NOT Do

- This document does not contain implementation code.
- It does not define specific agent behaviors beyond workflow rules.
- It does not provide technical specifications for individual modules or components.
- It is not a design document for features; it is a process and governance specification.
- It does not serve as a user interface guide or API reference.

---

## Public Interface

```python
# No public class/function signatures — this is a workflow specification, not an implementable module
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `BOARD.md` | file path | Source of truth for project status and task ownership | Must be updated after every task completion |
| `QUESTIONS.md` | file path | Channel for agents to raise unresolved questions | Agents must stop and write questions here if uncertain |
| `TASKS/BACKLOG/` | directory | Location where new tasks are created | Tasks follow naming convention: `PHASE-XX_TASK-NNN_short-description.md` |
| `TASKS/REVIEW/` | directory | Location for reviewing completed work | Review must include acceptance criteria, test results, and file boundaries |
| `LOCKS.md` | file path | Tracks current ownership of modules or features | Agents must check before modifying any domain |

---

## Edge Cases and Error Handling

- What happens if a task is created without following the naming convention? → Task will be rejected during review; agent must correct it in `TASKS/BACKLOG/`.  
- What happens if an agent fails to update `BOARD.md` after completing work? → The task remains unverified, and the agent may be flagged for process non-compliance.  
- What happens when a question is raised but not answered? → Task progress halts until a response is provided in `QUESTIONS.md`.  
- What if two agents try to modify the same module simultaneously? → Ownership is enforced via `LOCKS.md`; only the holder can proceed without explicit approval from the manager.  
- What if no one responds to a question after 24 hours? → The manager must intervene and either resolve or escalate.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - None — this is a governance document, not a technical implementation.  
- Internal modules this depends on:  
  - `vjlive1/.agent/workflows/manager-job.md` — serves as the primary source of rules and reference.  
  - `WORKSPACE/COMMS/BOARD.md`, `QUESTIONS.md`, `LOCKS.md`, `TASKS/BACKLOG/`, `TASKS/REVIEW/` — all are required for workflow execution.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_task_creation_naming_convention` | New tasks follow the correct naming format (`PHASE-XX_TASK-NNN_...`) |
| `test_board_update_after_completion` | After a task is reviewed and marked done, BOARD.md reflects updated status |
| `test_questions_resolution_deadline` | A question raised in QUESTIONS.md must be answered within 24 hours or escalated |
| `test_locks_prevent_concurrent_modification` | Only one agent can modify a locked module at a time; others must wait |
| `test_review_process_completeness` | Every review includes: acceptance criteria, test results, file boundaries, and app runtime status |

**Minimum coverage:** 100% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-W1: Manager Job Workflow Specification` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 0, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

See the following references in `vjlive1/.agent/workflows/manager-job.md`:

- **L1–20**: Defines the PRIME DIRECTIVE — VJLive Reborn Build Manager, establishing identity and core purpose.  
- **L17–36**: Lists core characteristics including 60fps as sacred, signal standard (0.0–10.0), state consistency, multi-node support, collaboration tiers, plugin system, agent memory, Lumen scripting, licensing model, and projection mapping.  
- **L33–52**: Outlines Rule 1 (Architecture Before Code), Rule 2 (Every Phase Ships a Running App), Rule 3 (Small Domains, Hard Boundaries), Rule 4 (Commit or Die), Rule 5 (Tests Are Not Optional).  
- **L49–68**: Details Rule 6 (No Salvage Without Inspection), Rule 7 (No Hallucinating Next Steps), and Rule 8 (The Board Is Truth).  
- **L65–84**: Describes the full workflow: starting a session, creating tasks, reviewing work, answering questions.  

All referenced rules are directly applicable to this specification. No gaps exist in legacy references for governance, process flow, or enforcement mechanisms. This spec is derived entirely from these foundational documents and does not introduce new assumptions beyond what is explicitly stated.