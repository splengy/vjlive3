# LOCKS.md — File Check-In / Check-Out Registry

**Purpose:** Prevent agent collisions on the same file. ALWAYS check this before editing.
**Protocol:** Check out before editing, check in when committed.

> [!WARNING]
> If the file you want to edit is locked by another agent, do NOT edit it.
> Post to AGENT_SYNC.md or use `vjlive-switchboard` to coordinate.

## Active Locks

| File Path | Agent | Checked Out | ETA (mins) | Status |
|-----------|-------|-------------|------------|--------|
| *(no active locks)* | — | — | — | — |

---

## Lock Protocol

### Checking Out a File
1. Add a row to the Active Locks table above
2. If using MCP: `checkout_file(file_path, agent_id, eta_mins)`
3. Edit the file
4. Commit your changes

### Checking In a File
1. Remove the row from Active Locks
2. If using MCP: `checkin_file(file_path, agent_id)`
3. Write handoff note in AGENT_SYNC.md if handing off

### Lock Conflict Resolution
- Locks auto-expire after stated ETA (enforced by `vjlive-switchboard` server)
- If ETA has passed and no checkin: post in AGENT_SYNC.md, assume lock available after 15min
- Escalate to User if repeated conflicts on hot files

---

## Completed Lock History

| File Path | Agent | Duration | Completed |
|-----------|-------|----------|-----------|
| WORKSPACE/PRIME_DIRECTIVE.md | Antigravity | ~10min | 2026-02-20 |
| WORKSPACE/SAFETY_RAILS.md | Antigravity | ~10min | 2026-02-20 |
| WORKSPACE/COMMS/* | Antigravity | ~5min | 2026-02-20 |
| WORKSPACE/KNOWLEDGE/* | Antigravity | ~5min | 2026-02-20 |
