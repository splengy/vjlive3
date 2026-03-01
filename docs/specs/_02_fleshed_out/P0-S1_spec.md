# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P0-S1_sigil.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-S1 — Sigil

**Phase:** Phase 2 / P2-H3  
**Assigned To:** Alex Turner  
**Spec Written By:** Jordan Lee  
**Date:** 2025-04-05

---

## What This Module Does

The `Sigil` module generates dynamic, visually expressive shader effects based on real-time system metrics and user-defined parameters. It interprets hardware state (e.g., CPU load, GPU temperature) as a "manifold" of complexity, heat, and chaos to produce evolving visual patterns—inspired by the `silicon_canyon.frag` shader's use of dynamic gradients and jittered textures. The module outputs a colorized fragment output that can be rendered in real time over a canvas.

---

## What It Does NOT Do

- It does not perform hardware monitoring or sensor reading directly; it consumes metrics from external sources (e.g., `vjlive1.metrics.HardwareMonitor`).  
- It does not compile or manage GLSL shaders—this is handled by the rendering engine.  
- It does not handle audio input, user interaction, or UI rendering.  
- It does not store visual history or generate animations over time independently.

---

## Public Interface

```python
class Sigil:
    def __init__(self, hardware_monitor: 'HardwareMonitor', config: dict) -> None:
        """
        Initialize the sigil effect with live metrics and configuration.
        
        Args:
            hardware_monitor: Source of real-time system metrics (CPU, GPU, RAM)
            config: Dictionary containing parameters like "chaos_threshold", "color_scheme"
        """
    
    def update(self, dt: float) -> tuple[float, vec3]:
        """
        Update the sigil effect based on current system state.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            (adrenaline_level: float, color_output: vec3)
        """
    
    def stop(self) -> None:
        """Gracefully release any held resources."""
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `hardware_monitor` | `HardwareMonitor` | Source of real-time system metrics (CPU, GPU, RAM) | Must be non-null; must provide `get_load()`, `get_temperature()` |
| `config` | `dict` | Configuration parameters including: <br> - `chaos_threshold`: float [0.0–1.0] <br> - `color_scheme`: str ["classic", "neon", "magma"] <br> - `complexity_factor`: float [0.1–2.0] | All values must be within bounds; defaults provided if missing |
| `dt` | `float` | Delta time in seconds (from rendering loop) | Must be ≥ 0.0; typically 1/60 or 1/120 sec |
| `adrenaline_level` | `float` | Output scalar representing system "energy" state | Range: [0.0, 1.0] — derived from load and temperature |
| `color_output` | `vec3` | Final fragment color (R, G, B) in range [0.0–1.0] | Must be valid RGB triplet; derived from manifold logic |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Use `NullDevice` pattern: return default values (`adrenaline=0.0`, `color=(0.2, 0.3, 0.5)`) and log warning.  
- What happens on bad input? → If `config` contains invalid keys or out-of-range values, raise `ValueError` with message: `"Invalid config parameter: key=value"`  
- What is the cleanup path? → `stop()` calls internal resource release (e.g., timer cancellation), logs shutdown event, and sets state to `stopped`. No exceptions should be raised during cleanup.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `pyvulkan` — used for GPU context access — fallback: use software rendering via CPU-based color blending  
  - `numpy` — used for vector math and array operations — fallback: use built-in Python floats with scalar math  
- Internal modules this depends on:  
  - `vjlive1.metrics.HardwareMonitor` — provides real-time system metrics  
  - `vjlive1.effects.shaders.silicon_canyon.frag` — serves as the primary visual logic reference for manifold behavior  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware_monitor` | Module starts without crashing if hardware monitor is None or missing |
| `test_update_with_normal_metrics` | Core update returns valid adrenaline and color output when metrics are within bounds |
| `test_update_with_high_load` | High CPU/GPU load increases adrenaline level and shifts color toward "magenta" (electric) spectrum |
| `test_update_with_low_chaos_threshold` | When chaos threshold is low, jitter effect is minimal or absent |
| `test_error_on_invalid_config` | Invalid config parameter raises ValueError with clear message |
| `test_stop_resources_cleanup` | stop() method releases internal timers and logs shutdown cleanly without exceptions |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-2] P0-S1: Implement Sigil module for dynamic visual effects` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/effects/shaders/shaders/silicon_canyon.frag (L1-20)
```glsl
#version 330 core
uniform float adrenaline; 
uniform vec3 manifold; // [X: Complexity, Y: Heat, Z: Chaos]
varying vec2 vTexCoord;

void main() {
    vec2 uv = vTexCoord * 2.0 - 1.0;
    
    // Flat-shaded "Raytraced" spheres logic
    float dist = length(uv) - 0.5;
    float shade = floor(dist * 5.0) / 5.0; // Sharp gradient stepping
    
    vec3 sky = vec3(0.0, 0.5, 1.0);     // 90s Windows Sky Blue
    vec3 object = vec3(1.0, 0.2, 0.5);  // Electric Magenta
    
    // Add "Chaos" jitter
    if(manifold.z > 0.7) uv += fract(sin(time) * 10.0) * 0.05;

    vec3 color = mix(object, sky, step(0.0, dist + (shade * 0.2)));
    gl_FragColor = vec4(color, 1.0);
}
```

### vjlive1/effects/shaders/shaders/silicon_canyon.frag (L17-21)
```glsl
    if(manifold.z > 0.7) uv += fract(sin(time) * 10.0) * 0.05;

    vec3 color = mix(object, sky, step(0.0, dist + (shade * 0.2)));
    gl_FragColor = vec4(color, 1.0);
}
```

### vjlive1/effects/shaders/shaders/silicon_canyon.frag (L18-21)
```glsl
    vec3 color = mix(object, sky, step(0.0, dist + (shade * 0.2)));
    gl_FragColor = vec4(color, 1.0);
}
```

### vjlive1/effects/shaders/shaders/silicon_canyon.frag (L19-21)
```glsl
    vec3 color = mix(object, sky, step(0.0, dist + (shade * 0.2)));
    gl_FragColor = vec4(color, 1.0);
}
```

### vjlive1/effects/shaders/shaders/silicon_canyon.frag (L20-21)
```glsl
    gl_FragColor = vec4(color, 1.0);
}
```