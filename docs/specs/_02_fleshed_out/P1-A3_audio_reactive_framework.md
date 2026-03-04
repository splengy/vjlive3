# P1-A3 Audio-Reactive Effect Framework

## Overview
The Audio-Reactive Effect Framework (A3) provides a standardized integration layer for audio-reactive effects in VJLive3. It defines protocols and mechanisms to enable real-time audio data distribution to effects while maintaining performance constraints (<1ms per frame). This specification focuses on the integration glue between existing audio components without redesigning core classes.

## Key Components

### 1. AudioReactiveEffect
A protocol/Mixin that Effects must implement to receive audio data. Defines:
- `on_audio_features(features: AudioFeatures)`: Called per frame with latest audio data
- `get_audio_params() -> dict`: Returns effect-specific audio parameters
- `set_audio_sensitivity(sensitivity: float)`: Adjusts sensitivity to audio changes

*Implementation Note:* Effects should inherit from `AudioReactiveEffect` or implement its methods directly.

### 2. AudioEffectBus
A registry that connects one `AudioAnalyzer` to multiple Effects. Responsibilities:
- Maintains list of registered Effects
- Distributes `AudioFeatures` from analyzer to all registered Effects per frame
- Handles fallback to `DummyAudioAnalyzer` when no real audio device is available

### 3. EffectChain Integration
The `EffectChain.render()` method now accepts an `audio_reactor` parameter (instance of `AudioEffectBus`). During rendering:
1. Bus collects `AudioFeatures` from analyzer
2. Bus invokes `on_audio_features()` on all registered Effects
3. Effects modify parameters via `set_audio_sensitivity()` as needed

## Public Interface
- Effects must implement `AudioReactiveEffect` protocol
- Bus is initialized with `AudioAnalyzer` (defaults to `DummyAudioAnalyzer` if none provided)
- `EffectChain.render(audio_reactor=bus_instance)` must be used for activation

## Edge Cases
1. **No Audio Device**: Bus automatically uses `DummyAudioAnalyzer` with silence features
2. **Performance**: Bus must process <1ms per frame (optimized via direct memory access to `AudioFeatures`)
3. **Parameter Consistency**: `get_audio_params()` must return stable defaults when no audio is available

## Test Plan (8+ Tests)
1. Register/unregister Effects with bus
2. Verify `on_audio_features` called per frame
3. Test `DummyAudioAnalyzer` fallback
4. Validate parameter persistence across frames
5. Stress test with 10+ Effects
6. Measure frame processing time
7. Test parameter updates via `set_audio_sensitivity`
8. Edge case: Bus with no registered Effects

## References
- `src/vjlive3/audio/analyzer.py` (AudioAnalyzer/DummyAudioAnalyzer)
- `src/vjlive3/render/chain.py` (EffectChain.render() hook)
- `docs/specs/_02_fleshed_out/P1-A1_audio_analyzer.md` (existing audio component spec)
- `docs/specs/_02_fleshed_out/P1-A5_audio_reactivity.md` (reactivity patterns)

---

## As-Built Implementation Notes

**Date:** 2026-03-03 | **Agent:** Antigravity | **Coverage:** 93%

### Files Created
- `src/vjlive3/audio/reactive_effect.py` — 167 lines
- `tests/audio/test_reactive_effect.py` — 12 tests

### Actual Public Interface

```python
class AudioReactiveEffect:           # pure mixin, no ABC
    def on_audio_features(self, features: AudioFeatures) -> None
    def get_audio_params(self) -> dict  # returns safe defaults if no data yet
    def set_audio_sensitivity(self, sensitivity: float) -> None  # clamped ≥0
    def get_audio_sensitivity(self) -> float

class AudioEffectBus:
    def __init__(self, analyzer: Optional[AudioAnalyzer] = None)  # → DummyAudioAnalyzer
    def register(self, effect: Any) -> None      # idempotent
    def unregister(self, effect: Any) -> None
    def process_frame(self) -> AudioFeatures     # fan-out + returns features
    # AudioReactor-compatible extensions (not in original spec):
    def get_energy(self) -> float
    def get_band(self, band: str = "bass") -> float
    def get_feature(self, name: str, default: float = 0.0) -> float
    def set_analyzer(self, analyzer: AudioAnalyzer) -> None
    effect_count: int      # property
    frame_count: int       # property
    last_frame_ms: float   # property — last process_frame() overhead in ms
```

### ADRs
1. **Mixin not Protocol** — `AudioReactiveEffect` is a Python mixin, not `typing.Protocol`. Chosen for simpler multiple-inheritance with existing Effect classes without requiring structural subtyping.
2. **AudioReactor API on Bus** — Added `get_energy()`, `get_band()`, `get_feature()` so `AudioEffectBus` is a drop-in replacement for `AudioReactor` in `EffectChain.render(audio_reactor=...)` — no adapter needed.
3. **Thread safety** — `threading.RLock` guards the effects list, consistent with the A1 `AudioAnalyzer` pattern.