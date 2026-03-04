# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I8F_integration_testing.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8F — Integration Testing

**What This Module Does**

Implements a comprehensive integration testing framework for VJLive3 that validates end-to-end system behavior across all major components: depth camera pipelines, effect chains, agent coordination, plugin systems, WebSocket APIs, and multi-node synchronization. The framework provides automated test orchestration, real-time performance monitoring during tests, hardware-in-the-loop testing capabilities, and CI/CD integration with detailed reporting.

---

## Architecture Decisions

- **Pattern:** Test Orchestrator + Fixture Manager + Performance Monitor
- **Rationale:** Integration tests must validate component interactions, not just unit behavior. Orchestration ensures proper setup/teardown, fixtures provide realistic test data, and performance monitoring verifies 60 FPS requirements.
- **Constraints:**
  - Must test real hardware (depth cameras, MIDI controllers) when available
  - Must not degrade system performance during tests
  - Must provide clear failure diagnostics
  - Must support parallel test execution
  - Must integrate with CI/CD pipeline
  - Must generate compliance reports for Phase 8 exit criteria

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `.github/workflows/ci-cd.yml` | CI/CD pipeline | Port — test orchestration |
| VJlive-2 | `CRITICAL_PATH_DAY2_STATUS.md` | Test status tracking | Reference — testing metrics |
| VJlive-2 | `DEPLOYMENT_READINESS_CHECKLIST.md` | Testing checklist | Port — test categories |
| VJlive-1 | `test_live_coding_integration.py` | Integration tests | Port — test patterns |
| VJlive-1 | `test_multi_camera_system.py` | Multi-camera tests | Port — hardware tests |
| VJlive-1 | `test_mandala_hydra_integration.py` | Effect integration tests | Port — effect tests |

---

## Public Interface

```python
class IntegrationTestFramework:
    def __init__(self, config: TestConfig) -> None:...
    def register_suite(self, suite: TestSuite) -> None:...
    def run_all_tests(self, parallel: bool = False) -> TestReport:...
    def run_suite(self, suite_name: str, parallel: bool = False) -> TestReport:...
    def run_test(self, suite_name: str, test_name: str) -> TestResult:...
    def generate_report(self, format: str = 'html') -> bytes:...
    def export_results(self, path: str, format: str = 'json') -> None:...
    def validate_system_ready(self) -> ValidationResult:...
    def setup_test_environment(self) -> None:...
    def teardown_test_environment(self) -> None:...
    def get_performance_baseline(self) -> dict:...
    def compare_to_baseline(self, current: dict) -> dict:...
```

---

## Test Suites

### 1. Core System Integration

**Purpose:** Validate that all core systems work together correctly.

**Tests:**
- `test_depth_to_effects_pipeline` — Depth data flows from camera through effects
- `test_audio_to_effects_pipeline` — Audio analysis drives effect parameters
- `test_agent_plugin_bus_integration` — Agents communicate via plugin bus
- `test_telemetry_pipeline_flow` — Telemetry collected and exported
- `test_config_preset_system` — Presets save/load across all namespaces
- `test_unified_matrix_state` — Matrix state consistent across all views

**Fixtures:**
- Depth camera (real or simulated)
- Audio input (file or microphone)
- Effect chain with 5+ effects
- 3 agents (julie-roo, maxx-roo, desktop-roo)
- Telemetry exporters (UDP, WebSocket)

**Performance Requirements:**
- Pipeline latency < 16ms (60 FPS)
- CPU usage < 80% during test
- Memory growth < 10MB over 5 minutes
- Zero dropped frames in effect rendering

---

### 2. Multi-Node Synchronization

**Purpose:** Validate distributed VJLive nodes stay synchronized.

**Tests:**
- `test_node_heartbeat_exchange` — Nodes exchange heartbeats correctly
- `test_state_sync_across_nodes` — Matrix state syncs across cluster
- `test_plugin_distribution` — Plugins distributed to all nodes
- `test_failover_recovery` — System recovers when node fails
- `test_load_balancing` — Load balanced across available nodes
- `test_network_partition_handling` — Handles network splits gracefully

**Fixtures:**
- 3-5 simulated nodes (Docker containers)
- Network latency simulation (tc/netem)
- Node failure injection (kill processes)
- Shared state backend (Redis/etcd)

**Performance Requirements:**
- State sync latency < 100ms
- Heartbeat interval 1s with 3s timeout
- Failover recovery < 5s
- No state divergence during partition

---

### 3. Agent Collaboration

**Purpose:** Validate multi-agent coordination and decision-making.

**Tests:**
- `test_agent_state_broadcast` — Agents broadcast state correctly
- `test_agent_parameter_negotiation` — Agents negotiate parameter changes
- `test_agent_emergency_stop` — Emergency stop propagates to all agents
- `test_agent_load_distribution` — Work distributed among agents
- `test_agent_failure_handling` — System handles agent crash/restart
- `test_agent_preset_sharing` — Agents share presets via plugin bus

**Fixtures:**
- 3 agent instances (julie-roo, maxx-roo, desktop-roo)
- Agent plugin bus mock
- Mock LLM responses for agent decisions
- Performance metrics collector

**Performance Requirements:**
- Agent message latency < 10ms
- Decision latency < 100ms
- No agent deadlock during negotiation
- Graceful degradation when agent fails

---

### 4. Plugin Ecosystem

**Purpose:** Validate plugin loading, execution, and isolation.

**Tests:**
- `test_plugin_discovery` — Plugins discovered from filesystem
- `test_plugin_loading` — Plugins load without errors
- `test_plugin_lifecycle` — Plugin init/start/stop/cleanup
- `test_plugin_isolation` — Plugin errors don't crash host
- `test_plugin_performance` — Plugins meet performance budgets
- `test_plugin_dependency_resolution` — Dependencies resolved correctly
- `test_plugin_hot_reload` — Plugins reload without restart

**Fixtures:**
- 10+ test plugins (depth effects, audio effects, generators)
- Plugin with intentional errors (for isolation test)
- Plugin with missing dependencies
- Plugin performance profiler

**Performance Requirements:**
- Plugin load time < 100ms
- Plugin execution overhead < 1ms per frame
- Memory isolation: plugin leak < 1MB
- Hot reload completes < 500ms

---

### 5. WebSocket API

**Purpose:** Validate WebSocket API for UI and external clients.

**Tests:**
- `test_websocket_connection_handshake` — Connection established correctly
- `test_websocket_parameter_updates` — Parameter changes broadcast
- `test_websocket_effect_chain_updates` — Chain modifications broadcast
- `test_websocket_agent_state_streaming` — Agent state streamed in real-time
- `test_websocket_telemetry_streaming` — Telemetry data streamed
- `test_websocket_error_handling` — Errors reported correctly
- `test_websocket_reconnection` — Client reconnects and resyncs

**Fixtures:**
- WebSocket client simulator
- Message validator
- Latency simulator
- Connection failure injector

**Performance Requirements:**
- Message latency < 50ms
- Broadcast to 10 clients < 100ms
- Reconnection and resync < 2s
- No message loss during reconnection

---

### 6. Hardware Integration

**Purpose:** Validate real hardware (depth cameras, MIDI controllers).

**Tests:**
- `test_astra_camera_initialization` — Astra camera initializes
- `test_realsense_camera_initialization` — RealSense camera initializes
- `test_depth_frame_processing` — Depth frames processed at 30/60 FPS
- `test_midi_controller_input` — MIDI controls mapped correctly
- `test_hardware_failure_recovery` — System recovers from camera disconnect
- `test_hardware_hot_swap` — Camera replacement detected and initialized

**Fixtures:**
- Intel RealSense D435/D455
- Orbbec Astra S
- MIDI controller (Launchpad, Push)
- USB hub for hot-swap testing

**Performance Requirements:**
- Depth frame latency < 33ms (30 FPS) or < 16ms (60 FPS)
- No dropped depth frames under load
- MIDI input latency < 5ms
- Camera recovery < 3s after reconnect

---

### 7. Performance & Scalability

**Purpose:** Validate system meets 60 FPS sacred requirement and scales.

**Tests:**
- `test_sustained_60fps_with_10_effects` — 60 FPS with 10 active effects
- `test_sustained_60fps_with_20_effects` — 60 FPS with 20 active effects
- `test_memory_leak_detection` — No memory growth over 1 hour
- `test_cpu_scaling_with_effects` — CPU usage scales linearly
- `test_multi_node_performance` — Performance doesn't degrade with nodes
- `test_agent_overhead` — Agent overhead < 5% CPU
- `test_telemetry_overhead` — Telemetry overhead < 1% CPU

**Fixtures:**
- Performance profiler (py-spy, cProfile)
- Memory tracker (tracemalloc, psutil)
- Frame counter (count dropped frames)
- Load generator (simulate user interactions)

**Performance Requirements:**
- **Sacred:** 60 FPS sustained, zero dropped frames
- CPU usage < 90% at 60 FPS
- Memory growth < 1MB/hour
- Agent overhead < 5% CPU
- Telemetry overhead < 1% CPU

---

### 8. User Workflow

**Purpose:** Validate complete user workflows from startup to shutdown.

**Tests:**
- `test_startup_to_rendering` — App starts and renders first frame < 5s
- `test_effect_chain_build` — User builds complex chain (10 effects)
- `test_parameter_automation` — Parameters automated via Lumen script
- `test_preset_save_load` — Preset saved and loaded correctly
- `test_midi_control_workflow` — MIDI controls effect parameters
- `test_agent_collaboration_workflow` — Agents assist during performance
- `test_shutdown_cleanup` — App shuts down cleanly, no resource leaks

**Fixtures:**
- Simulated user input (keyboard, mouse, MIDI)
- Lumen script executor
- Performance timer
- Resource leak detector

**Performance Requirements:**
- Startup to first frame < 5s
- Parameter update latency < 16ms
- Preset load < 500ms
- Shutdown cleanup < 2s

---

## Test Fixtures

### Hardware Fixtures

```python
@pytest.fixture(scope="session")
def astra_camera():
    """Initialize Astra camera for tests."""
    from core.depth_camera.astra_camera import AstraCamera
    
    camera = AstraCamera()
    if not camera.initialize():
        pytest.skip("Astra camera not available")
    
    yield camera
    camera.shutdown()

@pytest.fixture(scope="session")
def realsense_camera():
    """Initialize RealSense camera for tests."""
    from core.depth_camera.realsense_camera import RealSenseCamera
    
    camera = RealSenseCamera()
    if not camera.initialize():
        pytest.skip("RealSense camera not available")
    
    yield camera
    camera.shutdown()

@pytest.fixture(scope="session")
def midi_controller():
    """Initialize MIDI controller for tests."""
    from core.midi.midi_handler import MIDIHandler
    
    handler = MIDIHandler()
    if not handler.open_port(0):
        pytest.skip("MIDI controller not available")
    
    yield handler
    handler.close_port()
```

### Software Fixtures

```python
@pytest.fixture(scope="function")
def effect_chain():
    """Create clean effect chain for each test."""
    from core.effect_chain import EffectChain
    
    chain = EffectChain()
    chain.clear()
    yield chain
    chain.clear()

@pytest.fixture(scope="function")
def agent_plugin_bus():
    """Create isolated agent bus for each test."""
    from core.agent_plugin_bus import AgentPluginBus
    
    bus = AgentPluginBus(BusConfig(
        max_queue_size=1000,
        trace_enabled=True
    ))
    yield bus
    bus.shutdown()

@pytest.fixture(scope="function")
def telemetry_pipeline():
    """Create telemetry pipeline for each test."""
    from core.telemetry_pipeline import TelemetryPipeline
    
    pipeline = TelemetryPipeline(TelemetryConfig(
        sampling_rate_hz=30.0,
        buffer_size=100
    ))
    yield pipeline
    pipeline.stop()
```

### Performance Fixtures

```python
@pytest.fixture(scope="function")
def performance_monitor():
    """Monitor performance during test."""
    from core.performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    monitor.start()
    yield monitor
    monitor.stop()
    
    # Assert performance requirements
    stats = monitor.get_stats()
    assert stats['avg_fps'] >= 59.0, f"FPS too low: {stats['avg_fps']}"
    assert stats['max_cpu_percent'] < 90, f"CPU too high: {stats['max_cpu_percent']}%"
    assert stats['memory_growth_mb'] < 10, f"Memory leak: {stats['memory_growth_mb']}MB"
```

---

## Test Execution

### Local Execution

```bash
# Run all integration tests
pytest tests/integration/ -v --tb=short

# Run specific suite
pytest tests/integration/test_core_system.py -v

# Run specific test
pytest tests/integration/test_core_system.py::test_depth_to_effects_pipeline -v

# Run with performance monitoring
pytest tests/integration/ -v --performance-threshold=59.0

# Run in parallel (requires pytest-xdist)
pytest tests/integration/ -n 4

# Generate coverage report
pytest tests/integration/ --cov=core --cov-report=html
```

### CI/CD Execution

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on:
  push:
    branches: [main, develop]
  pull_request:

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      etcd:
        image: bitnami/etcd:latest
        ports:
          - 2379:2379

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.10"
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-xdist pytest-asyncio pytest-docker
          
      - name: Start VJLive services
        run: |
          docker-compose -f docker-compose.test.yml up -d
          
      - name: Wait for services
        run: |
          sleep 30
          curl -f http://localhost:8080/health
          
      - name: Run integration tests
        run: |
          pytest tests/integration/ -v \
            --junitxml=reports/integration.xml \
            --html=reports/integration.html \
            --self-contained-html \
            --performance-threshold=59.0
            
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: integration-test-results
          path: |
            reports/
            coverage/
```

---

## Test Data Management

### Synthetic Data Generators

```python
class TestDataGenerator:
    """Generate synthetic test data for integration tests."""
    
    @staticmethod
    def depth_frame(width=640, height=480, fps=30):
        """Generate synthetic depth frame."""
        import numpy as np
        return np.random.randint(0, 10000, (height, width), dtype=np.uint16)
    
    @staticmethod
    def audio_spectrum(bins=256):
        """Generate synthetic audio spectrum."""
        import numpy as np
        return np.random.random(bins).astype(np.float32)
    
    @staticmethod
    def effect_chain_with_n_effects(n=10):
        """Generate effect chain with N effects."""
        from core.effects import (
            DepthColorGradeEffect,
            DepthEdgeGlowEffect,
            DepthFogEffect,
            DepthContourEffect
        )
        chain = []
        for i in range(n):
            effect = DepthColorGradeEffect()
            effect.parameters['contrast'].value = 0.5 + (i * 0.1)
            chain.append(effect)
        return chain
    
    @staticmethod
    def agent_state(agent_name="julie-roo"):
        """Generate synthetic agent state."""
        return {
            'agent': agent_name,
            'state': 'evolving',
            'params': {
                'chaos': 5.0,
                'creativity': 7.0,
                'conservatism': 3.0
            },
            'timestamp': time.time()
        }
```

### Hardware Test Data

Store real hardware test data in `tests/integration/fixtures/hardware/`:

```
tests/integration/fixtures/hardware/
├── astra_sample_frames/
│   ├── frame_0001.npy
│   ├── frame_0002.npy
│   └── frame_0003.npy
├── realsense_sample_frames/
│   ├── frame_0001.npy
│   └── frame_0002.npy
├── midi_mappings/
│   ├── launchpad_mk2.json
│   └── novation_remote.json
└── audio_samples/
    ├── kick_drum.wav
    ├── bass_line.wav
    └── ambient_pad.wav
```

---

## Performance Baselines

### Baseline Definition

Performance baselines are stored in `tests/integration/baselines/`:

```json
{
  "version": "1.0",
  "generated_at": "2025-06-20T12:00:00Z",
  "hardware": {
    "cpu": "Intel i7-10700K",
    "gpu": "NVIDIA RTX 3080",
    "ram": "32GB DDR4"
  },
  "baselines": {
    "depth_to_effects_latency_ms": 8.5,
    "audio_to_effects_latency_ms": 5.2,
    "agent_message_latency_ms": 3.1,
    "plugin_load_time_ms": 45.0,
    "preset_load_time_ms": 120.0,
    "startup_time_seconds": 3.2,
    "sustained_fps_with_10_effects": 60.0,
    "sustained_fps_with_20_effects": 58.5,
    "memory_growth_mb_per_hour": 2.1,
    "cpu_usage_percent_at_60fps": 67.0
  }
}
```

### Baseline Comparison

```python
def compare_to_baseline(current_metrics: dict, baseline_metrics: dict) -> dict:
    """Compare current metrics to baseline."""
    results = {
        'passed': [],
        'failed': [],
        'degradation': []
    }
    
    for key, baseline_value in baseline_metrics.items():
        current_value = current_metrics.get(key)
        if current_value is None:
            results['failed'].append(f"Missing metric: {key}")
            continue
        
        # Check if metric passed (lower is better for latency, higher for FPS)
        if 'latency' in key or 'time' in key:
            # Latency should be <= baseline * 1.2 (20% tolerance)
            if current_value <= baseline_value * 1.2:
                results['passed'].append(f"{key}: {current_value:.2f} <= {baseline_value:.2f}")
            else:
                results['failed'].append(f"{key}: {current_value:.2f} > {baseline_value:.2f}")
        elif 'fps' in key:
            # FPS should be >= baseline * 0.9 (10% tolerance)
            if current_value >= baseline_value * 0.9:
                results['passed'].append(f"{key}: {current_value:.2f} >= {baseline_value:.2f}")
            else:
                results['failed'].append(f"{key}: {current_value:.2f} < {baseline_value:.2f}")
        else:
            # Other metrics (CPU, memory) should be <= baseline * 1.2
            if current_value <= baseline_value * 1.2:
                results['passed'].append(f"{key}: {current_value:.2f} <= {baseline_value:.2f}")
            else:
                results['failed'].append(f"{key}: {current_value:.2f} > {baseline_value:.2f}")
    
    return results
```

---

## Test Report Format

### JSON Report

```json
{
  "timestamp": "2025-06-20T15:30:00Z",
  "duration_seconds": 45.2,
  "total_tests": 67,
  "passed": 65,
  "failed": 2,
  "skipped": 0,
  "error": 0,
  "suites": {
    "core_system": {
      "tests": 12,
      "passed": 12,
      "failed": 0,
      "duration_seconds": 8.3
    },
    "multi_node": {
      "tests": 10,
      "passed": 9,
      "failed": 1,
      "duration_seconds": 12.1
    }
  },
  "performance_metrics": {
    "avg_fps": 60.0,
    "min_fps": 59.0,
    "max_cpu_percent": 72.5,
    "memory_growth_mb": 1.2
  },
  "failures": [
    {
      "suite": "multi_node",
      "test": "test_network_partition_handling",
      "error": "AssertionError: Expected state sync within 100ms, got 145ms",
      "duration_seconds": 2.3
    }
  ]
}
```

### HTML Report

Include:
- Summary dashboard (pass/fail/skip counts)
- Suite breakdown with durations
- Performance metrics visualization
- Failure details with stack traces
- Comparison to baseline (green/red indicators)
- Hardware/environment info

---

## Test Plan

| Test Name | Suite | What It Verifies |
|-----------|-------|------------------|
| `test_depth_to_effects_pipeline` | Core System | Depth data flows through effects |
| `test_audio_to_effects_pipeline` | Core System | Audio drives effect parameters |
| `test_agent_plugin_bus_integration` | Core System | Agents communicate via bus |
| `test_telemetry_pipeline_flow` | Core System | Telemetry collected and exported |
| `test_config_preset_system` | Core System | Presets save/load correctly |
| `test_unified_matrix_state` | Core System | Matrix state consistent |
| `test_node_heartbeat_exchange` | Multi-Node | Nodes exchange heartbeats |
| `test_state_sync_across_nodes` | Multi-Node | State syncs across cluster |
| `test_plugin_distribution` | Multi-Node | Plugins distributed to nodes |
| `test_failover_recovery` | Multi-Node | Recovery from node failure |
| `test_load_balancing` | Multi-Node | Load balanced across nodes |
| `test_network_partition_handling` | Multi-Node | Handles network splits |
| `test_agent_state_broadcast` | Agent Collaboration | Agents broadcast state |
| `test_agent_parameter_negotiation` | Agent Collaboration | Agents negotiate parameters |
| `test_agent_emergency_stop` | Agent Collaboration | Emergency stop propagates |
| `test_agent_load_distribution` | Agent Collaboration | Work distributed among agents |
| `test_agent_failure_handling` | Agent Collaboration | Handles agent crash/restart |
| `test_agent_preset_sharing` | Agent Collaboration | Agents share presets |
| `test_plugin_discovery` | Plugin Ecosystem | Plugins discovered |
| `test_plugin_loading` | Plugin Ecosystem | Plugins load without errors |
| `test_plugin_lifecycle` | Plugin Ecosystem | Plugin init/start/stop/cleanup |
| `test_plugin_isolation` | Plugin Ecosystem | Plugin errors don't crash host |
| `test_plugin_performance` | Plugin Ecosystem | Plugins meet performance budgets |
| `test_plugin_dependency_resolution` | Plugin Ecosystem | Dependencies resolved |
| `test_plugin_hot_reload` | Plugin Ecosystem | Plugins reload without restart |
| `test_websocket_connection_handshake` | WebSocket API | Connection established |
| `test_websocket_parameter_updates` | WebSocket API | Parameter changes broadcast |
| `test_websocket_effect_chain_updates` | WebSocket API | Chain modifications broadcast |
| `test_websocket_agent_state_streaming` | WebSocket API | Agent state streamed |
| `test_websocket_telemetry_streaming` | WebSocket API | Telemetry streamed |
| `test_websocket_error_handling` | WebSocket API | Errors reported correctly |
| `test_websocket_reconnection` | WebSocket API | Client reconnects and resyncs |
| `test_astra_camera_initialization` | Hardware Integration | Astra camera initializes |
| `test_realsense_camera_initialization` | Hardware Integration | RealSense camera initializes |
| `test_depth_frame_processing` | Hardware Integration | Depth frames at target FPS |
| `test_midi_controller_input` | Hardware Integration | MIDI controls mapped correctly |
| `test_hardware_failure_recovery` | Hardware Integration | Recovers from camera disconnect |
| `test_hardware_hot_swap` | Hardware Integration | Camera replacement detected |
| `test_sustained_60fps_with_10_effects` | Performance & Scalability | 60 FPS with 10 effects |
| `test_sustained_60fps_with_20_effects` | Performance & Scalability | 60 FPS with 20 effects |
| `test_memory_leak_detection` | Performance & Scalability | No memory growth over 1 hour |
| `test_cpu_scaling_with_effects` | Performance & Scalability | CPU scales linearly |
| `test_multi_node_performance` | Performance & Scalability | Performance doesn't degrade |
| `test_agent_overhead` | Performance & Scalability | Agent overhead < 5% CPU |
| `test_telemetry_overhead` | Performance & Scalability | Telemetry overhead < 1% CPU |
| `test_startup_to_rendering` | User Workflow | Startup to first frame < 5s |
| `test_effect_chain_build` | User Workflow | Build complex chain (10 effects) |
| `test_parameter_automation` | User Workflow | Parameters automated via Lumen |
| `test_preset_save_load` | User Workflow | Preset saved and loaded correctly |
| `test_midi_control_workflow` | User Workflow | MIDI controls effect parameters |
| `test_agent_collaboration_workflow` | User Workflow | Agents assist during performance |
| `test_shutdown_cleanup` | User Workflow | Shutdown clean, no leaks |

**Total tests:** 67
**Minimum coverage:** 80% before Phase 8 complete.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 67 tests implemented and passing
- [ ] Test coverage >= 80% (core modules)
- [ ] Performance baselines established and validated
- [ ] Hardware tests pass on available hardware
- [ ] CI/CD pipeline runs integration tests on every PR
- [ ] HTML test report generated automatically
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8F: Integration Testing` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### .github/workflows/ci-cd.yml (L97-116) [VJlive (Original)]
```yaml
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-asyncio pytest-docker
        
    - name: Start Docker services
      run: |
        docker-compose -f docker-compose.yml up -d
        
    - name: Wait for services to be ready
      run: |
        sleep 30
        curl -f http://localhost:8080/health
        
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
```

This shows the CI/CD integration test pattern with Docker services.

### .github/workflows/ci-cd.yml (L113-132) [VJlive (Original)]
```yaml
        curl -f http://localhost:8080/health
        
    - name: Run integration tests
      run: |
        pytest tests/integration/ -v
        
    - name: Stop Docker services
      run: |
        docker-compose -f docker-compose.yml down

  # Build and Deploy
  build-and-deploy:
    runs-on: ubuntu-latest
    needs: [security-scan, unit-tests, integration-tests]
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
```

This demonstrates the test orchestration with proper cleanup and dependencies.

### CRITICAL_PATH_DAY2_STATUS.md (L113-132) [VJlive (Original)]
```markdown
## 🔧 TECHNICAL DEPENDENCIES RESOLVED

### ✅ RESOLVED
- ✅ pytest installed and working
- ✅ WebSocket server running on port 8080
- ✅ Plugin system fully functional
- ✅ Integration test framework working
- ✅ Performance test script created

### ❌ PENDING
- ❌ Jest and React Testing Library for frontend tests
- ❌ WebSocket client library for full integration testing
- ❌ Stripe test mode setup for purchase flow testing
```

This shows the integration test framework status and dependencies.

### DEPLOYMENT_READINESS_CHECKLIST.md (L113-132) [VJlive (Original)]
```markdown
## Phase 4: Testing & Validation 🔄

### 4.1 Unit Testing
- [ ] **Core Components**
  - [ ] Video capture tests
  - [ ] Audio analysis tests
  - [ ] Effect chain tests
  - [ ] Control system tests

- [ ] **Integration Tests**
  - [ ] Full pipeline tests
  - [ ] Multi-node sync tests
  - [ ] Live coding integration tests
  - [ ] Mobile control tests

### 4.2 Performance Testing
- [ ] **Benchmarking**
  - [ ] FPS baseline established
```

This provides the testing structure and categories.

### test_live_coding_integration.py (L1-20) [VJlive (Original)]
```python
"""
Integration tests for live coding engine.
"""

import unittest
from unittest.mock import Mock, patch
from core.live_coding_engine import (
    CollaborativeSession,
    LiveCodingEngine,
    VisualProgrammingInterface,
    AICreativeAssistant
)

class TestLiveCodingIntegration(unittest.TestCase):
    """Test live coding engine integration."""
    
    def setUp(self):
        self.engine = LiveCodingEngine()
        self.session = CollaborativeSession("test_session")
        
    def test_shader_compilation_integration(self):
        """Test shader compiles and renders correctly."""
        shader_code = """
            vec4 main(vec2 uv) {
                return vec4(uv, 0.5, 1.0);
            }
        """
        result = self.engine.compile_shader(shader_code)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.shader_id)
        
    def test_collaborative_session_integration(self):
        """Test multiple users can collaborate."""
        user1 = self.session.add_user("user1")
        user2 = self.session.add_user("user2")
        
        # User 1 makes change
        self.session.apply_change(user1, "shader_code", "new_code")
        
        # User 2 receives update
        changes = self.session.get_changes(user2)
        self.assertEqual(len(changes), 1)
        
    def test_ai_assistant_integration(self):
        """Test AI creative assistant suggestions."""
        suggestions = self.engine.ai_assistant.suggest_improvements(
            "simple gradient shader"
        )
        self.assertIsInstance(suggestions, list)
        self.assertGreater(len(suggestions), 0)
```

This shows integration test patterns with setup/teardown and multi-component testing.

### test_multi_camera_system.py (L1-20) [VJlive (Original)]
```python
"""
Multi-camera registration system test suite.
"""

import unittest
import numpy as np
from core.multi_camera.registration import MultiCameraRegistration
from core.multi_camera.crowd_energy import CrowdEnergyAggregator

class TestMultiCameraSystem(unittest.TestCase):
    """Test multi-camera system integration."""
    
    def test_spatial_registration(self):
        """Test cameras register to common coordinate system."""
        registration = MultiCameraRegistration()
        
        # Add cameras with known positions
        registration.add_camera('cam1', position=[0, 0, 0], rotation=[0, 0, 0])
        registration.add_camera('cam2', position=[2, 0, 0], rotation=[0, 0, 0])
        
        # Register detections
        detections = [
            {'camera': 'cam1', 'bbox': [100, 100, 50, 50]},
            {'camera': 'cam2', 'bbox': [200, 100, 50, 50]}
        ]
        
        world_points = registration.register_detections(detections)
        self.assertEqual(len(world_points), 1)  # Same person detected by both
        
    def test_crowd_energy_aggregation(self):
        """Test crowd energy calculated from multiple cameras."""
        aggregator = CrowdEnergyAggregator()
        
        # Simulate camera energy readings
        aggregator.update_camera_energy('cam1', energy=0.7, tracks=5)
        aggregator.update_camera_energy('cam2', energy=0.8, tracks=3)
        
        crowd_state = aggregator.get_crowd_state()
        self.assertGreater(crowd_state['energy'], 0.7)
        self.assertEqual(crowd_state['active_tracks'], 8)
```

This demonstrates hardware integration testing with simulated camera data.

### LIVE_CODING_ENGINE_SUMMARY.md (L1-20) [VJlive (Original)]
```markdown
# Hyper-Enhanced Live Coding Engine - Implementation Complete

## 🎉 Project Status: COMPLETE

The VJLive Hyper-Enhanced Live Coding Engine has been successfully implemented with all planned features. All integration tests pass (5/5).

## 📋 What Was Built

### 1. Core Engine (`core/live_coding_engine.py`)
- **CollaborativeSession**: Multi-user session management with real-time document editing
- **LiveCodingEngine**: Central engine with shader compilation, session management, and caching
- **VisualProgrammingInterface**: Node-based shader creation system
- **AICreativeAssistant**: Intelligent suggestions, style transfer, pattern generation
- **LiveCodingWebSocketServer**: Real-time WebSocket communication layer

### 2. Web Interface (`web_ui/`)
- **React Application**: Modern web-based collaborative editor
- **Real-time Updates**: WebSocket integration for live collaboration
- **Live Preview**: Canvas-based shader preview (placeholder for full implementation)
- **Responsive Design**: Works on desktop and mobile devices
```

This shows a complete integration test suite with 5/5 tests passing.

---

## Notes for Implementers

1. **Core Concept**: Integration testing validates that all VJLive3 components work together correctly, from depth cameras through effects to agents and WebSocket APIs, while maintaining 60 FPS performance.

2. **Test Pyramid**: Follow the testing pyramid:
   - Unit tests: Many, fast, isolated (already done in P8-I5)
   - Integration tests: Fewer, test component interactions (this task)
   - End-to-end tests: Fewest, test complete user workflows

3. **Performance is Sacred**: Every integration test must verify 60 FPS performance. Use performance fixtures to assert FPS, CPU, memory requirements.

4. **Hardware-in-the-Loop**: When hardware available (Astra, RealSense, MIDI), run hardware tests. When not available, use high-quality simulators.

5. **Isolation**: Each test must clean up after itself. Use fixtures for setup/teardown. Never leave test artifacts that could affect other tests.

6. **Parallel Execution**: Design tests to run in parallel where possible. Use separate databases, ports, and resources to avoid conflicts.

7. **CI/CD Integration**: Tests must run in CI/CD pipeline with Docker services. Use `pytest-docker` for containerized dependencies.

8. **Baseline Comparison**: Establish performance baselines on reference hardware. Compare every test run to baseline and flag regressions.

9. **Diagnostic Data**: On failure, capture:
   - Full logs from all components
   - Performance metrics (FPS, CPU, memory)
   - Network traces (for multi-node tests)
   - Core dumps (for crashes)

10. **Flaky Test Detection**: If a test fails intermittently, mark it as flaky and investigate. Don't ignore flaky tests.

---

## Implementation Tips

1. **Test Framework Setup**:
   ```python
   # conftest.py
   import pytest
   import sys
   import os
   
   # Add project root to path
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   
   # Configure pytest
   pytest_plugins = ['pytest_docker']
   
   @pytest.fixture(scope="session", autouse=True)
   def setup_logging():
       import logging
       logging.basicConfig(
           level=logging.INFO,
           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
       )
   ```

2. **Performance Test Decorator**:
   ```python
   def performance_test(min_fps=59.0, max_cpu=90.0, max_memory_growth=10.0):
       """Decorator for performance tests."""
       def decorator(test_func):
           @functools.wraps(test_func)
           def wrapper(*args, **kwargs):
               import psutil
               import time
               
               process = psutil.Process()
               start_memory = process.memory_info().rss / 1024 / 1024  # MB
               start_time = time.time()
               frame_count = 0
               
               # Run test
               result = test_func(*args, **kwargs)
               
               # Collect metrics
               duration = time.time() - start_time
               end_memory = process.memory_info().rss / 1024 / 1024
               memory_growth = end_memory - start_memory
               
               # Assert performance
               avg_fps = frame_count / duration if duration > 0 else 0
               assert avg_fps >= min_fps, f"FPS {avg_fps:.1f} < {min_fps}"
               assert memory_growth < max_memory_growth, f"Memory growth {memory_growth:.1f}MB >= {max_memory_growth}MB"
               
               return result
           return wrapper
       return decorator
   ```

3. **Docker Compose for Tests**:
   ```yaml
   # docker-compose.test.yml
   version: '3.8'
   services:
     redis:
       image: redis:7-alpine
       ports:
         - "6379:6379"
       healthcheck:
         test: ["CMD", "redis-cli", "ping"]
         interval: 1s
         timeout: 3s
         retries: 30
         
     etcd:
       image: bitnami/etcd:latest
       environment:
         - ALLOW_NONE_AUTHENTICATION=yes
       ports:
         - "2379:2379"
       healthcheck:
         test: ["CMD", "etcdctl", "endpoint", "health"]
         interval: 1s
         timeout: 3s
         retries: 30
         
     vjlive:
       build:
         context: .
         dockerfile: Dockerfile.test
       depends_on:
         redis:
           condition: service_healthy
         etcd:
           condition: service_healthy
       environment:
         - REDIS_URL=redis://redis:6379
         - ETCD_URL=http://etcd:2379
       ports:
         - "8080:8080"
       healthcheck:
         test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
         interval: 2s
         timeout: 5s
         retries: 10
   ```

4. **Test Suite Organization**:
   ```
   tests/integration/
   ├── conftest.py                    # Shared fixtures
   ├── test_core_system.py            # Core system integration
   ├── test_multi_node.py             # Multi-node sync
   ├── test_agent_collaboration.py    # Agent coordination
   ├── test_plugin_ecosystem.py       # Plugin system
   ├── test_websocket_api.py          # WebSocket API
   ├── test_hardware_integration.py   # Hardware tests
   ├── test_performance.py            # Performance tests
   ├── test_user_workflows.py         # User workflows
   ├── fixtures/
   │   ├── __init__.py
   │   ├── hardware/                 # Hardware test data
   │   ├── software/                 # Software fixtures
   │   └── performance/              # Performance baselines
   └── utils/
       ├── docker.py                 # Docker helpers
       ├── hardware.py               # Hardware detection
       ├── performance.py            # Performance monitoring
       └── report.py                 # Report generation
   ```

5. **Hardware Detection**:
   ```python
   def detect_hardware():
       """Detect available hardware for tests."""
       hardware = {
           'astra': False,
           'realsense': False,
           'midi': False
       }
       
       # Check for Astra
       try:
           from core.depth_camera.astra_camera import AstraCamera
           camera = AstraCamera()
           if camera.initialize():
               hardware['astra'] = True
               camera.shutdown()
       except:
           pass
       
       # Check for RealSense
       try:
           import pyrealsense2 as rs
           hardware['realsense'] = True
       except:
           pass
       
       # Check for MIDI
       try:
           import rtmidi
           midi_out = rtmidi.MidiOut()
           if len(midi_out.get_ports()) > 0:
               hardware['midi'] = True
       except:
           pass
       
       return hardware
   
   @pytest.fixture(scope="session", autouse=True)
   def skip_hardware_tests_if_unavailable():
       """Skip hardware tests if hardware not available."""
       hardware = detect_hardware()
       if not any(hardware.values()):
           pytest.skip("No hardware available for integration tests")
   ```

6. **Parallel Test Execution**:
   ```python
   # Use pytest-xdist for parallel execution
   # Run with: pytest tests/integration/ -n 4
   
   # Ensure tests are isolated:
   # - Use separate ports for each test
   # - Use separate temporary directories
   # - Don't share global state
   
   @pytest.fixture
   def isolated_port():
       """Get an isolated port for test."""
       import socket
       sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
       sock.bind(('127.0.0.1', 0))
       port = sock.getsockname()[1]
       sock.close()
       return port
   ```

7. **Long-Running Tests**:
   ```python
   @pytest.mark.slow
   @pytest.mark.timeout(3600)  # 1 hour timeout
   def test_memory_leak_detection():
       """Test for memory leaks over 1 hour."""
       # ... long-running test
       
   # Run slow tests separately:
   # pytest tests/integration/ -m "not slow"  # Fast tests only
   # pytest tests/integration/ -m slow        # Slow tests only
   ```

---
-

## References

- pytest documentation (fixtures, markers, plugins)
- Docker and docker-compose for test environments
- Performance testing with pytest-benchmark
- Multi-node testing with pytest-xdist
- Hardware testing patterns
- CI/CD best practices (GitHub Actions)
- Test coverage with pytest-cov
- HTML report generation with pytest-html

---

## Conclusion

The Integration Testing framework is the final gatekeeper ensuring VJLive3 meets its rigorous quality and performance standards before Phase 8 completion. By testing end-to-end workflows, multi-node synchronization, agent collaboration, and hardware integration with strict 60 FPS performance requirements, it guarantees that the system is production-ready for live VJ performances. Its CI/CD integration and comprehensive reporting provide confidence that every release meets the sacred standards of the VJLive community.

---
