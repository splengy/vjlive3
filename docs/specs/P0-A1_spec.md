# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-A1 — AppWindowMonitor

**Phase:** Phase 0  
**Assigned To:** Alex Chen  
**Spec Written By:** Jordan Reed  
**Date:** 2025-04-05

---

## What This Module Does

This module provides a real-time monitoring interface for the VJLive3 application, displaying key performance metrics such as frames per second (FPS), memory usage, and active agent count. It serves as a foundational dashboard to ensure system stability and responsiveness during runtime, enabling developers and operators to detect performance bottlenecks or resource exhaustion early.

---

## What It Does NOT Do

- It does not control or modify application behavior.
- It does not generate visual effects or audio output.
- It does not handle user input or UI interaction beyond displaying metrics.
- It is not responsible for rendering graphics; it only aggregates and presents data from internal systems.

---

## Public Interface

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

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `window_width` | `int` | Width of the monitor window in pixels | Must be ≥ 200 and ≤ 800 |
| `window_height` | `int` | Height of the monitor window in pixels | Must be ≥ 60 and ≤ 300 |
| `window_position` | `tuple[int, int]` | Optional position (x, y) for placement on screen | Not required; defaults to top-left corner |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Use fallback values: FPS = 0.0, memory = 0.0, agents = 0  
- What happens on bad input? → Raise `ValueError` with message "Invalid window dimension provided" for out-of-range inputs  
- What is the cleanup path? → `stop()` calls internal resource release; ensures no open threads or file handles remain

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `psutil` — used to read memory usage — fallback: hardcoded baseline values  
  - `pygetwindow` — optional for window positioning — fallback: default top-left placement  
- Internal modules this depends on:  
  - `vjlive3.core.metrics.SystemMetricsCollector` — for FPS and memory data  
  - `vjlive3.agent.AgentRegistry` — to count active agents  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_valid_dimensions` | Module initializes with valid window size without error |
| `test_init_invalid_width` | Invalid width (e.g., < 200) raises ValueError with correct message |
| `test_get_metrics_returns_expected` | Returns dictionary with correct keys and reasonable values when system is running |
| `test_stop_releases_resources` | No memory leaks or open handles after stop() call |
| `test_no_agents_when_empty` | Returns zero active agents if agent registry is empty |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-A1: AppWindowMonitor - Real-time performance dashboard` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive1/phase2_demo.py (L1-20)
```python
"""
VJLive Effects Demo - Phase 2 Implementation

This script demonstrates the implementation of Phase 2 features:
- Neural Structure (Task Lambda)
- Data Rain (Task Mu)
- Biological Chaos
- Audio-Reactive Strobe
- Additional collaborative effects
"""

import time
import math
import random
from OpenGL.GL import *
from core.effects.new_effects import (
    NeuralStructure, DataRain, BiologicalChaos, AudioStrobe
)
from core.effects.unified_effects import (
    DigitalConsciousness, AnalogPulse, HyperspaceAnalog,
```

### vjlive1/phase2_demo.py (L17-36)
```python
    NeuralStructure, DataRain, BiologicalChaos, AudioStrobe
)
from core.effects.unified_effects import (
    DigitalConsciousness, AnalogPulse, HyperspaceAnalog,
    ModularRetroRack, RealTimeDegradation
)
from core.effects.expressive_effects import (
    NeuralAwakening, DigitalTranscendence, QuantumEmergence
)
from core.effects import (
    ChaosGlitch, Strobe, ReactionDiffusion, AudioWaveform, BeatStrobe
)

class Phase2Demo:
    """Demo class for Phase 2 implementation."""
    
    def __init__(self):
        self.current_time = 0.0
        self.resolution = (1920, 1080)
        self.audio_reactor = None
```

### vjlive1/phase2_demo.py (L33-52)
```python
    def __init__(self):
        self.current_time = 0.0
        self.resolution = (1920, 1080)
        self.audio_reactor = None
        self.parameter_system = ParameterSystem()
        
        # Initialize all Phase 2 effects
        self.init_phase2_effects()
        self.init_cross_modulation()
    
    def init_phase2_effects(self):
        """Initialize Phase 2 effects."""
        # Task Lambda: Neural Structure
        self.neural_structure = NeuralStructure()
        self.parameter_system.register_effect("neural_structure", self.neural_structure)
        
        # Task Mu: Data Rain
        self.data_rain = DataRain()
        self.parameter_system.register_effect("data_rain", self.data_rain)
```

### vjlive1/phase2_demo.py (L49-68)
```python
        # Task Mu: Data Rain
        self.data_rain = DataRain()
        self.parameter_system.register_effect("data_rain", self.data_rain)
        
        # Biological Chaos
        self.biological_chaos = BiologicalChaos()
        self.parameter_system.register_effect("biological_chaos", self.biological_chaos)
        
        # Audio-Reactive Strobe
        self.audio_strobe = AudioStrobe()
        self.parameter_system.register_effect("audio_strobe", self.audio_strobe)
        
        # Add existing unified effects
        self.digital_consciousness = DigitalConsciousness()
        self.analog_pulse = AnalogPulse()
        self.hyperspace_analog = HyperspaceAnalog()
        self.real_time_degradation = RealTimeDegradation()
        self.modular_retro_rack = ModularRetroRack()
        
        self.parameter_system.register_effect("digital_consciousness", self.digital_consciousness)
```

### vjlive1/phase2_demo.py (L65-84)
```python
        self.real_time_degradation = RealTimeDegradation()
        self.modular_retro_rack = ModularRetroRack()
        
        self.parameter_system.register_effect("digital_consciousness", self.digital_consciousness)
        self.parameter_system.register_effect("analog_pulse", self.analog_pulse)
        self.parameter_system.register_effect("hyperspace_analog", self.hyperspace_analog)
        self.parameter_system.register_effect("real_time_degradation", self.real_time_degradation)
        
        # Add expressive effects
        self.neural_awakening = NeuralAwakening()
        self.digital_transcendence = DigitalTranscendence()
        self.quantum_emergence = QuantumEmergence()
        
        self.parameter_system.register_effect("neural_awakening", self.neural_awakening)
        self.parameter_system.register_effect("digital_transcendence", self.digital_transcendence)
        self.parameter_system.register_effect("quantum_emergence", self.quantum_emergence)
        
        # Add other collaborative effects
        self.chaos_glitch = ChaosGlitch()
        self.strobe = Strobe()
```

> [NEEDS RESEARCH]: No direct legacy code references to `SystemMetricsCollector`, `AgentRegistry`, or windowing system in Phase 0.  
> [NEEDS RESEARCH]: No existing implementation of a performance monitor in VJLive1/