# P4-COR075: LLMService — Intelligent Language Model Integration

## Mission Context
The `LLMService` is the core service for integrating Large Language Models into VJLive3. It provides intelligent crowd analysis, visual response generation, and AI-powered suggestions for live visual performance. This service handles multiple LLM providers (OpenAI, Anthropic, local models), manages API keys securely, and provides rate limiting and caching for optimal performance.

## Technical Requirements

### Core Responsibilities
1. **Multi-Provider LLM Integration**
   - Support multiple LLM providers: OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), local models (Llama, Mistral)
   - Provider abstraction layer with unified interface
   - Hot-swapping between providers without service interruption
   - Provider-specific optimizations and feature detection

2. **Crowd Analysis**
   - Analyze audience energy and emotional state from crowd data
   - Generate crowd emotion profiles (happy, engaged, bored, energetic)
   - Predict audience response to visual changes
   - Provide real-time crowd insights to agents

3. **Visual Response Generation**
   - Generate effect suggestions based on crowd analysis
   - Create parameter recommendations for transitions
   - Produce natural language descriptions of visual intent
   - Suggest color palettes and mood-appropriate effects

4. **Performance Optimization**
   - Rate limiting per provider to manage costs
   - Response caching to reduce redundant API calls
   - Async operations to avoid blocking main thread
   - Batch processing for multiple analysis requests
   - Token usage tracking and optimization

5. **Security and Reliability**
   - Secure API key storage and rotation
   - Input sanitization to prevent prompt injection
   - Output validation and filtering
   - Graceful degradation when providers are unavailable
   - Comprehensive error handling and retry logic

### Architecture Constraints
- **Singleton Pattern**: One global `LLMService` instance coordinated via `AIIntegration`
- **Async Operations**: All LLM API calls must be non-blocking
- **Thread Safety**: Concurrent requests from multiple agents must be safe
- **Provider Abstraction**: Clean separation between provider implementations
- **Rate Limiting**: Per-provider quotas with backoff and retry
- **Cost Awareness**: Token counting and usage tracking

### Key Interfaces
```python
class LLMService:
    def __init__(self, config: LLMConfig, event_bus: Optional[EventBus] = None):
        """Initialize LLM service with configuration."""
        pass

    def initialize(self) -> None:
        """Load providers, validate API keys, start service."""
        pass

    def start(self) -> None:
        """Begin accepting requests."""
        pass

    def stop(self) -> None:
        """Pause service."""
        pass

    def cleanup(self) -> None:
        """Close connections, cleanup resources."""
        pass

    def analyze_crowd(self, crowd_data: CrowdData) -> CrowdAnalysis:
        """Analyze crowd energy and emotional state."""
        pass

    def generate_suggestion(self, context: PerformanceContext, intent: str) -> Suggestion:
        """Generate visual effect suggestion based on intent."""
        pass

    def describe_visual(self, frame: np.ndarray) -> str:
        """Generate natural language description of visual content."""
        pass

    def recommend_parameters(self, effect_type: str, mood: MoodState) -> Dict[str, float]:
        """Recommend effect parameters based on mood and context."""
        pass

    def get_available_providers(self) -> List[ProviderInfo]:
        """List all configured and available providers."""
        pass

    def set_default_provider(self, provider_id: str) -> None:
        """Set the default LLM provider."""
        pass

    def get_usage_stats(self) -> UsageStats:
        """Get token usage and cost statistics."""
        pass

    def get_status(self) -> LLMServiceStatus:
        """Return service health and provider status."""
        pass
```

### Dependencies
- **ConfigManager**: Load `LLMConfig` (provider settings, API keys, rate limits)
- **EventBus**: Publish `CrowdAnalyzed`, `SuggestionGenerated`, `ProviderStatusChanged` events
- **HealthMonitor**: Report LLM service health and provider availability
- **AIIntegration**: Coordinate with other AI subsystems
- **CrowdAnalysisAggregator**: Consumer of crowd analysis results
- **AISuggestionEngine**: Consumer of visual suggestions
- **AgentManager**: Provider for agent decision-making

## Implementation Notes

### Provider Abstraction
```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate text completion."""
        pass

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate text embedding."""
        pass

    @abstractmethod
    def get_usage(self) -> UsageStats:
        """Get token usage statistics."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass

class OpenAIProvider(LLMProvider):
    # OpenAI-specific implementation
    pass

class AnthropicProvider(LLMProvider):
    # Anthropic-specific implementation
    pass

class LocalProvider(LLMProvider):
    # Local model implementation (llama.cpp, etc.)
    pass
```

### Crowd Analysis Pipeline
1. **Input**: Crowd energy metrics, audience count, motion data
2. **Prompt Engineering**: Construct prompt with crowd data and performance context
3. **LLM Inference**: Send to provider with appropriate temperature and max_tokens
4. **Parsing**: Extract structured crowd emotion and energy level
5. **Validation**: Ensure results are within expected ranges
6. **Caching**: Store analysis for similar crowd states

### Visual Response Generation
1. **Context Gathering**: Current mood, recent effects, audience response
2. **Intent Parsing**: Understand user's creative intent from natural language
3. **Suggestion Generation**: Generate specific effect and parameter recommendations
4. **Validation**: Ensure suggestions are safe and within bounds
5. **Ranking**: Multiple suggestions ranked by relevance and creativity

### Rate Limiting and Caching
- **Per-Provider Quotas**: Different limits for different providers
- **Token Bucket**: Smooth rate limiting with burst capacity
- **Response Cache**: Cache keyed by prompt hash and parameters
- **Cache Invalidation**: Time-based and context-based invalidation
- **Cost Tracking**: Token counting and cost estimation per provider

### Security Measures
- **API Key Storage**: Encrypted storage, rotation support
- **Input Sanitization**: Escape special characters, limit prompt length
- **Output Filtering**: Remove sensitive information, validate structure
- **Audit Logging**: All API calls logged with timestamps and costs
- **Access Control**: Role-based access to LLM configuration

## Verification Checkpoints

### 1. Unit Tests (≥80% coverage)
- [ ] `tests/llm/test_service.py`: LLMService lifecycle, provider management
- [ ] `tests/llm/test_providers.py`: Provider implementations (OpenAI, Anthropic, Local)
- [ ] `tests/llm/test_crowd_analysis.py`: Crowd analysis accuracy and performance
- [ ] `tests/llm/test_suggestions.py`: Suggestion generation and validation
- [ ] `tests/llm/test_rate_limiting.py`: Rate limiting, caching, cost tracking
- [ ] `tests/llm/test_security.py`: API key handling, input sanitization, output filtering

### 2. Integration Tests
- [ ] LLMService + CrowdAnalysisAggregator: Crowd data flows to analysis
- [ ] LLMService + AISuggestionEngine: Suggestions drive visual effects
- [ ] LLMService + AgentManager: Agents use LLM for decision-making
- [ ] LLMService + EventBus: LLM events trigger system responses

### 3. Performance Tests
- [ ] Crowd analysis latency: <2 seconds for real-time analysis
- [ ] Suggestion generation: <3 seconds for complex intents
- [ ] Cache hit rate: >70% for repeated similar requests
- [ ] Rate limiting: No quota exceeded under load
- [ ] Memory usage: <200 MB for service + 3 providers

### 4. Manual QA
- [ ] Test all configured providers (OpenAI, Anthropic, local)
- [ ] Verify crowd analysis matches expected audience states
- [ ] Test suggestion generation for various creative intents
- [ ] Simulate provider failures, verify fallback behavior
- [ ] Monitor cost tracking and usage statistics

## Resources

### Legacy References
- `vjlive/llm_service.py` — LLMService (legacy implementation)
- `vjlive/llm_integration.py` — LLM model integration
- `vjlive/ai_assistant.py` — AI assistant using LLM
- `vjlive/co_creation_enhanced.py` — Creative assistant with LLM

### Existing VJLive3 Code
- `src/vjlive3/core/ai_integration.py` — AI subsystem coordination
- `src/vjlive3/core/event_bus.py` — Event bus for LLM events
- `src/vjlive3/agents/agent_manager.py` — Agent integration
- `src/vjlive3/audio/engine.py` — Crowd data from audio analysis

### External Documentation
- OpenAI API: https://platform.openai.com/docs/
- Anthropic Claude: https://docs.anthropic.com/
- LangChain LLM integration: https://python.langchain.com/docs/modules/model_io/
- Prompt engineering: "Prompt Engineering for Generative AI"

## Success Criteria

### Functional Completeness
- [ ] LLMService supports at least 3 different providers (OpenAI, Anthropic, Local)
- [ ] Crowd analysis accuracy >90% on test dataset
- [ ] Suggestion generation produces relevant and creative results
- [ ] Rate limiting prevents quota exceeded errors
- [ ] Response cache hit rate >70%

### Performance
- [ ] Crowd analysis latency: <2 seconds
- [ ] Suggestion generation: <3 seconds for complex intents
- [ ] Memory usage: <200 MB for service + 3 providers
- [ ] Concurrent requests: Handle 10 simultaneous requests

### Reliability
- [ ] Service recovers from provider failures automatically
- [ ] No crashes during 24-hour continuous operation
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Security
- [ ] API keys stored encrypted at rest
- [ ] Input sanitization prevents prompt injection
- [ ] Output filtering removes sensitive information
- [ ] Complete audit log of all API calls

### Integration
- [ ] LLMService integrates with AIIntegration for unified AI coordination
- [ ] Crowd analysis feeds into AgentManager for decision-making
- [ ] Suggestions integrate with AISuggestionEngine
- [ ] Configuration persists across application restarts

## Dependencies (Blocking)
- P4-COR009: AIIntegration (for AI subsystem coordination)
- P4-COR017: AISuggestionEngine (for suggestion generation)
- P4-COR049: CrowdAnalysis (for crowd analysis output)
- ConfigManager: For loading `LLMConfig` with API keys
- EventBus: For publishing LLM events
- HealthMonitor: For provider health reporting

## Notes for Implementation Engineer (Beta)

This is a **critical AI service** component. It must be:
- **Secure**: API keys are sensitive, handle with extreme care
- **Reliable**: Provider failures must not crash the system
- **Cost-Aware**: Track token usage and prevent runaway costs
- **Well-Tested**: 80% coverage mandatory, include provider failure simulations

Start by:
1. Reading `vjlive/llm_service.py` to understand legacy design
2. Defining `LLMConfig` Pydantic model with provider configurations
3. Implementing provider abstraction layer (OpenAI, Anthropic, Local)
4. Building crowd analysis pipeline with prompt engineering
5. Adding suggestion generation with context awareness
6. Implementing rate limiting, caching, and cost tracking
7. Writing tests alongside implementation (TDD style)

The spec is **auto-approved**. Proceed to implementation following the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
