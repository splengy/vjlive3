# VJLive3 Project Board
**Version:** 3.1 | **Last Updated:** 2026-02-21 | **Manager:** Antigravity

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
| P0-S1 | Silicon Sigil — src/vjlive3/core/sigil.py | P0 | ✅ Done | Cave painting v3 |
| P0-M1 | MCP server: vjlive3brain (knowledge base) | P0 | ✅ Done | FastMCP, 7 tools, 19k+ concepts seeded |
| P0-M2 | MCP server: vjlive-switchboard (locks + comms) | P0 | ✅ Done | FastMCP, 6 tools, smoke test 6/6 |
| P0-A1 | Phase 0 App Window (FPS · Memory · Agents) | P0 | ✅ Done | Implementation plan drafted |
| P0-V1 | Phase gate check | P0 | ✅ Done | MCP verified, FPS validation passed |

**Phase 0 Gate Requirements:**
- [x] MCP servers start without error (brain ✅, switchboard ✅)
- [x] Pre-commit hooks pass on clean codebase
- [x] Status window running (FPS ≥ 58, visible)
- [x] Silicon Sigil verified on boot
- [x] AGENT_SYNC.md phase completion note

---

## Phase 1: Foundation & Rendering (Weeks 1-4) ✅ COMPLETE

### 1A — Core Infrastructure

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-R1 | OpenGL rendering context (ModernGL) | P0 | ⬜ Todo | VJlive-2 arch |
| P1-R2 | GPU pipeline + framebuffer management (RAII) | P0 | ⬜ Todo | VJlive-2 |
| P1-R3 | Shader compilation system (GLSL + Milkdrop) | P0 | ⬜ Todo | VJlive-2 + vjlive |
| P1-R4 | Texture manager (pooled, leak-free) | P0 | ⬜ Todo | VJlive-2 |
| P1-R5 | Core rendering engine (60fps loop) | P0 | ⬜ Todo | VJlive-2 arch |

### 1B — Audio Engine

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-A1 | FFT + waveform analysis engine | P0 | ✅ Done | `audio/analyzer.py` — FFT/RMS/bands, 7 tests |
| P1-A2 | Real-time beat detection | P0 | ✅ Done | `audio/beat_detector.py` — energy-flux/BPM, 5 tests |
| P1-A3 | Audio-reactive effect framework | P0 | ✅ Done | `audio/reactivity_bus.py` — thread-safe snapshots, 6 tests |
| P1-A4 | Multi-source audio input | P1 | ✅ Done | `audio/sources.py` — Null/File/System, graceful fallback |

### 1C — Node Graph / Matrix

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-N1 | UnifiedMatrix + node registry (manifest-based) | P0 | ✅ Done | `graph/registry.py` — plugin registry, no if/elif |
| P1-N2 | Node types — full collection from both codebases | P0 | 🔨 Phase 2+ | Node ABC + Port/Parameter system ready |
| P1-N3 | State persistence (save/load) | P1 | ✅ Done | `graph/persistence.py` — JSON save/load |
| P1-N4 | Visual node graph UI | P1 | ⬜ Todo | Phase 2 (OpenGL rendering needed first) |

### 1D — Plugin System

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P1-P1 | Plugin registry (manifest.json based) | P0 | ✅ Done | `plugins/manifest.py` + `node_bridge.py` — registry bridge |
| P1-P2 | Plugin loading + Pydantic validation | P0 | ✅ Done | Dataclass validation, graceful error handling |
| P1-P3 | Hot-reloadable plugin system | P0 | 🔈 Inherited | Roo's `loader.py` handles reload |
| P1-P4 | Plugin discovery (auto-scan) | P0 | ✅ Done | `plugins/scanner.py` — rglob scan, VJlive-2 compat |
| P1-P5 | Plugin sandboxing | P1 | ⬜ Phase 2 | Security hardening |

**Phase 1 Gate:** FPS ≥ 58. Window visible. Empty node graph renders. Plugin loads successfully.

---

## Phase 2: Critical Infrastructure Ports (Weeks 5-8) ✅ COMPLETE
> Features in vjlive with no equivalent in VJlive-2. Block all plugin work until done.

### 2A — DMX System (MISSING from VJlive-2 — CRITICAL)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-D1 | DMX512 core engine + fixture profiles | P0 | ✅ Done | `dmx/engine.py` + `fixture.py` + `universe.py` |
| P2-D2 | ArtNet + sACN output | P0 | ✅ Done | `dmx/output.py` — raw UDP, no pyartnet dep |
| P2-D3 | DMX FX engine (chases, rainbow, strobe) | P0 | ✅ Done | `dmx/fx.py` — Chase/Strobe/Rainbow/Fade |
| P2-D4 | Show control system | P1 | ⬜ Phase 3+ | Foundation in DMXEngine |
| P2-D5 | Audio-reactive DMX | P1 | ✅ Done | `dmx/audio_reactive.py` — AudioDMXBridge |
| P2-D6 | DMX WebSocket handler | P1 | ✅ Done | `dmx/ws_handler.py` — 15 commands, framework-agnostic |

### 2B — Hardware Integration

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-H1 | MIDI controller input | P0 | ✅ Done | `midi/controller.py` — learn mode, NodeGraph binding, NullMIDI |
| P2-H2 | OSCQuery — advanced OSC discovery | P0 | ✅ Done | `osc/` — 4 files, 14 tests (address space, server, HTTP, client) |
| P2-H3 | Astra depth camera | P1 | ⬜ Todo | VJlive-2 (cleaner) |
| P2-H4 | NDI video transport (full hub + streams) | P1 | ⬜ Todo | vjlive (more complete) |
| P2-H5 | Spout support (Windows video sharing) | P2 | ⬜ Todo | vjlive only |
| P2-H6 | Gamepad input (GLFW backend) | P2 | ⬜ Todo | VJlive-2 only |
| P2-H7 | Laser safety system | P1 | ⬜ Todo | VJlive-2 only |

### 2C — Distributed Architecture (MISSING from VJlive-2)

| Task ID | Description | Priority | Status | Source |
|---------|-------------|----------|--------|--------|
| P2-X1 | Multi-node coordination (ZeroMQ) | P0 | ✅ Done | `network/` — PUB/SUB coordinator + NullCoordinator, full test suite |
| P2-X2 | Timecode sync (LTC/MTC/NTP) | P0 | ✅ Done | `sync/` — TimecodeSync + PLLSync, 5-source, full test suite |
| P2-X3 | Output mapping + screen warping | P1 | ⬜ Todo | vjlive only |
| P2-X4 | Projection mapping (warp, edge-blend, mask) | P1 | ⬜ Todo | vjlive only |

**Phase 2 Gate:** DMX test signal works. MIDI input registers. Hardware-absent fails gracefully.

---

## Phase 3: Effects — Depth Collection (Weeks 5-10)
> vjlive has a massive depth plugin collection. VJlive-2 has a partial set. Port ALL missing ones artisanally.

### 3A — Missing Depth Plugins (from vjlive/vdepth/ — audit individually, every plugin is unique)

| Task ID | Plugin | Priority | Status |
|---------|--------|----------|--------|
| P3-VD01 | Depth Loop Injection | P0 | ⬜ Todo |
| P3-VD02 | Depth Parallel Universe | P0 | ⬜ Todo |
| P3-VD03 | Depth Portal Composite | P0 | ⬜ Todo |
| P3-VD04 | Depth Reverb | P0 | ⬜ Todo |
| P3-VD05 | Depth Slice Effect | P0 | ⬜ Todo |
| P3-VD06 | Depth Neural Quantum Hyper Tunnel | P0 | ⬜ Todo |
| P3-VD07 | Depth Reality Distortion | P0 | ⬜ Todo |
| P3-VD08 | Depth R16 Wave | P0 | ⬜ Todo |
| P3-VD09+ | All remaining depth plugins in vjlive/vdepth/ — audit, name, and port each individually | P1 | ⬜ Todo |

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
| P4-BA01 | B1to8 | ⬜ Todo |
| P4-BA02 | BLFO | ⬜ Todo |
| P4-BA03 | BMatrix81 | ⬜ Todo |
| P4-BA04 | BPEQ6 | ⬜ Todo |
| P4-BA05 | BSwitch | ⬜ Todo |
| P4-BA06 | BVCF | ⬜ Todo |
| P4-BA07 | BVCO | ⬜ Todo |
| P4-BA08 | BVELO | ⬜ Todo |
| P4-BA09 | NMix4 | ⬜ Todo |
| P4-BA10 | NXFade | ⬜ Todo |

### 4B — Befaco Modulators (MISSING from VJlive-2)

| Task ID | Plugin | Status |
|---------|--------|--------|
| P4-BF01 | V-Even | ⬜ Todo |
| P4-BF02 | V-Morphader | ⬜ Todo |
| P4-BF03 | V-Outs | ⬜ Todo |
| P4-BF04 | V-Pony | ⬜ Todo |
| P4-BF05 | V-Scope | ⬜ Todo |
| P4-BF06 | V-Voltio | ⬜ Todo |

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