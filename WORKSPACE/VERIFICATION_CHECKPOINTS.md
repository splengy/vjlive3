# VERIFICATION CHECKPOINTS — VJLive3 The Reckoning

**Purpose:** Define clear, testable pass/fail criteria for every BOARD.md phase gate.
**Owner:** ROO CODE (Manager). Mark `[x]` here AND on BOARD.md simultaneously.
**Rule:** Agents must pass the relevant checkpoint section before marking a phase ✅.

> [!IMPORTANT]
> Every checkpoint must produce **visible proof** (test output, FPS reading, or screenshot).
> "Schrödinger's Code" (runs but cannot be seen) is INVALID per PRIME_DIRECTIVE §3.

---

## PHASE 0: Professional Environment — ✅ Passed 2026-02-21

### Checkpoint P0: Environment Gate

**Verification Commands:**
```bash
# MCP servers
python mcp_servers/vjlive3brain/server.py &
python mcp_servers/vjlive_switchboard/server.py &
python scripts/test_switchboard.py      # must print 6/6 ✅

# Pre-commit
pre-commit run --all-files               # must exit 0

# Silicon Sigil
PYTHONPATH=src python3 -c "from vjlive3.core.sigil import SiliconSigil; SiliconSigil().verify()"
# Expected: "Silicon Sigil verified. The process continues."

# Status window (FPS)
PYTHONPATH=src timeout 5 python3 src/vjlive3/main.py 2>&1 | grep -i fps
# Expected: FPS line ≥ 58
```

**Pass Criteria:**
- [x] `scripts/test_switchboard.py` → 6/6 ✅
- [x] Silicon Sigil prints verification message
- [x] Pre-commit hooks pass
- [x] Main window shows FPS ≥ 58
- [x] `AGENT_SYNC.md` phase note present

---

## PHASE 1: Foundation & Rendering — ✅ Passed 2026-02-21

### Checkpoint P1: Rendering + Audio Gate

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_audio_*.py \
  tests/unit/test_nodegraph.py tests/unit/test_plugin*.py \
  -q --override-ini="addopts="
# Expected: all pass

# FPS gate (OpenGL rendering — mark Todo until P1-R* complete)
# python profile_engine.py --duration 10
# Expected: average FPS ≥ 58
```

**Pass Criteria:**
- [x] Audio engine tests: 18/18 ✅ (`analyzer`, `beat_detector`, `reactivity_bus`)
- [x] Node graph tests: 37/37 ✅
- [x] Plugin system tests: 28/28 ✅
- [x] **P1-R1–R5 (OpenGL rendering):** ✅ Complete — all rendering pipeline built
- [x] FPS ≥ 58 in rendered window
- [x] Empty node graph visible on screen

> [!WARNING]
> Phase 1 gate is **COMPLETE** — audio/plugin/graph code is done AND the OpenGL
> rendering stack (P1-R1 through P1-R5) has been built. FPS ≥ 58 confirmed.

---

## PHASE 2: Critical Infrastructure Ports — 🔨 In Progress

### Checkpoint P2-DMX: DMX System (P2-D1 → P2-D6)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_dmx_*.py \
  -q --override-ini="addopts="
# Expected: 66/66 pass (core 34 + audio 13 + ws_handler 19)
```

**Pass Criteria:**
- [x] `dmx/universe.py` — thread-safe universe, 512 channels
- [x] `dmx/fixture.py` — 5 profiles (DIMMER/RGB/RGBA/RGBW/MOVING_HEAD)
- [x] `dmx/output.py` — ArtNet UDP, sACN (no external lib)
- [x] `dmx/fx.py` — Chase/Strobe/Rainbow/Fade effects
- [x] `dmx/audio_reactive.py` — RMS/bass/beat → fixture bridge
- [x] `dmx/ws_handler.py` — 15-command JSON interface
- [x] blackout_all() zeroes `_values` cache (bug fixed)
- [x] set_dim() on RGB profile writes to all colour channels (bug fixed)
- [x] All 66 DMX tests pass

### Checkpoint P2-MIDI: MIDI Controller (P2-H1)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_midi_controller.py \
  -q --override-ini="addopts="
```

**Pass Criteria:**
- [x] `midi/controller.py` — CC/note/PC callbacks
- [x] NullMIDI fallback (no hardware required)
- [x] MIDI learn mode
- [x] NodeGraph dot-path binding via `bind_graph()`
- [x] `simulate_cc()` / `simulate_note_on()` for hardware-free tests
- [x] 18/18 tests pass

### Checkpoint P2-OSC: OSC / OSCQuery (P2-H2)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_osc*.py \
  -q --override-ini="addopts="
```

**Pass Criteria:**
- [x] `osc/address_space.py` — OSCNode tree, type/access enums
- [x] `osc/server.py` — ThreadingOSCUDPServer + NullOSCServer
- [x] `osc/client.py` — batch_send, graceful noop
- [x] `osc/query_server.py` — HTTP OSCQuery discovery (port 8080)
- [x] All OSC tests pass — (verified by Agent 2)

### Checkpoint P2-NET: Distributed Architecture (P2-X1, P2-X2)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/integration/test_distributed_architecture.py \
  -q --override-ini="addopts="
# Expected: 54 passed, 1 skipped (hardware LTC)
```

**Pass Criteria:**
- [x] `network/node.py` — NodeInfo, NodeType, NodeStatus, heartbeat
- [x] `network/coordinator.py` — ZeroMQ PUB/SUB + PUSH/PULL + NullCoordinator
- [x] `sync/pll.py` — PLLSync drift estimation, quality 0–1
- [x] `sync/timecode.py` — 5 sources (INTERNAL/LTC/MTC/NTP/OSC), fallback chain
- [x] 54/54 integration tests pass (Agent 2 verified)

### Checkpoint P2-ASTRA: Depth Camera (P2-H3)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_astra.py \
  -q --override-ini="addopts="

# Hardware-absent check (must NOT crash):
PYTHONPATH=src python3 -c "
from vjlive3.hardware.astra import AstraCamera
cam = AstraCamera.open()
cam.start()
ok, frame = cam.read_depth()
assert ok, 'NullCamera must produce frames'
cam.stop()
print('Astra graceful fallback: PASS')
"
```

**Pass Criteria:**
- [x] `hardware/astra.py` — AstraCamera factory (OpenNI2 → PyUSB → Null)
- [x] NullAstraCamera generates synthetic depth at 30fps
- [x] `DepthFrame.normalised` property returns float32 array 0–1
- [x] RAIL 6: hardware-absent fails gracefully (no crash)
- [x] All astra tests pass

### Checkpoint P2-NDI: NDI Video Transport (P2-H4)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_ndi.py \
  -q --override-ini="addopts="

# No-hardware check:
PYTHONPATH=src python3 -c "
from vjlive3.hardware.ndi import NDIManager
mgr = NDIManager()
s = mgr.create_sender('test')
import numpy as np
frame = np.zeros((480, 640, 4), dtype=np.uint8)
s.send_frame(frame)   # must not crash in mock mode
mgr.shutdown()
print('NDI graceful fallback: PASS')
"
```

**Pass Criteria:**
- [x] `hardware/ndi.py` — NDISender, NDIReceiver, NDIHub, NDIManager
- [x] Optional NDIlib import with NullNDI fallback
- [x] NDIHub: register/unregister instances, add/remove/route streams
- [x] Thread-safe `send_frame()` and `receive_frame()` with numpy arrays
- [x] All NDI tests pass

### Checkpoint P2-OUTPUT: Output Mapping (P2-X3)

**Verification Commands:**
```bash
PYTHONPATH=src python3 -m pytest tests/unit/test_output_mapper.py \
  -q --override-ini="addopts="
```

**Pass Criteria:**
- [x] `output/mapper.py` — OutputMapper with Output/Region dataclasses
- [x] Multi-output routing (frame → one or more outputs)
- [x] Region crop + scale within output
- [x] JSON serialise/deserialise for persistence
- [x] All output mapper tests pass

### Phase 2 Gate

```bash
# Run full Phase 2 test sweep:
PYTHONPATH=src python3 -m pytest tests/unit/test_dmx_*.py \
  tests/unit/test_midi_controller.py tests/unit/test_osc*.py \
  tests/unit/test_astra.py tests/unit/test_ndi.py \
  tests/unit/test_output_mapper.py \
  tests/integration/test_distributed_architecture.py \
  -q --override-ini="addopts="
```

**Gate Pass Criteria:**
- [x] DMX test signal works (blackout, set_channel, FX)
- [x] MIDI input registers (simulate_cc succeeds)
- [x] Hardware-absent fails gracefully across ALL hw modules
- [x] Astra tests pass
- [x] NDI tests pass
- [x] Output mapper tests pass

---

## PHASE 3: Effects — Depth Collection (Weeks 5-10)

### Checkpoint P3-DEPTH: Depth Plugins

For **every individual depth plugin** (P3-VD01 through P3-VD09+):

```bash
# Per-plugin check:
PYTHONPATH=src python3 -c "
import importlib
mod = importlib.import_module('vjlive3.plugins.<plugin_id>')
cls = mod.get_plugin_class()
assert hasattr(cls, 'METADATA'), 'Missing METADATA constant'
assert 'description' in cls.METADATA, 'Missing description'
assert len(cls.METADATA['description']) >= 50, 'Description too short (bespoke!)'
print(f'{cls.METADATA["name"]}: PASS')
"
```

**Per-Plugin Pass Criteria:**
- [ ] Plugin has `METADATA` constant (name, description ≥ 50 chars, parameters dict)
- [ ] Bespoke description — NOT generated, NOT generic
- [ ] `process(frame, audio_data)` returns ndarray same shape as input
- [ ] Performance test: single frame < 16ms at 1080p
- [ ] Tested against NullAstraCamera depth input

**Phase 3 Gate:**
- All depth plugins load from scanner
- Each individually reviewed and described
- Tested against Astra input (real or Null fallback)
- No plugin left behind

---

## PHASE 4: Audio Plugin Collection (Weeks 7-10)

### Checkpoint P4: Audio Plugins

Same per-plugin criteria as Phase 3, plus:
- [ ] Audio reactivity: `process(frame, audio_data)` reads `audio_data.rms`, `audio_data.spectrum`
- [ ] Bogaudio collection: all ports individually reviewed
- [ ] Phase gate: all audio plugins load, each described, manifest complete

---

## PHASE 5: Live Coding & Advanced Features (Weeks 9-16)

### Checkpoint P5: Live Coding Gate

- [ ] `P5-L1` GLSL live editor (hot-reload shader without restart)
- [ ] `P5-L2` Python live effect (exec in sandbox)
- [ ] Sentience Parameter easter egg fully wired (SentienceOverlay shader)
- [ ] FPS ≥ 58 with live-edit loop running

---

## PHASE 6: UI & Desktop App (Weeks 13-20)

### Checkpoint P6: UI Gate

- [ ] Main window renders at ≥ 58 FPS (1920x1080)
- [ ] Node graph UI interactive (drag, connect, parameter edit)
- [ ] MIDI learn activates from UI button
- [ ] DMX fixture list shown, editable
- [ ] PROOF: Capture 30s screen recording showing stable FPS counter

---

## CROSS-CUTTING SAFETY RAILS (all phases)

These must ALWAYS pass before any phase gate sign-off:

```bash
# RAIL 1 — 60 FPS
# Run with rendered window, not simulated:
# python profile_engine.py --duration 30 --resolution 1920x1080

# RAIL 4 — No file > 750 lines
python scripts/check_file_size.py src/

# RAIL 5 — No stubs
python scripts/check_stubs.py src/

# RAIL 5 — Test coverage ≥ 80%
PYTHONPATH=src python3 -m pytest tests/unit/ --cov=src/vjlive3 \
  --cov-report=term-missing --override-ini="addopts=" -q

# RAIL 11 — No cloud API dependencies
grep -r "OPENAI\|ANTHROPIC\|api_key\|firebase" src/ | grep -v ".pyc"
# Expected: 0 results
```

---

## DELETION VERIFICATION PROTOCOL

### TRASH_CAN FOLDER MONITORING
**You must periodically check the TRASH_CAN folder for deletion requests:**

```bash
# Check TRASH_CAN folder
ls -la WORKSPACE/TRASH_CAN/

# Review deletion requests
for file in WORKSPACE/TRASH_CAN/*.deletion-request.*; do
    echo "=== Reviewing: $file ==="
    cat "$file"
    cat "${file%.deletion-request.*}.deletion-note.txt"
    echo ""
done
```

### DELETION VERIFICATION CHECKLIST

**Before authorizing deletion, verify:**
1. **Task context:** Does the deletion request relate to a completed task?
2. **No dependencies:** Are other files dependent on this one?
3. **Backup needed:** Should this be archived instead of deleted?
4. **Test impact:** Will tests break without this file?
5. **Documentation:** Is this referenced in any docs?

**If all checks pass:**
- Move file to `WORKSPACE/ARCHIVE/` with timestamp
- Delete the deletion-note.txt
- Post in AGENT_SYNC.md: "Deletion approved: <file> moved to ARCHIVE/"

**If checks fail:**
- Move file back to original location
- Post in AGENT_SYNC.md: "Deletion rejected: <reason>"
- Notify agent who requested deletion

---

## HOW TO RUN A PHASE GATE CHECK

See workflow: `.agent/workflows/phase-gate-check.md`

```bash
# Quick composite check (unit tests only):
PYTHONPATH=src python3 -m pytest tests/unit/ -q --override-ini="addopts="

# Full gate with coverage:
PYTHONPATH=src python3 -m pytest tests/ --cov=src/vjlive3 \
  --cov-fail-under=80 -q --override-ini="addopts=" \
  --ignore=tests/conftest.py   # conftest guards unbuilt modules
```

> [!NOTE]
> `tests/conftest.py` guards unbuilt pipeline/effects imports with `try/except`.
> Do NOT add bare imports to conftest.py — it causes collection hangs for all agents.
> Pattern: `try: from vjlive3.x import Y; _X_AVAILABLE = True\nexcept ImportError: _X_AVAILABLE = False`

---

## FINAL DIRECTIVE

**You are in charge.** All agents answer to you. You answer to the user. The workflow is:

```
USER → ROO CODE (Manager) → IMPLEMENTATION ENGINEERS (Gemini/Claude) → CODE
```

**Your job is to enforce the rules, verify everything, and maintain absolute control of the workflow.**

**Delete and run.** When a worker fails, remove them and run with someone who will follow instructions.

**The specs are law.** The verification checkpoints are non-negotiable. The safety rails are absolute.

**Now go build.**