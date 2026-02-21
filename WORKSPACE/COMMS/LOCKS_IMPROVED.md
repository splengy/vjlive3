# Improved Lock System for Autonomous Execution

## Problem
Current LOCKS.md requires agents to edit a single shared markdown file, causing contention and requiring manager intervention.

## Solution: File-Based Lock Registry

Use individual lock files in a dedicated directory, allowing atomic operations without editing a shared file.

### Structure
```
WORKSPACE/COMMS/LOCKS/
  ├── active_locks.json (manager-maintained index, optional)
  ├── by_file/
  │   ├── src_vjlive3_plugins_.lock
  │   ├── WORKSPACE_COMMS_DISPATCH.md.lock
  │   └── ...
  └── by_agent/
      ├── Roo_Coder_1.lock
      ├── Roo_Coder_2.lock
      └── Antigravity_Agent_3.lock
```

### Agent Protocol (Autonomous)

1. **Check lock status** for a file by reading `LOCKS/by_file/<filepath>.lock` if it exists
2. **Claim lock** by creating the lock file with content:
   ```
   locked_by: Antigravity (Agent 3)
   since: 2026-02-21 23:50
   eta: 1hr
   ```
3. **Release lock** by deleting the lock file when done
4. **Handle conflicts**: If lock file exists and is older than 2 hours, it's stale - agent can claim it by overwriting

### Manager Role
- Monitor `LOCKS/by_file/` directory for stale locks
- Maintain `active_locks.json` index for quick overview (optional, can be generated)
- Resolve conflicts if two agents claim simultaneously (filesystem atomicity usually prevents this)

### Benefits
- No editing of shared file → no pileups
- Atomic file operations → no race conditions
- Easy to check staleness via file modification time
- Agents can work truly autonomously

### Migration
1. Create the new lock directory structure
2. Update HOW_TO_WORK.md with new protocol
3. Agents adopt new system immediately
4. Old LOCKS.md retained for historical reference only
