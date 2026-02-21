# Lock System Migration Plan

## Problem Statement
The current LOCKS.md system requires agents to edit a single shared markdown file, causing:
- File contention and pileups
- Manager bottleneck (agents wait for lock approvals)
- Race conditions when multiple agents try to edit simultaneously

## Proposed Solution: File-Based Lock Registry

Replace the shared LOCKS.md with a directory of individual lock files that can be created/deleted atomically.

### New Structure
```
WORKSPACE/COMMS/LOCKS/
  ├── by_file/           # Lock files keyed by file path
  │   ├── src_vjlive3_plugins_.lock
  │   ├── WORKSPACE_COMMS_DISPATCH.md.lock
  │   └── ...
  └── by_agent/          # Optional: agent-centric view
      ├── Roo_Coder_1.lock
      ├── Roo_Coder_2.lock
      └── Antigravity_Agent_3.lock
```

### Lock File Format
```
locked_by: Antigravity (Agent 3)
since: 2026-02-21 15:43
eta: 1hr
```

### Agent Protocol (Updated HOW_TO_WORK.md Step 2)

**Before editing ANY file:**

1. **Check for existing lock:**
   - Look in `WORKSPACE/COMMS/LOCKS/by_file/`
   - Convert target file path: replace `/` with `_`, remove leading `./` or `WORKSPACE/`
   - Example: `src/vjlive3/plugins/registry.py` → check for `src_vjlive3_plugins_registry.py.lock`

2. **If lock exists:**
   - Read contents to see who holds it and since when
   - If `since` > 2 hours ago → stale lock, you may claim it (overwrite)
   - If still valid → STOP, post in AGENT_SYNC.md: "BLOCKED: need <file> locked by <agent>"

3. **Claim the lock:**
   - Create lock file with proper format
   - Use atomic file creation (no race condition)
   - Do NOT check LOCKS.md anymore

4. **When finished:**
   - Delete your lock file
   - Never leave stale locks

### Manager Role
- Monitor `by_file/` directory for stale locks (>2hrs)
- No need to approve individual locks - agents self-manage
- Only intervene on conflicts or abuse

### Migration Steps

1. **Create directory structure:**
   ```bash
   mkdir -p WORKSPACE/COMMS/LOCKS/by_file
   ```

2. **Convert existing LOCKS.md entries to individual lock files:**
   - For each entry in LOCKS.md Active Locks table
   - Create corresponding `.lock` file in `by_file/`
   - Use exact format shown above

3. **Clear LOCKS.md** (or keep as historical reference only)

4. **Update HOW_TO_WORK.md** Step 2 with new protocol (see below)

5. **Notify agents** in AGENT_SYNC.md:
   ```
   LOCK SYSTEM UPDATE: Using file-based locks now. See HOW_TO_WORK.md Step 2.
   LOCKS.md is deprecated. Do not edit it.
   ```

6. **Test with one agent** before full rollout

### Updated HOW_TO_WORK.md Step 2 (Replace lines 26-35)

```markdown
## STEP 2 — CHECK THE LOCK

**Use the file-based lock system (no shared markdown editing):**

1. **Check if lock exists:** Look for `WORKSPACE/COMMS/LOCKS/by_file/<filepath>.lock`
   - Convert file path: replace `/` with `_` and remove leading `./` or `WORKSPACE/`
   - Example: `src/vjlive3/plugins/registry.py` → `src_vjlive3_plugins_registry.py.lock`
   - Example: `WORKSPACE/COMMS/DISPATCH.md` → `WORKSPACE_COMMS_DISPATCH.md.lock`

2. **If lock file exists:**
   - Read it to see who holds it and for how long
   - If `since` time is > 2 hours old → lock is stale, you may claim it (overwrite)
   - If still valid → STOP, post in `AGENT_SYNC.md` that you are blocked

3. **If no lock or stale lock → claim it:**
   - Create lock file with content:
   ```
   locked_by: Your Agent Name
   since: YYYY-MM-DD HH:MM
   eta: 30min (or 1hr, 2hr, etc.)
   ```
   - Use atomic file creation (no race condition possible)

4. **When done:**
   - Delete your lock file
   - Never leave stale locks

**Critical:** This system eliminates shared file editing. No agent should ever edit `LOCKS.md` directly.
```

### Benefits

- ✅ **No shared file contention** - each lock is independent
- ✅ **Atomic operations** - file creation/deletion is atomic at OS level
- ✅ **Autonomous** - agents self-assign without manager approval
- ✅ **Stale detection** - file mtime makes staleness obvious
- ✅ **Scalable** - adding more agents doesn't increase contention
- ✅ **Simple** - no markdown table parsing, just read/write files

### Rollback Plan

If issues arise, simply:
1. Stop agents from using new system
2. Revert to LOCKS.md (still intact)
3. Investigate and fix

---

**Status:** Ready for implementation. Requires manual file edits due to permission constraints.
