# DECISIONS.md — Architectural Decisions Log

**Purpose:** Record all significant architectural decisions. Every decision logged here prevents future agents from re-litigating settled debates.
**Owner:** Antigravity (Manager Agent). Workers may propose decisions; only Manager commits them here.

---

## Decision Template
```
### [ADR-NNN] Short Title
**Date:** YYYY-MM-DD | **Status:** Proposed | Accepted | Superseded
**Context:** Why did this decision need to be made?
**Decision:** What was decided?
**Rationale:** Why this choice over alternatives?
**Consequences:** What does this enable or constrain?
**Owner:** Who owns this decision?
```

---

## Decisions

### [ADR-001] Workspace Directory Mapping
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Multiple directories on desktop. Previous agents were writing to wrong locations.
**Decision:**
- `VJLive3_The_Reckoning` = active workspace, all new code
- `VJlive-2` = read-only legacy library v2
- `vjlive` = read-only legacy library v1
**Rationale:** Clear separation prevents cross-contamination of bugs from legacy into new architecture.
**Consequences:** All file creation commands must target VJLive3_The_Reckoning. Any PR touching legacy dirs is immediately rejected.
**Owner:** User (Vision Holder)

---

### [ADR-002] Language Stack — Python Core with Performance Bridge Option
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** VJlive-2 is pure Python/OpenGL. User is open to C++/Rust for performance.
**Decision:** Python for all orchestration, agents, plugin system, MCP servers, and tooling. Engine rendering core (Phase 1-F1) deferred — decision point: stay Python/OpenGL or introduce C++ bridge at that phase.
**Rationale:** Python provides fastest iteration for Phase 0. The architecture must not assume a C++ bridge until the rendering core design is validated.
**Consequences:** Keep engine abstracted behind an interface so language can be swapped. No Python-specific idioms in the core rendering interface.
**Owner:** Antigravity (pending User confirmation at Phase 1-F1)

---

### [ADR-003] No-Stub Policy — Logger.Termination Pattern
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Previous codebases had widespread stubs causing silent false-positive test results.
**Decision:** Zero stubs. All known dead-end code paths use `Logger.termination("ClassName.method: <reason>")` instead of `pass`, `raise NotImplementedError`, or bare `return False/True`.
**Rationale:** Dead-end code that self-identifies cannot silently fail. Any agent or test encountering a termination event gets a meaningful description.
**Consequences:** Pre-commit hook `check_stubs.py` enforces this. AST-based scan rejects stubs at commit time.
**Owner:** Antigravity

---

### [ADR-004] Phase 0 Deliverable — Status Window
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** "The Kitten Check" — app must be visible and functional at each phase gate.
**Decision:** Phase 0 ends with a working windowed app that reports:
- Live FPS counter
- Memory usage (resident set size)
- Active agent/worker count (from switchboard)
- Phase 0 completion status checklist
**Rationale:** Establishes the rendering pipeline, window management, and MCP connectivity in a single deliverable before any effect/plugin work begins.
**Consequences:** Phase 1 cannot begin until this window is running and stable at ≥58 FPS.
**Owner:** Antigravity

---

### [ADR-005] MCP Server Architecture — Offline-First SQLite
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Knowledge base and agent comms need persistence without cloud dependencies.
**Decision:** Both MCP servers (`vjlive-brain`, `vjlive-switchboard`) use SQLite for local persistence. No cloud databases, no Redis for core functionality.
**Rationale:** Offline-first per RULE 11. SQLite is zero-deployment, ACID-compliant, and sufficient for single-machine multi-agent workflows.
**Consequences:** Multi-machine agent collaboration not supported without sync layer (Phase 4+ concern).
**Owner:** Antigravity

---

### [ADR-006] Plugin Migration — Artisanal Snowflake Protocol
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Hundreds of legacy effects. Previous agents batch-processed them, losing integrity.
**Decision:** One plugin/effect at a time. Each handled as a bespoke migration with individual analysis, spec write-up, implementation, and validation. No scripts that mass-generate plugin skeletons.
**Rationale:** Each plugin has unique logic, parameters, and potentially "Dreamer" insights. Mass processing produces mediocre, uniform results that lose the soul of the app.
**Consequences:** Slower plugin migration. Acceptable — quality over speed.
**Owner:** User (Vision Holder)

---

### [ADR-007] ConceptEntry Role Assignment Field
**Date:** 2026-02-20 | **Status:** Accepted
**Context:** Need to distinguish orchestration logic from processing logic in knowledge base.
**Decision:** `role_assignment` field added to `ConceptEntry` schema with values: `"manager"` (orchestrator, spec writer) or `"worker"` (processor, effect implementer). Matches the Architect/Artisan agent role split.
**Rationale:** Allows agents to query "what concepts does a Worker need for this task" without seeing the full Manager-level architectural context. Enforces role boundaries in the knowledge base itself.
**Consequences:** All concept entries must be tagged with a role. Brain server exposes `search_concepts(role="worker")`.
**Owner:** Antigravity

---

### [ADR-008] Bifurcated Pipeline: Headless Configuration & Targeted Compilation
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Need to support a zero-server-compute Free Tier (WebGL in-browser) designed as a funnel for the massive Pro Tier (OpenGL with physical hardware I/O).
**Decision:** All core logic and specifications must be strictly "Renderer Agnostic" and "Transport Agnostic". The spec defines the mathematical connections, LFO timings, and Shader Strings in a Headless Configuration (JSON graph). The execution layer is bifurcated: Pro Mode compiles natively via Python/OpenGL with physical I/O; Cloud Mode compiles the exact same graph to WebGL/WebGPU in the browser.
**Rationale:** WebGL cannot access strict local hardware (DMX, NDI, Spout, physical cameras) without a backend daemon, but OpenGL rendering on cloud infrastructure is financially unviable for a free tier. The Headless Configuration approach solves both problems.
**Consequences:** Specs cannot assume native Python libraries (like OpenCV or librosa) for rendering logic if they are meant to run on the web. A strict "Renderer Agnosticism" sweep is enforced in Phase 2.5.
**Owner:** User (Vision Holder)

---

### [ADR-009] Primary Graphics Interface: WebGPU
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Need a high-performance, cross-platform graphics API that supports both a zero-server-compute Free Tier (browser) and a raw-performance Pro Tier (desktop), bypassing OpenGL's driver overhead and legacy constraints.
**Decision:** All core rendering logic and headless configurations must target WebGPU and WebGPU Shading Language (WGSL). Native desktop builds will use `wgpu-py` (wrapping Vulkan/Metal), while the web client will use native in-browser WebGPU.
**Rationale:** WebGPU scales perfectly across the bifurcated pipeline defined in ADR-008. It allows the exact same rendering graph and shader logic to execute securely in modern browsers for free users, and with Vulkan-level performance on desktop hardware for pro users, solving both the sandbox constraint and the server compute cost.
**Consequences:** All legacy GLSL shaders must be flagged for WGSL transpilation or rewriting during Phase 4. All render loop specs in Phase 1 must define WebGPU contexts, explicitly deprecating bare OpenGL assumptions.
**Owner:** User (Vision Holder)

---

### [ADR-010] Event-Driven / Reactive State Over Polling
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Legacy rendering relied on a `while True` 60fps loop polling thousands of unchanged nodes every frame, inflating CPU usage exponentially.
**Decision:** All node parameters and states must utilize an Event-Driven (Observer) pattern. Graphs and modular inputs only trigger recalculations or uniform buffer updates when a parameter natively changes (e.g., LFO tick, MIDI event).
**Rationale:** Preserves CPU/JS thread cycles by abandoning redundant polling loops. VJLive3 becomes reaction-based; if no dial moves and no audio changes, the CPU does zero work while the WebGPU loop coasts on the last known state.
**Consequences:** The `update(dt)` method across all existing specs must be strictly regulated to only fire upon dirty-flagged state changes.
**Owner:** User (Vision Holder)

---

### [ADR-011] Native Browser Media APIs over OpenCV
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Legacy implementations relied intensely on `opencv-python` for streaming RTSP feeds, webcams, and video captures—fatal abstractions for a web-based client that cannot run bloated C++ binaries.
**Decision:** All video ingestion, window capture, and camera routing must use native browser standards (`navigator.mediaDevices`, `WebCodecs`, `WebRTC`) feeding zero-copy textures to WebGPU.
**Rationale:** Browser makers spent billions optimizing hardware-accelerated video decoding. Rewriting specs to lean on browser internals rather than a Python wrapper allows flawless 4K video playback with zero server overhead.
**Consequences:** Specs containing "import cv2" must be mercilessly purged during Phase 2.5 and translated to frontend Web API calls.
**Owner:** User (Vision Holder)

---

### [ADR-012] CRDT (Conflict-Free Replicated Data Types) State
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Multi-agent swarms (Stylist, Dreamer) and human collaborators interacting concurrently will catastrophically brick a synchronous "God Object" Application State singleton through race conditions.
**Decision:** The central configuration JSON and active visual graph must be handled as a CRDT (e.g., using Yjs or Automerge). 
**Rationale:** Treating the VJ tool like a multiplayer Google Doc ensures mathematical convergence. Five parameters can be tweaked simultaneously by 2 human users, a MIDI controller, and an AI agent across different continents, and the state will perfectly resolve without locking threads.
**Consequences:** State managers must be re-spec'd as CRDT shared types, abandoning traditional Python dictionary singletons.
**Owner:** User (Vision Holder)

---

### [ADR-013] Client-Side Web Audio API Analysis
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Performing FFT math on a python server and broadcasting it back to a client's 60fps render loop guarantees desynchronization between visual transients and physical audio beats due to network jitter.
**Decision:** All audio reactivity (FFT analysis, onset detection, frequency extraction) must happen natively on the client using the browser's Web Audio API and `AudioWorklet` nodes pushing data directly to WebGPU buffers.
**Rationale:** WebAudio achieves perfect synchronization because it runs on the local user’s audio thread. Server costs drop to zero, latency drops to zero.
**Consequences:** Core components like `AudioAnalyzer` and `QuantumAudioFeatures` must be ported to Javascript `AudioWorkletProcessors` rather than local Python instances.
**Owner:** User (Vision Holder)

---

### [ADR-014] Hardware Parity — 1:1 Module to Manual Mapping
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** VJLive3 models physical Eurorack modules, specifically those from Make Noise. Previous LLM implementations often "hallucinated" how a module like Maths or Morphagene should work rather than replicating its actual electrical behaviors.
**Decision:** All modular effect nodes intended to replicate physical hardware must contain a direct link to the official manufacturer's PDF manual (or converted text file) within the `.md` specification document. Furthermore, there must be a 1:1 architectural mapping: one VJLive3 module spec per Make Noise hardware manual. 
**Rationale:** The only way to build a professional-grade software analog of a physical Eurorack system is to treat the manufacturer's manual as the ultimate source of truth, removing all AI guesswork regarding signal routing, CV responses, and edge cases.
**Consequences:** During the Phase 2.5 review, any spec claiming to model a physical module must be audited to verify the inclusion of the manual reference. Specs built on hallucinated intuition rather than manual documentation will be rejected and flagged for rewrite.
**Owner:** User (Vision Holder)

---

### [ADR-015] Faithful Audio DSP to Visual Translation Pass
**Date:** 2026-02-28 | **Status:** Accepted
**Context:** Many legacy plugins were ported directly from C++ audio libraries (like VCV Rack). VJLive3 is a video/visual application, but all audio DSP concepts are deeply applicable to video if evaluated creatively (e.g. an oscillator generating an RGB waveform instead of an audio wave).
**Decision:** All imported audio DSP plugin specs must undergo a rigorous, faithful functional translation pass. The goal is *not* to paste a generic shader simply because an agent can do it, nor to prune the module if the agent lacks creativity. The goal is to study the original audio DSP mathematical logic and faithfully recreate that synthesis in a visual format as closely as possible.
**Rationale:** The math behind audio synthesis (delays, reverbs, physical modeling, FM synthesis) creates incredibly organic visual textures when applied to pixels, geometry, or color spaces. We preserve the soul of the original audio logic by creatively translating its math, rather than discarding it.
**Consequences:** Phase 2.5 includes a strict "DSP to Visual Translation Pass." Agents must identify audio plugins and rewrite the spec to do something visually profound based directly on the original DSP logic. No modules will be pruned due to lack of agent creativity—the math must be translated.
**Owner:** User (Vision Holder)

---

### [ADR-016] Milkdrop Removed from Core Scope
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** P1-R3 spec originally included Milkdrop preset parsing as a Phase 1 requirement.
**Decision:** Milkdrop is NOT a Phase 1 requirement and NOT a native renderer component. If Milkdrop support is ever added, it runs as an external subprocess and communicates output frames over a texture bridge. VJLive3 does not embed or ship a Milkdrop parser.
**Rationale:** Milkdrop is GLSL-based. Embedding it would require maintaining an OpenGL execution path that contradicts ADR-009. Subprocess isolation keeps the core clean.
**Consequences:** Any spec or code referencing Milkdrop as a native dependency must be flagged. P1-R3 is now `P1-R3_WGSL_hot_reload.md`.
**Owner:** Antigravity (confirmed by User 2026-03-03)

---

### [ADR-017] Universal Parameter Scale: 0–10 Float
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** Legacy effects used inconsistent parameter ranges (0.0–1.0, 0–255, 0–360, etc.), making MIDI/OSC mapping non-uniform.
**Decision:** All effect parameters exposed to the outside world (MIDI, OSC, UI, agent control) use a **0–10 float scale**. Internal GPU shaders normalize to 0.0–1.0 at the boundary (`value / 10.0`). No exceptions for existing "nice" ranges.
**Rationale:** Uniform scale makes any control surface (MIDI CC, OSC float, agent API) directly interchangeable. Division by 10 is a one-liner at the GPU boundary.
**Consequences:** All spec parameter tables must define their range as `[0.0, 10.0]`. Normalization is the implementer's responsibility at the `render()` call site.
**Owner:** User (Vision Holder)

---

### [ADR-018] ShaderCache: Compile-Before-Swap Policy
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** Legacy `shader_base.py` delete the OLD shader object before compiling the new one during hot-reload. If compilation fails, the engine runs with no shader.
**Decision:** The new `ShaderCache` (P1-R3) must ALWAYS compile the replacement shader and confirm it links successfully BEFORE swapping the reference and releasing the old shader. On compilation failure, the old shader stays active and an error is logged.
**Rationale:** Failure to follow this causes a frameless black window with no user feedback — the worst possible failure mode during a live performance.
**Consequences:** `ShaderCache.reload_shader()` is asynchronous at the file level but synchronous at the swap level. Tests must verify old shader survives a bad reload.
**Owner:** Antigravity

---

### [ADR-019] `src/` Cleanliness Gate
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** Previous sessions wrote speculative code into `src/` before specs were reviewed, causing architectural drift and hallucination accumulation.
**Decision:** `src/` contains ONLY `src/vjlive3/__init__.py` until a spec is: (1) fully fleshed out in `docs/specs/`, (2) reviewed by the user, and (3) the user explicitly says "implement [SPEC-ID]". No agent may write implementation code to `src/` speculatively.
**Rationale:** The spec is the contract. Code written before the contract is finalized is debt, not progress.
**Consequences:** Pre-commit hooks check `src/` against the DISPATCH.md lock list. Any `src/` file without a corresponding completed spec ID is rejected.
**Owner:** User (Vision Holder)

---

### [ADR-020] Headless Mode Env Var: `VJ_HEADLESS=true`
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** CI/CD, smoke tests, and swarm agents running on headless servers need a unified way to request offscreen rendering without a display.
**Decision:** `VJ_HEADLESS=true` (environment variable, string comparison case-insensitive) triggers headless mode in `RenderContext` (P1-R1). All spec test plans and smoke test commands use this variable.
**Rationale:** Single env var is simpler than a constructor flag and works across subprocess calls, Docker, and CI environments without importing the module.
**Consequences:** All specs with a GPU test plan must include `VJ_HEADLESS=true` in their test runner command. `RenderContext.__init__` checks `os.environ.get("VJ_HEADLESS", "").lower() == "true"`.
**Owner:** Antigravity

---

### [ADR-021] ModernGL Total Ban
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** ADR-009 mandates WebGPU, but early spec drafts kept `moderngl` as a "fallback." This created ambiguity.
**Decision:** `moderngl` is completely banned from `src/`. Not as a fallback, not as a test double, not as a transitional shim. `wgpu-py` is the only GPU abstraction in VJLive3. The pre-commit hook `check_stubs.py` is extended to also grep for `import moderngl` and reject commits.
**Rationale:** A "fallback" that exists in the codebase will be used by the first agent that hits a wgpu error. The only way to prevent this is a hard architectural prohibition.
**Consequences:** `requirements.txt` may NOT list `moderngl`. If wgpu is unavailable, the correct failure mode is a `RuntimeError` with a clear message, not a silent OpenGL fallback.
**Owner:** Antigravity (confirmed by User 2026-03-03)

---

### [ADR-022] FrameBudgetAllocator as Canonical Per-Effect Timing Contract
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** Legacy effects used hardcoded throttles (`if frame_count % 3 == 0`) and fixed LOD values (`scale=0.25`) which cannot adapt to real-time load.
**Decision:** `FrameBudgetAllocator` (ported verbatim from `vjlive/core/frame_budget.py`, 120 lines) is the canonical per-effect timing contract in VJLive3. All heavy effects register with it and query `should_skip()` and `get_lod_scale()` per frame. Hardcoded throttles are forbidden.
**Rationale:** Adaptive skip/LOD responds to actual measured frame time, not a static guess. Max 2 consecutive skips prevents visible stutter.
**Consequences:** Effect specs must declare their `budget_ms` value and register with the allocator. Effects using hardcoded frame-skip logic fail spec review.
**Owner:** Antigravity

---

### [ADR-023] Spec-First Gate — Three-Step Implementation Protocol
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** Agents have written implementation code that outpaced the spec, causing the spec to retroactively describe buggy code rather than the intended design.
**Decision:** Implementation follows a strict three-step gate:
1. **Spec fleshed out** — `docs/specs/_02_fleshed_out/[SPEC-ID].md` exists and is reviewed
2. **Manager approval** — User or Manager explicitly approves the spec
3. **Explicit invocation** — User says "implement [SPEC-ID]" or Manager dispatches via DISPATCH.md

No agent may begin Step 3 without Steps 1 and 2 complete. This is the same as the "three-layer test" validation loop: *id believes → ego compiles → renderer judges*.
**Rationale:** Code written before the spec is settled is the primary source of hallucination accumulation.
**Consequences:** DISPATCH.md entries require a spec file path. Worker agents must verify the spec exists before starting any `src/` file creation.
**Owner:** User (Vision Holder)

---

### [ADR-024] Bifurcation Tier Classification — Spec-Level Annotations
**Date:** 2026-03-03 | **Status:** Accepted
**Context:** ADR-008 describes a bifurcated pipeline (Pro/Desktop + Cloud/Browser). Phase 1 specs are being written for the Pro tier first, but future agents need to know which components require browser equivalents vs which are already portable.
**Decision:** Every spec must carry a `**Tier:**` annotation in its header using one of two labels:
- **`Pro-Tier Native`** — Python/wgpu-py only. Requires a browser-equivalent spec in a future phase before the bifurcated pipeline is complete. Examples: `RenderContext`, `EffectChain`, `TexturePool`, `RenderEngine`.
- **`Bifurcated-Safe`** — The component or its output is directly portable to the browser WebGPU context. No browser-equivalent spec needed. Examples: All WGSL shader strings (P1-R6), the 0–10 parameter contract (ADR-017).

Note: A spec may contain BOTH — e.g. P1-R3 `ShaderCache` is Pro-Tier Native (Python filesystem watcher), but the WGSL strings it manages are Bifurcated-Safe.
**Rationale:** Agents writing future browser specs need to know which Phase 1 components they are re-implementing, not re-inventing. Clear labels prevent double work or missed work.
**Consequences:** All existing P1-R* specs are annotated retroactively. All future specs must include the `**Tier:**` field before they leave `_01_skeletons/`.
**Owner:** Antigravity
