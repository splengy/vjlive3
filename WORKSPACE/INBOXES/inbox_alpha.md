# Implementation Tasks — Phase 4 Audio Plugin Collection

**Assigned By:** Manager-Gemini-3.1
**Date:** 2026-02-22
**Priority:** P0-P1 — Complete Phase 4 Audio Plugin collection

---

## Context

Phase 4 requires implementing 17 audio plugins from both Bogaudio and Befaco collections. These are audio-reactive effects that respond to live audio input. All specifications have been created and approved. These plugins provide essential audio processing, mixing, and modulation capabilities for VJLive3.

---

## Task List

### 4A — Bogaudio Collection (10 modules)

#### P4-BA01: B1to8 (8-channel mixer with mute/solo)
**Spec:** `docs/specs/phase4_audio/P4-BA01_B1to8.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA02: BLFO (low-frequency oscillator)
**Spec:** `docs/specs/phase4_audio/P4-BA02_BLFO.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA03: BMatrix81 (8x1 router/switcher)
**Spec:** `docs/specs/phase4_audio/P4-BA03_BMatrix81.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA04: BPEQ6 (6-band parametric EQ)
**Spec:** `docs/specs/phase4_audio/P4-BA04_BPEQ6.md`
**Priority:** P0
**Dependencies:** numpy, scipy
**Test coverage:** ≥80%

#### P4-BA05: BSwitch (2-channel switch)
**Spec:** `docs/specs/phase4_audio/P4-BA05_BSwitch.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA06: BVCF (voltage-controlled filter)
**Spec:** `docs/specs/phase4_audio/P4-BA06_BVCF.md`
**Priority:** P0
**Dependencies:** numpy, scipy
**Test coverage:** ≥80%

#### P4-BA07: BVCO (voltage-controlled oscillator)
**Spec:** `docs/specs/phase4_audio/P4-BA07_BVCO.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA08: BVELO (envelope follower)
**Spec:** `docs/specs/phase4_audio/P4-BA08_BVELO.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA09: NMix4 (4-channel mixer with VU)
**Spec:** `docs/specs/phase4_audio/P4-BA09_NMix4.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BA10: NXFade (crossfader)
**Spec:** `docs/specs/phase4_audio/P4-BA10_NXFade.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

### 4B — Befaco Modulators (6 modules)

#### P4-BF01: V-Even (even harmonic distortion)
**Spec:** `docs/specs/phase4_audio/P4-BF01_V-Even.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BF02: V-Morphader (morphing filter)
**Spec:** `docs/specs/phase4_audio/P4-BF02_V-Morphader.md`
**Priority:** P0
**Dependencies:** numpy, scipy
**Test coverage:** ≥80%

#### P4-BF03: V-Outs (output router)
**Spec:** `docs/specs/phase4_audio/P4-BF03_V-Outs.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BF04: V-Pony (vactrol-based filter)
**Spec:** `docs/specs/phase4_audio/P4-BF04_V-Pony.md`
**Priority:** P0
**Dependencies:** numpy, scipy
**Test coverage:** ≥80%

#### P4-BF05: V-Scope (oscilloscope)
**Spec:** `docs/specs/phase4_audio/P4-BF05_V-Scope.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

#### P4-BF06: V-Voltio (voltage-controlled amplifier)
**Spec:** `docs/specs/phase4_audio/P4-BF06_V-Voltio.md`
**Priority:** P0
**Dependencies:** numpy
**Test coverage:** ≥80%

### 4C — Audio Reactive (1 module)

#### P4-AR01: Audio Reactive Collection (audit and port existing audio-reactive visual effects)
**Spec:** `docs/specs/phase4_audio/P4-AR01_Audio_Reactive_Collection.md`
**Priority:** P1
**Dependencies:** numpy, vjlive3.audio.audio_analyzer
**Test coverage:** ≥80%

---

### P8-I8: Parity Testing (Legacy VJLive vs VJLive3)

**Spec:** `docs/specs/phase8_integration/P8-I8_Parity_Testing.md`
**Priority:** P0
**Dependencies:** ast, json, pytest
**Test coverage:** ≥80%

---

## Instructions

1. Read each specification file thoroughly before starting implementation.
2. Implement modules in order: P4-BA01 through P4-AR01.
3. Follow the Definition of Done in each spec:
   - All tests pass
   - No file over 750 lines
   - No stubs
   - Git commit with proper message
   - Update BOARD.md
   - Write AGENT_SYNC.md handoff note
4. Use the pre-commit hooks to verify:
   - `scripts/check_stubs.py`
   - `scripts/check_file_size.py`
   - `scripts/check_performance_regression.py`
5. Respect all Safety Rails in `WORKSPACE/SAFETY_RAILS.md`.
6. Coordinate with other agents via `WORKSPACE/COMMS/AGENT_SYNC.md`.

---

## Critical Notes

- These are **audio** modules — real-time performance is critical.
- All modules must conform to the `PluginBase` interface in `src/vjlive3/plugins/api.py`.
- Parameter ranges and defaults must match the legacy manifest specifications exactly.
- Ensure proper handling of edge cases: audio clipping, buffer underruns, invalid parameters.

---

## Verification

After completing each module:
1. Run tests: `pytest tests/plugins/test_<plugin_name>.py`
2. Check coverage: `pytest --cov=src/vjlive3/plugins`
3. Update `BOARD.md` status to ✅ Done
4. Write completion note in `WORKSPACE/COMMS/STATUS/P4-<task-id>.txt`
5. Create `task_completion_P4-<task-id>.md` with summary

---

**Begin implementation. Report progress via AGENT_SYNC.md.**