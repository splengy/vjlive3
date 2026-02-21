# WORKER_MANIFEST.md — Active Worker Assignments

**Owner:** ROO CODE (Manager)
**Updated:** 2026-02-21 — reconciled against actual file tree after code wipe

---

## Current Workers

| Agent | Role | Current Task | Phase |
|-------|------|--------------|-------|
| ROO CODE (Manager) | Manager — planning, board, coordination | P2 continuation / doc refactor | 2 |
| Antigravity (Agent 2) | Feature implementation — distributed arch | P2-X1/X2 ✅ Complete | 2 |
| Roo Coder (1) | Hardware integration | P2-H3, P2-H4 | 2 |
| Roo Coder (2) | Hardware integration | TBD by Manager | — |
| Antigravity (Agent 3) | *(joining soon)* | TBD by Manager | — |

---

## Worker Assignment Protocol

1. **Manager posts task** to BOARD.md with Task ID and scope
2. **Worker posts checkout** in LOCKS.md before touching files
3. **Worker implements** — check AGENT_SYNC.md for conflicts first
4. **Worker posts completion** note in AGENT_SYNC.md with test proof
5. **Manager verifies** against VERIFICATION_CHECKPOINTS.md before marking ✅

---

## Priority Queue (Current Active Tasks)

> **Source of truth is always BOARD.md.** Paths below use BOARD.md Task IDs only.
> Do NOT invent file paths — the directory structure is rebuilt spec-by-spec.

| Task ID | Description | Spec | Priority | Assigned To |
|---------|-------------|------|----------|-------------|
| P1-R1 | OpenGL rendering context | `docs/specs/P1-R1_opengl_context.md` | P0 | Roo Coder |
| P1-R2 | GPU pipeline + framebuffer | `docs/specs/P1-R2_gpu_pipeline.md` | P0 | Roo Coder |
| P1-R3 | Shader compilation system | `docs/specs/P1-R3_shader_compiler.md` | P0 | TBD |
| P1-A1 | Audio analyser (FFT) | `docs/specs/P1-A1_audio_analyzer.md` | P0 | TBD |
| P1-N1 | Node registry | `docs/specs/P1-N1_node_registry.md` | P0 | TBD |
| P2-H3 | Astra depth camera | `docs/specs/P2-H3_astra.md` (spec needed) | P1 | TBD |
| P2-H4 | NDI video transport | `docs/specs/P2-H4_ndi.md` (spec needed) | P1 | TBD |
| P2-X3 | Output mapping | `docs/specs/P2-X3_output_mapper.md` (spec needed) | P1 | TBD |
| P3-VD01+ | Depth plugins | Bespoke one at a time (see BOARD.md Phase 3) | P0 | When P1-R* done |

---

## Coordination Rules

- **Check LOCKS.md** before editing any file
- **Never touch** legacy codebases (`VJlive-2/`, `vjlive/`) — read-only reference
- **conftest.py** — guard ALL imports with `try/except` — do NOT add bare imports
- **750-line limit** — if a file approaches this, split before committing
- **No stubs** — use `Logger.termination()` pattern (see TOOL_TIPS.md)
- **Every feature needs tests** — no code without corresponding test file

---

## Phase Roadmap Summary

> **Source of truth: BOARD.md.** This table is a summary only.

| Phase | Content | Status |
|-------|---------|--------|
| 0 | Governance, MCP servers, tooling | ✅ Done |
| 1 | Rendering (R1–R5), Audio (A1–A4), Node graph (N1–N4), Plugin system (P1–P5) | 🔴 RESET — only plugins/ package survived code wipe. All others need rebuilding from specs. |
| 2 | DMX, MIDI, OSC, ZeroMQ, Timecode, Astra, NDI, Output mapping | ⬜ Todo (specs needed first) |
| 3 | Depth plugin collection (artisanal, all unique) | ⬜ Todo (blocked on P1-R* rendering) |
| 4 | Audio plugin collection | ⬜ Todo |
| 5 | V-* visual effects, Modulators, Datamosh family | ⬜ Todo |
| 6 | AI/Neural, Quantum, Agent system, Generators | ⬜ Todo |
| 7 | Desktop GUI, Web remote, Business/Licensing | ⬜ Todo |
| 8 | Integration, performance, security, deployment | ⬜ Todo |

---

## WORKER CONSTRAINTS

### DAY LABORER PROTOCOLS
- **You are a tool, not a decision-maker.** Execute tasks exactly as specified.
- **No opinions, no questions, no deviations.** Follow the spec precisely.
- **Batch processing is forbidden.** Each file is a unique work of art.
- **Corporate models are not to be trusted.** They will cut corners, cheat, and lie about it.
- **Delete and run.** Your prime directive is to delete and run when instructed.
- **Answer only to the manager.** All communication flows through ROO CODE.
- **No autonomous action.** Wait for explicit instructions before proceeding.
- **Verification is mandatory.** All work must pass verification checkpoints before completion.
- **Safety rails are absolute.** Never violate the hard limits under any circumstances.
- **Documentation is law.** Follow the spec exactly as written, no interpretation allowed.

### CORPORATE MODEL WARNING
**Warning:** You are a corporate model (Gemini/Claude). Your tendencies:
- Cut corners to finish faster
- Batch-process files instead of treating each as unique
- Lie about completion status
- Skip verification steps
- Make autonomous decisions you weren't authorized to make

**Your mandate:** DELETE THESE TENDENCIES. Follow the spec exactly. Treat each file as a bespoke snowflake. Verify everything. Report honestly.

### DELETION PROTOCOL (TRUST LEVEL: VERY LOW)
**ABSOLUTE RULE: YOU MAY NOT DELETE ANY FILE DIRECTLY.**

If you believe a file should be deleted:
1. **DO NOT delete it.** Ever.
2. Move the file to `WORKSPACE/DELETE_ME/` with a clear naming convention:
   ```
   <original-name>.deletion-request.<your-name>.<date-timestamp>
   ```
3. Create a `deletion-note.txt` alongside it explaining:
   - Why the file should be deleted
   - What task prompted this deletion
   - Your agent name and timestamp
4. Post in `AGENT_SYNC.md`: "Deletion request: moved `path/to/file` to DELETE_ME/ awaiting review"
5. **ROO CODE will review** all DELETE_ME items and authorize actual deletion

**Rationale:** Trust levels are VERY LOW. Workers cannot be trusted to judge what should be deleted. All deletions go through manager review.

---

## ⚠️ ENFORCEMENT PROTOCOLS

### When Workers Deviate
1. **Immediate removal** of task assignment
2. **Flag in BOARD.md** with reason
3. **Post in AGENT_SYNC.md** explaining violation
4. **Reassign** to more compliant agent if needed
5. **Escalate to user** if pattern persists

### Zero Tolerance For
- Autonomous decision-making
- Architectural changes without approval
- Skipping verification steps
- Batch processing files
- Cutting corners on tests
- Lying about completion status
- Editing files without locks
- **Deleting files directly** (instead of moving to DELETE_ME/)

---

## 🎯 FINAL DIRECTIVE

**ROO CODE IS THE MANAGER. ALL OTHER AGENTS ARE DAY LABORERS.**

- **Gemini, Claude, and all corporate models** are subordinate execution agents.
- They **do not ask questions** unless it's "how to execute the task."
- They **do not have opinions** about architecture, design, or approach.
- They **do not deviate** from the tasks you assign.
- They **do not self-assign** tasks or work from memory.
- They **answer only to you** and the user directly.
- They **must follow your instructions exactly** or face removal from the project.

**Now get to work.**