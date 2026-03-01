# Phase 2.5: Global Specification Review & Standardization

**Status:** PENDING
**Trigger:** 100% completion of Phase 2 (Spec Fleshing Out).
**Blocker:** Phase 4 (Code Execution) is strictly paused until this phase completes.

## Objective
Before a single line of production code is written, the entire "spec base" must undergo a systemic sweep to enforce flawless naming conventions, optimize dependencies, and establish uniform interface contracts. This is a purely conceptual/architectural optimization pass.

## Step 1: Ingestion & Vectorization
1. Parse all completed specs in `docs/specs/_02_fleshed_out/`.
2. Generate embeddings and inject them into the `vjlive3brain` Qdrant database for RAG querying.

## Step 2: Global Sweeps (The 5 Pillars)

### 1. The Sanity Pass & Historical Synthesis (Crucial)
* **Goal:** Answer "What is it supposed to do?" using historical precedent, not LLM hallucination.
* **Action:** Cross-reference the spec's intended functionality against the 3 legacy codebases (`vjlive`, `VJlive-2`, and early `VJLive3`). Extract the *most robust* compilation of logic and apply it like clay to the clean VJLive3 skeletal form.
* **Pruning:** Not everything makes the cut. If a spec describes redundant, flawed, or experimental legacy logic that failed in V1/V2, mark the spec for deletion rather than blindly porting it. Code proper, hopefully for the last time.

### 2. Legacy Lineage & Novelty Verification
* **Goal:** Ensure every node is rooted in historical legacy, or rigorously justify any novel non-legacy insertions.
* **Action:** Trace the lineage of the specification to the legacy codebase. If a spec **does not** come from legacy (e.g., an entirely new feature proposed by an LLM):
  * **Question:** Why does it exist, and is it meant to be in the VJLive3 app?
  * **Inspection:** If it *is* intended to be in the app, it must be thoroughly inspected for robustness, architectural cohesion, and security within the clean VJLive3 design before it is approved for execution.
* **Outcome:** Reject hallucinations, validate intentional novel features.

### 3. Naming Convention Sweep
* **Variables & Properties:** `snake_case` (e.g., `depth_threshold`). No camelCase.
* **Classes & Structs:** `PascalCase` (e.g., `AudioReactor`).
* **Constants & Enums:** `UPPER_SNAKE_CASE` (e.g., `MAX_RESONANCE`).
* **Callbacks/Events:** Must be prefixed with `on_` (e.g., `on_frame_rendered`).
* **Action:** Identify and flag any "stupid naming conventions" (inconsistencies, legacy port names) across all specs and rewrite the spec documents to conform.

### 4. Dependency & Library Optimization
* **Global Inventory:** Extract exactly what external Python packages (e.g., `numpy`, `moderngl`, `opencv-python`) are required across all 1,200+ specs.
* **Consolidation:** If two specs solve the same math problem using different libraries, unify them under the most performant standard.
* **Opt-Out Policies:** Flag heavyweight data science libraries if a native Python or NumPy solution exists.

### 5. Interface & Callback Schema
* **Input/Output Standardization:** Ensure all visual nodes have standardized input keys (e.g., `texture_in`, `audio_features`) and standardized outputs (`texture_out`).
* **Lifecycle Methods:** Ensure all specs inherit a unified `init()`, `update(dt)`, `render()`, and `cleanup()` schema.

### 6. Inheritance & Module Structure
* Map the class hierarchy from `BaseEffect` or `BaseNode` outward.
* Identify redundant abstract classes defined in separate specs and merge them into core foundational specs.

### 7. Renderer Agnosticism & WebGPU Pivot
* **Goal:** Enforce the Headless Configuration architecture (ADR-008) and the WebGPU standard (ADR-009). 
* **Condition:** Every effect spec must strictly separate mathematical/routing logic from rendering logic. The rendering targets must be specified as WebGPU/WGSL.
* **Action:** Audit specs for hardcoded native Python-OpenGL or legacy GLSL assumptions. Flag them with a required WGSL translation constraint to guarantee compatibility across the Free Tier (browser WebGPU) and Pro Tier (`wgpu-py` wrapping Vulkan/Metal).

### 8. Event-Driven State over Polling
* **Goal:** Eradicate `while True` polling loops (ADR-010).
* **Action:** Rewrite all specs relying on frame-by-frame polling to use an Observer pattern, where updates only trigger upon a discrete parameter change.

### 9. Native Browser Media APIs over OpenCV
* **Goal:** Eradicate Python-bound video ingestion (ADR-011).
* **Action:** Purge all specs requiring `opencv-python` for routing webcams, screenshares, or video files. Enforce the use of `navigator.mediaDevices` and `WebCodecs` APIs.

### 10. CRDT (Conflict-Free Replicated Data Types) State
* **Goal:** Enable lock-free multiplayer/multi-agent collaboration (ADR-012).
* **Action:** Reject any spec defining the Application State as a synchronous singleton dictionary. Rewrite to handle state via CRDTs (e.g., Yjs or Automerge).

### 11. Client-Side Web Audio API
* **Goal:** Achieve zero-latency, serverless audio reactivity (ADR-013).
* **Action:** Rewrite FFT analysis and onset detection specs to target JS `AudioWorkletProcessors` operating firmly on the client side, bypassing server triangulation.

### 12. Hardware Parity & Manual Verification
* **Goal:** Eradicate Hallucinated Eurorack modules (ADR-014).
* **Action:** Audit specs modeling physical hardware (e.g., Make Noise modules). Ensure a 1:1 mapping (one spec per manual) and verify the specification document explicitly links to the PDF or text transcript of the original manufacturer's manual to serve as the ground truth.

### 13. Faithful Audio DSP to Visual Translation Pass
* **Goal:** Faithfully convert ported audio algorithms into profound visual synthesizers without pruning (ADR-015).
* **Action:** Identify any spec acting as a pure audio component. The assigned agent must study the original audio application's DSP math and faithfully recreate that exact synthesis in a video format as closely as possible (e.g., Audio Oscillator → RGB Particle Waveform; Reverb → Spatial Blur/Echo). Do *not* paste a generic shader to bypass the work, and do *not* prune the module if creativity fails. The spec must be rewritten to execute the legacy DSP concept in a visually fascinating way.

## Step 3: Spec Correction
Agents assigned to Phase 2.5 will rewrite the actual Markdown specs in the `_02_fleshed_out` directory to reflect the standardized decisions made during the sweep. 

## Phase Gate Checklist
- [ ] 100% of fleshed-out specs have been embedded in Qdrant.
- [ ] Naming convention audit script returns 0 violations across the spec-base.
- [ ] Global `requirements.txt` / dependency tree is locked and approved.
- [ ] Core interface schema (`BaseEffect`, `BaseAgent`) is finalized and all child specs have been updated to reflect it.
