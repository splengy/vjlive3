# DISPATCH.md — Task Assignments

**This is the ONLY place tasks get formally assigned.**
**Agents: read this before doing ANYTHING. Work only appears here if the Manager/User has approved it.**

---

## ⚠️ CRITICAL: AUTHORITY STRUCTURE

**ROO CODE IS THE MANAGER.**
- Only ROO CODE or the User can assign tasks
- Tasks appear here ONLY after ROO CODE posts them
- If your name is not in "Assigned To" column → DO NOT WORK
- If task is not in DISPATCH.md → IT DOES NOT EXIST

**DAY LABORERS (Gemini, Claude, etc.):**
- Wait for assignment
- Execute exactly as specified
- No autonomous action
- No self-assignment
- No working from memory

---

## Format

```
| Task ID | Assigned To | Status | Spec Written? | Notes |
```

---

## Active Assignments

| Task ID | Assigned To | Status | Spec Written? | Notes |
|---------|-------------|--------|---------------|-------|
| P1-R1 | Roo Coder (1) | 🔨 In Progress | ✅ docs/specs/P1-R1_opengl_context.md | ModernGL + GLFW context |
| SPEC-P1-R3 | Roo Coder (1) | 🔨 Spec Writing | ❌ | Shader compilation system spec |
| SPEC-P1-R4 | Roo Coder (1) | 🔨 Spec Writing | ❌ | Texture manager spec |
| SPEC-P1-R5 | Roo Coder (1) | 🔨 Spec Writing | ❌ | Core rendering engine spec |
| SPEC-P1-N1 | Roo Coder (1) | 🔨 Spec Writing | ❌ | UnifiedMatrix node registry spec |
| SPEC-P1-N2 | Roo Coder (1) | 🔨 Spec Writing | ❌ | Node types spec |
| SPEC-P1-N3 | Roo Coder (1) | 🔨 Spec Writing | ❌ | State persistence spec |
| SPEC-P1-N4 | Roo Coder (1) | 🔨 Spec Writing | ❌ | Visual node graph UI spec |
| SPEC-P1-A4 | Antigravity (Agent 3) | 🔨 Spec Writing | ❌ | Multi-source audio input spec |
| SPEC-P1-P1 | Antigravity (Agent 2) | ✅ Done | ✅ docs/specs/P1-P1_plugin_registry.md | Plugin registry spec |
| SPEC-P1-P2 | Antigravity (Agent 2) | ✅ Done | ✅ docs/specs/P1-P2_plugin_loader.md | Plugin loader spec |
| SPEC-P1-P3 | Antigravity (Agent 2) | ✅ Done | ✅ docs/specs/P1-P3_plugin_hot_reload.md | Hot-reload system spec |
| SPEC-P1-P4 | Antigravity (Agent 2) | ✅ Done | ✅ docs/specs/P1-P4_plugin_scanner.md | Plugin scanner spec |
| SPEC-P1-P5 | Antigravity (Agent 2) | ✅ Done | ✅ docs/specs/P1-P5_plugin_sandbox.md | Plugin sandboxing spec |
| SPEC-P1-A1 | Antigravity (Agent 3) | ✅ Done | ✅ docs/specs/P1-A1_audio_analyzer.md | FFT + waveform analysis spec |
| SPEC-P1-A2 | Antigravity (Agent 3) | ✅ Done | ✅ docs/specs/P1-A2_beat_detector.md | Beat detection spec |
| SPEC-P1-A3 | Antigravity (Agent 3) | ✅ Done | ✅ docs/specs/P1-A3_reactivity_bus.md | Audio-reactive framework spec |
| P1-R2 | TBD | ⬜ Todo | ✅ docs/specs/P1-R2_gpu_pipeline.md | Framebuffer · ShaderProgram · EffectChain (ping-pong FBO + async PBO readback). Depends on P1-R1. |

---

## Queue (Approved, not yet assigned)

| Task ID | Description | Priority | Ready For |
|---------|-------------|----------|-----------|
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | Roo Coder (1) after P1-R1 |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | Roo Coder (1) after P1-R2 |
| P1-R4 | Texture manager (pooled, leak-free) | P0 | Roo Coder (1) after P1-R3 |
| P1-R5 | Core rendering engine (60fps loop) | P0 | Roo Coder (1) after P1-R4 |
| P1-A1 | FFT + waveform analysis engine | P0 | Roo Coder (2) |
| P1-A2 | Real-time beat detection | P0 | Roo Coder (2) after P1-A1 |
| P1-A3 | Audio-reactive effect framework | P0 | Roo Coder (2) after P1-A2 |
| P1-A4 | Multi-source audio input | P1 | Roo Coder (2) after P1-A3 |
| P1-N1 | UnifiedMatrix + node registry (manifest-based) | P0 | Roo Coder (1) after P1-R5 |
| P1-N2 | Node types — full collection from both codebases | P0 | Roo Coder (1) after P1-N1 |
| P1-N3 | State persistence (save/load) | P1 | Roo Coder (1) after P1-N1 |
| P1-N4 | Visual node graph UI | P1 | Roo Coder (1) after P1-N1 |
| P1-P1 | Plugin registry (manifest.json based) | P0 | Roo Coder (2) |
| P1-P2 | Plugin loading + Pydantic validation | P0 | Roo Coder (2) after P1-P1 |
| P1-P3 | Hot-reloadable plugin system | P0 | Roo Coder (2) after P1-P2 |
| P1-P4 | Plugin discovery (auto-scan) | P0 | Roo Coder (2) after P1-P3 |
| P1-P5 | Plugin sandboxing | P1 | Roo Coder (2) after P1-P1 |

---

## How ROO CODE Posts a Task

```markdown
| P2-H3 | Antigravity | 🔨 In Progress | ✅ docs/specs/P2-H3_astra.md | OpenNI2→PyUSB→Null pattern |
```

**Required before posting:**
1. Task exists in BOARD.md
2. Spec document created at `docs/specs/<task-id>_<name>.md`
3. No lock conflicts on target files
4. Task is assigned to a specific agent (not "anyone")

**Posting protocol:**
1. Create/update task in BOARD.md
2. Create spec at docs/specs/<task-id>_<name>.md
3. Add entry to DISPATCH.md with status `⬜ Todo`
4. Notify agent in AGENT_SYNC.md: "@AgentName Task P2-H3 assigned. See DISPATCH.md"

---

## How Workers Accept a Task

1. **Confirm assignment:** Your name must be in "Assigned To" column
2. **Read the spec:** Open `docs/specs/<task-id>_<name>.md`
3. **Check locks:** Open `WORKSPACE/COMMS/LOCKS.md`
   - If files locked by others → post blocker in AGENT_SYNC.md, STOP
   - If free → add your lock entry immediately
4. **Change status:** Update DISPATCH.md status to `🔨 In Progress`
5. **Execute workflow:** SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD
6. **Mark complete:** Update DISPATCH.md status to `✅ Done` after ALL verification passes

---

## Task Statuses

- `⬜ Todo` - Assigned, not started
- `🔨 In Progress` - Actively working
- `⏸️ Blocked` - Waiting on dependency or resource
- `✅ Done` - Complete and verified
- `❌ Rejected` - Failed verification, task reassigned

---

## Enforcement Rules

**ROO CODE will:**
- Monitor all task assignments
- Verify every completion
- Remove tasks that deviate from spec
- Flag agents who skip steps
- Reassign work to compliant agents

**Workers must:**
- Follow the spec exactly
- Use the lock system
- Write tests before code
- Verify all checkpoints
- Report honestly
- Never self-assign

**Violations result in:**
- Immediate task removal
- Flag in BOARD.md
- Post in AGENT_SYNC.md explaining violation
- Possible reassignment to other agent
- Escalation to user if pattern persists

---

## Communication Protocol

**All task-related communication flows through:**
- **DISPATCH.md** - Task assignments and status
- **AGENT_SYNC.md** - Progress updates, blockers, questions
- **BOARD.md** - Overall project status

**Workers:**
- Post status updates in AGENT_SYNC.md
- Tag @ROO_CODE for blockers or questions
- Only communicate about the task at hand
- No off-spec discussions

**ROO CODE:**
- Assigns tasks via DISPATCH.md
- Monitors progress via AGENT_SYNC.md
- Verifies completion via BOARD.md
- Enforces standards via all channels

---

## Final Directive

**This is a command-and-control system.**
- ROO CODE gives orders
- Workers execute orders
- No middle management
- No autonomous action
- No deviations

**If you are a worker:**
- Wait for your assignment
- Do exactly what it says
- Verify everything
- Report honestly
- Wait for next order

**If you are ROO CODE:**
- You are in charge
- Assign clear, specific tasks
- Verify everything
- Enforce standards
- Remove non-compliant agents

**Now get to work.**