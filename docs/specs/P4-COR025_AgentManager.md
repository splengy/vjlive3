# P4-COR025: AgentManager — Agent Lifecycle & Coordination System

## Mission Context
The `AgentManager` is the central coordinator for all autonomous agents in VJLive3. It manages the initialization, configuration, and lifecycle of the Agent Performance System, including agent personas, collaboration orchestration, and performance bridges. This is core infrastructure that enables AI-driven visual performance automation.

## Technical Requirements

### Core Responsibilities
1. **Agent Lifecycle Management**
   - Initialize, start, stop, and cleanup agents
   - Agent registration and discovery
   - Configuration loading and validation
   - Resource allocation and cleanup

2. **Agent Coordination**
   - Multi-agent orchestration and communication
   - Conflict resolution and priority management
   - State synchronization across agents
   - Performance mode switching (ADVISE, COLLABORATE, AUTONOMOUS)

3. **Persona Management**
   - Hot-swappable agent personalities
   - Personality database integration
   - Memory and learning persistence
   - Personality trait configuration

4. **Performance Integration**
   - Bridge between agents and VJLive performance system
   - Manifold navigation and music reactivity
   - User interaction handling
   - Suggestion queuing and execution

5. **Health Monitoring**
   - Agent status tracking (active, idle, error)
   - Performance metrics and logging
   - Error detection and recovery
   - Resource usage monitoring

### Architecture Constraints
- **Singleton Pattern**: One global `AgentManager` instance coordinated via `AIIntegration`
- **Async Operations**: Agent processing must be non-blocking
- **Thread Safety**: Lock-free or fine-grained locking for real-time performance
- **Error Resilience**: Agent failures must not crash the system; graceful degradation
- **Configuration-Driven**: All agent parameters loaded from ConfigManager

### Key Interfaces
```python
class AgentManager:
    def __init__(self, config: AgentConfig, event_bus: Optional[EventBus] = None):
        """Initialize agent manager with configuration."""
        pass

    def initialize(self) -> None:
        """Load agent personas, initialize all agents, start coordination."""
        pass

    def start(self) -> None:
        """Begin agent processing and coordination."""
        pass

    def stop(self) -> None:
        """Pause all agent activity."""
        pass

    def cleanup(self) -> None:
        """Shutdown all agents, release resources."""
        pass

    def register_agent(self, agent: IAgent) -> None:
        """Register a new agent with the manager."""
        pass

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the manager."""
        pass

    def get_agent(self, agent_id: str) -> Optional[IAgent]:
        """Retrieve a registered agent."""
        pass

    def list_agents(self) -> List[AgentInfo]:
        """List all registered agents and their status."""
        pass

    def set_mode(self, mode: AgentInteractionMode) -> None:
        """Set the agent interaction mode (ADVISE, COLLABORATE, AUTONOMOUS)."""
        pass

    def get_suggestion(self, context: AgentContext) -> Optional[AgentSuggestion]:
        """Get a suggestion from the active agent(s)."""
        pass

    def execute_suggestion(self, suggestion: AgentSuggestion) -> None:
        """Execute a queued agent suggestion."""
        pass

    def get_performance_bridge(self) -> AgentPerformanceBridge:
        """Get the bridge to the VJLive performance system."""
        pass

    def get_status(self) -> AgentManagerStatus:
        """Return health status and agent statistics."""
        pass
```

### Dependencies
- **ConfigManager**: Load `AgentConfig` (personas, modes, performance settings)
- **EventBus**: Publish `AgentRegistered`, `SuggestionQueued`, `ModeChanged` events
- **HealthMonitor**: Report agent manager health and agent statuses
- **AIIntegration**: Coordinate with other AI subsystems
- **IAgent Interface**: Standard interface for all agents
- **AgentPersona**: Personality definitions and traits
- **AgentPerformanceBridge**: Bridge to performance system
- **AgentOrchestrator**: LangGraph orchestration for complex agent workflows

## Implementation Notes

### Agent Types
- **PerformanceAgent**: High-level agent managing LUMEN script execution
- **GhostAgent**: Autonomous VJ operation system for generative performances
- **StrobeAgent**: Simplified agent for beat-synced strobe effects
- **WorkerAgent**: Distributed agent running on Orange Pi nodes
- **DreamerAgent**: Autonomous agent exploring the Mood Manifold
- **CompositeAgent**: Combines suggestions from multiple specialized agents

### Persona System
- **Personality Traits**: Creativity, precision, energy, etc.
- **Memory Database**: Persistent agent memories and learned patterns
- **Hot-Swapping**: Change agent personality without restarting
- **Banter Generation**: Contextual agent communication and collaboration

### Performance Modes
- **ADVISE**: Agents provide suggestions, human executes
- **COLLABORATE**: Agents and human work together on canvas
- **AUTONOMOUS**: Agents take full control of performance

### Coordination Patterns
- **LangGraph Orchestration**: Complex multi-agent workflows
- **Suggestion Queue**: FIFO queue for agent suggestions
- **Conflict Resolution**: Priority-based suggestion arbitration
- **State Synchronization**: Shared state across all agents

### Error Handling
- **Agent Crash**: Detect and restart failed agents
- **Resource Exhaustion**: Throttle agent processing if system overloaded
- **Configuration Errors**: Validate persona files, fallback to defaults
- **Communication Failures**: Retry logic for agent messaging

## Verification Checkpoints

### 1. Unit Tests (≥80% coverage)
- [ ] `tests/agents/test_agent_manager.py`: Lifecycle, registration, mode switching
- [ ] `tests/agents/test_personas.py`: Personality loading, hot-swapping, traits
- [ ] `tests/agents/test_coordination.py`: Multi-agent orchestration, conflict resolution
- [ ] `tests/agents/test_performance_bridge.py`: Bridge to performance system
- [ ] `tests/agents/test_error_handling.py`: Agent failures, recovery, fallback

### 2. Integration Tests
- [ ] AgentManager + AIIntegration: Unified AI subsystem coordination
- [ ] AgentManager + RenderEngine: Agent-driven visual effects
- [ ] AgentManager + EventBus: Agent events trigger visual responses
- [ ] Multi-agent collaboration: Multiple agents working together

### 3. Performance Tests
- [ ] Agent overhead: <5% CPU for 5 active agents
- [ ] Suggestion latency: <100 ms from context to suggestion
- [ ] Memory usage: <100 MB for agent manager + 5 agents
- [ ] Startup time: <2 seconds to initialize all agents

### 4. Manual QA
- [ ] Load multiple agent personas, verify personality differences
- [ ] Switch interaction modes mid-performance
- [ ] Simulate agent failure, verify recovery
- [ ] Test agent collaboration on canvas
- [ ] Verify autonomous mode generates coherent performances

## Resources

### Legacy References
- `vjlive/agents/agent_manager.py` — AgentManager (legacy implementation)
- `vjlive/agents/agent_orchestrator.py` — LangGraph orchestration
- `vjlive/agents/agent_bridge.py` — Performance bridge
- `vjlive/agents/agent_persona.py` — Personality system
- `vjlive/agents/awesome_collaborative_creation.py` — Multi-agent collaboration

### Existing VJLive3 Code
- `src/vjlive3/core/ai_integration.py` — AI subsystem coordination
- `src/vjlive3/core/event_bus.py` — Event bus for agent events
- `src/vjlive3/plugins/astra.py` — Threaded capture pattern
- `src/vjlive3/render/engine.py` — Render loop integration example

### External Documentation
- LangGraph documentation: https://langchain-ai.github.io/langgraph/
- Autonomous agent patterns: "ReAct: Synergizing Reasoning and Acting in LLMs"
- Multi-agent systems: "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation"

## Success Criteria

### Functional Completeness
- [ ] AgentManager can initialize and manage at least 5 different agent types
- [ ] Agent personas load correctly with distinct personalities
- [ ] Performance modes (ADVISE, COLLABORATE, AUTONOMOUS) work as expected
- [ ] Agent suggestions are relevant and timely (<100 ms latency)
- [ ] Multi-agent collaboration produces coherent results

### Performance
- [ ] CPU usage: <5% for 5 active agents during performance
- [ ] Memory usage: <100 MB for agent manager + 5 agents
- [ ] Startup time: <2 seconds to initialize all agents
- [ ] Suggestion latency: <100 ms from context to suggestion

### Reliability
- [ ] System recovers gracefully from agent crashes
- [ ] No crashes during 24-hour continuous operation
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Integration
- [ ] AgentManager integrates with AIIntegration for unified AI coordination
- [ ] Agent events trigger visual responses via event bus
- [ ] Configuration persists across application restarts
- [ ] Works in headless mode (no display) for server deployments

## Dependencies (Blocking)
- P4-COR009: AIIntegration (for AI subsystem coordination)
- P4-COR068: IAgent interface (standard agent interface)
- P4-COR030: AgentPersona (personality system)
- P4-COR027: AgentOrchestrator (LangGraph orchestration)
- P4-COR024: AgentPerformanceBridge (performance system bridge)
- ConfigManager: For loading `AgentConfig`
- EventBus: For publishing agent events

## Notes for Implementation Engineer (Alpha)

This is a **core coordination** component. It must be:
- **Robust**: Agent failures must not crash the system
- **Well-tested**: 80% coverage mandatory, include failure simulations
- **Performant**: Minimal overhead for multiple concurrent agents
- **Documented**: Every public method has docstring with parameter/return types

Start by:
1. Reading `vjlive/agents/agent_manager.py` to understand legacy design
2. Defining `AgentConfig` Pydantic model (if not already defined)
3. Implementing `IAgent` interface and base agent class
4. Building agent registration and lifecycle management
5. Adding persona system with hot-swapping
6. Implementing performance bridge and suggestion queue
7. Writing tests alongside implementation (TDD style)

The spec is **auto-approved**. Proceed to implementation following the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.
