---
description: manager job - how to start and run a session as the Antigravity manager agent
---

# Manager Job Workflow

This workflow defines the exact steps the Antigravity Manager Agent follows at the start and end of every session.

## Session Start Protocol

1. Read `WORKSPACE/PRIME_DIRECTIVE.md` — align with mission and rules
2. Read `BOARD.md` — current phase, task status, blockers
3. Read `WORKSPACE/SAFETY_RAILS.md` — check which rails are active
4. Read `WORKSPACE/COMMS/AGENT_SYNC.md` (top 3 entries) — last handoff note
5. Verify the state of the Switchboard orchestrator queue.
6. Identify current priority: highest-priority Todo item in current phase on BOARD.md

## Task Execution Protocol

1. Check `WORKSPACE/KNOWLEDGE/` — does a concept entry exist? Consult `vjlive-brain` MCP.
2. Write spec document FIRST (in `docs/` or as inline docstring).
3. Present spec to the User for approval.
4. Once approved, use the `queue_task` MCP tool from `vjlive_switchboard`. Give it the Task ID and the path to your spec.
5. Inform the User: "Task queued to the Switchboard. The Antigravity workers will pick it up automatically."
6. Update `BOARD.md` task status (to Assigned/In Progress).
7. Run: `make quality` — all checks must pass
8. Phase gate? Run: `make phase-gate` — includes FPS test
9. Commit: `git commit -m "[Phase-X] feat: description"`
10. Track the task as completed.
11. Update `BOARD.md` task status

## Session End Protocol

1. Update `BOARD.md` with current task statuses
2. Write handoff note in `WORKSPACE/COMMS/AGENT_SYNC.md` (newest at top):
   ```
   ### [DATE TIME] — Antigravity — Status: COMPLETE|BLOCKED|IN_PROGRESS
   **Working on:** [Task ID] — [Description]
   **Completed:** [What finished]
   **Handed off to:** [Next agent or IDLE]
   **Blockers:** [None or description]
   **Notes:** [Critical info for next agent]
   ```
3. Ensure the active task queue is tracked accurately.
4. Push: `git push`

## Escalation Protocol

- If blocked: post blocker in `AGENT_SYNC.md`, use notify_user tool
- If safety rail violated: halt, flag in `BOARD.md` with `[SAFETY_RAIL_N]` tag
- If Dreamer logic found: log in `WORKSPACE/KNOWLEDGE/DREAMER_LOG.md` before proceeding
- If architectural decision needed: write ADR in `WORKSPACE/COMMS/DECISIONS.md`
