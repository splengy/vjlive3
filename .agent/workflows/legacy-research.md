---
description: Mandatory legacy code research — must be completed before writing or rewriting any spec
---

# /legacy-research — Legacy Code Research Protocol

> **This workflow is a prerequisite gate for every coding task in VJLive3.**
> No agent may write code for any module without first completing this workflow for that module.
> No agent may submit a spec without evidence from this workflow embedded in it.

---

## What This Is

VJLive3 is a port and synthesis of two working codebases:

```
/home/happy/Desktop/claude projects/vjlive/      ← v1 (Python + C++)
/home/happy/Desktop/claude projects/VJlive-2/    ← v2 (Python, more complete)
```

There are **~40-50GB of working code** across these two repos. Your job is to port the best version of what already exists — **not to invent anything from scratch**.

---

## Steps

// turbo-all

### Step 1 — Identify the module to research

Read your task assignment from your designated INBOX (e.g. `WORKSPACE/INBOXES/inbox_alpha.md`).
Note the Task ID (e.g. `P1-A3`), the module name, and the existing spec file path.

### Step 2 — Search v1 for matching code

```bash
grep -r "<module_keyword>" "/home/happy/Desktop/claude projects/vjlive/" \
  --include="*.py" -l 2>/dev/null | head -20
```

Replace `<module_keyword>` with the core concept (e.g. `audio_reactor`, `beat`, `plugin_loader`).
If nothing: try synonyms. Try directory-level exploration of `vjlive/core/`.

### Step 3 — Search v2 for matching code

```bash
grep -r "<module_keyword>" "/home/happy/Desktop/claude projects/VJlive-2/" \
  --include="*.py" -l 2>/dev/null | head -20
```

### Step 4 — Read every matching file in FULL

For each file found:
- Open it with `view_file`
- Read the ENTIRE file — not just the first few lines
- Note: class names, method signatures, data structures, algorithms, edge cases, threading, error handling

### Step 5 — Compare v1 and v2

Determine:
- Which version has the more complete implementation?
- What does v1 have that v2 dropped?
- What did v2 add that v1 didn't have?
- Are there bugs in either version worth fixing in the port?

### Step 6 — Document your findings in the spec

Open `docs/specs/<TASK_ID>_*.md`. Add or rewrite the `## Legacy Source` section:

```markdown
## Legacy Source

### v1: `vjlive/core/path/to/file.py`
- **Classes:** `AudioReactor(BeatConsumer)` with `on_beat()`, `get_smoothed_value()`
- **Key logic:** rolling average smoothing, exponential decay, 60fps update
- **Edge cases handled:** silence detection, BPM=0 guard
- **What v1 does well:** lightweight, no deps beyond numpy

### v2: `VJlive-2/core/audio_reactor.py`
- **Classes:** `AudioReactor` (enhanced), `ReactivityBus` (new in v2)
- **Key logic:** multi-channel routing, per-param smoothing curves, attack/release
- **What v2 adds:** multi-target routing, richer smoothing, thread-safe dispatch
- **What v2 drops:** nothing from v1

### Port Decision
Port v2 `ReactivityBus` as the primary architecture.
Preserve v1's lightweight `AudioReactor` as the single-channel fast-path.
```

### Step 7 — Rewrite the spec if needed

If the existing spec does not match what's actually in the legacy code:
- Rewrite it to reflect the real implementation
- Update public interface signatures to match what already works
- Flag anything in the spec that doesn't exist in either codebase as `[NEW — no legacy equivalent]`

### Step 8 — Post completion

In `WORKSPACE/COMMS/AGENT_SYNC.md`:

```
### [DATE] — [AGENT] — RESEARCH COMPLETE
**Task:** RESEARCH:P1-XX
**Found in v1:** path/to/file.py — [ClassName]
**Found in v2:** path/to/file.py — [ClassName]
**Port decision:** [v1/v2/merged — reason]
**Spec updated:** [yes/no — what changed]
**Ready for:** Coding task P1-XX can now proceed
```

---

## Rules

- ❌ Do NOT write any code during this task — research only
- ❌ Do NOT start the coding task until the Manager drops the execution task in your INBOX.
- ✅ DO quote actual code from the legacy files — copy class signatures verbatim
- ✅ DO flag every case where legacy code is missing as `[NEW — no legacy equivalent]`
- ✅ DO update the spec with real class/method names from the actual legacy code
