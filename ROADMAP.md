# VJLive3 Short-Term Roadmap
**Updated:** 2026-02-25 13:10

## Current State
- **First pass** (NPU spec gen): RUNNING — 27/544 done, ~35 hrs remaining
- **Second pass** (Roo enrichment): READY — pipeline tools deployed, Roo on both OPis
- **Pipeline tools**: `spec_gate.py`, `pick_task.py`, `code_validator.py`, `ROO_INSTRUCTIONS.md`
- **Infrastructure**: Julie (.60) + Maxx (.50) mounted via SSHFS to `~/VJLive3`

## What Happens Next (in order)

### 1. Start Roo enrichment on both OPis — NOW
- Julie-Roo: `cat ~/VJLive3/agent-heartbeat/ROO_INSTRUCTIONS.md` → follow workflow
- Maxx-Roo: same
- Both enrich skeleton specs in parallel as first pass feeds them

### 2. First pass completes — ~36 hrs
- 544 skeleton specs land in `docs/specs/`
- Monitor: `python3 agent-heartbeat/spec_gate.py`

### 3. Second pass completes — Roo catches up
- All specs enriched with prose, scope, integration, performance
- Monitor: `python3 agent-heartbeat/spec_gate.py` (📖 enriched count)

### 4. Spec review gate
- Human reviews flagged specs (⚠️ needs_review)
- Fills remaining [NEEDS RESEARCH] gaps
- Signs off on quality

### 5. Code generation (THIRD pass — future)
- Antigravity generates code FROM enriched specs
- `code_validator.py` gates: syntax, stubs, pytest, 80% coverage
- One task at a time. No batching. No word salad.

## Rules (from incident reports)
- **No batching code gen** — one file at a time, verify before next
- **No `rm` commands** — ever
- **No self-enrichment** — Roo does the second pass, not Antigravity
- **No fabricated tests** — every test must exercise real logic
- **Read PRIME_DIRECTIVE.md** at session start
