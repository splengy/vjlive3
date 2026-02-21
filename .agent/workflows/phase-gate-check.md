---
description: phase gate check - required steps before marking a phase complete and advancing
---

# Phase Gate Check Workflow

**"VJ apps are like kittens — you don't hand people a headless one."**

No phase is complete until this checklist passes in full. Do not update BOARD.md to `[x]` until every item is checked.

## The Kitten Check — Required for Every Phase Gate

### 1. App Window Visible
```bash
# Launch the app (from VJLive3_The_Reckoning directory)
python -m vjlive3.main

# Confirm:
# - Window opens (not headless, not CLI-only)
# - No crash on startup
# - Title bar shows correct phase/version
```
> **FAIL CONDITION:** If the window does not open, the phase is not complete. Period.

### 2. FPS Validation
```bash
# 60-second FPS test (runs via Makefile target)
make phase-gate

# If running manually:
python -m vjlive3.core.fps_test --duration 60 --resolution 1920x1080
# NOTE: fps_test module must exist; check BOARD.md for status.

# Acceptance criteria:
# ✅ Average FPS ≥ 58 (2-frame GC buffer)
# ✅ Frame time variance < 5ms
# ✅ No dropped frame runs longer than 100ms
# ✅ Memory usage stable (no upward trend over 60s)
```
> **FAIL CONDITION:** Average below 58 FPS → open `WORKSPACE/COMMS/PERFORMANCE_DEBUG.md` root cause
> **NOTE:** FPS test only applies once Phase 1 rendering (P1-R1–R5) is implemented.

### 3. Quality Gate
```bash
make quality
# Runs: ruff, mypy, check_stubs, check_file_size, pytest --cov
# ALL must pass — zero exceptions
```

### 4. Silicon Sigil Verification
> **⚠️ STATUS:** `vjlive3.core.sigil` was part of the Phase 0 code and is currently in `WORKSPACE/DELETE_ME/`.
> This check is **BLOCKED** until `src/vjlive3/core/sigil.py` is restored/rebuilt as part of Phase 1 core infrastructure.
> When the module exists, run:
```bash
python -c "from vjlive3.core.sigil import sigil; sigil.verify()"
# Must output: "Silicon Sigil verified. The process continues."
```

### 5. BOARD.md Update
- Mark all phase tasks `[x]`
- Add phase completion timestamp
- Set next phase tasks to `Todo`

### 6. AGENT_SYNC.md Handoff Note
Write a phase completion note (newest at top):
```
### [DATE] — [AgentName] — Status: PHASE COMPLETE
**Phase:** Phase N — [Phase Name]
**Completed:** All tasks per BOARD.md
**FPS validation:** XX.X avg over 60s — PASS
**Kitten check:** Window running ✅
**Handed off to:** [Next agent / IDLE]
**Notes:** [Phase summary, anything to know going in to the next phase]
```

### 7. Git Tag
```bash
git add -A
git commit -m "[Phase-N] ✅ Phase N complete — <summary>"
git tag -a "phase-N-complete" -m "Phase N: <title> — FPS: XX, Coverage: XX%"
git push && git push --tags
```

## Phase 0 Specific Gate

Phase 0 is complete when:
- [ ] Status window shows: live FPS · memory · active agents · phase checklist
- [ ] Silicon Sigil verified on startup
- [ ] MCP servers (vjlive-brain + vjlive-switchboard) start without error
- [ ] Pre-commit hooks install and pass on clean codebase
- [ ] BOARD.md Phase 0 all `[x]`
- [ ] FPS ≥ 58 with status window running

## Escalation

If any gate item fails:
1. Do NOT advance the phase
2. Flag in BOARD.md with `⚠️ PHASE GATE BLOCKED — [reason]`
3. Post blocker in AGENT_SYNC.md
4. Notify User via `notify_user` tool if blocked more than 30 minutes
