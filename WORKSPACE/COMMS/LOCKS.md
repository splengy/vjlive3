# LOCKS.md — File Lock Registry

**Check this before touching any file. Add your lock before editing. Remove when done.**

**Rule: If a file is listed here, you DO NOT touch it. Post in AGENT_SYNC.md that you are blocked.**

---

## Active Locks

| File Path | Locked By | Since | ETA |
|-----------|-----------|-------|-----|
| docs/specs/P1-A1_audio_analyzer.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 30min |
| docs/specs/P1-A2_beat_detector.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 30min |
| docs/specs/P1-A3_reactivity_bus.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 30min |
| docs/specs/P1-A4_audio_sources.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 30min |
| docs/specs/P1-P1_plugin_registry.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 1hr |
| docs/specs/P1-P2_plugin_loader.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 1hr |
| docs/specs/P1-P3_hot_reload.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 1hr |
| docs/specs/P1-P4_scanner.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 1hr |
| docs/specs/P1-N1_node_registry.md | Antigravity (Agent 3) | 2026-02-21 02:59 | 1hr |


---

## How to Lock

**Before editing ANY file:**
1. Check LOCKS.md for conflicts
2. If file is locked → STOP, post in AGENT_SYNC.md that you're blocked
3. If file is free → add your lock entry immediately

**Add a row when you start editing:**
```
| src/vjlive3/audio/analyzer.py | Antigravity | 2026-02-21 01:45 | 30min |
```

**Format:**
- **File Path:** Exact path relative to workspace
- **Locked By:** Your agent name (Antigravity, Roo Coder, etc.)
- **Since:** Current timestamp (YYYY-MM-DD HH:MM)
- **ETA:** Estimated time to complete (30min, 1hr, etc.)

---

## How to Unlock

**When your task is committed and done:**
1. Delete your lock entry from LOCKS.md
2. Post completion note in AGENT_SYNC.md
3. Update BOARD.md status to [x]

**Never leave locks stale.** If you can't complete within ETA, update the ETA or post in AGENT_SYNC.md.

---

## Conflict Protocol

**If you need a file that is locked:**
1. **DO NOT EDIT IT** - This is a hard rule
2. **Post in AGENT_SYNC.md:** "BLOCKED: need `path/to/file` locked by [Agent] since [time]"
3. **Wait for response** - Agent must respond within 2 hours
4. **If no response after 2 hours:** Post "STALE LOCK: [Agent] has had `path/to/file` locked since [time] with no update"

**Lock expiration:**
- Locks > 2 hours without update are considered stale
- You may post in AGENT_SYNC.md to claim stale locks
- ROO CODE will resolve conflicts and reassign if needed

---

## Enforcement Rules

**ROO CODE will:**
- Monitor all lock usage
- Remove stale locks after 2 hours
- Flag agents who violate lock protocol
- Reassign work if conflicts persist

**Workers must:**
- Check locks before every edit
- Add locks immediately when starting work
- Remove locks when done
- Never edit locked files
- Report conflicts properly

**Violations result in:**
- Immediate task removal
- Flag in BOARD.md
- Post in AGENT_SYNC.md explaining violation
- Possible reassignment to other agent
- Escalation to user if pattern persists

---

## Lock Hierarchy

**Critical files (never edit without explicit approval):**
- `WORKSPACE/PRIME_DIRECTIVE.md` - Hard lock, only ROO CODE can edit
- `WORKSPACE/ROO_CODE_MANAGER_INSTRUCTIONS.md` - Hard lock, only ROO CODE can edit
- `WORKSPACE/SAFETY_RAILS.md` - Hard lock, only ROO CODE can edit
- `WORKSPACE/VERIFICATION_CHECKPOINTS.md` - Hard lock, only ROO CODE can edit

**Standard files:**
- All source code files
- Test files
- Documentation files
- Spec files

**Locking order:**
1. Check if file is in critical lock list
2. Check if file is already locked
3. Add your lock if free
4. Start work immediately

---

## Final Directive

**The lock system is your protection.**
- It prevents conflicts
- It ensures accountability
- It enforces workflow

**If you violate the lock system:**
- You will be caught
- You will be flagged
- You will be removed

**Now check the locks before you touch anything.**