# Spec: P1-P5 — Plugin Sandboxing

**Phase:** Phase 1 / P1-P5
**Assigned To:** Antigravity (Agent 2)
**Authorized By:** Roo Code via DISPATCH.md — SPEC-P1-P5
**Depends On:** P1-P1 (registry), P1-P2 (loader)
**Date:** 2026-02-21

---

## What This Module Does

Wraps a plugin's `process()` call in safety boundaries so that a misbehaving plugin
cannot crash the engine. Catches exceptions, enforces a per-frame time budget,
and tracks error counts per plugin. If a plugin exceeds the error threshold it is
automatically disabled. All of this is transparent to the host — it calls
`sandbox.call(name, frame, audio_data)` instead of calling the plugin directly.

## What It Does NOT Do

- Does NOT use OS-level process isolation (that is too expensive for 60fps)
- Does NOT prevent all possible bugs (infinite loops without timeout require threads)
- Does NOT sandbox disk or network access (trust model: plugins are authored in-house)
- Does NOT support async plugins — synchronous frame processing only

## Public Interface

```python
from typing import Any, Optional
import numpy as np
from vjlive3.plugins.registry import PluginRegistry

@dataclass
class SandboxResult:
    success: bool
    output: Optional[np.ndarray]   # None on failure
    error: Optional[str]           # None on success
    elapsed_ms: float

class PluginSandbox:
    def __init__(
        self,
        registry: PluginRegistry,
        frame_budget_ms: float = 14.0,    # must finish in < 14ms (leaves 2ms margin for 60fps)
        max_errors: int = 5,              # disable plugin after 5 consecutive errors
    ) -> None: ...

    def call(
        self,
        plugin_name: str,
        frame: np.ndarray,
        audio_data: Any,
        **kwargs: Any,
    ) -> SandboxResult:
        """Call plugin safely. Returns SandboxResult. Never raises."""

    def disable(self, plugin_name: str) -> None:
        """Manually disable a plugin."""

    def enable(self, plugin_name: str) -> None:
        """Re-enable a previously disabled plugin."""

    def is_disabled(self, plugin_name: str) -> bool: ...

    def error_count(self, plugin_name: str) -> int: ...

    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Return per-plugin stats: error_count, avg_ms, disabled."""
```

## Safety Sequence (per call)

1. Check if plugin is disabled → SandboxResult(success=False, output=None, error="disabled")
2. Retrieve class from registry → SandboxResult(success=False, error="not found") if missing
3. Create/cache plugin instance (lazy init)
4. Record `t0 = time.perf_counter()`
5. Call `instance.process(frame, audio_data, **kwargs)` inside `try/except Exception`
6. Record elapsed ms
7. On exception: increment error_count; if ≥ max_errors → disable and log; return failure result
8. On success: validate output is `np.ndarray` same shape as input; return success result
9. Log warning if elapsed > `frame_budget_ms`

## Plugin Instance Contract

Every plugin class registered in the registry must implement:
```python
class MyPlugin:
    METADATA: Dict[str, Any]     # required — name, description, parameters
    
    def process(
        self,
        frame: np.ndarray,       # uint8 RGBA (H, W, 4)
        audio_data: Any,         # AudioSnapshot or None
        **kwargs: Any,
    ) -> np.ndarray:             # must return same shape as input
        ...
```

## Edge Cases

- Plugin not in registry: SandboxResult failure, do NOT crash
- Plugin `process()` raises: log, count error, return input frame unchanged
- Plugin returns wrong shape: log warning, return input frame unchanged
- Plugin auto-disabled: log `"Plugin {name} disabled after {n} consecutive errors"`
- Re-enabling clears error count

## Dependencies

- `vjlive3.plugins.registry` (P1-P1)
- `numpy`
- Standard library: `time`, `threading`, `logging`

## Test Plan

| Test | What It Verifies |
|------|-----------------|
| `test_call_happy_path` | valid plugin returns processed frame |
| `test_call_unknown_plugin` | SandboxResult failure, no crash |
| `test_call_plugin_raises` | exception caught, error_count increments |
| `test_auto_disable` | after max_errors consecutive failures, plugin disabled |
| `test_manual_disable_enable` | disable/enable/is_disabled API |
| `test_wrong_output_shape` | returns input frame, logs warning |
| `test_stats` | get_stats returns per-plugin dict |
| `test_frame_budget_warning` | slow plugin logs warning |
| `test_re_enable_clears_error_count` | error_count resets after enable() |

**Minimum coverage:** 80%

## Definition of Done

- [ ] Spec reviewed by Roo Code before code starts
- [ ] `src/vjlive3/plugins/sandbox.py` written, < 750 lines
- [ ] All 9 tests pass
- [ ] BOARD.md P1-P5 updated to ✅ Done
- [ ] Lock released, AGENT_SYNC.md handoff written
