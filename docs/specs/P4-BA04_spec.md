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

- What happens if hardware is missing? → [NEEDS RESEARCH]  
- What happens on bad input? → If `in_cv` is not provided, defaults to 0.0; if any gain parameter is invalid (e.g., non-float), raises `TypeError`. If a gain value exceeds float range, silently clamps to ±float('inf') and uses 0.1 multiplier.  
- What is the cleanup path? → No explicit cleanup required as no external resources are held. Module state is preserved across calls.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `typing` — used for type hints — fallback: built-in Python typing  
- Internal modules this depends on:  
  - `vjlive2.plugins.core.vbogaudio_base.BogaudioNode`

---

## Test Plan

| Test Name                     | What It Verifies |
|------------------------------|------------------|
| `test_init_no_parameters`   | Module initializes with default gains (all 5.0) |
| `test_process_audio_valid_input` | Core processing returns expected output when in_cv is provided |
| `test_process_audio_missing_in_cv` | Missing 'in_cv' raises no error and defaults to 0.0 |
| `test_gain_parameter_range` | Gains outside valid float range are handled gracefully |
| `test_output_clipping`      | Output value is clipped between -10 and 10 |
| `test_negative_gain_effect` | Negative gain values reduce output magnitude correctly |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-4] P4-BA04: BPEQ6 module implementation` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

**Legacy Code References:**  
See `vjlive2/plugins/core/vbogaudio_bpeq6/__init__.py` for full implementation logic and parameter mapping.  
- Initialization: gains default to 5.0, mapped via `(gain - 5.0) * 2.0` to produce ±5.0 range.  
- Processing loop: each gain is applied as `out += g * 0.1`, where `g` is derived from parameter.  
- Output clamping: final output bounded between -10 and 10.  
- Input handling: `in_cv` defaults to 0.0 if missing.