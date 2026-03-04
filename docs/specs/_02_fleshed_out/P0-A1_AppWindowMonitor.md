# Spec Template — Copy this file for every new task
**File naming:** `docs/specs/<task-id>_<module-name>.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

--- ## Task: P0-A1 — AppWindowMonitor
**Phase:** Phase 0
**Assigned To:** Alex Chen
**Spec Written By:** Jordan Reed
**Date:** 2025-04-05

--- ## What This Module Does
This module provides a real-time monitoring interface for the VJLive3 application, displaying key performance metrics such as frames per second (FPS),, memory usage and active agent count. It serves as a foundational dashboard to ensure system stability and responsiveness during runtime, enabling developers and operators to detect performance bottlenecks or resource exhaustion early.

--- ## What It Does NOT Do
- It does not control or modify application behavior.
- It does not generate visual effects or audio output.
- It does not handle user input or UI interaction beyond displaying metrics.
- It is not responsible for rendering graphics; it only aggregates and presents data from internal systems.

--- ## Public Interface
```python
class AppWindowMonitor:
    def __init__(self, window_width: int = 300, window_height: int = 120) -> None:
        """Initialize the monitor with default dimensions."""
        pass

    def start(self) -> None:
        """Begin monitoring and updating metrics in real time."""
        pass

    def stop(self) -> None:
        """Stop monitoring and release any held resources."""
        pass

    def get_metrics(self) -> dict[str, float]:
        """Return current performance metrics as a dictionary."""
        return {
            "fps": float,
            "memory_mb": float,
            "active_agents": int
        }
```

--- ## Inputs and Outputs
| Name | | Type Description | Constraints |
|----------|------|--------------|--------|
| ``window_width | `int` | Width of the monitor window in pixels | Must be ≥ 200 and ≤ 800 |
| `window_height` | `int` | Height of the monitor window in pixels | Must be ≥ 60 and ≤ 300 |
| `window_position` | `tuple[int, int]` | Optional position (x, y) for placement on screen | Not required; defaults to top-left corner |

--- ## Edge Cases and Error Handling
- **What happens if hardware is missing?** → Use fallback values: FPS = 0.0, memory = 0.0, agents = 0
- **What happens on bad input?** → Raise `ValueError` with message "Invalid window dimension provided" for out-of-range inputs
- **What is the cleanup path?** → `stop()` calls internal resource release; ensures no open threads or file handles remain

--- ## Dependencies
- **External libraries needed (and what happens if they are missing):**
  - `psutil` — used to read memory usage — fallback: hardcoded baseline values
  - `pygetwindow` — optional for window positioning — fallback: default top-left placement
  - **Internal modules this depends on:**
    - `vjlive3.core.metrics.SystemMetricsCollector` — for FPS and memory data
    - `vjlive3.agent.AgentRegistry` — to count active agents

--- ## Test Plan
| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_valid_dimensions` | Module initializes with valid window size without error |
| `test_init_invalid_width` | Invalid width (e.g., < 200) raises ValueError with correct message |
| `test_get_metrics_returns_expected` | Returns dictionary with correct keys and reasonable values when system is running |
| `test_stop_releases_resources` | No memory leaks or open handles after stop() call |
| `test_no_agents_when_empty` | Returns zero active agents if agent registry is empty |

**Minimum coverage:** 80% before task is marked done.

--- ## Definition of Done
- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-0] P0-A1: AppWindowMonitor - Real-time performance dashboard` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
