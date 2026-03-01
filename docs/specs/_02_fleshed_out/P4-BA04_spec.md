# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/P4-BA04_bpeq6.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P4-BA04 — BPEQ6

**Phase:** Phase 4  
**Assigned To:** Alex Chen  
**Spec Written By:** Samira Patel  
**Date:** 2025-04-05

---

## What This Module Does

The BPEQ6 module implements a basic band-pass equalizer with six frequency bands (100Hz, 250Hz, 1kHz, 3kHz, 6kHz, 12kHz). It processes an input CV signal and applies per-band gain adjustments to modify the output audio level. Each gain parameter is mapped from a knob value (centered at 5.0) to a linear gain multiplier applied as a small additive offset (×0.1), resulting in a dynamic filter-like effect. The module outputs a clipped signal within the [-10, 10] range.

---

## What It Does NOT Do

- Implement true frequency filtering or band-pass resonance.
- Apply time-domain processing such as delay, reverb, or phase shifting.
- Support real-time audio streaming with latency compensation.
- Provide user interface for visual tuning (e.g., sliders in UI).
- Handle multiple input sources beyond CV signal.

---

## Public Interface

```python
class BPEQ6:
    def __init__(self, name: str = "BPEQ6", parameters: Dict[str, float] = None) -> None:
        """
        Initialize the BPEQ6 module.
        
        Args:
            name: Human-readable name for the node (default: "BPEQ6").
            parameters: Dictionary of parameter values. Keys are 'gain1' to 'gain6'.
                        Defaults to 5.0 for each gain if not provided.
        """
    
    def process_audio(self, dt: float, **kwargs) -> Dict[str, Any]:
        """
        Process the input CV signal and return modified output.

        Args:
            dt: Time delta (used for timing, currently unused).
            **kwargs: Keyword arguments passed from audio engine. Must include 'in_cv'.

        Returns:
            Dictionary with key 'out' containing processed audio value.
        """
```

---

## Inputs and Outputs

| Name       | Type         | Description                                  | Constraints |
|------------|--------------|----------------------------------------------|-------------|
| `name`     | `str`        | Module identifier (e.g., "BPEQ6")           | Required, default: "BPEQ6" |
| `parameters` | `Dict[str, float]` | Dictionary of gain values for each band. Keys: 'gain1' to 'gain6'. | Each value must be a float; defaults to 5.0 if not provided |
| `in_cv`    | `float`      | Input control voltage (CV) signal           | Must be present in kwargs, default: 0.0 |
| `out`      | `float`      | Processed output audio value               | Clipped between -10 and 10 |

---

## Edge Cases and Error Handling

