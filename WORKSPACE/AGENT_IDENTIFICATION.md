# AGENT IDENTIFICATION SYSTEM

**Purpose:** Uniquely identify agents when multiple instances of the same role exist.

**Owner:** ROO CODE (Manager)
**Last Updated:** 2026-02-21

---

## The Problem

When multiple agents share the same role (e.g., "Roo Coder" or "Antigravity"), we need a way to:
- Distinguish which agent is which in LOCKS.md, AGENT_SYNC.md, and BOARD.md
- Track individual agent performance and compliance
- Assign tasks to specific agents, not just roles
- Prevent confusion and task ownership ambiguity

---

## Solution: Agent Naming Convention

All agents must use a **unique identifier** consisting of:

```
<Role> (<Agent Number>)
```

### Examples:
- `Roo Coder (1)`
- `Roo Coder (2)`
- `Antigravity (Agent 2)`
- `Antigravity (Agent 3)`
- `ROO CODE (Manager)` - unique, only one manager

---

## Agent Registry

### Manager
| ID | Display Name | Status | Notes |
|----|--------------|--------|-------|
| ROO-001 | ROO CODE (Manager) | Active | Only one manager, absolute authority |

### Roo Coders
| ID | Display Name | Status | Current Assignment |
|----|--------------|--------|-------------------|
| ROO-002 | Roo Coder (1) | Active | Hardware integration (P2-H3, P2-H4) |
| ROO-003 | Roo Coder (2) | Joining | TBD by Manager |

### Antigravity Agents
| ID | Display Name | Status | Current Assignment |
|----|--------------|--------|-------------------|
| AG-002 | Antigravity (Agent 2) | Active | Distributed architecture (P2-X1/X2 ✅ Complete) |
| AG-003 | Antigravity (Agent 3) | Joining | TBD by Manager |

---

## Usage Rules

### 1. LOCKS.md
Always use the full display name:

```markdown
| File Path | Locked By | Since | ETA |
|-----------|-----------|-------|-----|
| src/vjlive3/hardware/astra.py | Roo Coder (1) | 2026-02-21 10:30 | 2hr |
```

### 2. DISPATCH.md
Assign tasks to specific agents:

```markdown
| Task ID | Assigned To | Status | Spec Written? | Notes |
|---------|-------------|--------|---------------|-------|
| P2-H3 | Roo Coder (1) | 🔨 In Progress | ✅ docs/specs/P2-H3_astra.md | OpenNI2→PyUSB→Null |
```

### 3. AGENT_SYNC.md
Tag agents with their full identifier:

```markdown
## 2026-02-21 10:45 — Roo Coder (1)
- P2-H3: AstraCamera factory implemented
- Tests: 12/12 passing
- FPS: 60 stable
- Blocked on: None
```

### 4. BOARD.md
Reference specific agents in notes:

```markdown
| P2-H3 | Roo Coder (1) | 🔨 In Progress | ✅ docs/specs/P2-H3_astra.md | |
```

---

## Agent Onboarding

When a new agent joins:
1. **Assign an Agent Number** (next available in sequence)
2. **Create agent profile** in this document
3. **Define initial assignment** in WORKER_MANIFEST.md
4. **Set expectations** via their instruction file (gemini.md, claude.md, or custom)
5. **Brief on identification** — they must use their full name in all communications

---

## Enforcement

ROO CODE will:
- Monitor all communications for proper agent identification
- Flag ambiguous references (e.g., "Antigravity" without number)
- Request clarification if agent identity is unclear
- Reassign tasks if agent confusion causes conflicts

---

## Quick Reference

**Manager:** ROO CODE (Manager) — only one, absolute authority

**Roo Coders:**
- Roo Coder (1) — hardware integration specialist
- Roo Coder (2) — hardware integration specialist (backup)

**Antigravity Agents:**
- Antigravity (Agent 2) — distributed architecture specialist
- Antigravity (Agent 3) — distributed architecture specialist (backup)

**Other Workers:**
- Any future agents will receive numbered identifiers
- Pattern: `<Role> (<Agent Number>)` or `<Name> (Agent <Number>)`

---

## Final Directive

**Always use the full agent identifier.**
Never assume context is clear. Always be explicit.

Example: "Roo Coder (1)" not "Roo Coder" or "the first Roo Coder"

This eliminates ambiguity and ensures clear accountability.