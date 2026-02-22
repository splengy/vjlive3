# Spec: P8-I2 — Performance Benchmarks (60fps Target Verified)

**File naming:** `docs/specs/phase8_integration/P8-I2_Performance_Benchmarks.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I2 — Performance Benchmarks

**Phase:** Phase 8 / P8-I2
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

Performance Benchmarks provides comprehensive performance testing and validation for VJLive3. It measures frame rates, memory usage, GPU utilization, and latency across various workloads, ensuring the system meets the 60fps target and identifying performance bottlenecks for optimization.

---

## What It Does NOT Do

- Does not replace continuous monitoring (delegates to P8-I3)
- Does not handle performance tuning (provides data only)
- Does not include stress testing (focused on target scenarios)
- Does not manage hardware detection (uses available hardware)

---

## Public Interface

```python
class PerformanceBenchmarks:
    def __init__(self, target_fps: float = 60.0, duration: float = 30.0) -> None: ...
    
    def run_benchmark_suite(self, suite_name: str, config: BenchmarkConfig) -> BenchmarkResult: ...
    def run_single_benchmark(self, benchmark_id: str, workload: Workload) -> BenchmarkResult: ...
    
    def measure_frame_rate(self, render_func: Callable, num_frames: int) -> FrameRateMetrics: ...
    def measure_memory_usage(self, operation: Callable) -> MemoryMetrics: ...
    def measure_gpu_metrics(self) -> GPUMetrics: ...
    
    def compare_to_baseline(self, baseline: BenchmarkResult) -> ComparisonReport: ...
    def generate_performance_report(self, results: List[BenchmarkResult], format: str = "html") -> str: ...
    
    def validate_fps_target(self, fps: float) -> bool: ...
    def get_bottleneck_suggestions(self, result: BenchmarkResult) -> List[str]: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `target_fps` | `float` | Target frame rate | > 0 |
| `duration` | `float` | Benchmark duration in seconds | > 0 |
| `suite_name` | `str` | Benchmark suite name | Non-empty |
| `config` | `BenchmarkConfig` | Benchmark configuration | Valid config |
| `benchmark_id` | `str` | Benchmark identifier | Non-empty |
| `workload` | `Workload` | Workload definition | Valid workload |
| `render_func` | `Callable` | Render function to measure | Callable |
| `num_frames` | `int` | Number of frames to test | > 0 |
| `operation` | `Callable` | Operation to measure | Callable |
| `baseline` | `BenchmarkResult` | Baseline result for comparison | Valid result |
| `results` | `List[BenchmarkResult]` | Results to report | Valid results |
| `format` | `str` | Report format | 'html', 'json', 'csv' |
| `fps` | `float` | Measured frame rate | > 0 |

**Output:** `BenchmarkResult`, `FrameRateMetrics`, `MemoryMetrics`, `GPUMetrics`, `ComparisonReport`, `str`, `bool`, `List[str]` — Various benchmark results

---

## Edge Cases and Error Handling

- What happens if hardware doesn't meet minimum? → Run reduced benchmarks, report limitations
- What happens if benchmark crashes? → Capture partial results, log error
- What happens if frame rate unstable? → Report variance, suggest investigation
- What happens if memory measurement fails? → Skip memory metrics, continue
- What happens on cleanup? → Clear GPU resources, reset state

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `psutil` — for system metrics — fallback: raise ImportError
  - `py3nvml` or `gpustat` — for GPU metrics — fallback: skip GPU metrics
- Internal modules this depends on:
  - `vjlive3.render.chain` (for rendering benchmarks)
  - `vjlive3.audio.audio_analyzer` (for audio benchmarks)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_benchmark_suite` | Runs benchmark suites correctly |
| `test_single_benchmark` | Runs individual benchmarks |
| `test_frame_rate_measurement` | Measures FPS accurately |
| `test_memory_measurement` | Measures memory usage |
| `test_gpu_metrics` | Collects GPU metrics |
| `test_baseline_comparison` | Compares to baseline correctly |
| `test_edge_cases` | Handles errors gracefully |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I2: Performance benchmarks (60fps target)` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## Verification Checkpoint

- [ ] Spec reviewed and approved
- [ ] Implementation ready to begin
- [ ] All dependencies verified
- [ ] Test plan complete
- [ ] Definition of Done clear

---

*Specification based on VJlive-2 performance benchmarking module.*