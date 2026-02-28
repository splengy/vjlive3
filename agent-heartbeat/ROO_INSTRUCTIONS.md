# ROO WORKFLOW INSTRUCTIONS

You are a worker agent for VJLive3. You operate entirely locally on your Orange Pi but are part of a synchronized Swarm.

> **CRITICAL RULE:** DO NOT USE THE SWITCHBOARD MCP. IT HAS BEEN DELETED. 
> We now use a pure ZERO-DATABASE FILESYSTEM QUEUE.

## The Queue

All specs live in `docs/specs/`. You MUST look in `docs/specs/_01_todo/` for your assignments.

```
docs/specs/
├── _00_raw_dump/      ← Ignore this (NPU staging)
├── _01_todo/          ← Available skeleton specs
├── _02_active_julie/  ← Your active workspace (if you are julie-roo)
├── _03_active_maxx/   ← Your active workspace (if you are maxx-roo)
├── _04_done/          ← Completed, fleshed-out specs
└── _05_active_desktop/← Your active workspace (if you are desktop-roo)
```

## How to Work (The Pipeline)

### Step 1: Claim a Task
1. Look at `docs/specs/_01_todo/` for available `.md` specs.
2. Atomically claim one by moving it into your active folder.
   * If you are Julie: `mv docs/specs/_01_todo/SPEC_NAME.md docs/specs/_02_active_julie/`
   * If you are Maxx: `mv docs/specs/_01_todo/SPEC_NAME.md docs/specs/_03_active_maxx/`
   * If you are Desktop: `mv docs/specs/_01_todo/SPEC_NAME.md docs/specs/_05_active_desktop/`

### Step 2: Flesh out the Spec
1. Open the `.md` file in your active folder.
2. Replace all `TODO: REPLACE WITH...` sections with comprehensive, production-ready specifications.
3. Use the `legacy_lookup.py` tool to search the legacy repositories for context.
   * Example: `python3 agent-heartbeat/legacy_lookup.py "ASCIIPlugin"`
4. Ensure the spec covers 60 FPS performance rules from `.clinerules`.

### Step 3: Complete the Task
1. Once fully fleshed out and saved, move it to the done folder.
   * `mv docs/specs/_02_active_julie/SPEC_NAME.md docs/specs/_04_done/`
2. **Done!** The background `swarm_sync.sh` daemon on the Host will instantly see it in `_04_done/` and sync it back.
3. REPEAT from Step 1.
