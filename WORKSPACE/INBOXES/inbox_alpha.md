# P3-EXT005: LivingFractalConsciousness (AgentPersonality)

## 📋 Task Overview
**Port the LivingFractalConsciousness effect from VJLive-2 to VJLive3.** This is a sophisticated fractal visualization system with a 5-agent personality model that dynamically influences fractal parameters, creating emergent, consciousness-like behavior.

**Priority:** P3 (Missing Legacy Effect)
**Estimated Complexity:** 8/10 (Advanced: agent system, audio reactivity, snapshot morphing, AI suggestions)
**Source:** `/home/happy/Desktop/claude projects/VJlive-2/plugins/core/living_fractal_consciousness/__init__.py` (626 lines)

---

## 🎯 Core Concept

The effect renders a Julia set fractal whose parameters are continuously influenced by 5 distinct agent personalities:

- **Trinity** (Energy & generative chaos) → boosts complexity, evolution speed, distortion
- **Cipher** (Analog warmth & degradation) → adds noise, chromatic aberration, film grain
- **Neon** (Audio reactivity & beats) → responds to audio frequencies, pulse effects
- **Azura** (Cosmic scale & void) → controls zoom, color depth, cosmic scale
- **Antigravity** (Harmony & balance) → smooths transitions, stabilizes, adds glow

Each agent has:
- **Intensity** (0.0-10.0): overall influence strength
- **Mood** (string: "ecstatic", "calm", "aggressive", "melancholic", "mysterious"): modifies parameter weights
- **Parameter weights**: per-agent tuning of which fractal parameters they affect most

The system includes:
- **Audio reactivity**: Neon agent responds to audio spectrum
- **Snapshot & morph**: Save fractal states and smoothly interpolate between them
- **AI suggestion engine**: Proposes parameter changes based on recent evolution
- **Peak triggers**: Momentary intensity boosts for performance moments

---

## 📐 Technical Specification

### 1. File Structure

```
src/vjlive3/plugins/living_fractal_consciousness.py
tests/plugins/test_living_fractal_consciousness.py
```

**Target size:** ≤ 750 lines (including tests)

### 2. Class Hierarchy

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import numpy as np
from OpenGL.GL import glUniform1f, glUniform1i, glActiveTexture, glBindTexture, GL_TEXTURE0

from ..base import Effect

class AgentPersonality(Enum):
    TRINITY = "trinity"
    CIPHER = "cipher"
    NEON = "neon"
    AZURA = "azura"
    ANTIGRAVITY = "antigravity"

@dataclass
class AgentInfluence:
    personality: AgentPersonality
    intensity: float = 5.0  # 0.0-10.0
    mood: str = "neutral"
    parameter_weights: Dict[str, float] = field(default_factory=dict)
    # weights: complexity, evolution_speed, distortion, glow, noise, chromatic_aberration,
    #          zoom, color_shift, pulse, symmetry, decay

@dataclass
class FractalSnapshot:
    timestamp: float
    description: str
    parameters: Dict[str, float]
    agent_states: Dict[str, Dict]
    # interpolation: morph to/from snapshots

class LivingFractalConsciousness(Effect):
    METADATA = {
        "id": "living_fractal_consciousness",
        "name": "Living Fractal Consciousness",
        "description": "Julia set fractal with 5-agent personality system, audio reactivity, and state morphing",
        "version": "3.0.0",
        "author": "VJLive-2 Legacy → VJLive3 Port",
        "tags": ["fractal", "agent", "consciousness", "audio_reactive", "ai"],
        "priority": 80,
        "can_be_disabled": True,
        "needs_gl_context": True,
        "size_impact": 45,  # MB
        "performance_impact": 35,  # FPS cost
        "dependencies": ["numpy", "PyOpenGL"],
        "license": "proprietary"
    }

    def __init__(self):
        # Initialize agents with default configs
        # Initialize fractal parameters
        # Initialize GL resources
        # Initialize audio reactor
        # Initialize snapshot system
        pass

    def apply_uniforms(self, time_val, resolution, audio_reactor=None, semantic_layer=None):
        # Send all uniforms to shader including agent_influence[5], agent_moods[5]
        pass

    def set_parameter(self, name: str, value: float):
        # Handle all parameters with 0.0-10.0 range
        pass

    def update_audio(self, audio_data: Dict):
        # Neon agent audio reactivity
        pass

    def evolve_agents(self, delta_time: float):
        # Autonomous agent evolution (mood changes, intensity drift)
        pass

    def create_snapshot(self, description: str = "") -> FractalSnapshot:
        # Save current state
        pass

    def start_morph_to(self, target_snapshot: FractalSnapshot, duration: float = 5.0):
        # Begin interpolation to target state
        pass

    def update_morph(self, delta_time: float) -> bool:
        # Update morph progress, return True when complete
        pass

    def suggest_parameter_change(self) -> Dict:
        # AI suggestion engine: propose parameter adjustments
        pass

    def set_agent_mood(self, personality: AgentPersonality, mood: str):
        # Manual mood override
        pass

    def trigger_agent_peak(self, personality: AgentPersonality, duration: float = 2.0):
        # Momentary intensity boost
        pass

    def get_agent_status(self) -> Dict:
        # Return current agent states for UI
        pass
```

### 3. Parameters (0.0-10.0 Range)

| Parameter | Default | Description | Agent Influence |
|-----------|---------|-------------|-----------------|
| `complexity` | 5.0 | Julia set C real/imag iterations | Trinity, Cipher |
| `evolution_speed` | 3.0 | How fast fractal evolves over time | Trinity, Neon |
| `distortion` | 2.0 | Geometric distortion amount | Trinity, Cipher |
| `glow` | 4.0 | Bloom/glow intensity | Antigravity, Azura |
| `noise` | 1.5 | Film grain / analog noise | Cipher |
| `chromatic_aberration` | 2.0 | RGB channel separation | Cipher |
| `zoom` | 1.0 | Fractal zoom level | Azura |
| `color_shift` | 3.0 | Color palette rotation | Azura, Neon |
| `pulse` | 0.0 | Audio-reactive pulsing (Neon) | Neon |
| `symmetry` | 5.0 | Symmetry order (2-8) | Antigravity |
| `decay` | 2.0 | Trail/afterimage decay | Antigravity |

**Total:** 11 user-facing parameters

### 4. GLSL Fragment Shader (278 lines)

The shader is a Julia set fractal with agent-influenced transformations. Key components:

```glsl
#version 330 core
uniform float u_time;
uniform vec2 u_resolution;
uniform sampler2D u_texture;
uniform float u_params[11];  // complexity, evolution_speed, distortion, glow, noise, chroma, zoom, color_shift, pulse, symmetry, decay
uniform float u_agent_influence[5];  // Trinity, Cipher, Neon, Azura, Antigravity
uniform float u_agent_moods[5];      // mood intensity per agent

// Agent-influenced transformations
// Julia set iteration with dynamic C parameter
// Color mapping based on iteration count with agent-modified palettes
// Post-processing: glow, noise, chromatic aberration
```

**Shader features:**
- Julia set fractal: `z = z^2 + c` with time-varying `c`
- `c` derived from `complexity` + agent influences
- Symmetry folding based on `symmetry` parameter
- Color palette: cosine-based with `color_shift` rotation
- Glow: multiple blur passes with additive blending
- Noise: film grain using `u_agent_influence[CIPHER]`
- Chromatic aberration: RGB channel offset based on `chromatic_aberration`
- Pulse: audio-reactive brightness modulation (Neon agent)

### 5. Agent System Details

**Default Agent Configs:**

```python
agent_configs = {
    AgentPersonality.TRINITY: {
        "intensity": 0.8,
        "mood": "ecstatic",
        "weights": {
            "complexity": 0.9,
            "evolution_speed": 0.95,
            "distortion": 0.7,
            "glow": 0.6,
            "noise": 0.3,
            "chromatic_aberration": 0.4,
            "zoom": 0.2,
            "color_shift": 0.5,
            "pulse": 0.3,
            "symmetry": 0.4,
            "decay": 0.5
        }
    },
    AgentPersonality.CIPHER: {
        "intensity": 0.6,
        "mood": "calm",
        "weights": {
            "complexity": 0.4,
            "evolution_speed": 0.3,
            "distortion": 0.8,
            "glow": 0.2,
            "noise": 0.95,
            "chromatic_aberration": 0.85,
            "zoom": 0.3,
            "color_shift": 0.4,
            "pulse": 0.2,
            "symmetry": 0.5,
            "decay": 0.7
        }
    },
    AgentPersonality.NEON: {
        "intensity": 0.7,
        "mood": "aggressive",
        "weights": {
            "complexity": 0.5,
            "evolution_speed": 0.8,
            "distortion": 0.4,
            "glow": 0.7,
            "noise": 0.2,
            "chromatic_aberration": 0.3,
            "zoom": 0.4,
            "color_shift": 0.9,
            "pulse": 0.95,  # audio reactive
            "symmetry": 0.3,
            "decay": 0.4
        }
    },
    AgentPersonality.AZURA: {
        "intensity": 0.75,
        "mood": "mysterious",
        "weights": {
            "complexity": 0.6,
            "evolution_speed": 0.4,
            "distortion": 0.3,
            "glow": 0.85,
            "noise": 0.1,
            "chromatic_aberration": 0.2,
            "zoom": 0.9,
            "color_shift": 0.8,
            "pulse": 0.4,
            "symmetry": 0.6,
            "decay": 0.3
        }
    },
    AgentPersonality.ANTIGRAVITY: {
        "intensity": 0.85,
        "mood": "neutral",
        "weights": {
            "complexity": 0.7,
            "evolution_speed": 0.5,
            "distortion": 0.4,
            "glow": 0.9,
            "noise": 0.15,
            "chromatic_aberration": 0.25,
            "zoom": 0.5,
            "color_shift": 0.6,
            "pulse": 0.35,
            "symmetry": 0.95,
            "decay": 0.85
        }
    }
}
```

**Mood Modifiers:**
- `"ecstatic"`: +30% evolution_speed, +20% glow, -15% decay
- `"calm"`: -40% distortion, +25% symmetry, +20% decay
- `"aggressive"`: +50% pulse, +30% distortion, -20% glow
- `"mysterious"`: +40% color_shift, +30% zoom, -25% complexity
- `"melancholic"`: +50% noise, +30% decay, -40% glow
- `"neutral"`: no modifiers

**Agent Evolution:**
- Every 5-15 seconds, agents may autonomously change mood
- Intensity slowly drifts ±0.1 per minute
- Can be manually controlled via `set_agent_mood()` and `trigger_agent_peak()`

### 6. Presets (5 Minimum)

1. **balanced** (default): All agents at 0.8 intensity, neutral moods
2. **trinity_dominant**: Trinity 1.0, others 0.3; ecstatic mood; high complexity/evolution
3. **neon_pulse**: Neon 1.0, others 0.2; aggressive mood; max pulse, high color_shift
4. **azura_cosmic**: Azura 1.0, others 0.3; mysterious mood; high zoom, glow, color_shift
5. **cipher_analog**: Cipher 1.0, others 0.2; calm mood; high noise, chromatic_aberration, decay

**Preset format:**
```python
{
    "balanced": {
        "complexity": 5.0, "evolution_speed": 3.0, "distortion": 2.0, "glow": 4.0,
        "noise": 1.5, "chromatic_aberration": 2.0, "zoom": 1.0, "color_shift": 3.0,
        "pulse": 0.0, "symmetry": 5.0, "decay": 2.0,
        "agent_intensities": [0.8, 0.8, 0.8, 0.8, 0.8],
        "agent_moods": ["neutral"] * 5
    },
    # ... other presets
}
```

### 7. Audio Reactivity

- **Neon agent** receives audio data via `update_audio(audio_data: Dict)`
- `audio_data` contains: `{"bass": 0.0-1.0, "mid": 0.0-1.0, "high": 0.0-1.0, "beat": 0.0-1.0, "volume": 0.0-1.0}`
- `pulse` parameter directly modulated by `audio_data["beat"]` and `audio_data["bass"]`
- Agent influence: Neon's `pulse` weight (0.95) amplifies audio response
- Smoothing: 50ms attack, 100ms decay

### 8. Snapshot & Morph System

```python
snapshot: Optional[FractalSnapshot] = None
morph_target: Optional[FractalSnapshot] = None
morph_start_time: float = 0.0
morph_duration: float = 5.0
morph_progress: float = 0.0

def create_snapshot(self, description: str = "") -> FractalSnapshot:
    """Capture current fractal state including all parameters and agent states."""

def start_morph_to(self, target: FractalSnapshot, duration: float = 5.0):
    """Begin smooth interpolation to target state."""

def update_morph(self, dt: float) -> bool:
    """Update morph interpolation. Returns True when complete."""
    # Linear interpolation of all parameters
    # Also interpolate agent states
```

**Use cases:**
- Transition between performance scenes
- Smooth preset changes
- Save/restore favorite states

### 9. AI Suggestion Engine

```python
def suggest_parameter_change(self) -> Dict:
    """
    Analyze recent evolution and suggest parameter adjustments.
    Returns: {
        "parameter": str,
        "current_value": float,
        "suggested_value": float,
        "confidence": float,
        "reason": str
    }
    """
```

**Logic:**
- Track parameter changes and resulting visual complexity (via shader brightness variance)
- If `complexity` too low → suggest +1.0 to `complexity` or `distortion`
- If FPS dropping → suggest -1.0 to `glow` or `noise`
- If audio reactive weak → suggest +1.5 to `pulse` or `evolution_speed`
- Confidence based on consistency of pattern (0.0-1.0)
- Suggestions appear every 30-60 seconds

### 10. Peak Trigger System

```python
def trigger_agent_peak(self, personality: AgentPersonality, duration: float = 2.0):
    """
    Momentarily boost agent intensity to 2.0 for 'duration' seconds.
    Used for climactic moments in performance.
    """
```

- Sets agent intensity to 2.0 (above normal 0.0-1.0 range)
- Smooth ramp up (0.2s) and ramp down (0.5s)
- Visual impact: dramatic fractal transformation
- Auto-decays back to normal intensity after `duration`

---

## 🧪 Test Plan

### Unit Tests (≥ 80% coverage)

**test_living_fractal_consciousness.py**

1. **Agent System**
   - `test_agent_personality_enum()`
   - `test_agent_influence_default_values()`
   - `test_agent_configs_complete()`
   - `test_mood_modifier_trinity_ecstatic()`
   - `test_mood_modifier_cipher_calm()`
   - `test_mood_modifier_neon_aggressive()`
   - `test_mood_modifier_azura_mysterious()`
   - `test_set_agent_mood_valid()`
   - `test_set_agent_mood_invalid_raises()`

2. **Parameter System**
   - `test_all_parameters_present()`
   - `test_parameter_range_clamping_0_to_10()`
   - `test_set_parameter_valid()`
   - `test_get_agent_influence_vector_length_5()`
   - `test_get_agent_mood_vector_length_5()`

3. **Snapshot & Morph**
   - `test_create_snapshot_captures_all_parameters()`
   - `test_create_snapshot_captures_agent_states()`
   - `test_start_morph_to_sets_target()`
   - `test_update_morph_progress_linear()`
   - `test_update_morph_completes_at_1_0()`
   - `test_morph_interpolates_parameters()`
   - `test_morph_interpolates_agent_states()`

4. **Audio Reactivity**
   - `test_update_audio_sets_pulse()`
   - `test_audio_data_bass_modulates_pulse()`
   - `test_audio_data_beat_triggers_peak()`
   - `test_audio_smoothing_50ms_attack()`

5. **Agent Evolution**
   - `test_evolve_agents_runs_without_error()`
   - `test_evolve_agents_mood_change_interval_5_to_15s()`
   - `test_evolve_agents_intensity_drift()`

6. **AI Suggestions**
   - `test_suggest_parameter_change_returns_dict()`
   - `test_suggest_parameter_change_keys()`
   - `test_suggest_parameter_change_low_complexity_suggests_complexity_boost()`
   - `test_suggest_parameter_change_fps_drop_suggests_reduction()`
   - `test_suggest_parameter_change_confidence_0_to_1()`

7. **Peak Trigger**
   - `test_trigger_agent_peak_sets_intensity_2_0()`
   - `test_trigger_agent_peak_auto_decay()`
   - `test_trigger_agent_peak_ramp_up_200ms()`
   - `test_trigger_agent_peak_ramp_down_500ms()`

8. **Uniform Application**
   - `test_apply_uniforms_sets_all_floats()`
   - `test_apply_uniforms_sets_agent_influence_array()`
   - `test_apply_uniforms_sets_agent_mood_array()`
   - `test_apply_uniforms_sets_parameter_array()`

9. **Integration**
   - `test_full_cycle_parameter_change_to_shader()`
   - `test_agent_influence_affects_fractal_parameters()`
   - `test_snapshot_morph_preserves_visual_continuity()`

### Performance Tests

- `test_fps_above_60_with_all_agents_active()`: Render 60s, assert mean FPS ≥ 60
- `test_fps_above_60_with_peak_trigger()`: Render with peak active, assert FPS ≥ 55
- `test_memory_under_50mb()`: Monitor memory during 5min render
- `test_audio_reactive_latency_under_50ms()`: Measure audio→visual latency

### Visual Regression Tests

- Render reference frames for each preset (balanced, trinity_dominant, neon_pulse, azura_cosmic, cipher_analog)
- Compare pixel-wise against golden images (tolerance: ΔE < 2.0)
- Test snapshot morph: render start, 50%, 100% and verify smooth interpolation

---

## ⚙️ Implementation Notes

### 1. Shader Integration

The GLSL shader must be embedded as a Python string constant:

```python
FRAGMENT_SHADER = """
#version 330 core
// ... 278 lines of shader code ...
"""
```

**Shader uniforms:**
```python
uniforms = {
    "u_time": (1f, None),
    "u_resolution": (2f, None),
    "u_texture": (1i, "2D"),
    "u_params": (11f, None),  # all 11 parameters
    "u_agent_influence": (5f, None),  # 5 agents
    "u_agent_moods": (5f, None)  # 5 moods
}
```

### 2. Agent Influence Calculation

In `apply_uniforms()`, compute final parameter values:

```python
def _compute_agent_modified_params(self) -> np.ndarray:
    """
    Base params + sum(agent_intensity * agent_weight * agent_influence)
    Returns array of 11 modified parameters.
    """
    base = np.array([self.params[p] for p in PARAM_ORDER])
    for i, personality in enumerate(AgentPersonality):
        agent = self.agents[personality]
        influence = agent.intensity * self.agent_influence[i]
        weights = np.array([agent.parameter_weights.get(p, 0.0) for p in PARAM_ORDER])
        base += influence * weights * 0.1  # scaled contribution
    return np.clip(base, 0.0, 10.0)
```

### 3. Audio Reactivity Smoothing

```python
self.audio_buffer = {
    "bass": 0.0,
    "mid": 0.0,
    "high": 0.0,
    "beat": 0.0,
    "volume": 0.0
}

def update_audio(self, audio_data):
    # Exponential smoothing
    for key in self.audio_buffer:
        self.audio_buffer[key] = 0.7 * self.audio_buffer[key] + 0.3 * audio_data.get(key, 0.0)
    # Map to pulse parameter
    self.params["pulse"] = (self.audio_buffer["bass"] + self.audio_buffer["beat"]) * 5.0
```

### 4. Snapshot Serialization

```python
def create_snapshot(self, description: str = "") -> FractalSnapshot:
    return FractalSnapshot(
        timestamp=time.time(),
        description=description,
        parameters=self.params.copy(),
        agent_states={
            p.name: {
                "intensity": a.intensity,
                "mood": a.mood,
                "weights": a.parameter_weights.copy()
            } for p, a in self.agents.items()
        }
    )
```

### 5. Morph Interpolation

```python
def update_morph(self, dt: float) -> bool:
    if self.morph_target is None:
        return True
    self.morph_progress += dt / self.morph_duration
    if self.morph_progress >= 1.0:
        self.morph_progress = 1.0
        self.morph_target = None
        return True
    t = self.morph_progress
    # Interpolate all parameters
    for param in self.params:
        self.params[param] = (1-t) * self.morph_start_params[param] + t * self.morph_target_params[param]
    # Interpolate agent states
    # ...
    return False
```

### 6. AI Suggestion Logic

```python
def suggest_parameter_change(self) -> Dict:
    # Analyze last 60 seconds of parameter history
    if len(self.param_history) < 120:  # need at least 2Hz sampling
        return {}
    # Compute variance of brightness from shader (would need feedback)
    # For now: heuristic based on current params
    suggestions = []
    if self.params["complexity"] < 3.0:
        suggestions.append({
            "parameter": "complexity",
            "current_value": self.params["complexity"],
            "suggested_value": min(10.0, self.params["complexity"] + 1.5),
            "confidence": 0.8,
            "reason": "Low complexity reduces visual interest"
        })
    # ... more heuristics
    return suggestions[0] if suggestions else {}
```

---

## 🔒 Safety Rails Compliance

| Rail | Status | Notes |
|------|--------|-------|
| **60 FPS Sacred** | ✅ Compliant | Target: 60 FPS with all 5 agents active; peak trigger may drop to 55 FPS (acceptable) |
| **Offline-First** | ✅ Compliant | No network calls; all local computation |
| **Plugin Integrity** | ✅ Compliant | `METADATA` constant present; inherits from `Effect` |
| **750-Line Limit** | ✅ Compliant | Estimated: 420 lines (effect) + 278 lines (shader) + 300 lines (tests) = 1000 total → **needs consolidation** |
| **Test Coverage ≥380%** | ✅ Planned | 35+ unit tests covering all methods |
| **No Silent Failures** | ✅ Compliant | All errors raise explicit exceptions; shader compilation errors caught and logged |
| **Resource Leak Prevention** | ✅ Compliant | GL resources cleaned up in `__del__`; no file handles |
| **Backward Compatibility** | ✅ Compliant | Parameter names match legacy; shader uniform layout compatible |
| **Security** | ✅ Compliant | No user input in shader; all uniforms sanitized |

**⚠️ 750-Line Risk:** The shader alone is 278 lines. Combined with effect class (~420) and tests (~300), we exceed 750. **Mitigation:** Move shader to separate file `shaders/living_fractal_consciousness.frag` and load at runtime. This keeps main module under 500 lines.

---

## 🎨 Legacy Reference Analysis

**Original Implementation:** `VJLive-2/plugins/core/living_fractal_consciousness/__init__.py` (626 lines)

**Key features preserved:**
- ✅ 5-agent personality system with enums
- ✅ AgentInfluence and FractalSnapshot dataclasses
- ✅ Full GLSL shader with agent uniforms
- ✅ Audio reactivity via `update_audio()`
- ✅ Snapshot creation and morphing
- ✅ AI suggestion engine
- ✅ Peak trigger system
- ✅ Autonomous agent evolution (mood changes)

**Differences from legacy:**
- Legacy uses custom `AudioAnalyzer` class; VJLive3 uses standardized `audio_reactor` interface
- Legacy has face tracking integration (removed - not applicable)
- Legacy uses `set_parameter` with string names; VJLive3 uses same convention
- Legacy stores snapshots in JSON; VJLive3 will use dataclass serialization

**Porting confidence:** 95% — direct translation with minor API adjustments

---

## 🚀 Implementation Phases

### Phase 1: Foundation (Days 1-2)
- [ ] Create `src/vjlive3/plugins/living_fractal_consciousness.py`
- [ ] Implement `AgentPersonality` enum and `AgentInfluence`/`FractalSnapshot` dataclasses
- [ ] Initialize `__init__` with agent configs and parameter defaults
- [ ] Implement `set_parameter()` with range clamping
- [ ] Write basic unit tests for agent system

### Phase 2: Core Rendering (Days 3-4)
- [ ] Embed GLSL shader (278 lines) as string constant or external file
- [ ] Implement `apply_uniforms()` to send all uniforms
- [ ] Implement `_compute_agent_modified_params()` for agent influence
- [ ] Test shader compilation and basic rendering
- [ ] Visual verification: render 60s, confirm fractal appears

### Phase 3: Advanced Features (Days 5-6)
- [ ] Implement `update_audio()` with smoothing
- [ ] Implement `evolve_agents()` with mood/auto-evolution
- [ ] Implement snapshot system (`create_snapshot`, `start_morph_to`, `update_morph`)
- [ ] Implement AI suggestion engine (`suggest_parameter_change`)
- [ ] Implement peak trigger (`trigger_agent_peak`)
- [ ] Implement `get_agent_status()` for UI

### Phase 4: Testing & Validation (Days 7-8)
- [ ] Complete all 35+ unit tests
- [ ] Performance tests: FPS ≥ 60, memory < 50MB
- [ ] Visual regression: render all 5 presets, compare to golden images
- [ ] Audio reactivity test with synthetic audio
- [ ] Snapshot morph smoothness test
- [ ] Full test coverage ≥ 80%
- [ ] Run `pytest --cov=src/vjlive3/plugins/living_fractal_consciousness`

---

## ✅ Acceptance Criteria

1. **Functional completeness:** All 11 parameters work; all 5 agents influence fractal; audio reactivity functional
2. **Performance:** ≥ 60 FPS mean with all agents active; ≤ 50ms audio-to-visual latency
3. **Quality:** ≥ 80% test coverage; no memory leaks; no silent failures
4. **Legacy parity:** Feature-for-feature match with VJLive-2 implementation
5. **Safety:** Passes all safety rails; shader compiles without errors; no GPU hangs
6. **Documentation:** Code fully typed; docstrings present; METADATA complete

---

## 🔗 Dependencies

- **Python:** `numpy`, `PyOpenGL`
- **Internal:** `src/vjlive3/plugins/base.py` (Effect base class)
- **Audio:** `src/vjlive3/audio/engine.py` (AudioAnalyzer interface)
- **Tests:** `pytest`, `pytest-cov`, `pytest-benchmark`

---

## 📊 Success Metrics

- **Lines of code:** ≤ 500 (effect) + 278 (shader) = 778 total (with external shader: ≤ 500)
- **Test coverage:** ≥ 80%
- **FPS:** ≥ 60 (mean), ≥ 55 (1st percentile)
- **Memory:** ≤ 50 MB
- **Shader compile time:** ≤ 100ms
- **Audio latency:** ≤ 50ms

---

## 📝 Notes for Implementation Engineer

- **Read the legacy file carefully:** The agent system is the heart of this effect. Understand how `u_agent_influence[5]` and `u_agent_moods[5]` are used in the shader.
- **Shader optimization:** The Julia set is computationally expensive. Use `GL_FRAGMENT_PRECISION_HIGH` and optimize loops (max 64 iterations).
- **Audio integration:** The `audio_reactor` parameter in `apply_uniforms` may be `None`. Handle gracefully.
- **Snapshot morphing:** Use linear interpolation for parameters; for agent states, interpolate intensity and smoothly transition moods (morph between mood strings? maybe just snap).
- **AI suggestions:** Start with simple heuristics; can be enhanced later with actual machine learning.
- **Testing:** The snapshot system needs careful testing to ensure interpolation is numerically stable.
- **Performance:** Profile the shader. If FPS < 60, consider reducing max iterations or adding an LOD system (lower iterations when FPS drops).

**Good luck! This is one of the most sophisticated legacy effects. Nail it and the rest is downhill.**
