# P3-EXT176: TestBassCanon3 Test Plugin

## Specification Status
- **Phase**: Pass 2 (Detailed Technical Spec)
- **Target Phase**: Pass 3 (Implementation)
- **Priority**: P0
- **Module**: `test_bass_cannon_3` test suite
- **Implementation Path**: `src/vjlive3/plugins/test_bass_cannon_3.py`
- **Plugin Type**: Test/Demo/Benchmark

## Executive Summary
TestBassCanon3 is a comprehensive integration test plugin that validates bass-reactive effect chains under realistic performance conditions. It tests audio spectrum analysis, frequency filtering, effect triggering, and visual response timing across multiple simultaneous bass-sensitive effects.

## Problem Statement
Bass-reactive effects are critical for VJ performances but often have:
- Timing issues (responses lag or lead music)
- Frequency detection problems (false triggers, missing peaks)
- Interaction bugs (multiple bass effects interfere)
- Performance issues (heavy audio processing)

There is no comprehensive test fixture that exercises the full bass-reactive pipeline with realistic audio and multiple simultaneous effects, making it difficult to catch regressions.

## Solution Overview
TestBassCanon3 creates a test harness that:
1. Loads audio test signals (synthetic bass patterns)
2. Routes through bass-reactive effect chain
3. Validates frequency detection accuracy
4. Measures response timing
5. Tests multi-effect interactions
6. Benchmarks performance
7. Generates test report

Acts as both automated test and performance benchmark for bass effects.

## Detailed Behavior
### Phase 1: Audio Signal Generation
Create synthetic test signals with known bass patterns using:
- Sine waves at specific frequencies
- Kick drum patterns with exponential decay
- Sub-bass sweeps

### Phase 2: Bass Analyzer Initialization
Set up frequency analyzers for:
- Sub-bass: 20-60Hz
- Mid-bass: 60-250Hz
- Bass: 250-500Hz

### Phase 3: Multiple Effect Chain
Initialize 5 different bass-reactive effects simultaneously:
1. Bass Cannon (P3-BASS-CANNON)
2. Bass Reactor (P3-BASS-REACTOR)
3. Bass Modulator (P3-BASS-MOD)
4. Bass Visualizer (P3-BASS-VIS)
5. Bass Echo (P3-BASS-ECHO)

### Phase 4: Effect Triggering
Apply audio frames and validate:
- Frequency detection accuracy
- Parameter response thresholds
- Visual feedback synchronization

### Phase 5: Timing Measurement
Record latency metrics:
- Audio peak detection: <50ms
- Parameter update: <30ms
- Visual response: <50ms

### Phase 6: Interaction Testing
Verify:
- No cross-talk between effects (correlation <0.1)
- Independent parameter responses
- Consistent timing across effects

### Phase 7: Report Generation
Output:
- JSON report with all metrics
- HTML visualization of test results
- Performance benchmark summary

## Mathematical Formulations
### Synthetic Bass Signal
$$s(t) = A
