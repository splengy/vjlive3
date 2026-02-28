# VJLive3: The 3-Pass Architectural Rulebook
**STATUS: IRONCLAD CONSTITUTION**
**TARGET AUDIENCE: ANTIGRAVITY (OVERSEER) & ROO CODE (WORKERS)**

> [!CAUTION]
> **READ THIS BEFORE TAKING ANY ACTION.**
> The previous Antigravity agent hallucinated a completely different architecture, ignored the Qdrant database, and deleted the user's tracking board containing 1,000+ plugins. **You are strictly forbidden from altering this architecture, deleting BOARD.md, or bypassing the pass-gates.**

## 1. The Source of Truth
The legacy codebase of 1000+ plugins (the project's payload) does **NOT** exist in the local SQLite database (`vjlive3brain.sqlite`).
The **TRUE Source of Knowledge** is the Qdrant Vector Database running on the NPU node **Maxx (`192.168.1.60:6333`)**.
- Collection: `vjlive_code`
- **DO NOT** attempt to guess, hallucinate, or rewrite legacy implementations from scratch. If you need a legacy payload, query Maxx.

## 2. The 3-Pass Spec Pipeline
To prevent AI code destruction at scale, zero production Python code is allowed to be written until a specification has survived three distinct passes.

### Pass 1: Skeleton Generation (Qwen 4B)
- **Actor:** Qwen (running on Orange Pi NPUs).
- **Action:** Pulls context from Maxx Qdrant, generates a barebones markdown template (`P1-XXX_spec.md`).
- **Destination:** Output dropped into `docs/specs/_01_skeletons/`.

### Pass 2: Fleshing (Roo Code 'doc-flesher')
- **Actor:** Roo Code (Julie, Maxx, or Desktop).
- **Action:** Picks up a skeleton from `_01_skeletons/`. Maps out the 10+ parameters, edge cases, GUI needs, and legacy GLSL/Python code references.
- **Destination:** Moves the completed, highly detailed 20-100KB markdown spec to `docs/specs/_02_fleshed_out/`.

### Pass 3: Frontier Analysis (Antigravity Overseer)
- **Actor:** Antigravity (You).
- **Action:** 
  1. Ingest all specs currently sitting in `_02_fleshed_out/`.
  2. Identify code reuse, shared utility requirements, and overarching dependencies.
  3. Generate a master Mermaid architectural diagram for these components to prevent duplicative code logic.
  4. Wait for explicit human approval. Do not write code.

### Pass 4: Production Execution
- **Actor:** Roo Code (Execution Mode).
- **Action:** Only triggered *after* Pass 3 approval. Writes the actual `src/` Python code, ensuring 60FPS performance and 80%+ test coverage.

## 3. Strict Prohibitions (Zero Tolerance)
1. **DO NOT DELETE `BOARD.md`**: `BOARD.md` tracks the state of over 1,100 plugins. You must update rows from `⬜ PENDING` to `🟩 COMPLETED`. You may never delete the file or wipe un-processed rows.
2. **DO NOT HALLUCINATE ARCHITECTURE**: You do not get to dictate the workflow. The 3-Pass system is law.
3. **DO NOT WRITE CODE EARLY**: If a spec hasn't passed Pass 3 Analysis, you cannot write its Python code. No exceptions.
4. **DO NOT IGNORE THE GOLDEN SPEC**: `docs/specs/_GOLDEN_EXAMPLE_CORE.md` (derived from P3-EXT001_ascii_effect) is the absolute template standard for all specifications.

If you violate these prohibitions, you will cause another catastrophic data loss event. Adhere to the bounds.
