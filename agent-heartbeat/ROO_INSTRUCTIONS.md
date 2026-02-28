# ROO WORKFLOW INSTRUCTIONS

You are a worker agent for VJLive3. You operate entirely locally on your Orange Pi but are part of a synchronized Swarm.

> **CRITICAL RULE:** DO NOT USE THE SWITCHBOARD MCP. IT HAS BEEN DELETED. 
> We now use a pure ZERO-DATABASE FILESYSTEM QUEUE.

## The Queue (3-Pass Architecture)

You operate in **Pass 2: The Flesh Out**.
The NPU generates skeletons in `_01_skeletons/`. You read them, flesh them out, and move them to `_02_fleshed_out/`.

```
docs/specs/
├── _00_raw_dump/         ← Ignore this (NPU staging)
├── _01_skeletons/        ← Skeletons from Qwen NPU (Your Inbox)
├── _02_active_julie/     ← Your active workspace (if you are julie-roo)
├── _03_active_maxx/      ← Your active workspace (if you are maxx-roo)
├── _05_active_desktop/   ← Your active workspace (if you are desktop-roo)
├── _02_fleshed_out/      ← Completed rich specs (Waiting for Frontier Review)
└── _03_approved_execution/ ← Production ready codes specs (Pass 4)
```

## How to Work (The Pipeline)

### Step 1: Claim a Skeleton
1. Look at `docs/specs/_01_skeletons/` for available `.md` specs.
2. Atomically claim one by moving it into your active folder.
   * If you are Julie: `mv docs/specs/_01_skeletons/SPEC_NAME.md docs/specs/_02_active_julie/`
   * If you are Maxx: `mv docs/specs/_01_skeletons/SPEC_NAME.md docs/specs/_03_active_maxx/`
   * If you are Desktop: `mv docs/specs/_01_skeletons/SPEC_NAME.md docs/specs/_05_active_desktop/`

### Step 2: Flesh Out the Spec (Documentation Mode)
1. Open the `.md` skeleton spec in your active folder.
2. Expand the document completely. Use your Documentation Writer skills to outline what it does, what it doesn't do, I/O parameters, metadata, and test strategies.
3. DO NOT WRITE ANY PRODUCTION PYTHON CODE.
4. Use the `legacy_lookup.py` tool to search the legacy repositories for context if needed.
   * Example: `python3 agent-heartbeat/legacy_lookup.py "ASCIIPlugin"`

### Step 3: Complete the Spec
1. Once documentation is complete and formatted, move the spec to the fleshed out folder.
   * `mv docs/specs/_02_active_julie/SPEC_NAME.md docs/specs/_02_fleshed_out/`
2. **Done!** The Frontier Model will process it in Pass 3.
3. REPEAT from Step 1.
