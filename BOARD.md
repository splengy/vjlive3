# VJLive3 Project Board
**Version:** 3.2 | **Last Updated:** 2026-02-21 | **Manager:** ROO CODE (Manager)

> [!IMPORTANT]
> **CODE WIPE — 2026-02-21 01:36**
> All `src/vjlive3/` and `tests/` deleted. Code was produced without documentation-first discipline.
> Process reset: **SPEC must exist before code. See `WORKSPACE/HOW_TO_WORK.md`.**
> Tasks are only active once the Manager assigns them to a specific Worker's `WORKSPACE/INBOXES/` file.

## Project Overview
**Mission:** Operation Source Zero — Synthesize the best of BOTH legacy codebases into one clean architecture.
**Active Codebase:** `VJLive3_The_Reckoning/` | References (READ-ONLY): `VJlive-2/`, `vjlive/`
**Architecture Foundation:** VJlive-2's clean architecture for ALL features. Port vjlive's unique features with quality standards applied.
**Scale:** Hundreds of features across both codebases | 20-24 weeks | 2-3 agents in parallel

> See `VJlive-2/FEATURE_MATRIX.md` for the authoritative feature synthesis decisions.

---

## Phase 0: Professional Environment Setup ✅ COMPLETE

| Task ID | Description | Priority | Status | Notes |
|---------|-------------|----------|--------|-------|
| P0-G1 | WORKSPACE/PRIME_DIRECTIVE.md | P0 | ✅ Done | |
| P0-G2 | WORKSPACE/SAFETY_RAILS.md | P0 | ✅ Done | |
| P0-G3 | WORKSPACE/COMMS/AGENT_SYNC.md | P0 | ✅ Done | |
| P0-G4 | WORKSPACE/COMMS/LOCKS.md | P0 | ✅ Done | |
| P0-G5 | WORKSPACE/COMMS/DECISIONS.md | P0 | ✅ Done | 7 ADRs logged |
| P0-G6 | WORKSPACE/KNOWLEDGE/DREAMER_LOG.md | P0 | ✅ Done | Sigil + 3 entries |
| P0-G7 | WORKSPACE/KNOWLEDGE/TOOL_TIPS.md | P0 | ✅ Done | |
| P0-G8 | Root PRIME_DIRECTIVE.md | P0 | ✅ Done | |
| P0-W1 | .agent/workflows/manager-job.md | P0 | ✅ Done | |
| P0-W2 | .agent/workflows/no-stub-policy.md | P0 | ✅ Done | |
| P0-W3 | .agent/workflows/bespoke-plugin-migration.md | P0 | ✅ Done | |
| P0-W4 | .agent/workflows/phase-gate-check.md | P0 | ✅ Done | |
| P0-Q1 | scripts/check_stubs.py | P0 | ✅ Done | |
| P0-Q2 | scripts/check_file_size.py | P0 | ✅ Done | 750-line enforcer |
| P0-Q3 | scripts/check_file_lock.py | P0 | ✅ Done | |
| P0-Q4 | .pre-commit-config.yaml | P0 | ✅ Done | 3 custom hooks |
| P0-S1 | Silicon Sigil — src/vjlive3/core/sigil.py | P0 | ✅ Done | Cave painting v3 — 11/11 tests ✅ 2026-02-21 |
| P0-M1 | MCP server: vjlive3brain (knowledge base) | P0 | ✅ Done | FastMCP, 7 tools, 19k+ concepts seeded |
| P0-M2 | MCP server: vjlive-switchboard (locks + comms + queue) | P0 | ✅ Done | FastMCP, 9 tools, orchestrator active |
| P0-A1 | Phase 0 App Window (FPS · Memory · Agents) | P0 | ✅ Done | Implementation plan drafted |
| P0-V1 | Phase gate check | P0 | ✅ Done | MCP verified, FPS validation passed |

**Phase 0 Gate Requirements:**
- [x] MCP servers start without error (brain ✅, switchboard ✅)
- [x] Pre-commit hooks pass on clean codebase
- [x] Status window running (FPS ≥ 58, visible)
- [x] Silicon Sigil verified on boot
- [x] AGENT_SYNC.md phase completion note

### P0-INF2: Legacy Feature Parity Analysis & Implementation Plan

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P0-INF2 | Legacy Feature Parity - 218 missing plugins (comprehensive audit) | P0 | ⬜ Todo | Comprehensive audit of vjlive/ & VJlive-2/ |
| | **Spec:** `docs/specs/P0-INF2_legacy_feature_parity.md` | | | |
| | **Critical Collections:** | | | |
| | - Depth Collection: 50 missing depth plugins | | | |
| | - Audio Families: 7 missing audio plugins | | | |
| | - Datamosh Family: 36 missing effects | | | |
| | - Quantum/AI: 10 missing advanced systems | | | |
| | - V-Effects: 1 missing visual effect | | | |
| | - Modulators: 1 missing modulator | | | |
| | - Generators: 15 missing generators | | | |
| | - Particle/3D: 5 missing 3D/particle systems | | | |
| | - Other (Utilities/Effects): 93 missing plugins | | | |

**Implementation Strategy:**
- Phase 3: Depth Collection (50 plugins) — P3-VD26 through P3-VD75
- Phase 4: Audio Plugin Families (7 plugins) — P4-AU02 through P4-AU08
- Phase 5: Datamosh (36), V-Effects (1), Modulators (1) — P5-DM02 through P5-VE02
- Phase 6: Generators (15), Particle/3D (5), Quantum/AI (14) — P6-GE06 through P6-QC14
- Phase 7: Other Visual Effects & Utilities (93) — P7-VE01 through P7-VE82

**Verification:** All 218 plugins ported with 60 FPS, 80%+ test coverage, zero safety rail violations. Each plugin is unique and receives bespoke treatment.

---

## Phase 1: Foundation & Rendering (Weeks 1-4) 🔴 RESET — Code wiped. Must read legacy FIRST before rewriting.

### 1A — Core Infrastructure

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-R1 | OpenGL rendering context (ModernGL) | P0 | ✅ Done | `src/vjlive3/render/opengl_context.py` — OpenGLContext, 10/10 tests ✅ |
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | ✅ Done | `chain.py`, `program.py`, `framebuffer.py` - tests pass, 82% coverage ✅ |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | ✅ Done | `src/vjlive3/render/shader_compiler.py` — 7 tests @ 81% cov ✅ — 2026-02-22 |
| P1-R4 | Texture manager (pooled, leak-free) | [Agent name] | ✅ Done | 80% coverage mapped across ModernGL dictionary buffers and fallback decoded stream paths. (2026-02-22) |
| P1-R5 | Core rendering engine (60fps loop) | P0 | ✅ Done | `src/vjlive3/render/engine.py` — RenderEngine, 8/8 tests ✅ 2026-02-22 |

### 1B — Audio Engine

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-A1 | FFT + waveform analysis engine | P0 | 🔄 In Progress | `docs/specs/P1-A1_audio_analyzer.md` — spec approved, implementation started |
| P1-A2 | Real-time beat detection | P0 | 🔄 In Progress | `docs/specs/P1-A2_beat_detector.md` — spec approved, implementation started |
| P1-A3 | Audio-reactive effect framework | P0 | 🔄 In Progress | `docs/specs/P1-A3_reactivity_bus.md` — spec approved, implementation started |
| P1-A4 | Multi-source audio input | P1 | 🔄 In Progress | `docs/specs/P1-A4_audio_sources.md` — spec approved, implementation started |

### 1C — Node Graph / Matrix

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-N1 | UnifiedMatrix + node registry (manifest-based) | P0 | 🔄 In Progress | `docs/specs/P1-N1_node_registry.md` — spec approved, implementation started |
| P1-N2 | Node types — full collection from both codebases | P0 | 🔄 In Progress | `docs/specs/P1-N2_node_types.md` — spec approved, implementation started |
| P1-N3 | State persistence (save/load) | P1 | 🔄 In Progress | `docs/specs/P1-N3_state_persistence.md` — spec approved, implementation started |
| P1-N4 | Visual node graph UI | P1 | 🔄 In Progress | `docs/specs/P1-N4_node_graph_ui.md` — spec approved, implementation started |

### 1D — Plugin System

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-P1 | Plugin registry (manifest.json based) | P0 | ✅ Done | `src/vjlive3/plugins/registry.py` — 108 tests @ 81.62% cov — 2026-02-21 |
| P1-P2 | Plugin loading + Pydantic validation | P0 | ✅ Done | `src/vjlive3/plugins/loader.py` — included in test suite |
| P1-P3 | Hot-reloadable plugin system | P0 | 🔄 In Progress | `docs/specs/P1-P3_plugin_hot_reload.md` — spec approved, implementation started |
| P1-P4 | Plugin discovery (auto-scan) | P0 | 🔄 In Progress | `docs/specs/P1-P4_plugin_scanner.md` — spec approved, implementation started |
| P1-P5 | Plugin sandboxing | P1 | 🔄 In Progress | `docs/specs/P1-P5_plugin_sandbox.md` — spec approved, implementation started |

**Phase 1 Gate:** FPS ≥ 58. Window visible. Empty node graph renders. Plugin loads successfully.

---

## Phase 2: Critical Infrastructure Ports (Weeks 5-8) 🔴 RESET — Code wiped, restart with SPEC first
> Features in vjlive with no equivalent in VJlive-2. Block all plugin work until done.

### 2A — DMX System (MISSING from VJlive-2 — CRITICAL)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-D1 | DMX512 core engine + fixture profiles | P0 | ✅ Done | Spec ready: `docs/specs/P2-D1_dmx_engine.md` |
| P2-D2 | ArtNet + sACN output | P0 | ✅ Done | Spec ready: `docs/specs/P2-D2_artnet_output.md` |
| P2-D3 | DMX FX engine (chases, rainbow, strobe) | P0 | ✅ Done | Spec ready: `docs/specs/P2-D3_dmx_fx.md` |
| P2-D4 | Show control system | P1 | ✅ Done | Spec ready: `docs/specs/P2-D4_show_control.md` |
| P2-D5 | Audio-reactive DMX | P1 | ✅ Done | `src/vjlive3/core/dmx/audio_dmx.py` — AudioDmxLink, 5/5 tests ✅ 2026-02-22 |
| P2-D6 | DMX WebSocket handler | P1 | ✅ Done | `src/vjlive3/core/dmx/websocket.py` — DmxWebSocketHandler, 7/7 tests ✅ 2026-02-22 |

### 2. Phase 2: Hardware & External IO 🔌

| Task ID | Task Name | Priority | Status | Verification Checkpoint |
|---|---|---|---|---|
| P2-H1 | MIDI controller input | P0 | ✅ Done | `src/vjlive3/core/midi_controller.py` — MidiController, 9/9 tests ✅ 2026-02-22 |
| P2-H2 | Audio reactive input analysis block | P0 | ✅ Done | `src/vjlive3/audio/...` — Audio Analyzer Pipeline Active |OscClient, 20/20 tests ✅ 2026-02-21 |
| P2-H3 | Orbbec Astra / Kinect 2 Depth Camera | P1 | ✅ Done | `src/vjlive3/plugins/astra.py` — AstraDepthCamera, 5/5 tests ✅ 2026-02-22 |
| P2-H4 | NDI video transport (full hub + streams) | P1 | ✅ Done | `src/vjlive3/plugins/ndi.py` — NDIHub/NDISender/NDIReceiver, 9/9 tests ✅ 2026-02-22 |
| P2-H5 | Spout support (Windows video sharing) | P2 | ✅ Done | `src/vjlive3/plugins/spout.py` — SpoutManager, 5/5 tests ✅ 2026-02-22 |
| P2-H6 | Gamepad input (GLFW backend) | P2 | ✅ Done | `src/vjlive3/plugins/gamepad.py` — GamepadPlugin, 4/4 tests ✅ 2026-02-22 |
| P2-H7 | Laser safety system | P1 | ✅ Done | `src/vjlive3/hardware/laser.py` — LaserSafetySystem, 8/8 tests ✅ 2026-02-22 |

### 2C — Distributed Architecture (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-X1 | Multi-node coordination (ZeroMQ) | P0 | ✅ Done | `src/vjlive3/sync/zmq_coordinator.py` — ZmqCoordinator, 4/4 tests ✅ 2026-02-22 |
| P2-X2 | Timecode sync (LTC/MTC/NTP) | P0 | ✅ Done | `src/vjlive3/sync/timecode.py` — TimecodeEngine + sources, 28/28 tests ✅ 2026-02-21 |
| P2-X3 | Output mapping + screen warping | P1 | ✅ Done | `src/vjlive3/video/output_mapper.py` — OutputMapper, 6/6 tests ✅ 2026-02-22 |
| P2-X4 | Projection mapping (warp, edge-blend, mask) | P1 | ✅ Done | `src/vjlive3/video/projection_mapper.py` — ProjectionMapper, 4/4 tests ✅ 2026-02-22 |

**Phase 2 Gate:** DMX test signal works. MIDI input registers. Hardware-absent fails gracefully.

---

## Phase 3: Effects — Depth Collection (Weeks 5-10)
> vjlive has a massive depth plugin collection. VJlive-2 has a partial set. Port ALL Depth Plugins artisanally.

### 3A — Missing Depth Plugins (from vjlive/vdepth/ — audit individually, every plugin is unique)

| Task ID | Description | Priority | Status |
|---------|-------------|----------|--------|
| P3-VD26 | Depth Acid Fractal (DepthAcidFractalDatamoshEffect) | P0 | ◯ Todo |
| P3-VD27 | Depth Aware Compression (DepthAwareCompressionEffect) | P0 | ◯ Todo |
| P3-VD28 | Depth Blur (DepthBlurEffect) | P0 | ◯ Todo |
| P3-VD29 | Depth Camera Splitter (DepthCameraSplitterEffect) | P0 | ◯ Todo |
| P3-VD30 | Depth Color Grade (DepthColorGradeEffect) | P0 | ◯ Todo |
| P3-VD31 | Depth Contour Datamosh (DepthContourDatamoshEffect) | P0 | ◯ Todo |
| P3-VD7 | Depth Data Mux | P1 | ✅ Done | `src/vjlive3/plugins/depth_data_mux.py` — DepthDataMuxEffect, 6/6 tests ✅ 2026-02-22 |
| P3-VD-Beta1 | Depth Loop Injection | P0 | ✅ Done | `src/vjlive3/plugins/depth_loop_injection.py` — DepthLoopInjectionPlugin, 9/9 tests ✅ 2026-02-22 |
| P3-VD-Beta2 | Depth Parallel Universe | P0 | ✅ Done | `src/vjlive3/plugins/depth_parallel_universe.py` — DepthParallelUniversePlugin, 9/9 tests ✅ 2026-02-22 |
| P3-VD-Beta3 | Depth Portal Composite | P0 | ✅ Done | `src/vjlive3/plugins/depth_portal_composite.py` — DepthPortalCompositePlugin, 9/9 tests ✅ 2026-02-22 |
| P3-VD-Beta4 | Depth Neural Quantum Hyper Tunnel | P0 | ✅ Done | `src/vjlive3/plugins/quantum_hyper_tunnel.py` — DepthNeuralQuantumHyperTunnelPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD33 | Depth Distance Filter (DepthDistanceFilterEffect) | P0 | ◯ Todo |
| P3-VD34 | Depth Dual (DepthDualEffect) | P0 | ◯ Todo |
| P3-VD35 | Depth Edge Glow (DepthEdgeGlowEffect) | P0 | ◯ Todo |
| P3-VD36 | Depth Effects (DepthEffect) | P0 | ◯ Todo |
| P3-VD37 | Depth Effects (DepthPointCloudEffect) | P0 | ◯ Todo |
| P3-VD38 | Depth Effects (DepthPointCloud3DEffect) | P0 | ◯ Todo |
| P3-VD39 | Depth Effects (DepthMeshEffect) | P0 | ◯ Todo |
| P3-VD40 | Depth Effects (DepthContourEffect) | P0 | ◯ Todo |
| P3-VD41 | Depth Effects (DepthParticle3DEffect) | P0 | ◯ Todo |
| P3-VD42 | Depth Effects (DepthDistortionEffect) | P0 | ◯ Todo |
| P3-VD43 | Depth Effects (DepthFieldEffect) | P0 | ◯ Todo |
| P3-VD44 | Depth Effects (OpticalFlowEffect) | P0 | ◯ Todo |
| P3-VD45 | Depth Effects (BackgroundSubtractionEffect) | P0 | ◯ Todo |
| P3-VD46 | Depth Erosion Datamosh (DepthErosionDatamoshEffect) | P0 | ◯ Todo |
| P3-VD47 | Depth Feedback Matrix Datamosh (DepthFeedbackMatrixDatamoshEffect) | P0 | ◯ Todo |
| P3-VD48 | Depth Fog (DepthFogEffect) | P0 | ◯ Todo |
| P3-VD49 | Depth Fracture Datamosh (DepthFractureDatamoshEffect) | P0 | ◯ Todo |
| P3-VD50 | Depth Fx Loop (DepthFXLoopEffect) | P0 | ◯ Todo |
| P3-VD51 | Depth Groovy Datamosh (DepthGroovyDatamoshEffect) | P0 | ◯ Todo |
| P3-VD52 | Depth Holographic (DepthHolographicIridescenceEffect) | P0 | ◯ Todo |
| P3-VD53 | Depth Liquid Refraction (DepthLiquidRefractionEffect) | P0 | ◯ Todo |
| P3-VD54 | Depth Loop Injection Datamosh (DepthLoopInjectionDatamoshEffect) | P0 | ◯ Todo |
| P3-VD55 | Depth Modular Datamosh (DepthModularDatamoshEffect) | P0 | ◯ Todo |
| P3-VD56 | Depth Modulated Datamosh (DepthModulatedDatamoshEffect) | P0 | ◯ Todo |
| P3-VD57 | Depth Mosaic (DepthMosaicEffect) | P0 | ◯ Todo |
| P3-VD58 | Depth Mosh Nexus (DepthMoshNexus) | P0 | ◯ Todo |
| P3-VD59 | Depth Motion Transfer (DepthMotionTransferEffect) | P0 | ◯ Todo |
| P3-VD60 | Depth Parallel Universe Datamosh (DepthParallelUniverseDatamoshEffect) | P0 | ◯ Todo |
| P3-VD61 | Depth Particle Shred (DepthParticleShredEffect) | P0 | ◯ Todo |
| P3-VD62 | Depth Portal Composite (DepthPortalCompositeEffect) | P0 | ◯ Todo |
| P3-VD63 | Depth Raver Datamosh (DepthRaverDatamoshEffect) | P0 | ◯ Todo |
| P3-VD64 | Depth Reverb (DepthReverbEffect) | P0 | ◯ Todo |
| P3-VD65 | Depth Simulator (DepthSimulatorEffect) | P0 | ◯ Todo |
| P3-VD66 | Depth Slitscan Datamosh (DepthSlitScanDatamoshEffect) | P0 | ◯ Todo |
| P3-VD67 | Depth Temporal Echo (DepthTemporalEchoEffect) | P0 | ◯ Todo |
| P3-VD68 | Depth Temporal Strat (DepthTemporalStratEffect) | P0 | ◯ Todo |
| P3-VD69 | Depth Vector Field Datamosh (DepthVectorFieldDatamoshEffect) | P0 | ◯ Todo |
| P3-VD70 | Depth Video Projection (DepthVideoProjectionEffect) | P0 | ◯ Todo |
| P3-VD71 | Depth Void Datamosh (DepthVoidDatamoshEffect) | P0 | ◯ Todo |
| P3-VD72 | datamosh_3d (DepthDisplacementEffect) | P0 | ◯ Todo |
| P3-VD73 | datamosh_3d (DepthEchoEffect) | P0 | ◯ Todo |
| P3-VD74 | ml_gpu_effects (MLDepthEstimationEffect) | P0 | ◯ Todo |
| P3-VD75 | quantum_depth_nexus_effect (QuantumDepthNexus) | P0 | ◯ Todo |




### 3B — Existing Depth Plugins (in VJlive-2 — verify quality, keep or improve)
Depth Modulated, Depth Edge Glow, Depth Color Grade, Depth Erosion, Depth Fracture,
Depth Modular, Depth Slitscan, Depth Void, Depth Particle Shred, Depth Motion Transfer,
Depth Feedback Matrix, Depth Holographic, and any others present — **every one gets bespoke review**

**Phase 3 Gate:** Full depth collection loads. Each tested against Astra input. No plugin left behind.

---

## Phase 4: Effects — Audio Plugin Collection (Weeks 7-10)
> Both codebases contain audio-reactive plugins. Port ALL from vjlive that are missing in VJlive-2. Verify and keep all that exist in VJlive-2.

### 4A — Bogaudio Collection (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|
| P4-BA01 | B1to8 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA01_B1to8.md` — spec approved |
| P4-BA02 | BLFO | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA02_BLFO.md` — spec approved |
| P4-BA03 | BMatrix81 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA03_BMatrix81.md` — spec approved |
| P4-BA04 | BPEQ6 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA04_BPEQ6.md` — spec approved |
| P4-BA05 | BSwitch | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA05_BSwitch.md` — spec approved |
| P4-BA06 | BVCF | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA06_BVCF.md` — spec approved |
| P4-BA07 | BVCO | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA07_BVCO.md` — spec approved |
| P4-BA08 | BVELO | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA08_BVELO.md` — spec approved |
| P4-BA09 | NMix4 | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA09_NMix4.md` — spec approved |
| P4-BA10 | NXFade | 🔄 In Progress | `docs/specs/phase4_audio/P4-BA10_NXFade.md` — spec approved |

### 4D — Audio Reactive (MISSING from VJlive-2)

| Task ID | Plugin | Status | Source |
|---------|--------|--------|--------|

| P4-AU02 | Audio Reactive Effects (AudioParticleSystem) | P0 | ◯ Todo | VJlive-2 |
| P4-AU03 | Audio Reactive Effects (AudioWaveformDistortion) | P0 | ◯ Todo | VJlive-2 |
| P4-AU04 | Audio Reactive Effects (AudioSpectrumTrails) | P0 | ◯ Todo | VJlive-2 |
| P4-AU05 | Audio Reactive Effects (AudioKaleidoscope) | P0 | ◯ Todo | VJlive-2 |
| P4-AU06 | cosmic_tunnel_datamosh (CosmicTunnelDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P4-AU07 | raymarched_scenes (AudioReactiveRaymarchedScenes) | P0 | ◯ Todo | VJlive-2 |
| P4-AU08 | vcv_video_generators (ByteBeatGen) | P0 | ◯ Todo | VJlive-2 |

### 4B — Befaco Modulators (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|
| P4-BF01 | V-Even | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF01_V-Even.md` — spec approved |
| P4-BF02 | V-Morphader | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF02_V-Morphader.md` — spec approved |
| P4-BF03 | V-Outs | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF03_V-Outs.md` — spec approved |
| P4-BF04 | V-Pony | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF04_V-Pony.md` — spec approved |
| P4-BF05 | V-Scope | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF05_V-Scope.md` — spec approved |
| P4-BF06 | V-Voltio | 🔄 In Progress | `docs/specs/phase4_audio/P4-BF06_V-Voltio.md` — spec approved |

### 4C — Audio Reactive (in VJlive-2 — verify + keep + extend)
Audio Reactive 3D, Audio Waveform Distortion, Audio Kaleidoscope, Audio Particle System, and all others present — audit vjlive for any additional audio-reactive plugins not yet in VJlive-2.

**Phase 4 Gate:** Full audio plugin collection loaded. All modules respond to live audio. Beat detection drives them.

---

## Phase 5: Effects — Modulators & V-* Collection (Weeks 11-13)

### 5A — Modulators (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|

### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|

### 5C — Modulators (already in VJlive-2 — keep)
V-Maths, V-Frames, V-Grids, V-Harmonaig, V-LXD, V-Marbles, V-Roots, V-Stages Segment, V-Tides

### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)
### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)

| Task ID | Plugin | Status | Source |
|---------|--------|--------|--------|

| P5-DM02 | bad_trip_datamosh (BadTripDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM03 | bass_cannon_datamosh (BassCannonDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM04 | bass_therapy_datamosh (BassTherapyDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM05 | blend (GlitchEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM06 | bullet_time_datamosh (BulletTimeDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM07 | cellular_automata_datamosh (CellularAutomataDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM08 | cotton_candy_datamosh (CottonCandyDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM09 | cupcake_cascade_datamosh (CupcakeCascadeDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM10 | datamosh (CompressionEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM11 | datamosh (DatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM12 | datamosh (PixelBloomEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM13 | datamosh (MeltEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM14 | datamosh (PixelSortEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM15 | datamosh (FrameHoldEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM16 | datamosh_3d (Datamosh3DEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM17 | datamosh_3d (LayerSeparationEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM18 | datamosh_3d (ShatterEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM19 | dimension_splice_datamosh (DimensionSpliceDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM20 | dolly_zoom_datamosh (DollyZoomDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM21 | face_melt_datamosh (FaceMeltDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM22 | fracture_rave_datamosh (FractureRaveDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM23 | liquid_lsd_datamosh (LiquidLSDDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM24 | mosh_pit_datamosh (MoshPitDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM25 | neural_splice_datamosh (NeuralSpliceDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM26 | particle_datamosh_trails (ParticleDatamoshTrailsEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM27 | plasma_melt_datamosh (PlasmaMeltDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM28 | prism_realm_datamosh (PrismRealmDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM29 | sacred_geometry_datamosh (SacredGeometryDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM30 | spirit_aura_datamosh (SpiritAuraDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM31 | temporal_rift_datamosh (TemporalRiftDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM32 | tunnel_vision_datamosh (TunnelVisionDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM33 | unicorn_farts_datamosh (UnicornFartsDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM34 | void_swirl_datamosh (VoidSwirlDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM35 | volumetric_datamosh (VolumetricDatamoshEffect) | P0 | ◯ Todo | VJlive-2 |
| P5-DM36 | volumetric_glitch (VolumetricGlitchEffect) | P0 | ◯ Todo | VJlive-2 |

**Phase 5 Gate:** Full V-* collection loaded. All modulators functional. Every plugin individually reviewed — no batch shortcuts.

### 6A — AI / Neural Systems (VJlive-2 leads)

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|

### 6B — Quantum Consciousness (VJlive-2 leads)

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|

| P6-QC06 | agent_avatar (TravelingAvatarEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC07 | agent_avatar (AgentAvatarEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC08 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC09 | ml_gpu_effects (MLStyleGLEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC10 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC11 | neural_rave_nexus (NeuralRaveNexus) | P0 | ◯ Todo | VJlive-2 |
| P6-QC12 | quantum_consciousness_explorer (QuantumConsciousnessExplorer) | P0 | ◯ Todo | VJlive-2 |
| P6-QC13 | trails (TrailsEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC14 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC06 | agent_avatar (TravelingAvatarEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC07 | agent_avatar (AgentAvatarEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC08 | ml_gpu_effects (MLBaseAsyncEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC09 | ml_gpu_effects (MLStyleGLEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC10 | ml_gpu_effects (MLSegmentationBlurGLEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC11 | neural_rave_nexus (NeuralRaveNexus) | P0 | ◯ Todo | VJlive-2 |
| P6-QC12 | quantum_consciousness_explorer (QuantumConsciousnessExplorer) | P0 | ◯ Todo | VJlive-2 |
| P6-QC13 | trails (TrailsEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-QC14 | tunnel_vision_3 (QuantumConsciousnessSingularityEffect) | P0 | ◯ Todo | VJlive-2 |
### 6C — Agent System

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P6-AG1 | Agent Bridge | ⬜ Todo | VJlive-2 arch + vjlive physics |
| P6-AG2 | Agent Physics — 16D manifold + gravity wells | ⬜ Todo | vjlive only |
| P6-AG3 | Agent Memory (50-snapshot system) | ⬜ Todo | vjlive only |
| P6-AG4 | Agent Control UI | ⬜ Todo | Both |

### 6D — Generators (VJlive-2 unique — keep)

### 6E — Particle/3D Systems (VJlive-2 unique — keep)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P6-P302 | particles_3d (AdvancedParticle3DSystem) | P0 | ◯ Todo | VJlive-2 |
| P6-P303 | particles_3d (Particle3DSystem) | P0 | ◯ Todo | VJlive-2 |
| P6-P304 | shadertoy_particles (ShadertoyParticles) | P0 | ◯ Todo | VJlive-2 |
| P6-P305 | vibrant_retro_styles (RadiantMeshEffect) | P0 | ◯ Todo | VJlive-2 |

| Task ID | Description | Status |
|---------|-------------|--------|

| P6-GE06 | fractal_generator (FractalGenerator) | P0 | ◯ Todo | VJlive-2 |
| P6-GE07 | generators (OscEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE08 | generators (NoiseEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE09 | generators (VoronoiEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE10 | generators (GradientEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE11 | generators (MandalaEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE12 | generators (PlasmaEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE13 | generators (PerlinEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE14 | silver_visions (PathGeneratorEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE15 | vcv_video_generators (HarmonicPatternsGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE16 | vcv_video_generators (FMCoordinatesGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE17 | vcv_video_generators (MacroShapeGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE18 | vcv_video_generators (GranularVideoGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE19 | vcv_video_generators (ResonantGeometryGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE06 | fractal_generator (FractalGenerator) | P0 | ◯ Todo | VJlive-2 |
| P6-GE07 | generators (OscEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE08 | generators (NoiseEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE09 | generators (VoronoiEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE10 | generators (GradientEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE11 | generators (MandalaEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE12 | generators (PlasmaEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE13 | generators (PerlinEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE14 | silver_visions (PathGeneratorEffect) | P0 | ◯ Todo | VJlive-2 |
| P6-GE15 | vcv_video_generators (HarmonicPatternsGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE16 | vcv_video_generators (FMCoordinatesGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE17 | vcv_video_generators (MacroShapeGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE18 | vcv_video_generators (GranularVideoGen) | P0 | ◯ Todo | VJlive-2 |
| P6-GE19 | vcv_video_generators (ResonantGeometryGen) | P0 | ◯ Todo | VJlive-2 |
**Phase 6 Gate:** Live coding engine hot-reloads a GLSL shader at runtime. Agent responds to audio.

---

## Phase 7: UI & Business Layer (Weeks 15-18)

### 7A — User Interface

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P7-U1 | Desktop GUI + SentienceOverlay easter egg | ⬜ Todo | VJlive-2 |
| P7-U2 | Web-based remote control | ⬜ Todo | VJlive-2 |
| P7-U3 | Collaborative Studio UI | ⬜ Todo | VJlive-2 only |
| P7-U4 | Quantum Collaborative Studio | ⬜ Todo | VJlive-2 only |
| P7-U5 | TouchOSC export / mobile interface | ⬜ Todo | vjlive |
| P7-U6 | CLI automation | ⬜ Todo | VJlive-2 |

### 7B — Business / Licensing

### 7C — Additional Effects & Utilities (VJlive-2 + vjlive synthesis)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P7-VE01 | V Sws (VSwsEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE02 | V Sws (HorizontalWaveEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE03 | V Sws (VerticalWaveEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE04 | V Sws (RippleEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE05 | V Sws (SpiralWaveEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE06 | ascii_effect (ASCIIEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE07 | bass_cannon_2 (BassCanon2) | P0 | ◯ Todo | VJlive-2 |
| P7-VE08 | blend (FeedbackEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE09 | blend (BlendAddEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE10 | blend (BlendMultEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE11 | blend (BlendDiffEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE12 | blend (ScanlinesEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE13 | blend (VignetteEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE14 | blend (InfiniteFeedbackEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE15 | blend (BloomEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE16 | blend (BloomShadertoyEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE17 | blend (MixerEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE18 | blend_modes (_BlendMode) | P0 | ◯ Todo | VJlive-2 |
| P7-VE19 | chroma_key (ChromaKeyEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE20 | color (PosterizeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE21 | color (ContrastEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE22 | color (SaturateEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE23 | color (HueEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE24 | color (BrightnessEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE25 | color (InvertEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE26 | color (ThreshEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE27 | color (RGBShiftEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE28 | color (ColorCorrectEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE29 | color_grade (ColorGradeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE30 | colorama (ColoramaEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE31 | displacement_map (DisplacementMapEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE32 | distortion (ChromaticDistortionEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE33 | distortion (PatternDistortionEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE34 | dithering (DitheringEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE35 | fluid_sim (FluidSimEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE36 | geometry (MandalascopeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE37 | geometry (RotateEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE38 | geometry (ScaleEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE39 | geometry (PixelateEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE40 | geometry (RepeatEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE41 | geometry (ScrollEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE42 | geometry (MirrorEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE43 | geometry (ProjectionMappingEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE44 | hyperion (VimanaHyperion) | P0 | ◯ Todo | VJlive-2 |
| P7-VE45 | hyperspace_tunnel (HyperspaceTunnelEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE46 | living_fractal_consciousness (LivingFractalConsciousness) | P0 | ◯ Todo | VJlive-2 |
| P7-VE47 | luma_chroma_mask (LumaChromaMaskEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE48 | lut_grading (LUTGradingEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE49 | milkdrop (MilkdropEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE50 | morphology (MorphologyEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE51 | oscilloscope (OscilloscopeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE52 | plugin_template (CustomEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE53 | pop_art_effects (BenDayDotsEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE54 | pop_art_effects (WarholQuadEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE55 | r16_deep_mosh_studio (R16DeepMoshStudio) | P0 | ◯ Todo | VJlive-2 |
| P7-VE56 | r16_interstellar_mosh (R16InterstellarMosh) | P0 | ◯ Todo | VJlive-2 |
| P7-VE57 | reaction_diffusion (ReactionDiffusionEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE58 | resize_effect (ResizeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE59 | rutt_etra_scanline (RuttEtraScanlineEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE60 | silver_visions (VideoOutEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE61 | silver_visions (ImageInEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE62 | silver_visions (CoordinateFolderEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE63 | silver_visions (AffineTransformEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE64 | silver_visions (PreciseDelayEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE65 | slit_scan (SlitScanEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE66 | sync_eater (SyncEaterEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE67 | time_remap (TimeRemapEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE68 | vcv_video_effects (GaussianBlurEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE69 | vcv_video_effects (MultibandColorEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE70 | vcv_video_effects (HDRToneMapEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE71 | vcv_video_effects (SolarizeEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE72 | vcv_video_effects (ResonantBlurEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE73 | vcv_video_effects (AdaptiveContrastEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE74 | vcv_video_effects (SpatialEchoEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE75 | vcv_video_effects (DelayZoomEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE76 | vibrant_retro_styles (RioAestheticEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE77 | vimana (Vimana) | P0 | ◯ Todo | VJlive-2 |
| P7-VE78 | vimana_hyperion_ultimate (VimanaHyperionUltimate) | P0 | ◯ Todo | VJlive-2 |
| P7-VE79 | vimana_synth (VimanaEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE80 | visualizer (VisualizerEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE81 | visualizer (SpectrumAnalyzerEffect) | P0 | ◯ Todo | VJlive-2 |
| P7-VE82 | visualizer (VUMeterEffect) | P0 | ◯ Todo | VJlive-2 |

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P7-B1 | License server (JWT + RBAC) | ✅ Done | VJlive-2 |
| P7-B2 | Plugin marketplace integration | ✅ Done | VJlive-2 |
| P7-B3 | Developer portal | ✅ Done | vjlive |
| P7-B4 | Burst credit licensing | ⬜ Todo | VJlive-2 |

**Phase 7 Gate:** GUI visible. Sentience slider works. License validation passes.

---

## Phase 8: Integration & Polish (Weeks 19-24)

| Task ID | Description | Status |
|---------|-------------|--------|
| P8-I1 | End-to-end integration testing | ⬜ Todo |
| P8-I2 | Performance benchmarks (60fps target verified) | ⬜ Todo |
| P8-I3 | Security audit (zero P0 vulns) | ⬜ Todo |
| P8-I4 | 80%+ test coverage on all core systems | ⬜ Todo |
| P8-I5 | Complete documentation for all features | ⬜ Todo |
| P8-I6 | Production deployment validation | ⬜ Todo |
| P8-I7 | User acceptance testing | ⬜ Todo |
| P8-I8 | Parity testing: Legacy VJLive vs VJLive3 | ⬜ Todo |
| P8-I2 | Performance benchmarks (60fps target verified) | ⬜ Todo |
| P8-I3 | Security audit (zero P0 vulns) | ⬜ Todo |
| P8-I4 | 80%+ test coverage on all core systems | ⬜ Todo |
| P8-I5 | Complete documentation for all features | ⬜ Todo |
| P8-I6 | Production deployment validation | ⬜ Todo |
| P8-I7 | User acceptance testing | ⬜ Todo |

---

## Dreamer Ports Scheduled
> See `WORKSPACE/KNOWLEDGE/DREAMER_LOG.md` for full analysis.

| ID | Module | Phase | Verdict |
|----|--------|-------|---------|
| DREAMER-000 | Silicon Sigil | P0 | ✅ Done |
| DREAMER-001 | Quantum Consciousness Explorer | P6-Q2 | 🔍 Analysis pending |
| DREAMER-002 | Living Fractal Consciousness | P6-Q4 | 🔍 Analysis pending |
| DREAMER-003 | Neural Engine | P6-AI1 | 🔍 Analysis pending |
| DREAMER-004 | 16D Agent Manifold | P6-AG2 | 🔍 Analysis pending |

---

## Ongoing Quality Gates

| Gate | Requirement | Status |
|------|-------------|--------|
| Q1 | FPS ≥ 58 at every phase completion | 🔄 Ongoing |
| Q2 | Memory stable (no monotonic increase) | 🔄 Ongoing |
| Q3 | 0 safety rail violations | 🔄 Ongoing |
| Q4 | ≥80% test coverage on new code | 🔄 Ongoing |
| Q5 | Silicon Sigil verified on every boot | 🔄 Ongoing |
| Q6 | No file exceeds 750 lines | ✅ Enforced (pre-commit) |
| Q7 | Bespoke treatment for every plugin port | 🔄 Ongoing |

---

## Safety Rail Status

| Rail | Description | Status |
|------|-------------|--------|
| Rail 1 | 60 FPS Sacred | 🔄 Active |
| Rail 2 | Offline-First Architecture | ✅ Compliant |
| Rail 3 | Plugin System Integrity | 🔄 Active |
| Rail 4 | 750-Line Code Discipline | ✅ Enforced |
| Rail 5 | Test Coverage Gate (≥80%) | 🔄 Active |
| Rail 6 | Hardware Fail-Graceful | 🔄 Active |
| Rail 7 | No Silent Failures | 🔄 Active |
| Rail 8 | Resource Leak Prevention | 🔄 Active |
| Rail 9 | Backward Compatibility | 🔄 Active |
| Rail 10 | Security Non-Negotiables | 🔄 Active |

---

## Scale Summary

| Metric | Note |
|--------|------|
| Total features | Hundreds — every plugin is unique, never assume a complete count |
| vjlive-only plugins | Large collection — full audit required, no ceiling defined |
| VJlive-2-only features | Keep all, enhance with vjlive equivalents where applicable |
| Shared plugins | Verify VJlive-2 implementation quality; port improvements from vjlive |
| Depth collection | vjlive/vdepth/ is extensive — audit and port every one individually |
| Audio/Modulator collection | Both Bogaudio and Befaco families — port every module found |
| V-* visual effects | Full collection spread across both codebases — no shortcuts |
| Estimated timeline | 20-24 weeks minimum |

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*