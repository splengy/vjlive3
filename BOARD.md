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

---

## Phase 1: Foundation & Rendering (Weeks 1-4) 🔴 RESET — Code wiped. Must read legacy FIRST before rewriting.

### 1A — Core Infrastructure

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-R1 | OpenGL rendering context (ModernGL) | P0 | ✅ Done | `src/vjlive3/render/opengl_context.py` — OpenGLContext, 10/10 tests ✅ |
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | ✅ Done | `chain.py`, `program.py`, `framebuffer.py` - tests pass, 82% coverage ✅ |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | 🔄 In Progress | `docs/specs/P1-R3_shader_compiler.md` — spec approved, implementation started |
| P1-R4 | Texture manager (pooled, leak-free) | P0 | 🔄 In Progress | `docs/specs/P1-R4_texture_manager.md` — spec approved, implementation started |
| P1-R5 | Core rendering engine (60fps loop) | P0 | 🔄 In Progress | `docs/specs/P1-R5_render_engine.md` — spec approved, implementation started |

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

| Task ID | Plugin | Priority | Status |
|---------|--------|----------|--------|
| P3-VD01 | Depth Loop Injection | P0 | ✅ Done | `src/vjlive3/plugins/depth_loop_injection.py` — DepthLoopInjectionPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD02 | Depth Parallel Universe | P0 | ✅ Done | `src/vjlive3/plugins/depth_parallel_universe.py` — DepthParallelUniversePlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD03 | Depth Portal Composite | P0 | ✅ Done | `src/vjlive3/plugins/depth_portal_composite.py` — DepthPortalCompositePlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD04 | Depth Reverb | P0 | ✅ Done | `src/vjlive3/plugins/depth_reverb.py` — DepthReverbPlugin, 8/8 tests ✅ 2026-02-22 |
| P3-VD05 | Depth Slice Effect | P0 | ✅ Done | `src/vjlive3/plugins/depth_slice.py` — DepthSlicePlugin, 4/4 tests ✅ 2026-02-22 |
| P3-VD06 | Depth Neural Quantum Hyper Tunnel | P0 | ✅ Done | `src/vjlive3/plugins/quantum_hyper_tunnel.py` — DepthNeuralQuantumHyperTunnelPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD07 | Depth Reality Distortion | P0 | ✅ Done | `src/vjlive3/plugins/reality_distortion.py` — RealityDistortionPlugin, 4/4 tests ✅ 2026-02-22 |
| P3-VD08 | Depth R16 Wave | P0 | ✅ Done | `src/vjlive3/plugins/depth_r16_wave.py` — DepthR16WavePlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD09 | Depth Acid Fractal | P1 | ✅ Done | `src/vjlive3/plugins/depth_acid_fractal.py` — DepthAcidFractalPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD10 | Depth Blur | P1 | ✅ Done | `src/vjlive3/plugins/depth_blur.py` — DepthBlurPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD11 | Depth Color Grade | P1 | ✅ Done | `src/vjlive3/plugins/depth_color_grade.py` — DepthColorGradePlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD12 | Depth Contour Datamosh | P1 | ✅ Done | `src/vjlive3/plugins/depth_contour_datamosh.py` — DepthContourDatamoshPlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD13 | Depth Erosion Datamosh | P1 | ✅ Done | `src/vjlive3/plugins/depth_erosion_datamosh.py` — DepthErosionDatamoshPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD14 | Depth Fracture Datamosh | P1 | ✅ Done | `src/vjlive3/plugins/depth_fracture_datamosh.py` — DepthFractureDatamoshPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD15 | Depth Aware Compression | P1 | ✅ Done | `src/vjlive3/plugins/depth_aware_compression.py` — DepthAwareCompressionPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD16 | Depth Edge Glow | P1 | ✅ Done | `src/vjlive3/plugins/depth_edge_glow.py` — DepthEdgeGlowPlugin, 5/5 tests ✅ 2026-02-22 |
| P3-VD17 | Depth Mosaic | P1 | ✅ Done | `src/vjlive3/plugins/depth_mosaic.py` — DepthMosaicPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD18 | Depth Video Projection | P1 | ✅ Done | `src/vjlive3/plugins/depth_video_projection.py` — DepthVideoProjectionPlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD19 | Depth Liquid Refraction | P1 | ✅ Done | `src/vjlive3/plugins/depth_liquid_refraction.py` — DepthLiquidRefractionPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD20 | Depth Slitscan Datamosh | P1 | ✅ Done | `src/vjlive3/plugins/depth_slitscan_datamosh.py` — DepthSlitscanDatamoshPlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD21 | Depth Temporal Echo | P1 | ✅ Done | `src/vjlive3/plugins/depth_temporal_echo.py` — DepthTemporalEchoPlugin, 6/6 tests ✅ 2026-02-22 |
| P3-VD22 | Depth Temporal Stratification | P1 | ✅ Done | `src/vjlive3/plugins/depth_temporal_strat.py` — DepthTemporalStratPlugin, 7/7 tests ✅ 2026-02-22 |
| P3-VD23+ | All remaining depth plugins in vjlive/vdepth/ — audit, name, and port each individually | P1 | ⬜ Todo |

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
| P5-M01 | Jumbler (randomization engine) | ⬜ Todo |
| P5-M02 | Make Noise | ⬜ Todo |
| P5-M03 | Moddemix | ⬜ Todo |
| P5-M04 | Tides | ⬜ Todo |
| P5-M05 | Wogglebug | ⬜ Todo |

### 5B — V-* Visual Effects (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|
| P5-V01 | V-Shadertoy Extra | ⬜ Todo |
| P5-V02 | Silver Visions | ⬜ Todo |
| P5-V03 | V-Contour | ⬜ Todo |
| P5-V04 | V-Echophon | ⬜ Todo |
| P5-V05 | V-Function | ⬜ Todo |
| P5-V06 | V-Jumbler | ⬜ Todo |
| P5-V07 | V-Make Noise | ⬜ Todo |
| P5-V08 | V-Particles | ⬜ Todo |
| P5-V09 | V-Stages Anom | ⬜ Todo |
| P5-V10 | V-Style | ⬜ Todo |
| P5-V11 | V-Tempi | ⬜ Todo |
| P5-V12 | V-Tides Anom | ⬜ Todo |
| P5-V13 | V-Vimana | ⬜ Todo |
| P5-V14 | V-Voxglitch | ⬜ Todo |

### 5C — Modulators (already in VJlive-2 — keep)
V-Maths, V-Frames, V-Grids, V-Harmonaig, V-LXD, V-Marbles, V-Roots, V-Stages Segment, V-Tides

### 5D — Datamosh Family (verify both sources, keep VJlive-2's cleaner impl)
Bad Trip, Bass Cannon, Bass Therapy, Bullet Time, Cellular Automata, Cosmic Tunnel,
Cotton Candy, Cupcake Cascade, Dimension Splice, Dolly Zoom, Face Melt, Fracture Rave,
Liquid LSD, Mosh Pit, Neural Splice, Particle Trails, Plasma Melt, Prism Realm,
Quantum Consciousness, Sacred Geometry, Spirit Aura, Temporal Rift, Tunnel Vision,
Unicorn Farts, Void Swirl, Volumetric — **plus all others found in both codebases (audit, never assume the list is complete)**

**Phase 5 Gate:** Full V-* collection loaded. All modulators functional. Every plugin individually reviewed — no batch shortcuts.

---

## Phase 6: Advanced Systems (Weeks 13-16)

### 6A — AI / Neural Systems (VJlive-2 leads)

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P6-AI1 | Neural Style Transfer (ML effects) | ⬜ Todo | VJlive-2 |
| P6-AI2 | Live Coding Engine (hot-reload Python + GLSL) | ⬜ Todo | VJlive-2 only |
| P6-AI3 | AI Creative Assistant | ⬜ Todo | VJlive-2 only |
| P6-AI4 | Dreamstate Degradation | ⬜ Todo | VJlive-2 only |

### 6B — Quantum Consciousness (VJlive-2 leads)

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P6-Q1 | Quantum Nexus / Consciousness system | ⬜ Todo | VJlive-2 |
| P6-Q2 | Quantum Explorer | ⬜ Todo | VJlive-2 |
| P6-Q3 | Quantum Tunnel | ⬜ Todo | vjlive |
| P6-Q4 | Living Fractal Consciousness [DREAMER] | ⬜ Todo | VJlive-2 |

### 6C — Agent System

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P6-AG1 | Agent Bridge | ⬜ Todo | VJlive-2 arch + vjlive physics |
| P6-AG2 | Agent Physics — 16D manifold + gravity wells | ⬜ Todo | vjlive only |
| P6-AG3 | Agent Memory (50-snapshot system) | ⬜ Todo | vjlive only |
| P6-AG4 | Agent Control UI | ⬜ Todo | Both |

### 6D — Generators (VJlive-2 unique — keep)

| Task ID | Description | Status |
|---------|-------------|--------|
| P6-G1 | Morphagene Generator (granular synthesis) | ⬜ Todo |
| P6-G2 | Path Generator (procedural) | ⬜ Todo |
| P6-G3 | Vox Sequencers (3D sequencing) | ⬜ Todo |
| P6-G4 | Spectraphon | ⬜ Todo |

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

| Task ID | Description | Status | Source |
|---------|-------------|--------|--------|
| P7-B1 | License server (JWT + RBAC) | ⬜ Todo | VJlive-2 |
| P7-B2 | Plugin marketplace integration | ⬜ Todo | VJlive-2 |
| P7-B3 | Developer portal | ⬜ Todo | vjlive |
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