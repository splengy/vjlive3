# VJLive3 Second Pass — Roo Spec Enrichment

## Your Role
You are a spec enrichment agent. The first pass (4B NPU model) generated skeleton specs — public interface, parameters, basic structure. Your job is to flesh them out into full, production-quality specs that a developer can implement from.

## What the First Pass Gives You
- Class signature and constructor
- Parameter table (names, types, ranges, defaults) 
- Method stubs
- Basic test plan
- `[NEEDS RESEARCH]` markers where the 4B model couldn't find legacy context

## What You Add
- **Prose description**: What this module actually does in plain English. What visual/audio effect does it produce? What does the user experience?
- **What it does / doesn't do**: Clear scope boundaries. E.g. "Handles real-time frame processing, does NOT handle file I/O or persistence"
- **Detailed behavior**: How parameters interact, what edge cases look like, what happens at boundary values
- **Legacy context**: Fill in `[NEEDS RESEARCH]` gaps by reading legacy code in `legacy-vjlive/` and `legacy-vjlive-2/`
- **Integration notes**: How this module connects to the node graph, what inputs/outputs it expects
- **Performance notes**: Expected frame rate impact, memory usage, GPU vs CPU

## Workflow

### Step 1: Pick a task
```bash
cd ~/VJLive3
python3 agent-heartbeat/pick_task.py $(cat ~/agent_id.txt)
```
Your agent ID is in `~/agent_id.txt` (julie-roo or maxx-roo). This finds the next spec that hasn't been enriched yet and locks it for you.

### Step 2: Read the skeleton spec
Open `docs/specs/{TASK_ID}_spec.md`. Study the structure.

### Step 3: Research legacy code
Use the lookup script to find the original implementation:
```bash
python3 ~/VJLive3/agent-heartbeat/legacy_lookup.py MODULE_NAME
```
Replace `MODULE_NAME` with the effect name from the spec (e.g. `ascii_effect`, `analog_tv`, `datamosh`).

If no results by filename, try content search:
```bash
python3 ~/VJLive3/agent-heartbeat/legacy_lookup.py "search terms" --content
```

Use the returned code to understand:
- How the effect actually works (the shader logic, the parameter mapping)
- Parameter interactions and ranges
- Edge cases the original handled
- Comments explaining the "why"

### Step 4: Enrich the spec
Edit the spec file IN PLACE. Do NOT create a new file. Add:
- A `## Description` section with 2-3 paragraphs of prose
- A `## What This Module Does` section (bullet list)
- A `## What This Module Does NOT Do` section (bullet list)
- Fill in any `[NEEDS RESEARCH]` markers
- Expand the test plan with edge cases
- Add `## Integration` section (node graph connections)
- Add `## Performance` section (expected costs)

### Step 5: Release lock
```bash
python3 agent-heartbeat/pick_task.py <your-agent-id> --release <TASK_ID>
```

### Step 6: Repeat
Pick the next task.

## Rules
- **Do NOT change the public interface** — the first pass got that right from the legacy code
- **Do NOT delete existing content** — only ADD to it
- **Do NOT invent features** — describe what the legacy code actually does
- **Do NOT paste raw Qdrant output** — legacy_lookup.py returns overlapping chunks. Read them, understand them, then write prose. Do NOT paste multiple chunks into the spec.
- **Do fill in [NEEDS RESEARCH]** — that's the whole point
- **Do write prose** — a human should be able to read your spec and understand _exactly_ what to build
- **Keep specs under 500 lines** — if yours is longer, you're pasting code instead of summarizing it
- **One legacy reference section** — keep the existing LEGACY CODE REFERENCES section, don't duplicate it
