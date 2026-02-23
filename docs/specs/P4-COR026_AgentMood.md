# P4-COR026: AgentMood — Agent Emotional State System

## Mission Context
The `AgentMood` system defines and manages the emotional states and mood dynamics for autonomous agents in VJLive3. It is part of the Awesome Collaborative Creation system and influences agent behavior, creativity, and interactions during live performance. This core infrastructure enables agents to exhibit personality-consistent emotional responses to the performance environment.

## Technical Requirements

### Core Responsibilities
1. **Mood State Management**
   - Define discrete mood states (e.g., happy, sad, energetic, calm, focused, chaotic)
   - Mood transitions with configurable triggers and durations
   - Mood intensity levels (0.0-1.0) for nuanced emotional expression
   - Mood persistence and decay over time

2. **Mood-Influenced Behavior**
   - Parameter modulation based on current mood
   - Creative decision-making influenced by emotional state
   - Interaction style adaptation (aggressive vs. gentle)
   - Color and visual preferences tied to mood

3. **Collaborative Mood Dynamics**
   - Mood contagion between agents (emotional synchronization)
   - Group mood aggregation for ensemble behavior
   - Conflict resolution when agents have opposing moods
   - Harmony optimization across multiple agents

4. **Performance Reactivity**
   - Mood response to audio features (beat, energy, tempo)
   - Mood shifts triggered by visual events
   - Audience interaction affecting agent mood
   - Time-of-day and performance phase influences

5. **Persistence and Learning**
   - Mood history tracking and pattern analysis
   - Learning which mood transitions are most effective
   - Personality-specific mood baselines
   - Configuration persistence across sessions

### Architecture Constraints
- **Lightweight**: Mood calculations must not impact 60 FPS render loop
- **Deterministic**: Mood transitions should be predictable and controllable
- **Configurable**: All mood parameters exposed via ConfigManager
- **Extensible**: Easy to add new mood states and transition rules
- **Thread-Safe**: Mood updates from multiple sources must be safe

### Key Interfaces
```python
class AgentMood:
    def __init__(self, config: MoodConfig, event_bus: Optional[EventBus] = None):
        """Initialize mood system with configuration."""
        pass

    def initialize(self) -> None:
        """Load mood definitions, set initial state."""
        pass

    def start(self) -> None:
        """Begin mood processing and updates."""
        pass

    def stop(self) -> None:
        """Pause mood updates."""
        pass

    def cleanup(self) -> None:
        """Save mood history, release resources."""
        pass

    def get_current_mood(self) -> MoodState:
        """Get the current mood state and intensity."""
        pass

    def set_mood(self, mood: MoodType, intensity: float = 1.0, duration: Optional[float] = None) -> None:
        """Directly set the agent's mood."""
        pass

    def transition_to(self, mood: MoodType, transition_time: float = 1.0) -> None:
        """Smoothly transition to a new mood."""
        pass

    def update(self, delta_time: float, context: PerformanceContext) -> None:
        """Update mood based on performance context (called each frame)."""
        pass

    def get_mood_parameter(self, param_name: str) -> float:
        """Get a mood-modulated parameter value (0.0-10.0)."""
        pass

    def get_color_palette(self) -> List[Color]:
        """Get the color palette associated with current mood."""
        pass

    def get_behavior_bias(self) -> BehaviorBias:
        """Get behavioral biases influenced by current mood."""
        pass

    def on_audio_feature(self, feature: AudioFeature) -> None:
        """React to audio features (beat, energy, etc.)."""
        pass

    def on_visual_event(self, event: VisualEvent) -> None:
        """React to visual events (effect triggered, parameter change)."""
        pass

    def on_agent_interaction(self, agent_id: str, interaction_type: InteractionType) -> None:
        """React to interactions with other agents."""
        pass

    def get_status(self) -> MoodSystemStatus:
        """Return mood system health and statistics."""
        pass
```

### Dependencies
- **ConfigManager**: Load `MoodConfig` (mood definitions, transition rules, personalities)
- **EventBus**: Publish `MoodChanged`, `MoodTransitionStarted`, `BehaviorBiasUpdated` events
- **HealthMonitor**: Report mood system health
- **AgentPersona**: Personality-specific mood baselines and preferences
- **PerformanceContext**: Current performance state (BPM, energy, audience response)
- **AudioFeature**: Audio analysis data for mood reactivity
- **AwesomeCollaborativeCreationSystem**: Multi-agent mood coordination

## Implementation Notes

### Mood State Design
```python
class MoodType(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ENERGETIC = "energetic"
    CALM = "calm"
    FOCUSED = "focused"
    CHAOTIC = "chaotic"
    MYSTERIOUS = "mysterious"
    PLAYFUL = "playful"
    SERIOUS = "serious"

class MoodState:
    mood: MoodType
    intensity: float  # 0.0 to 1.0
    timestamp: float  # When this mood started
    transition_progress: float  # 0.0-1.0 for smooth transitions
```

### Mood Transition Rules
- **Triggers**: Audio beat, parameter threshold, time interval, external event
- **Conditions**: Must satisfy preconditions (e.g., current mood, agent state)
- **Actions**: Set mood, modulate parameters, trigger visual effects
- **Duration**: Fixed time, conditional, or indefinite until next trigger

### Mood-Influenced Parameters
- **Creativity**: How experimental the agent is (0.0-10.0)
- **Precision**: How precise the agent's actions are (0.0-10.0)
- **Energy**: How intense the agent's contributions are (0.0-10.0)
- **RiskTaking**: Willingness to try unusual effects (0.0-10.0)
- **Collaboration**: How much the agent coordinates with others (0.0-10.0)

### Color Palettes
Each mood has an associated color palette:
- **Happy**: Bright, warm colors (yellows, oranges, pinks)
- **Sad**: Cool, desaturated colors (blues, grays, purples)
- **Energetic**: High saturation, contrasting colors (reds, cyans, neons)
- **Calm**: Earth tones, pastels (greens, soft blues, beiges)
- **Focused**: Monochromatic or limited palette (single hue variations)

### Mood Contagion
- Agents in proximity can influence each other's moods
- Contagion strength based on agent relationship and trust
- Group mood averaging for ensemble coherence
- Dampening factors to prevent mood instability

### Performance Reactivity
- **Beat Energy**: High beat energy → Energetic or Chaotic mood
- **Tempo**: Fast tempo → Energetic, Slow tempo → Calm or Sad
- **Audience Response**: Positive response → Happy, Negative → Serious
- **Time in Performance**: Early → Playful, Late → Serious or Focused

## Verification Checkpoints

### 1. Unit Tests (≥80% coverage)
- [ ] `tests/agents/test_mood.py`: Mood state management, transitions, intensity
- [ ] `tests/agents/test_mood_parameters.py`: Mood-modulated parameter calculation
- [ ] `tests/agents/test_mood_reactivity.py`: Audio and visual event reactions
- [ ] `tests/agents/test_mood_contagion.py`: Multi-agent mood influence
- [ ] `tests/agents/test_mood_persistence.py`: Mood history and learning

### 2. Integration Tests
- [ ] AgentMood + AgentManager: Mood influences agent behavior
- [ ] AgentMood + AwesomeCollaborativeCreationSystem: Group mood dynamics
- [ ] AgentMood + EventBus: Mood events trigger visual responses
- [ ] AgentMood + ConfigManager: Configuration loading and persistence

### 3. Performance Tests
- [ ] Mood update overhead: <1% CPU per agent per frame
- [ ] Transition smoothness: No jarring jumps in parameters
- [ ] Memory usage: <10 MB for mood system + 5 agents
- [ ] Scalability: 10+ agents with independent moods

### 4. Manual QA
- [ ] Manually trigger mood changes, verify smooth transitions
- [ ] Test mood reactivity to audio (beat, energy, tempo)
- [ ] Verify mood influences agent visual output (colors, parameters)
- [ ] Test multi-agent mood contagion and group dynamics
- [ ] Verify mood persistence across application restarts

## Resources

### Legacy References
- `vjlive/agents/awesome_collaborative_creation.py` — AgentMood and mood system
- `vjlive/agents/agent_persona.py` — Personality integration with mood
- `vjlive/agents/agent_bridge.py` — Performance bridge mood influences
- `vjlive/rhythm_consciousness.py` — Rhythm profile and mood connections

### Existing VJLive3 Code
- `src/vjlive3/core/ai_integration.py` — AI subsystem coordination
- `src/vjlive3/core/event_bus.py` — Event bus for mood events
- `src/vjlive3/audio/engine.py` — Audio features for mood reactivity
- `src/vjlive3/render/engine.py` — Render loop integration

### External Documentation
- Emotion modeling in AI: "Emotion Recognition and Synthesis in Human-Computer Interaction"
- Multi-agent emotional dynamics: "Modelling Emotion in Multi-Agent Systems"
- Color psychology: "Color Psychology and Color Therapy"

## Success Criteria

### Functional Completeness
- [ ] AgentMood can define and manage at least 8 distinct mood states
- [ ] Mood transitions are smooth (interpolated over time)
- [ ] Mood influences at least 5 agent behavior parameters
- [ ] Mood reactivity to audio features works in real-time
- [ ] Multi-agent mood contagion produces coherent group dynamics

### Performance
- [ ] Mood update overhead: <1% CPU per agent per frame
- [ ] Memory usage: <10 MB for mood system + 5 agents
- [ ] Transition smoothness: No visible parameter jumps
- [ ] Scalability: 10+ agents with independent moods

### Reliability
- [ ] System handles rapid mood changes without instability
- [ ] No crashes during 24-hour continuous operation
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Integration
- [ ] AgentMood integrates with AgentManager for agent lifecycle
- [ ] Mood events trigger visual responses via event bus
- [ ] Configuration persists across application restarts
- [ ] Works with AwesomeCollaborativeCreationSystem for multi-agent coordination

## Dependencies (Blocking)
- P4-COR025: AgentManager (for agent lifecycle coordination)
- P4-COR030: AgentPersona (for personality-specific mood baselines)
- P4-COR009: AIIntegration (for AI subsystem coordination)
- ConfigManager: For loading `MoodConfig`
- EventBus: For publishing mood events
- AudioEngine: For audio feature reactivity

## Notes for Implementation Engineer (Beta)

This is a **behavioral influence** component. It must be:
- **Lightweight**: Minimal CPU overhead, called every frame for each agent
- **Smooth**: All parameter changes must be interpolated, no jumps
- **Configurable**: All mood definitions and transitions in config files
- **Well-tested**: 80% coverage mandatory, include transition edge cases

Start by:
1. Reading `vjlive/agents/awesome_collaborative_creation.py` to understand legacy mood system
2. Defining `MoodConfig` Pydantic model with mood states and transition rules
3. Implementing `MoodState` class with smooth interpolation
4. Building mood parameter modulation system
5. Adding audio and visual event reactivity
6. Implementing mood contagion for multi-agent coordination
7. Writing tests alongside implementation (TDD style)

The spec is **auto-approved**. Proceed to implementation following the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
