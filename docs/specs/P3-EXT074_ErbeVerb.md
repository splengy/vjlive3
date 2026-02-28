# P3-EXT074: ErbeVerb (Resonant Reverb)

## Description

A strictly mathematical software emulation of the Make Noise Erbe-Verb hardware synthesizer module, applying variable-size delay ring buffering and feedback loops to Audio/CV signal flows within VJLive3.

## What This Module Does

This specification defines the conversion of `VJlive-2/core/effects/erbe_verb.py` into a P3-EXT component for VJLive3. Functioning primarily at control-rate or audio-rate, the algorithm operates an optimized 32-sample circular buffer (`self._delays = [0.0] * 32`) to simulate spatial boundaries based on `size`, `decay`, and high-frequency `absorb` factors.

## Public Interface

```python
class ErbeVerbEngine:
    """Core DSP algorithmic reverb model."""
    
    # Core Controls
    absorb: float    # High-freq loss / Damping
    decay: float     # Feedback amplification
    size: float      # Tail length
    density: float   # Diffusion (stubbed in v2)
    tilt: float      # Spectral tone
    mix: float       # Dry/Wet blend
    pre_delay: float # Offset read gap
    depth: float     # Modulation LFO depth
    speed: float     # Modulation LFO frequency
    
    def process(self, dt: float, input_signal: float) -> dict[str, float]:
        """Apply mathematical scattering returning 'output' and 'wet' keys."""
```

## Inputs and Outputs

*   **Inputs**: Frame delta time `dt` and an instantaneous floating point scalar `input_signal` derived from either an audio stream or Node property CV.
*   **Outputs**: A synchronized `wet`/`dry` blended value strictly clamped between `[-10.0, 10.0]` for safety within feedback loops.

## Implementation Notes

### Legacy References
- **Source Codebase**: `VJlive-2` and `vjlive`
- **File Paths**: 
  - Source Code: `core/effects/erbe_verb.py`
  - Hardware Manual: `vjlive/JUNK/manuals_make_noise/erbe-verb-manual.pdf`
- **Architectural Soul**: The legacy engine calculates the delay footprint dynamically: `size_len = max(2, int(self.size * 30))`. This is summed with `pre_delay` to set an exact modulo ring-buffer read distance.

### Key Algorithms & Integration
1. **Feedback Damping**: The legacy math uses `feedback_amt = (0.2 + self.decay * 0.75)` and `damping = (1.0 - self.absorb * 0.3)` explicitly. This preserves the exact sonic/visual characteristic.
2. **Read-Head LFO**: When modulation is active (`self.depth > 0.0`), a `math.sin` wave continuously warps the read head index backwards and forwards, creating classic pitch-shifting doppler effects within the reverb tail.

### Optimization Constraints & Safety Rails
- **Buffer Limitations**: The `32` length array must remain a fixed-size pre-allocation to satisfy the VJLive3 Zero-Allocation (Safety Rail #1) paradigm.
- **Node Graph Wrapping**: This Python DSP engine must be properly wrapped inside an `EffectNode` subclass that can tick 60 times a second if fed CV data, without drifting out of sync.

## Test Plan

*   **Logic (Pytest)**: Supply an impulse signal (`1.0` followed by `0.0`s) and track the decay ring-out to ensure it mathematically matches the V2 output curve precisely.

## Deliverables

1.  Pure python implementation inside `src/vjlive3/plugins/dsp/erbe_verb.py`.
2.  `ErbeVerbEffectNode` wrapper for graph integration.
