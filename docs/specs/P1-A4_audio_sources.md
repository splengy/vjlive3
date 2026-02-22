# Spec: P1-A4 — Audio Sources (Multi-Input Management)

**File naming:** `docs/specs/P1-A4_audio_sources.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P1-A4 — Audio Sources

**Phase:** Phase 1 / P1-A4
**Assigned To:** [Agent name]
**Spec Written By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## What This Module Does

The audio sources system manages multiple audio input sources, including system audio capture, file playback, microphone input, and network streams. It provides a unified interface for audio acquisition, format conversion, and buffering, ensuring consistent sample rates and channel configurations across all sources.

---

## What It Does NOT Do

- Does not perform audio analysis (delegates to P1-A1)
- Does not detect beats (delegates to P1-A2)
- Does not distribute audio to effects (delegates to P1-A3)
- Does not include advanced audio effects or processing

---

## Public Interface

```python
class AudioSource:
    def __init__(self, source_type: str, config: Dict[str, Any]) -> None: ...
    
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...
    
    def read(self, num_samples: int) -> np.ndarray: ...
    def get_sample_rate(self) -> int: ...
    def get_channels(self) -> int: ...
    
    def get_level(self) -> float: ...
    def get_name(self) -> str: ...


class AudioSourceManager:
    def __init__(self, target_sample_rate: int = 44100, buffer_size: int = 2048) -> None: ...
    
    def add_source(self, source: AudioSource) -> str: ...
    def remove_source(self, source_id: str) -> bool: ...
    def get_source(self, source_id: str) -> Optional[AudioSource]: ...
    
    def list_sources(self) -> List[str]: ...
    
    def mix_all(self) -> np.ndarray: ...
    def get_mixed_level(self) -> float: ...
    
    def start_all(self) -> None: ...
    def stop_all(self) -> None: ...
    
    def cleanup(self) -> None: ...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `source_type` | `str` | Type of audio source | 'system', 'file', 'mic', 'network' |
| `config` | `Dict[str, Any]` | Source configuration | Source-specific keys |
| `num_samples` | `int` | Number of samples to read | > 0 |
| `target_sample_rate` | `int` | Output sample rate | 8000-192000 |
| `buffer_size` | `int` | Internal buffer size | Power of 2, 256-8192 |

**Output:** `np.ndarray` — Mixed audio samples (1D or 2D for multi-channel)

---

## Edge Cases and Error Handling

- What happens if source fails to start? → Log error, mark source as failed
- What happens if source drops samples? → Insert silence, log warning
- What happens if sample rates mismatch? → Resample to target rate
- What happens if all sources stop? → Output silence
- What happens on cleanup? → Stop all sources, release resources

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — required for audio buffers — fallback: raise ImportError
  - `soundfile` or `pyaudio` — for audio I/O — fallback: use system defaults
- Internal modules this depends on:
  - None (standalone audio module)

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_hardware` | Module starts without crashing |
| `test_add_remove_source` | Source management works |
| `test_mix_all` | Mixes multiple sources correctly |
| `test_sample_rate_conversion` | Resamples to target rate |
| `test_buffer_management` | Buffering works without underruns |
| `test_source_failure` | Handles source failures gracefully |
| `test_level_monitoring` | Level meters work |
| `test_edge_cases` | Handles invalid configurations |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-1] P1-A4: Audio sources` message
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

*Specification based on VJlive-2 audio source management system.*