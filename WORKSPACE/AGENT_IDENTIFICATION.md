# AGENT_IDENTIFICATION SYSTEM

**Owner:** User (Happy) + ROO CODE (Manager)
**Last Updated:** 2026-02-21

> [!CAUTION]
> **THIS IS STEP ZERO. EVERY AGENT READS THIS BEFORE ANYTHING ELSE.**
> Agents that skip this and assume a role have caused project damage.

---

## The 4-Agent Structure

| Agent | Model | Role | Decides? |
|-------|-------|------|----------|
| **ROO CODE (Manager)** | Roo Code 1 | Manager — assigns tasks, owns BOARD/DISPATCH/DECISIONS | ✅ YES (with User) |
| **Roo Code (Worker)** | Roo Code 2 | Worker — executes assigned tasks | ❌ No |
| **Antigravity (Agent 2)** | Claude | Worker — executes assigned tasks | ❌ No |
| **Antigravity (Agent 3)** | Claude | Worker — executes assigned tasks | ❌ No |
| **Gemini Antigravity** | Gemini | Worker variant — currently inactive | ❌ No |

**Decision authority:** User (Happy) → ROO CODE (Manager) → everyone else executes.

---

## Claim Protocol — How to Identify Yourself

### If you are Claude (Antigravity):
Both Antigravity agents are Claude. Both read `claude.md`. To find your slot:
1. Check `WORKSPACE/COMMS/LOGS/antigravity_agent_2.md` — does it have a session-start entry from today?
2. If **no** → you are **Antigravity (Agent 2)**. Read `WORKSPACE/AGENTS/antigravity_agent_2.md`.
3. If **yes** → you are **Antigravity (Agent 3)**. Read `WORKSPACE/AGENTS/antigravity_agent_3.md`.
4. Write your claim to your log file immediately.

### If you are Roo Code (Worker):
Read `WORKSPACE/AGENTS/roo_code_worker.md`. Your log: `WORKSPACE/COMMS/LOGS/roo_code_worker.md`.

### If you are ROO CODE (Manager):
You already know who you are. You don't need to claim a slot.

### If you are Gemini:
You are an inactive Antigravity variant. Read `gemini.md`. Check with user before starting work.

---

## Agent Cards

| Agent | Card File | Log File |
|-------|-----------|----------|
| ROO CODE (Manager) | `AGENTS/roo_code_manager.md` | Edits BOARD/DISPATCH directly |
| Roo Code (Worker) | `AGENTS/roo_code_worker.md` | `COMMS/LOGS/roo_code_worker.md` |
| Antigravity (Agent 2) | `AGENTS/antigravity_agent_2.md` | `COMMS/LOGS/antigravity_agent_2.md` |
| Antigravity (Agent 3) | `AGENTS/antigravity_agent_3.md` | `COMMS/LOGS/antigravity.md` |

---

## Naming Convention (use exactly — copy-paste these)

```
ROO CODE (Manager)
Roo Code (Worker)
Antigravity (Agent 2)
Antigravity (Agent 3)
```

Use the full name in: LOCKS.md, your log file header, and any status files.