# Spec Template — P3-VD22 Depth Temporal Stratification

**File naming:** `docs/specs/P3-VD22_depth_temporal_strat.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-VD22 — Depth Temporal Stratification

**Phase:** Phase 3  
**Assigned To:** Worker Beta  
**Spec Written By:** Manager-Gemini-3.1  
**Date:** 2026-02-22  

---

## What This Module Does

This module ports the "Depth Temporal Stratification Datamosh" effect from the legacy `vdepth` codebase. It slices the scene into depth strata where each layer runs at a different time offset (foreground = live, background = older frames). At the boundaries between these temporal strata, datamosh artifacts (block displacement, motion warping) are generated because adjacent pixels are pulled from fundamentally different points in time. It also supports Hue-rotation per stratum and temporal strobing.

---

## What It Does NOT Do

- It does not allocate memory buffers for managing structural shader state in Python; it uses VJLive3 offset integration for validation checks.
- It does not process audio natively inside the plugin. Audio reactivity must be driven externally by modulating the exposed standard parameters.

---

## Public Interface

```python
from vjlive3.plugins.api import PluginBase, PluginContext

METADATA = {
    "name": "Depth Temporal Stratification",
    "description": "Slices the scene into depth strata running at different time offsets with datamoshed boundaries.",
    "version": "1.0.0",
    "parameters": [
        {"name": "num_strata", "type": "float", "min": 2.0, "max": 12.0, "default": 4.0},
        {"name": "strata_separation", "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "strata_offset", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "temporal_depth", "type": "float", "min": 0.0, "max": 1.0, "default": 0.6},
        {"name": "temporal_gradient", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "freeze_amount", "type": "float", "min": 0.0, "max": 1.0, "default": 0.3},
        {"name": "seam_datamosh", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "seam_width", "type": "float", "min": 0.0, "max": 1.0, "default": 0.4},
        {"name": "block_displace", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "motion_warp", "type": "float", "min": 0.0, "max": 1.0, "default": 0.5},
        {"name": "ghost_opacity", "type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
        {"name": "color_shift", "type": "float", "min": 0.0, "max": 1.0, "default": 0.2},
        {"name": "strobe_rate", "type": "float", "min": 0.0, "max": 1.0, "default": 0.0}
    ],
    "inputs": ["video_in", "video_b_in", "depth_in"],
    "outputs": ["video_out"]
}

class DepthTemporalStratPlugin(PluginBase):
    def __init__(self) -> None: ...
    def initialize(self, context: PluginContext) -> None: ...
    def process(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Port | Type | Description |
|------|------|-------------|
| `video_in` | GL Texture | Current frame feed |
| `video_b_in` | GL Texture | Optional second layer to merge temporal glitched slices into. |
| `depth_in` | GL Texture | Depth field regulating temporal speed |
| `video_out`| GL Texture | Output |

---

## Edge Cases and Error Handling

- **Missing Depth Input**: Bypasses safely, passing `video_in` unmodified to `video_out` (SAFETY RAIL #7).
- **Missing Secondary Video**: Projects cleanly by falling back onto itself or defaulting to bypass structure.

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_strat_manifest` | Verifies Pydantic compatibility and parameter ranges. |
| `test_strat_missing_depth` | Verifies graceful bypass when depth is lacking. |
| `test_strat_processing` | Confirms generic processing logic via structural texture offset logic (adds +16000). |
| `test_strat_fallback_video_b` | Validates it behaves appropriately with or without `video_b_in` supplied. |
| `test_strat_missing_video` | Verifies the safety check prevents operations on non-existent source. |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed
- [ ] All tests pass
- [ ] No file over 750 lines
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-3] P3-VD22: Depth Temporal Stratification plugin`
- [ ] BOARD.md updated
