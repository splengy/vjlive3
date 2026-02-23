# P4-COR017: AISuggestionEngine — Intelligent Visual Suggestion System

## Mission Context
The `AISuggestionEngine` is the AI-powered system that provides intelligent suggestions for timeline creation, effect selection, and parameter optimization in VJLive3. It analyzes the current performance context, learns from past decisions, and generates context-aware recommendations to enhance live visual performances. This is a core AI component that bridges LLM analysis with practical effect control.

## Technical Requirements

### Core Responsibilities
1. **Suggestion Generation**
   - Analyze performance context (mood, BPM, audience response, recent effects)
   - Generate effect suggestions with specific parameters and timing
   - Provide multiple ranked options for creative choice
   - Consider technical constraints (available effects, GPU load, DMX state)

2. **Timeline Optimization**
   - Suggest effect transitions and keyframe placements
   - Recommend parameter automation curves
   - Predict optimal timing for effect changes based on musical structure
   - Avoid repetitive or predictable patterns

3. **Learning and Adaptation**
   - Learn from user acceptance/rejection of suggestions
   - Adapt suggestion strategies based on performance history
   - Personalize suggestions to user's creative style
   - Track suggestion effectiveness (audience response, visual impact)

4. **Context Awareness**
   - Understand current mood and emotional intent
   - Recognize musical phrases and structural elements
   - Consider recent effects to avoid redundancy
   - Factor in technical state (available resources, hardware capabilities)

5. **Performance Optimization**
   - Generate suggestions in real-time (<2 seconds latency)
   - Cache and reuse suggestions for similar contexts
   - Batch process multiple suggestion requests
   - Rate limit to avoid overwhelming the user

### Architecture Constraints
- **Singleton Pattern**: One global `AISuggestionEngine` instance coordinated via `AIIntegration`
- **Low Latency**: Suggestions must be generated in <2 seconds
- **Context-Aware**: Must consume multiple data sources (audio, mood, performance state)
- **Learning System**: Must persist and update user preference models
- **Non-Blocking**: All suggestion generation must be async

### Key Interfaces
```python
class AISuggestionEngine:
    def __init__(self, config: SuggestionConfig, event_bus: Optional[EventBus] = None):
        """Initialize suggestion engine with configuration."""
        pass

    def initialize(self) -> None:
        """Load suggestion models, initialize learning system."""
        pass

    def start(self) -> None:
        """Begin accepting suggestion requests."""
        pass

    def stop(self) -> None:
        """Pause suggestion generation."""
        pass

    def cleanup(self) -> None:
        """Save learning models, cleanup resources."""
        pass

    def generate_suggestions(self, context: SuggestionContext, num_suggestions: int = 3) -> List[Suggestion]:
        """Generate a list of ranked suggestions for the given context."""
        pass

    def get_suggestion_for_transition(self, current_effect: str, target_mood: MoodState) -> Optional[Suggestion]:
        """Get a suggestion for transitioning from current to target mood."""
        pass

    def recommend_parameters(self, effect_type: str, context: SuggestionContext) -> Dict[str, float]:
        """Recommend specific parameter values for an effect."""
        pass

    def suggest_timeline_keyframes(self, audio_features: AudioFeatures, duration: float) -> List[KeyframeSuggestion]:
        """Suggest keyframe placements for parameter automation."""
        pass

    def learn_from_feedback(self, suggestion_id: str, accepted: bool, user_adjustments: Optional[Dict[str, Any]] = None) -> None:
        """Learn from user's acceptance/rejection of a suggestion."""
        pass

    def get_learning_stats(self) -> LearningStats:
        """Get statistics about the learning system."""
        pass

    def reset_learning_model(self) -> None:
        """Reset learned preferences to defaults."""
        pass

    def get_status(self) -> AISuggestionEngineStatus:
        """Return engine status and statistics."""
        pass
```

### Dependencies
- **ConfigManager**: Load `SuggestionConfig` (suggestion strategies, learning parameters)
- **EventBus**: Publish `SuggestionGenerated`, `SuggestionAccepted`, `SuggestionRejected` events
- **HealthMonitor**: Report suggestion engine health and performance
- **LLMService**: Generate creative suggestions using language models
- **AudioEngine**: Audio features for musical structure analysis
- **AgentMood**: Current mood state for mood-aware suggestions
- **PluginRegistry**: Available effects and their capabilities
- **PerformanceBridge**: Current performance state and history

## Implementation Notes

### Suggestion Context
```python
class SuggestionContext:
    """Complete context for suggestion generation."""

    timestamp: float
    performance_context: PerformanceContext
    current_effect: Optional[str]
    current_parameters: Dict[str, float]
    recent_effects: List[str]  # last 5-10 effects used
    recent_parameters: List[Dict[str, float]]
    audio_features: AudioFeatures
    mood: MoodState
    audience_response: Optional[AudienceResponse]
    user_preferences: UserPreferences
    technical_constraints: TechnicalConstraints
```

### Suggestion Structure
```python
class Suggestion:
    """A single AI-generated suggestion."""

    suggestion_id: str
    suggestion_type: SuggestionType  # EFFECT, PARAMETER, TRANSITION, TIMELINE
    effect_type: Optional[str]
    parameters: Dict[str, float]
    confidence: float  # 0.0-1.0
    reasoning: str  # natural language explanation
    expected_impact: float  # 0.0-1.0
    timestamp: float
    context_hash: str  # for deduplication
    learning_weight: float  # weight for learning updates
```

### Suggestion Types
- **EFFECT_SUGGESTION**: Recommend a new effect to add
- **PARAMETER_SUGGESTION**: Recommend parameter values for current effect
- **TRANSITION_SUGGESTION**: Suggest transition to new effect with timing
- **TIMELINE_SUGGESTION**: Recommend keyframe placements for automation

### Learning System
```python
class LearningModel:
    """Learns user preferences from feedback."""

    def __init__(self):
        self.acceptance_history: List[SuggestionFeedback] = []
        self.parameter_preferences: Dict[str, ParameterPreference] = {}
        self.effect_preferences: Dict[str, float] = {}  # effect → preference score
        self.context_patterns: List[ContextPattern] = []

    def update(self, feedback: SuggestionFeedback) -> None:
        """Update model with new feedback."""
        self.acceptance_history.append(feedback)
        self._update_parameter_preferences(feedback)
        self._update_effect_preferences(feedback)
        self._extract_context_pattern(feedback)

    def get_preference_score(self, effect_type: str, context: SuggestionContext) -> float:
        """Get learned preference score for effect in given context."""
        base_score = self.effect_preferences.get(effect_type, 0.5)
        context_match = self._match_context_pattern(context)
        return base_score * context_match

    def _update_parameter_preferences(self, feedback: SuggestionFeedback) -> None:
        """Learn preferred parameter ranges for effects."""
        if feedback.accepted:
            effect = feedback.suggestion.effect_type
            for param, value in feedback.suggestion.parameters.items():
                key = f"{effect}.{param}"
                if key not in self.parameter_preferences:
                    self.parameter_preferences[key] = ParameterPreference()
                self.parameter_preferences[key].add_value(value, feedback.user_adjustments)
```

### Suggestion Strategies
- **LLM-Based**: Use LLM to generate creative suggestions based on natural language context
- **Rule-Based**: Use hand-crafted rules for common patterns (e.g., build-up → heavy effect)
- **Collaborative Filtering**: Suggest effects liked by similar users
- **Reinforcement Learning**: Learn optimal suggestion policies from feedback
- **Hybrid**: Combine multiple strategies with weighted scoring

### Musical Structure Analysis
- **Beat Detection**: Identify beats and downbeats for timing
- **Phrase Detection**: Detect musical phrases (4/8/16 bar patterns)
- **Energy Analysis**: Track energy changes for build/release patterns
- **Tempo Tracking**: Monitor BPM changes for tempo-aware suggestions
- **Genre Classification**: Suggest effects appropriate for genre

## Verification Checkpoints

### 1. Unit Tests (≥80% coverage)
- [ ] `tests/suggestions/test_engine.py`: Suggestion generation, ranking, filtering
- [ ] `tests/suggestions/test_learning.py`: Learning model updates, preference tracking
- [ ] `tests/suggestions/test_strategies.py`: Different suggestion strategies
- [ ] `tests/suggestions/test_musical_analysis.py`: Musical structure detection
- [ ] `tests/suggestions/test_context.py`: Context parsing and feature extraction
- [ ] `tests/suggestions/test_feedback.py`: Feedback processing and model updates

### 2. Integration Tests
- [ ] AISuggestionEngine + LLMService: LLM-powered suggestions
- [ ] AISuggestionEngine + AudioEngine: Audio features drive suggestions
- [ ] AISuggestionEngine + AgentManager: Agents consume suggestions
- [ ] AISuggestionEngine + EventBus: Suggestion events trigger UI updates
- [ ] Learning system: Feedback improves future suggestions

### 3. Performance Tests
- [ ] Suggestion generation latency: <2 seconds for 3 suggestions
- [ ] Learning update latency: <100 ms per feedback
- [ ] Memory usage: <100 MB for engine + learning models
- [ ] Cache hit rate: >60% for similar contexts
- [ ] Concurrent requests: Handle 5 simultaneous suggestion requests

### 4. Manual QA
- [ ] Test suggestion generation in various performance contexts
- [ ] Verify learning improves suggestions over time
- [ ] Test musical phrase detection and timing suggestions
- [ ] Verify suggestion relevance and creativity
- [ ] Test feedback loop (accept/reject) updates learning model

## Resources

### Legacy References
- `vjlive/ai_suggestion_engine.py` — AISuggestionEngine (legacy implementation)
- `vjlive/ai_assistant.py` — AI assistant with suggestion capabilities
- `vjlive/co_creation_enhanced.py` — Creative assistant suggestions
- `vjlive/automation_timeline.py` — Timeline automation and keyframing

### Existing VJLive3 Code
- `src/vjlive3/core/ai_integration.py` — AI subsystem coordination
- `src/vjlive3/core/event_bus.py` — Event bus for suggestion events
- `src/vjlive3/audio/engine.py` — Audio features for musical analysis
- `src/vjlive3/agents/agent_manager.py` — Agent integration

### External Documentation
- Recommendation systems: "Collaborative Filtering: A User-Study"
- Reinforcement learning: "Reinforcement Learning: An Introduction"
- Musical structure analysis: "Automatic Music Structure Analysis"
- LLM prompt engineering: "Prompt Engineering for Generative AI"

## Success Criteria

### Functional Completeness
- [ ] AISuggestionEngine generates at least 3 ranked suggestions in <2 seconds
- [ ] Suggestions are relevant and creative (user rating >3/5)
- [ ] Learning system improves suggestion quality over time (20% improvement)
- [ ] Musical phrase detection accuracy >80%
- [ ] Integration with LLMService produces natural language reasoning

### Performance
- [ ] Suggestion generation latency: <2 seconds
- [ ] Learning update latency: <100 ms per feedback
- [ ] Memory usage: <100 MB for engine + learning models
- [ ] Cache hit rate: >60% for similar contexts

### Reliability
- [ ] Engine recovers from LLM provider failures gracefully
- [ ] No crashes during 24-hour continuous operation
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Integration
- [ ] AISuggestionEngine integrates with AIIntegration for unified AI coordination
- [ ] Suggestions consumed by AgentManager for autonomous decisions
- [ ] Suggestion events trigger UI updates via EventBus
- [ ] Configuration persists across application restarts
- [ ] Learning model persists and continues improving across sessions

## Dependencies (Blocking)
- P4-COR009: AIIntegration (for AI subsystem coordination)
- P4-COR075: LLMService (for LLM-powered suggestions)
- P1-A1: FFT + waveform analysis engine (for musical structure)
- P1-A2: Beat detection (for beat-synced suggestions)
- AgentMood: For mood-aware suggestions
- ConfigManager: For loading `SuggestionConfig`
- EventBus: For publishing suggestion events
- PluginRegistry: For available effects discovery

## Notes for Implementation Engineer (Alpha)

This is a **creative AI** component. It must be:
- **Creative**: Suggestions should be interesting and inspiring, not generic
- **Responsive**: <2 second latency is critical for live performance
- **Adaptive**: Learning system should improve suggestions based on feedback
- **Well-Tested**: 80% coverage mandatory, include learning system tests

Start by:
1. Reading `vjlive/ai_suggestion_engine.py` to understand legacy design
2. Defining `SuggestionConfig` Pydantic model with strategy weights
3. Implementing context parsing and feature extraction
4. Building multiple suggestion strategies (LLM-based, rule-based, collaborative)
5. Adding learning system with feedback processing
6. Implementing musical structure analysis for timing
7. Writing tests alongside implementation (TDD style)

The spec is **auto-approved**. Proceed to implementation following the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
