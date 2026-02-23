# INBOX: Implementation Engineer Assignment

**Agent:** Beta (Implementation Engineer)
**Task ID:** P4-COR075
**Task Name:** LLM Service (LLMService)
**Priority:** P0
**Phase:** Core Logic Parity (P0-INF4)
**Source:** Legacy
**Assigned By:** Manager-Gemini-3.1
**Date:** 2026-02-22

---

## Mission

Implement the `LLMService` — the core service for integrating Large Language Models into VJLive3. This service provides intelligent crowd analysis, visual response generation, and AI-powered suggestions for live visual performance. It must handle multiple LLM providers securely, manage costs, and provide real-time insights for autonomous agents.

## Specification

**Full Spec:** [`docs/specs/P4-COR075_LLMService.md`](docs/specs/P4-COR075_LLMService.md:0)

### Key Requirements

1. **Multi-Provider LLM Integration**
   - Support OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), local models (Llama, Mistral)
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

### Code Files
```
src/vjlive3/llm/
├── __init__.py
├── service.py              # LLMService class (main implementation)
├── config.py               # LLMConfig Pydantic model
├── providers/
│   ├── __init__.py
│   ├── base.py             # LLMProvider abstract base class
│   ├── openai.py           # OpenAI provider implementation
│   ├── anthropic.py        # Anthropic provider implementation
│   ├── local.py            # Local model provider implementation
│   └── __init__.py
├── crowd_analysis.py       # Crowd analysis pipeline
├── suggestions.py          # Visual response generation
├── rate_limiting.py        # Rate limiting and caching
├── security.py             # API key handling, input sanitization
├── utils.py                # Helper functions, prompt engineering
└── __init__.py

tests/llm/
├── __init__.py
├── test_service.py         # LLMService lifecycle, provider management
├── test_providers.py       # Provider implementations (OpenAI, Anthropic, Local)
├── test_crowd_analysis.py  # Crowd analysis accuracy and performance
├── test_suggestions.py     # Suggestion generation and validation
├── test_rate_limiting.py   # Rate limiting, caching, cost tracking
├── test_security.py        # API key handling, input sanitization, output filtering
└── test_integration.py     # LLMService + CrowdAnalysisAggregator integration
```

### Documentation
- Inline comments explaining provider abstraction and security measures
- Configuration examples in docstring
- Rate limiting and caching strategy documentation
- Security best practices and audit logging
- Cost tracking and optimization guidelines

### Verification
- [ ] Unit tests: ≥80% coverage across all modules
- [ ] Integration tests: LLMService + CrowdAnalysisAggregator + AISuggestionEngine
- [ ] Performance tests: Crowd analysis <2s, suggestion generation <3s
- [ ] Security tests: API key handling, input sanitization, output filtering
- [ ] Manual QA: Provider testing, crowd analysis, suggestion generation

## Workflow Protocol

**FOLLOW EXACTLY:** `SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD`

1. **Read the spec** thoroughly before starting
2. **Study legacy** implementation in `llm_service.py` and related modules
3. **Implement** with clean architecture patterns, singleton pattern
4. **Write tests** alongside implementation (mock providers, use test data)
5. **Verify all checkpoints:**
   - Run `pytest -v`
   - Check provider hot-swapping and rate limiting
   - Verify security measures (API key handling, input sanitization)
   - Ensure no blocking operations
   - Release locks in LOCKS.md
6. **Update BOARD.md** with `[x]` only after ALL verification passes
7. **Post completion** in `WORKSPACE/COMMS/AGENT_SYNC.md`

## Safety Rails Reminder

- **Rail 1:** No blocking calls in main thread — use async for all LLM API calls
- **Rail 3:** Proper provider registration and lifecycle management
- **Rail 4:** ≤750 lines per file (split service, providers, analysis, suggestions)
- **Rail 5:** ≥80% test coverage (include provider failure simulations)
- **Rail 7:** No silent failures — log all LLM errors and fallbacks
- **Rail 8:** Clean resource management (API connections, cache cleanup)
- **Rail 10:** Secure handling of API keys and credentials

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

## Next Steps

1. **Read the spec**: `docs/specs/P4-COR075_LLMService.md`
2. **Set up development environment**: Create project structure, add LLM dependencies
3. **Study legacy**: Review `llm_service.py` and related modules
4. **Implement configuration**: Define `LLMConfig` Pydantic model with provider settings
5. **Build provider abstraction**: OpenAI, Anthropic, Local provider implementations
6. **Implement crowd analysis**: Pipeline with prompt engineering and validation
7. **Add suggestion generation**: Context-aware visual recommendations
8. **Implement rate limiting**: Caching, cost tracking, quota management
9. **Add security measures**: API key handling, input sanitization, output filtering
10. **Write tests**: Unit tests alongside implementation (TDD style)

**Remember:** This is a **critical AI service** component. It must be secure, reliable, and cost-aware. Follow the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
