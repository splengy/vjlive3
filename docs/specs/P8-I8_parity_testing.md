# P8-I8: Parity Testing — Legacy VJLive vs VJLive3

**Status:** Draft  
**Priority:** P0 (Critical for Phase 8 Gate)  
**Assigned To:** Implementation Engineer  
**Created:** 2026-02-22  
**Manager:** ROO CODE  

---

## 1. What This Module Does

This task establishes a comprehensive parity testing framework to verify that **VJLive3** (the current codebase) achieves functional parity with the two legacy codebases:

- **VJlive-2**: The clean architecture reference implementation (~150 features)
- **vjlive**: The feature-rich legacy codebase (~250+ features, many unique)

The parity test will systematically compare capabilities across all domains: core systems, effects plugins, hardware integration, audio processing, advanced features (agents, quantum, AI), and UI/UX. It will identify gaps, regressions, and ensure no legacy feature is left behind in the synthesis mission.

---

## 2. Public Interface

### 2.1 Test Framework Structure

```
tests/parity/
├── __init__.py
├── test_core_systems.py       # Matrix, Renderer, Plugin System, Audio Engine
├── test_effects_plugins.py    # All effect plugins (datamosh, depth, audio, etc.)
├── test_hardware_integration.py  # Astra, NDI, Spout, MIDI, DMX, OSC
├── test_advanced_systems.py   # Agents, Quantum, AI, Live Coding, Collaborative Studio
├── test_ui_ux.py              # Desktop GUI, Web UI, TouchOSC, CLI
├── test_distributed.py        # Multi-node, Timecode sync, Output mapping
├── test_generators.py         # Morphagene, Path, Vox Sequencers, Spectraphon
├── test_modulators.py         # Bogaudio, Befaco, V-* collection
├── test_performance.py        # FPS, memory, GPU usage benchmarks
├── test_api_compatibility.py  # REST API, WebSocket, OSC endpoints
├── test_plugin_manifest.py    # Manifest schema compliance
├── test_feature_matrix.py     # Automated cross-check against FEATURE_MATRIX.md
└── report_generator.py        # HTML/JSON report with gap analysis
```

### 2.2 Key Test Functions

Each test module will contain:

```python
def test_feature_parity(feature_name: str, legacy_impl: str, current_impl: str):
    """Test that a specific feature exists and functions identically in both codebases."""
    pass

def test_plugin_manifest_compliance(plugin_path: str):
    """Verify plugin has complete manifest.json with all required fields."""
    pass

def test_plugin_load_and_initialize(plugin_class: Type[BaseEffect]):
    """Test plugin can be loaded, instantiated, and configured without errors."""
    pass

def test_plugin_render_performance(plugin_class: Type[BaseEffect], resolution: Tuple[int, int]):
    """Benchmark plugin rendering performance against legacy baseline."""
    pass

def test_hardware_fallback(device_type: str):
    """Test graceful degradation when hardware is absent."""
    pass

def test_api_endpoint_compatibility(endpoint: str, legacy_spec: dict):
    """Verify API endpoint matches legacy behavior (request/response format)."""
    pass
```

---

## 3. Inputs and Outputs

### 3.1 Inputs

**Legacy Codebases (Read-Only Reference):**
- `/home/happy/Desktop/claude projects/vjlive/` (feature-rich, messy)
- `/home/happy/Desktop/claude projects/VJlive-2/` (clean architecture, fewer features)

**Current Codebase (Under Test):**
- `/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/src/vjlive3/`
- `/home/happy/Desktop/claude projects/VJLive3_The_Reckoning/plugins/`

**Feature Specification:**
- `VJlive-2/FEATURE_MATRIX.md` — Authoritative synthesis decisions
- `BOARD.md` — Task tracking and completion status
- `docs/specs/` — All approved specifications

**Test Configuration:**
- `config/parity_testing.yaml` — Test settings, exclusions, performance thresholds
- `tests/parity/legacy_inventory.json` — Auto-generated inventory of legacy features

### 3.2 Outputs

**Test Results:**
- `tests/parity/results/parity_report_YYYY-MM-DD.json` — Machine-readable gap analysis
- `tests/parity/results/parity_report_YYYY-MM-DD.html` — Human-readable dashboard
- `tests/parity/results/performance_baseline.json` — FPS/memory benchmarks for regression detection

**Coverage Metrics:**
- Feature parity percentage (e.g., "87% of VJlive-2 features present")
- Plugin count: total, ported, missing, broken
- Test coverage: lines, branches, functions

**Gap Analysis:**
- Missing features list (with source codebase location)
- Broken/regressed features (tests failing)
- Performance regressions (FPS drop >5%)
- API incompatibilities (endpoint mismatches)

---

## 4. What It Does NOT Do

- ❌ **Does NOT modify any code** — This is a read-only verification suite
- ❌ **Does NOT port features** — That is handled by separate tasks (P1-P7)
- ❌ **Does NOT fix bugs** — It only identifies them
- ❌ **Does NOT write specs** — It validates against existing specs
- ❌ **Does NOT run on production** — Only on development/test environments
- ❌ **Does NOT test hardware-dependent features without simulation** — Uses mocks/simulators for absent hardware

---

## 5. Test Plan

### 5.1 Phase 1: Inventory Legacy Features (Automated)

**Goal:** Build a complete inventory of all features in both legacy codebases.

**Procedure:**
1. Scan `vjlive/` and `VJlive-2/` directories for:
   - Python modules in `plugins/`, `core/`, `effects/`
   - C++ extensions in `src/`
   - Shader files in `shaders/`
   - Configuration schemas in `config/`
   - UI components in `web_ui/`, `gui/`

2. Extract feature metadata:
   - Plugin class names, inheritance hierarchy
   - Manifest.json fields (if present)
   - Parameter definitions (types, ranges, defaults)
   - Dependencies (OpenGL, CUDA, hardware)
   - Test files (indicates testability)

3. Generate `tests/parity/legacy_inventory.json`:
```json
{
  "vjlive": {
    "plugins": {
      "depth_loop_injection": {
        "path": "plugins/depth_loop_injection.py",
        "class": "DepthLoopInjectionPlugin",
        "params": [...],
        "category": "depth",
        "unique": true
      }
    },
    "core_systems": {...},
    "hardware_integration": {...}
  },
  "vjlive-2": {...}
}
```

**Verification:**
- Inventory matches known counts from FEATURE_MATRIX.md
- No duplicate entries
- All file paths valid

---

### 5.2 Phase 2: Scan Current Codebase (Automated)

**Goal:** Build inventory of VJLive3 features.

**Procedure:**
1. Scan `src/vjlive3/` and `plugins/` directories
2. Extract same metadata as Phase 1
3. Compare against legacy inventory to identify:
   - ✅ Ported features (present in current + one or both legacy)
   - ⚠️ Missing features (in legacy but not current)
   - 🆕 New features (in current but not legacy) — may be intentional
   - ❌ Broken features (present but tests fail)

**Verification:**
- All plugins have `manifest.json` (RAIL 3)
- All manifests have required fields (name, description, parameters, etc.)
- All plugins have `METADATA` constant in code (PRIME_DIRECTIVE Rule 2)

---

### 5.3 Phase 3: Functional Parity Tests (Automated + Manual)

**Goal:** Verify that ported features function identically to legacy.

**Test Categories:**

#### A. Core Systems
- **Matrix/Node Graph**: Create node, connect parameters, save/load state
- **Renderer**: OpenGL context creation, shader compilation, framebuffer management
- **Plugin System**: Discovery, loading, validation, hot-reload (if applicable)
- **Audio Engine**: FFT analysis, beat detection, audio reactivity bus
- **Texture Manager**: Pooling, leak-free operation, format support

#### B. Effect Plugins (Automated per-plugin)
For each plugin in the inventory:

1. **Load Test**: Can plugin be instantiated with valid params?
2. **Parameter Test**: Do all parameters accept valid values and reject invalid?
3. **Render Test**: Does `render(frame, audio_data)` produce output without errors?
4. **Performance Test**: Does it meet FPS target? (e.g., 1920x1080 @ 60fps with N nodes)
5. **Memory Test**: No GPU/CPU memory leaks after 1000 frames
6. **Shader Compilation**: All GLSL compiles without errors or warnings

**Test Data:**
- Use synthetic test frames (color bars, noise, gradient)
- Use synthetic audio data (sine wave, white noise, FFT spectra)
- Compare output against legacy reference images (if available)

#### C. Hardware Integration (Simulated)
For each hardware interface:

1. **Device Detection**: Does system detect device presence/absence correctly?
2. **Fallback Mode**: When hardware missing, does it use simulation gracefully?
3. **Resource Cleanup**: Devices released on shutdown (no file descriptor leaks)
4. **Error Recovery**: Can disconnect/reconnect without crash?

**Devices to Test:**
- Astra Depth Camera (simulated if no hardware)
- NDI (can use test source)
- Spout (Windows only, may need mock)
- MIDI (use virtual MIDI port)
- DMX (use serial mock or ArtNet simulator)
- OSC (use test client)
- Gamepad (use virtual gamepad)

#### D. Advanced Systems
- **Agent System**: Agent creation, update cycle, decision making, memory
- **Quantum Consciousness**: Quantum random, pattern recognition, state sharing
- **AI/Neural**: Model loading, inference, style transfer, creative suggestions
- **Live Coding Engine**: Hot-reload shaders, Python code, error handling
- **Collaborative Studio**: Multi-user session, parameter sync, conflict resolution

#### E. UI/UX
- **Desktop GUI**: All windows visible, controls functional, FPS overlay
- **Web UI**: React components load, WebSocket communication, OSCQuery discovery
- **TouchOSC**: Layout export, control mapping, feedback
- **CLI**: Command-line arguments, automation scripts

#### F. Distributed Architecture (if implemented)
- **Multi-Node**: ZeroMQ coordination, state sync, fault tolerance
- **Timecode Sync**: LTC/MTC/NTP sources, jam sync, drift correction
- **Output Mapping**: Screen warping, edge-blend, mask support
- **Projection Mapping**: Calibration, perspective correction

---

### 5.4 Phase 4: Performance Parity (Automated Benchmarking)

**Goal:** Ensure VJLive3 meets or exceeds legacy performance.

**Benchmark Suite:**

```python
# tests/parity/test_performance.py

def benchmark_render_loop(node_count: int, resolution: Tuple[int, int], duration: float):
    """Measure FPS, frame time variance, memory growth."""
    pass

def benchmark_plugin_chain(plugin_classes: List[Type[BaseEffect]], ...):
    """Test chain of N plugins."""
    pass

def benchmark_audio_latency():
    """Measure audio input → visual output latency."""
    pass

def benchmark_startup_time():
    """Time from process start to first frame."""
    pass

def benchmark_memory_usage():
    """Track RSS, GPU memory over 1-hour run."""
    pass
```

**Baseline Comparison:**
- If legacy performance data exists, compare against it
- If not, establish VJLive3 baseline and flag regressions >5%
- Target: 60 FPS stable at 1920x1080 with 20-30 typical nodes

**Performance Thresholds (SAFETY_RAILS.md):**
- FPS ≥ 58 (2-frame buffer for GC spikes)
- Frame time variance < 5ms
- Memory stable (no monotonic increase)
- Startup < 10 seconds

---

### 5.5 Phase 5: API Compatibility (Automated)

**Goal:** Ensure external interfaces (REST, WebSocket, OSC) match legacy behavior.

**Test Coverage:**

1. **REST API Endpoints** (if applicable):
   - Request/response schema matches legacy
   - Error codes and messages consistent
   - Authentication/authorization behavior
   - Rate limiting behavior

2. **WebSocket Messages**:
   - Message format (JSON schema)
   - Event types and payloads
   - Binary message handling (frames, audio)
   - Reconnection behavior

3. **OSC/ArtNet/DMX**:
   - OSC address patterns
   - ArtNet universe mapping
   - DMX channel assignment

**Method:**
- Record legacy API traffic (use `mitmproxy` or similar)
- Replay same requests to VJLive3
- Compare responses (status, body, headers)
- Flag any differences

---

### 5.6 Phase 6: Feature Matrix Cross-Check (Automated)

**Goal:** Validate that every feature marked "✅ Port" or "⚠️ Port" in FEATURE_MATRIX.md is actually present and working in VJLive3.

**Procedure:**
1. Parse FEATURE_MATRIX.md to extract feature list with synthesis decisions
2. For each feature:
   - Check if feature exists in current codebase (file present, class defined)
   - Run minimal functional test (can instantiate, basic operation)
   - Verify test coverage ≥80% for that feature (SAFETY_RAIL 5)
3. Generate compliance report:
   - ✅ Compliant: Feature present, tests passing, coverage adequate
   - ⚠️ Partial: Feature present but tests missing/failing
   - ❌ Missing: Feature not found in current codebase
   - ❌ Broken: Feature present but non-functional

**Integration with BOARD.md:**
- This test will automatically update task status in BOARD.md for P1-P7 tasks
- Manager approval required for any "❌" findings (create bug tasks)

---

## 6. Success Criteria

### 6.1 Minimum Viable Parity (P0 — Must pass for Phase 8 Gate)

- ✅ **Core Systems**: 100% of VJlive-2 core systems present and functional
  - Matrix/Node Graph
  - Renderer (OpenGL pipeline)
  - Plugin System
  - Audio Engine (FFT + beat detection)
- ✅ **Critical Missing Features** (from vjlive) ported:
  - DMX512 system (P2-D1 through P2-D4)
  - Multi-node coordination (P2-X1)
  - Timecode sync (P2-X2)
  - Output mapping (P2-X3)
  - Projection mapping (P2-X4)
  - All 84 depth plugins (P3-VD01+)
  - Bogaudio collection (P4-BA01-BA10)
  - Befaco modulators (P4-BF01-BF06)
- ✅ **Performance**: 60 FPS stable with typical load (20-30 nodes @ 1080p)
- ✅ **Test Coverage**: ≥80% on all core systems (SAFETY_RAIL 5)

### 6.2 Full Parity (P1 — Target for Phase 8 completion)

- ✅ **All VJlive-2 features** present and tested (≈150 features)
- ✅ **All vjlive unique features** ported (≈180+ features)
- ✅ **All plugins** have complete manifest.json + METADATA constant
- ✅ **All hardware integrations** have graceful fallback
- ✅ **All advanced systems** (Agents, Quantum, AI) functional
- ✅ **API compatibility** 100% (no breaking changes from legacy)
- ✅ **Performance parity** or better (no regressions >5%)

### 6.3 Excellence (P2 — Stretch Goal)

- ✅ **Zero missing features** (100% parity)
- ✅ **Zero broken features** (all tests passing)
- ✅ **Performance improvements** over legacy (faster startup, lower latency)
- ✅ **Better test coverage** than legacy (legacy had 0%, target 90%+)
- ✅ **Documentation completeness** (all features documented, manifests creative)

---

## 7. Implementation Approach

### 7.1 Test Framework Choice

**Use pytest** with custom plugins:

```python
# tests/conftest.py
import pytest
from parity.inventory import load_legacy_inventory, load_current_inventory

@pytest.fixture(scope="session")
def legacy_inventory():
    return load_legacy_inventory()

@pytest.fixture(scope="session")
def current_inventory():
    return load_current_inventory()

@pytest.fixture
def parity_comparison(legacy_inventory, current_inventory):
    return compare_inventories(legacy_inventory, current_inventory)
```

**Custom pytest markers:**
```python
@pytest.mark.parity(category="core")
@pytest.mark.parity(category="plugin")
@pytest.mark.parity(category="hardware")
@pytest.mark.parity(category="performance")
```

### 7.2 Test Data Management

- **Synthetic test frames**: Generate programmatically (color bars, gradients, noise)
- **Legacy reference outputs**: Capture from legacy apps (if available) as PNG/EXR
- **Performance baselines**: Store in `tests/parity/baselines/` as JSON
- **Mock hardware**: Use `unittest.mock` or custom simulators (e.g., `SimulatedAstra`)

### 7.3 Continuous Integration

Add to `.github/workflows/parity.yml`:

```yaml
name: Parity Testing
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  parity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-html
      - name: Run parity tests
        run: |
          pytest tests/parity/ -v --cov=src/vjlive3 --cov=plugins --html=parity_report.html
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: parity-report
          path: parity_report.html
```

**Gate:** Parity test failures block merge to main.

---

## 8. Verification Checkpoints

Before marking P8-I8 complete, the following must pass:

1. ✅ **Inventory completeness**: `legacy_inventory.json` includes all known features from FEATURE_MATRIX.md
2. ✅ **Parity percentage**: ≥95% feature parity (target 100%)
3. ✅ **Test coverage**: ≥80% on core systems, ≥70% on plugins
4. ✅ **Performance**: All benchmarks within 5% of legacy baselines (or better)
5. ✅ **No broken features**: All ported features have passing tests
6. ✅ **Report generation**: HTML report clearly shows gaps and is reviewed by manager
7. ✅ **BOARD.md update**: All P1-P7 tasks verified and status updated based on parity results

---

## 9. Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Legacy codebases are incomplete or broken | Cannot establish true baseline | Use FEATURE_MATRIX.md as ground truth; treat legacy as reference only, not oracle |
| Hardware unavailable for testing | Some tests cannot run | Use simulators/mocks; mark hardware-dependent tests as "conditional" |
| Performance baselines missing | Cannot measure regression | Establish VJLive3 baseline first; future regressions detectable |
| Test suite too slow (1000+ plugins) | CI/CD blocked | Parallelize tests; run full suite nightly; run subset on PRs |
| Legacy features undocumented | Hard to discover | Use code scanning + manual review; involve domain experts |

---

## 10. Deliverables

1. **`tests/parity/`** — Complete test suite with 1000+ tests covering all features
2. **`tests/parity/legacy_inventory.json`** — Auto-generated inventory of legacy features
3. **`tests/parity/results/parity_report_YYYY-MM-DD.html`** — Human-readable dashboard
4. **`tests/parity/results/parity_report_YYYY-MM-DD.json`** — Machine-readable gap analysis
5. **`tests/parity/baselines/performance_baseline.json`** — Performance benchmarks
6. **`docs/parity_testing_results.md`** — Summary report for stakeholders
7. **Updated BOARD.md** — All P1-P7 tasks verified and status updated
8. **New GitHub Actions workflow** (`.github/workflows/parity.yml`) — Automated parity CI

---

## 11. Timeline

**Estimated Effort:** 5-7 days for a single Implementation Engineer

- Day 1: Inventory legacy features (automated scanner)
- Day 2: Scan current codebase, generate comparison report
- Day 3-4: Write functional parity tests (core systems + sample plugins)
- Day 5: Write performance benchmarking suite
- Day 6: Write API compatibility tests
- Day 7: Integrate CI, generate reports, verify against BOARD, final review

**Note:** This is a verification task, not a porting task. Do not fix any gaps found — just report them. Create separate tasks for any missing/broken features.

---

## 12. References

- `VJlive-2/FEATURE_MATRIX.md` — Authoritative feature synthesis decisions
- `BOARD.md` — Task tracking and completion status
- `WORKSPACE/PRIME_DIRECTIVE.md` — Implementation protocols
- `WORKSPACE/SAFETY_RAILS.md` — Performance and quality constraints
- `docs/specs/` — All approved specifications (P1-P7)
- `tests/` — Existing test suite (unit, integration, render)

---

**NEXT STEPS:**
1. Manager approves this spec
2. Implementation Engineer picks up task from inbox
3. Build inventory scanners (automated)
4. Run initial parity assessment
5. Write comprehensive test suite
6. Integrate into CI/CD
7. Generate final report and update BOARD

---

**Task ID:** P8-I8  
**Spec Version:** 1.0  
**Approval Required:** Yes — Manager signature needed before implementation