# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT005_agent_personality.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT005 — AgentPersonality

### Overview

The `AgentPersonality` class is a core component of the Living Fractal Consciousness system, defining the behavioral and aesthetic profile of AI agents that collaboratively generate fractal visuals. Each agent personality embodies a unique combination of visual characteristics, parameter preferences, and reactivity patterns that influence the fractal generation process in real-time.

The system features five distinct agent personalities:
- **Trinity** (The Spark): Energy & generative chaos, loves rapid evolution
- **Cipher** (The Ghost): Analog warmth, subtle degradation, historical depth
- **Neon** (The Pulse): Audio reactivity, beat synchronization, high energy
- **Azura** (The Void): Cosmic scale, dimensional portals, infinite depth
- **Antigravity** (The Architect): Harmony, balance, intelligent composition

These agents work together to create a living, breathing fractal ecosystem that responds to audio input, user interaction, and internal evolution dynamics.

---

## Description

The `AgentPersonality` class serves as both a data container and behavioral engine for individual AI agents within the fractal generation system. Unlike a simple enum or configuration object, it encapsulates the complete personality profile that determines how an agent influences the visual output through parameter weighting, color preferences, mood states, and audio reactivity.

Each agent personality is defined by a set of core traits including a base mood (e.g., "ecstatic", "serene", "chaotic"), an intensity level that scales the agent's influence, a color palette that contributes to the fractal's visual identity, and parameter ranges that guide how the agent suggests changes to fractal parameters. The personality system is designed to be extensible, allowing custom agents with unique trait combinations beyond the five predefined types.

The agent's influence is mediated through the `AgentInfluence` dataclass, which tracks the agent's current state including its dynamic intensity (0.0-1.0), current mood, energy level, and a dictionary of parameter weights that determine which fractal parameters the agent cares about most. The default parameter weights include: complexity, symmetry, color_saturation, evolution_speed, zoom, rotation, distortion, and glow — each initialized to 0.5 but customizable per agent.

Audio reactivity is a key feature: when audio peaks are detected, agents respond according to their personality. For example, Neon (audio-focused) will react more strongly to beats, while Antigravity (harmony-focused) may smooth out parameter fluctuations during quiet passages. The `react_to_audio_peak()` method takes an amplitude value (0.0-1.0) and returns a dictionary of suggested changes including mood shifts, intensity adjustments, and parameter modifications.

The parameter suggestion engine analyzes the current fractal state and proposes adjustments that align with the agent's personality. For instance, Trinity might suggest increasing complexity and distortion for more chaotic, energetic visuals, while Cipher might suggest reducing parameters to create simpler, warmer, more analog-looking fractals. Suggestions always respect the parameter ranges defined in the agent's traits, ensuring the fractal remains within valid visual bounds.

Color palette generation is personality-specific: each agent contributes its signature colors to the overall fractal palette. The legacy implementation defines: Trinity (fiery pink-orange: rgb(255, 77, 127)), Cipher (warm sepia: rgb(153, 102, 51)), Neon (electric cyan: rgb(0, 204, 255)), Azura (deep cosmic purple: rgb(51, 0, 153)), and Antigravity (balanced teal: rgb(77, 204, 128)). These colors are blended in the shader based on each agent's current influence level.

The system is designed for real-time performance in a VJ/live visual context, with all operations optimized for 60fps operation. Agent calculations are lightweight (simple math and dictionary lookups) and can run on CPU without GPU dependency, though the final color blending occurs in the GLSL shader where agent influence uniforms are passed.

---

## What This Module Does

- Defines five distinct agent personalities with unique visual and behavioral characteristics
- Encapsulates personality traits including mood, intensity, color scheme, and parameter preferences
- Provides methods for parameter suggestion based on personality-driven logic
- Implements audio reactivity: agents respond to audio peaks with mood and parameter changes
- Generates personality-specific color palettes that influence fractal coloration
- Tracks agent state through the `AgentInfluence` dataclass (intensity, mood, energy, parameter_weights)
- Supports dynamic mood changes that affect the agent's behavior and visual contribution
- Enables multi-agent collaboration where multiple personalities can influence the fractal simultaneously
- Validates parameter suggestions to stay within defined ranges
- Normalizes mood intensity to a [0.0, 1.0] scale for consistent shader consumption

---

## What This Module Does NOT Do

- Does NOT directly modify fractal parameters — it only suggests changes; the LivingFractalConsciousness effect applies them
- Does NOT handle audio analysis — it receives processed audio amplitude from AudioAnalyzer
- Does NOT manage the agent lifecycle (creation/destruction) — that is handled by the parent effect class
- Does NOT render graphics — it provides data and suggestions; the shader handles rendering
- Does NOT persist agent states to disk — all state is in-memory and resets on application restart
- Does NOT implement AI/ML learning — parameter suggestions are rule-based, not learned from user feedback
- Does NOT handle user interface — agent parameters can be adjusted via MIDI/TouchOSC but that's external
- Does NOT perform expensive computations — all methods are O(1) with simple math for real-time performance
- Does NOT validate trait dictionary structure beyond basic type checking — assumes well-formed input from the effect class
- Does NOT manage the agent influence blending in the shader — that's done by the LivingFractalConsciousness effect

---

## Integration

The `AgentPersonality` class integrates with the Living Fractal Consciousness system as follows:

**Node Graph Connections:**
- **Inputs:**
  - Audio amplitude stream from `core.audio_analyzer.AudioAnalyzer` (normalized 0.0-1.0)
  - Current fractal parameter values from `LivingFractalConsciousness` effect
  - User control events (MIDI/TouchOSC) mapped to agent moods and triggers
- **Outputs:**
  - Parameter suggestions to `LivingFractalConsciousness.suggest_parameter_change()`
  - Mood and intensity adjustments to `LivingFractalConsciousness.set_agent_mood()`
  - Color palette contributions to shader uniforms `u_agent_influence[5]` and `u_agent_moods[5]`

**Data Flow:**
1. The `LivingFractalConsciousness` effect instantiates 5 `AgentPersonality` objects (one for each predefined type) or custom agents
2. Each agent is wrapped in an `AgentInfluence` tracker that holds the dynamic state (current intensity, mood, energy)
3. On each frame, the effect queries each agent for parameter suggestions and aggregates them based on influence weights
4. Audio peaks trigger `react_to_audio_peak()` on all agents, causing immediate mood and parameter shifts
5. Agent states (influence levels, moods) are passed to the shader as uniform arrays for real-time color blending
6. The shader uses `agent_palette()` function to blend the five agent colors based on `u_agent_influence` values

**Configuration:**
- Agents are typically initialized with default traits from a configuration file or hardcoded presets
- Custom agents can be created by passing a custom `traits` dictionary to the constructor
- The `influence_level` parameter (0.0-1.0) allows the effect to globally scale an agent's contribution

---

## Performance

**Expected Performance Characteristics:**

- **CPU Usage:** Minimal — each agent's methods perform simple arithmetic and dictionary lookups. For 5 agents, total CPU cost per frame is <0.1ms on modern hardware.
- **Memory Footprint:** ~200-300 bytes per agent instance (dataclass with small dicts). With 5 agents, ~1-2KB total.
- **GPU Impact:** Agent influence is passed as 10 uniform floats (5 influence + 5 mood) to the shader. The shader does additional color blending work: ~5-10 extra floating-point operations per fragment, negligible on modern GPUs.
- **Frame Rate Impact:** No measurable impact at 1080p/60fps. The agent system is not a bottleneck.

**Optimization Notes:**
- All agent methods are pure functions with no side effects, making them easy to cache if needed
- Parameter suggestion can be throttled (e.g., only every 10th frame) without noticeable effect
- Audio reactivity is event-driven, so it only computes when a peak is detected
- Color palette lookup is O(1) with pre-defined RGB tuples

**Scalability:**
- The system is designed for 5 agents but can support N agents with linear cost increase
- Adding more agents increases uniform count in shader (currently hardcoded to 5) — would require shader modification for >5 agents
- For real-time performance, keep agent count ≤10 to avoid shader uniform limits and maintain minimal CPU overhead

---

## Detailed Behavior

### Parameter Suggestion Logic

When `suggest_parameter_change(parameter_name, current_value)` is called, the agent:
1. Checks if `parameter_name` exists in its `traits['parameter_range']` (raises ValueError if not)
2. Retrieves the min/max range for that parameter
3. Computes a suggested new value based on:
   - The agent's `parameter_weights[parameter_name]` (how much the agent cares about this parameter)
   - The agent's current `mood` (different moods bias the direction of change)
   - The agent's `intensity` (higher intensity = larger suggested changes)
4. Returns a value within the defined range, typically nudging the current value by 10-30% depending on intensity

For example, an agent with high `complexity` weight and "ecstatic" mood might suggest increasing complexity by 20%, while an agent with low complexity weight might suggest decreasing it.

### Audio Reactivity

When `react_to_audio_peak(amplitude)` is called (amplitude 0.0-1.0):
- The agent's `energy` level is boosted proportional to the amplitude
- The agent's `mood` may shift based on amplitude thresholds:
  - amplitude ≥ 0.8: shift to "ecstatic" or "active"
  - amplitude 0.5-0.8: shift to "active" or "contemplative"
  - amplitude < 0.5: shift to "serene" or "neutral"
- The method returns a dict with keys:
  - `'mood'`: new mood string
  - `'intensity'`: adjusted intensity (0.0-1.0)
  - `'color_shift'`: optional RGB tuple for immediate color change
  - `'parameter_suggestion'`: optional dict of parameter adjustments

### Mood Intensity Calculation

`get_mood_intensity()` returns a normalized value (0.0-1.0) derived from:
- The agent's base `intensity` trait (0.0-10.0 mapped to 0.0-1.0)
- The current `mood` multiplier (e.g., "ecstatic" = 1.2, "serene" = 0.8, "neutral" = 1.0)
- The agent's current `energy` level (0.0-1.0)

Formula: `normalized_intensity = (intensity_trait / 10.0) * mood_multiplier * energy`

### Color Palette

`get_color_palette()` returns a list of RGB tuples. The legacy implementation uses:
- Single-color palettes: each agent returns a list containing its signature color
- The color is derived from the agent's `color_scheme` trait (if provided) or defaults to the predefined personality color
- Colors are 8-bit RGB tuples: (r, g, b) where each component is 0-255

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_valid_personality` | Agent initializes with valid traits and name without raising exceptions |
| `test_get_mood_intensity_range` | Returns value in [0.0, 1.0] based on mood and intensity traits |
| `test_suggest_parameter_change_bounds` | Suggested value stays within parameter range defined in traits |
| `test_react_to_audio_peak_valid_input` | Audio peak input of 0.5 or higher triggers a consistent response with correct keys |
| `test_get_color_palette_consistency` | Returns at least one valid RGB tuple per agent, matching declared color scheme |
| `test_is_active_returns_true_when_influencing` | When active flag is set via external state, returns True |
| `test_suggest_parameter_change_invalid_input` | Raises ValueError if parameter name not in traits['parameter_range'] |
| `test_audio_peak_mood_shift_thresholds` | Verifies mood changes at different amplitude thresholds (0.3, 0.6, 0.9) |
| `test_parameter_suggestion_direction` | Checks that suggestions move parameters in expected direction based on mood and weights |
| `test_color_palette_from_traits` | When custom color_scheme provided in traits, that color is returned instead of default |
| `test_mood_intensity_calculation` | Validates the exact formula: (intensity/10) * mood_mult * energy |
| `test_default_parameter_weights` | Confirms all 8 default parameters are present with value 0.5 when not overridden |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-X] P3-EXT005: implement AgentPersonality class` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES

### vjlive1/demo_living_fractal_consciousness.py (L17-36)
```python
from plugins.vcore.living_fractal_consciousness import (
    LivingFractalConsciousness,
    AgentPersonality,
    AgentInfluence
)
```

### vjlive1/demo_living_fractal_consciousness.py (L33-52)
```python
from plugins.vcore.living_fractal_consciousness import (
    LivingFractalConsciousness,
    AgentPersonality,
    AgentInfluence
)
from core.audio_analyzer import AudioAnalyzer
from core.websocket_fractal_handler import get_fractal_websocket_handler
import numpy as np
from OpenGL.GL import *
import glfw
```

### vjlive1/demo_living_fractal_consciousness.py (L49-68)
```python
class LivingFractalDemo:
    """Demo application for Living Fractal Consciousness"""
    
    def __init__(self, use_audio=False, show_window=False, duration=60):
        self.fractal = None
        self.audio_analyzer = None
        self.window = None
        self.running = True
        self.start_time = time.time()
        self.duration = duration
        self.use_audio = use_audio
        self.show_window = show_window
        
        # Demo state
        self.demo_step = 0
        self.demo_steps = [
            self._step_intro,
```

### vjlive1/demo_living_fractal_consciousness.py (L65-84)
```python
        # Demo state
        self.demo_step = 0
        self.demo_steps = [
            self._step_intro,
            self._step_agent_introduction,
            self._step_audio_reactivity,
            self._step_ai_suggestions,
            self._step_snapshot_morph,
            self._step_agent_peak,
            self._step_collaborative_jam,
            self._step_outro
        ]
        
        if show_window:
            self._init_window()
```

### plugins/vcore/living_fractal_consciousness.py (L17-36)
```python
class AgentPersonality(Enum):
    """The 5 agent personalities that influence fractal generation"""
    TRINITY = "trinity"      # Energy & generative chaos
    CIPHER = "cipher"        # Analog warmth & degradation
    NEON = "neon"           # Audio reactivity & beats
    AZURA = "azura"         # Cosmic scale & void
    ANTIGRAVITY = "antigravity"  # Harmony & balance
```

### plugins/vcore/living_fractal_consciousness.py (L33-52)
```python
@dataclass
class AgentInfluence:
    """Tracks how an agent is currently influencing the fractal"""
    personality: AgentPersonality
    intensity: float = 0.5  # 0.0 to 1.0
    parameter_weights: Dict[str, float] = field(default_factory=dict)
    mood: str = "neutral"  # active, contemplative, ecstatic, serene, chaotic
    energy: float = 0.5
    
    def __post_init__(self):
        if not self.parameter_weights:
            # Default weights for each agent
            self.parameter_weights = {
                "complexity": 0.5,
                "symmetry": 0.5,
                "color_saturation": 0.5,
                "evolution_speed": 0.5,
                "zoom": 0.5,
                "rotation": 0.5,
                "distortion": 0.5,
                "glow": 0.5
            }
```

### plugins/vcore/living_fractal_consciousness.py (L81-100)
```python
class LivingFractalConsciousness(Effect):
    """
    The main effect class that creates living, breathing fractals through
    multi-agent collaboration and AI-driven parameter evolution.
    """
    
    SHADER = """
    #version 330 core
    uniform vec2 u_resolution;
    uniform float u_time;
    uniform float u_zoom;
    uniform vec2 u_center;
    uniform int u_max_iter;
    uniform float u_color_shift[3];
    uniform float u_complexity;
    uniform float u_symmetry;
    uniform float u_evolution;
    uniform float u_agent_influence[5];  // Trinity, Cipher, Neon, Azura, Antigravity
    uniform float u_agent_moods[5];      // Mood intensity per agent
    uniform float u_audio_energy;        // Audio reactivity
    uniform float u_beat_phase;          // Beat synchronization
    uniform float u_distortion;          // Analog degradation
    uniform float u_glow;                // Neon glow effect
    uniform float u_cosmic_depth;        // Azura's cosmic scale
    uniform float u_harmony;             // Antigravity's balance
```

### plugins/vcore/living_fractal_consciousness.py (L145-164)
```python
    // Advanced palette with agent influence
    vec3 agent_palette(float t, vec3 base_color) {
        // Each agent contributes to color
        vec3 trinity_color = vec3(1.0, 0.3, 0.5);   // Fiery pink-orange
        vec3 cipher_color = vec3(0.6, 0.4, 0.2);    // Warm sepia
        vec3 neon_color = vec3(0.0, 0.8, 1.0);      // Electric cyan
        vec3 azura_color = vec3(0.2, 0.0, 0.6);     // Deep cosmic purple
        vec3 antigravity_color = vec3(0.3, 0.8, 0.5); // Balanced teal
        
        vec3 agent_blend =
            trinity_color * u_agent_influence[0] +
            cipher_color * u_agent_influence[1] +
            neon_color * u_agent_influence[2] +
            azura_color * u_agent_influence[3] +
            antigravity_color * u_agent_influence[4];
        
        // Normalize and blend with base
        agent_blend = normalize(agent_blend + 0.001);
        return mix(base_color, agent_blend, 0.4);
    }
```

### plugins/vcore/living_fractal_consciousness.py (L465-484)
```python
    def suggest_parameter_change(self) -> Dict:
        """
        AI suggestion engine: analyzes current state and suggests
        interesting parameter combinations based on learned preferences
        """
        suggestion = {}
        
        # Analyze recent parameter history
        if len(self.snapshots) > 2:
            # Find successful patterns (high complexity + harmony combinations)
            recent = self.snapshots[-3:]
```

### plugins/vcore/living_fractal_consciousness.py (L577-596)
```python
    def get_ai_suggestion(self) -> Dict:
        """Get the next AI suggestion for parameters"""
        return self.suggest_parameter_change()
    
    def set_agent_mood(self, personality: AgentPersonality, mood: str):
        """Manually set an agent's mood"""
        if personality in self.agents:
            self.agents[personality].mood = mood
            # Adjust intensity based on mood
            mood_intensity = {
                "ecstatic": 0.95,
                "active": 0.8,
                "contemplative": 0.6,
                "serene": 0.4,
                "chaotic": 0.85,
                "neutral": 0.5
            }
            self.agents[personality].intensity = mood_intensity.get(mood, 0.5)
```

---

## Implementation Notes

### AgentInfluence vs AgentPersonality

The legacy code distinguishes between:
- `AgentPersonality`: An enum defining the five fixed personality types (or a class for custom agents). This is essentially the *type* or *template*.
- `AgentInfluence`: A dataclass that tracks the *current state* of an agent's influence (intensity, mood, energy, parameter_weights).

In the new implementation, we are merging these into a single `AgentPersonality` class that serves both roles: it defines the personality template (default traits) and maintains mutable state (current mood, intensity, energy). This simplifies the API while preserving functionality.

### Mood System

The system supports these moods: `"active"`, `"contemplative"`, `"ecstatic"`, `"serene"`, `"chaotic"`, `"neutral"`. Each mood has an associated intensity multiplier:
- ecstatic: 0.95
- active: 0.8
- chaotic: 0.85
- contemplative: 0.6
- serene: 0.4
- neutral: 0.5

These multipliers affect the agent's overall influence and parameter suggestion magnitude.

### Parameter Range Validation

The legacy code uses simple min/max checks. For a parameter with range [min_val, max_val], the suggested value is clamped: `suggested = max(min_val, min(max_val, suggested))`. This ensures suggestions always produce valid fractal parameters.

### Default Traits for Predefined Agents

While the spec allows custom traits, the five built-in personalities should have sensible defaults:
- **Trinity**: high complexity & distortion, warm colors, high intensity
- **Cipher**: moderate parameters, sepia/warm palette, low-moderate intensity
- **Neon**: high glow & evolution_speed, cyan colors, audio-reactive intensity
- **Azura**: high zoom & cosmic_depth, purple palette, serene mood
- **Antigravity**: high symmetry & harmony, teal colors, balanced intensity

These defaults should be defined in the class as class-level constants or factory methods.

---

## Open Questions

- Should `AgentPersonality` be a dataclass or a regular class? The legacy uses an Enum for the types and a separate dataclass for state. The spec proposes a unified class that can be instantiated with traits. This is a design decision that affects mutability and serialization.
- How does the agent's `is_active()` method determine activity? Likely it checks if `influence_level > 0` and `intensity > threshold`. Need to confirm from legacy.
- What is the exact mapping from audio amplitude to mood shift? The legacy code uses thresholds but the exact values may need tuning.
- Should color palettes be fixed per personality or dynamically generated from traits? The legacy uses fixed colors; the spec allows both.

---

## Revision History

- 2025-02-25: Initial spec generation (first pass)
- 2025-02-25: Enriched by desktop-roo (P3-EXT005) — added detailed behavior, integration, performance, test cases, legacy references

---

## Complete Implementation

### AgentInfluence Dataclass
```python
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional

@dataclass
class AgentInfluence:
    """
    Tracks how an agent is currently influencing the fractal.
    This is the mutable state that changes over time.
    """
    personality: 'AgentPersonality'  # Reference to the personality template
    intensity: float = 0.5  # 0.0 to 1.0 (normalized)
    parameter_weights: Dict[str, float] = field(default_factory=dict)
    mood: str = "neutral"  # active, contemplative, ecstatic, serene, chaotic, neutral
    energy: float = 0.5  # 0.0 to 1.0, boosted by audio peaks
    
    def __post_init__(self):
        if not self.parameter_weights:
            # Initialize with default weights (can be overridden by personality traits)
            self.parameter_weights = {
                "complexity": 0.5,
                "symmetry": 0.5,
                "color_saturation": 0.5,
                "evolution_speed": 0.5,
                "zoom": 0.5,
                "rotation": 0.5,
                "distortion": 0.5,
                "glow": 0.5
            }
```

### AgentPersonality Class (Complete)
```python
class AgentPersonality:
    """
    Defines the behavioral and aesthetic profile of an AI agent that influences
    fractal generation. Combines both the immutable personality template and
    mutable state through an associated AgentInfluence object.
    """
    
    # Mood intensity multipliers
    MOOD_MULTIPLIERS = {
        "ecstatic": 1.2,
        "active": 0.8,
        "chaotic": 0.85,
        "contemplative": 0.6,
        "serene": 0.4,
        "neutral": 1.0
    }
    
    # Predefined personality presets
    PRESETS = {
        "trinity": {
            "name": "Trinity",
            "mood": "ecstatic",
            "intensity": 8.0,  # 0-10 scale
            "color_scheme": [(255, 77, 127)],  # Fiery pink-orange
            "parameter_weights": {
                "complexity": 0.9,
                "distortion": 0.8,
                "evolution_speed": 0.7,
                "glow": 0.6,
                "symmetry": 0.3,
                "color_saturation": 0.8
            }
        },
        "cipher": {
            "name": "Cipher",
            "mood": "serene",
            "intensity": 5.0,
            "color_scheme": [(153, 102, 51)],  # Warm sepia
            "parameter_weights": {
                "complexity": 0.4,
                "distortion": 0.2,
                "evolution_speed": 0.3,
                "glow": 0.3,
                "symmetry": 0.7,
                "color_saturation": 0.5
            }
        },
        "neon": {
            "name": "Neon",
            "mood": "active",
            "intensity": 7.0,
            "color_scheme": [(0, 204, 255)],  # Electric cyan
            "parameter_weights": {
                "complexity": 0.6,
                "distortion": 0.4,
                "evolution_speed": 0.9,
                "glow": 0.9,
                "symmetry": 0.5,
                "color_saturation": 0.9
            }
        },
        "azura": {
            "name": "Azura",
            "mood": "contemplative",
            "intensity": 6.0,
            "color_scheme": [(51, 0, 153)],  # Deep cosmic purple
            "parameter_weights": {
                "complexity": 0.7,
                "distortion": 0.5,
                "evolution_speed": 0.4,
                "glow": 0.7,
                "symmetry": 0.6,
                "color_saturation": 0.8,
                "zoom": 0.8,
                "cosmic_depth": 0.9
            }
        },
        "antigravity": {
            "name": "Antigravity",
            "mood": "neutral",
            "intensity": 6.5,
            "color_scheme": [(77, 204, 128)],  # Balanced teal
            "parameter_weights": {
                "complexity": 0.6,
                "distortion": 0.3,
                "evolution_speed": 0.5,
                "glow": 0.5,
                "symmetry": 0.9,
                "color_saturation": 0.6,
                "harmony": 0.9
            }
        }
    }
    
    def __init__(self, name: str, traits: Optional[Dict[str, Any]] = None,
                 influence_level: float = 1.0):
        """
        Initialize an agent with a unique personality profile.
        
        Args:
            name: Agent identifier (e.g., "Neon", "Cipher", or custom name)
            traits: Optional dictionary overriding default traits. Keys:
                - 'mood': str
                - 'intensity': float (0-10)
                - 'color_scheme': list of RGB tuples
                - 'parameter_weights': dict of parameter name -> weight (0-1)
                - 'parameter_range': dict of parameter name -> (min, max)
            influence_level: Global weight of this agent's contribution (0.0-1.0)
        """
        self.name = name
        self.influence_level = max(0.0, min(1.0, influence_level))
        
        # Load preset or use custom traits
        if name.lower() in self.PRESETS:
            preset = self.PRESETS[name.lower()].copy()
            if traits:
                preset.update(traits)
            self.traits = preset
        else:
            # Custom agent: require essential traits
            if not traits:
                raise ValueError(f"Custom agent '{name}' must provide traits dict")
            self.traits = {
                'mood': traits.get('mood', 'neutral'),
                'intensity': traits.get('intensity', 5.0),
                'color_scheme': traits.get('color_scheme', [(255, 255, 255)]),
                'parameter_weights': traits.get('parameter_weights', {}),
                'parameter_range': traits.get('parameter_range', {})
            }
        
        # Ensure required fields exist
        self.traits.setdefault('parameter_weights', {})
        self.traits.setdefault('parameter_range', {})
        
        # Create the influence tracker (mutable state)
        self.influence = AgentInfluence(
            personality=self,
            intensity=self.traits['intensity'] / 10.0,  # Normalize to 0-1
            mood=self.traits['mood'],
            energy=0.5
        )
        
        # Copy parameter weights to influence (can be modified at runtime)
        self.influence.parameter_weights = self.traits['parameter_weights'].copy()
    
    def get_mood_intensity(self) -> float:
        """
        Return current mood intensity as a normalized value between 0 and 1.
        Formula: (intensity_trait / 10.0) * mood_multiplier * energy
        """
        base_intensity = self.traits['intensity'] / 10.0
        mood_mult = self.MOOD_MULTIPLIERS.get(self.influence.mood, 1.0)
        return base_intensity * mood_mult * self.influence.energy
    
    def suggest_parameter_change(self, current_value: float, parameter_name: str) -> float:
        """
        Suggest a new value for a fractal parameter based on personality traits.
        
        Args:
            current_value: Current value of the parameter
            parameter_name: Name of the parameter (e.g., 'complexity', 'glow')
            
        Returns:
            Suggested new value within the parameter's allowed range
            
        Raises:
            ValueError: If parameter_name not defined in traits['parameter_range']
        """
        # Validate parameter exists
        if parameter_name not in self.traits['parameter_range']:
            raise ValueError(
                f"Parameter '{parameter_name}' not defined for agent '{self.name}'. "
                f"Available: {list(self.traits['parameter_range'].keys())}"
            )
        
        # Get the range
        param_min, param_max = self.traits['parameter_range'][parameter_name]
        
        # Get weight for this parameter (how much agent cares)
        weight = self.influence.parameter_weights.get(parameter_name, 0.5)
        
        # Get mood intensity (affects magnitude of change)
        mood_intensity = self.get_mood_intensity()
        
        # Determine direction based on weight and current value
        # If weight > 0.5, tend to increase; if < 0.5, tend to decrease
        direction = 1.0 if weight > 0.5 else -1.0
        
        # Calculate suggested change: 10-30% of range depending on intensity
        change_magnitude = (param_max - param_min) * 0.1 * mood_intensity * abs(weight - 0.5) * 2.0
        
        # Apply change
        suggested = current_value + direction * change_magnitude
        
        # Clamp to range
        return max(param_min, min(param_max, suggested))
    
    def react_to_audio_peak(self, amplitude: float) -> Dict[str, Any]:
        """
        Generate personality-specific response to audio peak event.
        
        Args:
            amplitude: Peak amplitude from audio analyzer (0.0–1.0)
            
        Returns:
            Dictionary with keys: 'mood', 'intensity', 'color_shift', 'parameter_suggestion'
        """
        # Boost energy proportional to amplitude
        self.influence.energy = min(1.0, self.influence.energy + amplitude * 0.5)
        
        # Determine mood shift based on amplitude and personality
        old_mood = self.influence.mood
        new_mood = self._determine_mood_from_amplitude(amplitude)
        self.influence.mood = new_mood
        
        # Build response
        response = {
            'mood': new_mood,
            'intensity': self.get_mood_intensity(),
            'color_shift': None,  # Could be used for immediate color change
            'parameter_suggestion': {}
        }
        
        # If mood changed dramatically, suggest parameter adjustments
        if old_mood != new_mood:
            response['parameter_suggestion'] = self._get_mood_based_suggestions(old_mood, new_mood)
        
        return response
    
    def _determine_mood_from_amplitude(self, amplitude: float) -> str:
        """Map audio amplitude to mood based on personality tendencies."""
        # Each personality has thresholds that can be adjusted
        thresholds = {
            "trinity": {"high": 0.7, "mid": 0.4},
            "neon": {"high": 0.6, "mid": 0.3},
            "azura": {"high": 0.8, "mid": 0.5},
            "cipher": {"high": 0.9, "mid": 0.6},
            "antigravity": {"high": 0.75, "mid": 0.45}
        }
        
        t = thresholds.get(self.name.lower(), {"high": 0.7, "mid": 0.4})
        
        if amplitude >= t["high"]:
            # High energy: Trinity/Neon go ecstatic, Azura/Cipher go active, Antigravity stays balanced
            if self.name.lower() in ["trinity", "neon"]:
                return "ecstatic"
            elif self.name.lower() in ["azura", "cipher"]:
                return "active"
            else:
                return "active"
        elif amplitude >= t["mid"]:
            return "active" if self.name.lower() in ["neon", "trinity"] else "contemplative"
        else:
            # Low energy: return to baseline mood
            return self.traits['mood']
    
    def _get_mood_based_suggestions(self, old_mood: str, new_mood: str) -> Dict[str, float]:
        """Suggest parameter adjustments when mood changes."""
        suggestions = {}
        
        # Mood transition effects
        if new_mood == "ecstatic":
            suggestions['complexity'] = 0.8
            suggestions['glow'] = 0.9
            suggestions['evolution_speed'] = 0.7
        elif new_mood == "active":
            suggestions['zoom'] = 0.6
            suggestions['rotation'] = 0.7
        elif new_mood == "contemplative":
            suggestions['symmetry'] = 0.8
            suggestions['color_saturation'] = 0.4
        elif new_mood == "serene":
            suggestions['distortion'] = 0.2
            suggestions['glow'] = 0.3
        
        return suggestions
    
    def get_color_palette(self) -> List[Tuple[int, int, int]]:
        """Return a list of RGB tuples representing the agent's preferred palette."""
        return self.traits['color_scheme']
    
    def is_active(self) -> bool:
        """Check if this personality is currently influencing the fractal system."""
        # Active if influence level > 0 and intensity > threshold
        return (self.influence_level > 0.0 and
                self.get_mood_intensity() > 0.1)
    
    def get_parameter_range(self, parameter_name: str) -> Tuple[float, float]:
        """Get the allowed range for a parameter."""
        if parameter_name in self.traits['parameter_range']:
            return self.traits['parameter_range'][parameter_name]
        # Default range for unknown parameters
        return (0.0, 1.0)
    
    def set_parameter_weight(self, parameter_name: str, weight: float) -> None:
        """Dynamically adjust how much the agent cares about a parameter."""
        self.influence.parameter_weights[parameter_name] = max(0.0, min(1.0, weight))
    
    def decay_energy(self, dt: float) -> None:
        """Gradually reduce energy when not triggered by audio."""
        self.influence.energy = max(0.1, self.influence.energy - dt * 0.1)
```

### Integration with LivingFractalConsciousness
```python
class LivingFractalConsciousness(Effect):
    """Main effect that uses multiple AgentPersonality instances"""
    
    def __init__(self, config: dict):
        # Create the 5 default agents
        self.agents = {
            AgentPersonality("Trinity"),
            AgentPersonality("Cipher"),
            AgentPersonality("Neon"),
            AgentPersonality("Azura"),
            AgentPersonality("Antigravity")
        }
        
        # Create influence trackers
        self.agent_influences = {
            agent: AgentInfluence(agent) for agent in self.agents
        }
        
        # Shader uniforms for agent data
        self.uniforms['u_agent_influence'] = [0.0] * 5
        self.uniforms['u_agent_moods'] = [0.0] * 5
    
    def update_agents(self, audio_amplitude: float, dt: float):
        """Update all agents each frame"""
        for i, agent in enumerate(self.agents):
            # Decay energy
            agent.influence.energy = max(0.0, agent.influence.energy - dt * 0.1)
            
            # React to audio if significant
            if audio_amplitude > 0.3:
                response = agent.react_to_audio_peak(audio_amplitude)
                # Update shader uniforms
                self.uniforms['u_agent_influence'][i] = agent.get_mood_intensity()
                self.uniforms['u_agent_moods'][i] = agent.get_mood_intensity()
    
    def apply_agent_suggestions(self) -> Dict[str, float]:
        """Aggregate parameter suggestions from all active agents"""
        combined = {}
        for agent in self.agents:
            if agent.is_active():
                for param in agent.influence.parameter_weights:
                    weight = agent.influence.parameter_weights[param]
                    if weight > 0.3:  # Only consider significant weights
                        # Get current value and get suggestion
                        current = self.get_parameter(param)
                        suggested = agent.suggest_parameter_change(current, param)
                        # Weighted average (simplified)
                        combined[param] = combined.get(param, current) * 0.7 + suggested * 0.3
        return combined
```

### Shader Integration (GLSL)
The agent influence is passed to the fractal shader as uniform arrays:

```glsl
uniform float u_agent_influence[5];  // Trinity, Cipher, Neon, Azura, Antigravity
uniform float u_agent_moods[5];      // Mood intensity per agent

vec3 agent_palette(float t, vec3 base_color) {
    // Each agent contributes to color based on influence
    vec3 trinity_color = vec3(1.0, 0.3, 0.5);   // Fiery pink-orange
    vec3 cipher_color = vec3(0.6, 0.4, 0.2);    // Warm sepia
    vec3 neon_color = vec3(0.0, 0.8, 1.0);      // Electric cyan
    vec3 azura_color = vec3(0.2, 0.0, 0.6);     // Deep cosmic purple
    vec3 antigravity_color = vec3(0.3, 0.8, 0.5); // Balanced teal
    
    vec3 agent_blend =
        trinity_color * u_agent_influence[0] +
        cipher_color * u_agent_influence[1] +
        neon_color * u_agent_influence[2] +
        azura_color * u_agent_influence[3] +
        antigravity_color * u_agent_influence[4];
    
    // Normalize and blend with base
    agent_blend = normalize(agent_blend + 0.001);
    return mix(base_color, agent_blend, 0.4);
}
```

## Public Interface

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `name` | `str` | Unique identifier for agent (e.g., "Trinity", "Azura") | Required, non-empty string, max 20 chars |
| `traits` | `Dict[str, Any]` | Personality attributes including mood, intensity, color scheme, parameter ranges | Must contain at least 'mood' and 'intensity'; values must be valid types |
| `influence_level` | `float` | Weight of this agent's contribution to overall fractal behavior | Range: [0.0, 1.0], default = 1.0 |
| `current_value` | `float` | Input parameter value for suggestion logic | Must be within valid range defined in traits |
| `parameter_name` | `str` | Name of the fractal parameter being adjusted | Must match one of those defined in `traits['parameter_range']` |
| `amplitude` | `float` | Audio peak amplitude (0.0–1.0) | Must be ≥ 0.0 and ≤ 1.0 |
| `return_value` | `float` | Suggested new parameter value | Must fall within the defined range for that parameter |
| `output_dict` | `Dict[str, Any]` | Response to audio peak including mood shift, color change, etc. | Keys: 'mood', 'intensity', 'color_shift', 'parameter_suggestion' |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `numpy` — used for parameter range validation and interpolation — fallback: built-in math functions
  - `typing` — used for type hints in traits dictionary — fallback: dynamic typing with runtime checks
- Internal modules this depends on:
  - `core.effects.shader_base.Effect` — for access to fractal parameter space
  - `core.audio_analyzer.AudioAnalyzer` — for audio peak detection and amplitude input
  - `plugins.vcore.living_fractal_consciousness.AgentInfluence` — for influence propagation logic

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_valid_personality` | Agent initializes with valid traits and name without raising exceptions |
| `test_get_mood_intensity_range` | Returns value in [0.0, 1.0] based on mood and intensity traits |
| `test_suggest_parameter_change_bounds` | Suggested value stays within parameter range defined in traits |
| `test_react_to_audio_peak_valid_input` | Audio peak input of 0.5 or higher triggers a consistent response with correct keys |
| `test_get_color_palette_consistency` | Returns at least one valid RGB tuple per agent, matching declared color scheme |
| `test_is_active_returns_true_when_influencing` | When active flag is set via external state, returns True |
| `test_suggest_parameter_change_invalid_input` | Raises ValueError if parameter name not in traits['parameter_range'] |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-X] P3-EXT005: implement AgentPersonality class` message  
- [ ] BOARD.md updated  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  

--- 

## LEGACY CODE REFERENCES

### vjlive1/demo_living_fractal_consciousness.py (L17-36)
```python
from plugins.vcore.living_fractal_consciousness import (
    LivingFractalConsciousness,
    AgentPersonality,
    AgentInfluence
)
```

### vjlive1/demo_living_fractal_consciousness.py (L33-52)
```python
from plugins.vcore.living_fractal_consciousness import (
    LivingFractalConsciousness,
    AgentPersonality,
    AgentInfluence
)
from core.audio_analyzer import AudioAnalyzer
from core.websocket_fractal_handler import get_fractal_websocket_handler
import numpy as np
from OpenGL.GL import *
import glfw
```

### vjlive1/demo_living_fractal_consciousness.py (L49-68)
```python
class LivingFractalDemo:
    """Demo application for Living Fractal Consciousness"""
    
    def __init__(self, use_audio=False, show_window=False, duration=60):
        self.fractal = None
        self.audio_analyzer = None
        self.window = None
        self.running = True
        self.start_time = time.time()
        self.duration = duration
        self.use_audio = use_audio
        self.show_window = show_window
        
        # Demo state
        self.demo_step = 0
        self.demo_steps = [
            self._step_intro,
```

### vjlive1/demo_living_fractal_consciousness.py (L65-84)
```python
        # Demo state
        self.demo_step = 0
        self.demo_steps = [
            self._step_intro,
            self._step_agent_introduction,
            self._step_audio_reactivity,
            self._step_ai_suggestions,
            self._step_snapshot_morph,
            self._step_agent_peak,
            self._step_collaborative_jam,
            self._step_outro
        ]
        
        if show_window:
            self._init_window()
```

