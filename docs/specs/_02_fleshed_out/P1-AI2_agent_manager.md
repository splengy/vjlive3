# P1-AI2: AgentManager — Agent Lifecycle Management

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3 needs a centralized agent management system that:
- Manages the lifecycle of autonomous AI agents (creation, initialization, shutdown)
- Coordinates agent personalities and behaviors
- Handles agent communication and collaboration
- Manages agent resources (memory, compute, state)
- Integrates with the Consciousness Symphony and Hive Mind
- Provides agent status monitoring and health checks
- Supports hot-swapping of agent personalities

The legacy codebases have agent systems scattered across multiple modules.

---

## Proposed Solution

Implement `AgentManager` as a facade over individual agents with:

1. **Agent Lifecycle** — create, start, stop, pause, resume agents
2. **Personality Management** — hot-swappable personalities with memory
3. **Collaboration Coordination** — agent-to-agent communication
4. **Resource Management** — per-agent resource limits and monitoring
5. **State Integration** — broadcast agent status via ApplicationStateManager
6. **Hive Mind Integration** — collective intelligence coordination
7. **Health Monitoring** — agent health checks and auto-recovery

---

## API/Interface Definition

```python
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

class AgentStatus(Enum):
    """Agent lifecycle status."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    THINKING = "thinking"
    COLLABORATING = "collaborating"
    ERROR = "error"
    SHUTDOWN = "shutdown"

class AgentType(Enum):
    """Types of agents in VJLive."""
    CREATIVE = "creative"  # Creative partner, style transfer
    PERFORMANCE = "performance"  # Auto-director, ghost agent
    ANALYSIS = "analysis"  # Crowd analysis, anomaly detection
    SUGGESTION = "suggestion"  # AI suggestion engine
    ORCHESTRATOR = "orchestrator"  # Hive mind, symphony conductor

@dataclass
class AgentInfo:
    """Information about an agent."""
    agent_id: str
    name: str
    agent_type: AgentType
    status: AgentStatus
    personality: str
    created_at: float
    last_activity: float
    resource_usage: Dict[str, float] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None

@dataclass
class AgentConfig:
    """Configuration for an agent."""
    agent_id: str
    name: str
    agent_type: AgentType
    personality: str = "default"
    enabled: bool = True
    resource_limit: Dict[str, float] = field(default_factory=dict)
    auto_recovery: bool = True
    max_errors: int = 5

class AgentManager:
    """
    Manages AI agent lifecycles.

    Usage:
        agent_mgr = AgentManager(
            config=agent_config,
            state_mgr=app_state_mgr,
            llm_service=llm_svc
        )

        await agent_mgr.initialize()

        # Create agent
        agent = agent_mgr.create_agent(AgentConfig(...))

        # Start agent
        await agent_mgr.start_agent(agent.agent_id)

        # Get agent status
        info = agent_mgr.get_agent_info(agent.agent_id)
    """

    def __init__(
        self,
        config: Dict[str, Any],
        state_mgr: Optional['ApplicationStateManager'] = None,
        llm_service: Optional['LLMService'] = None
    ):
        """
        Initialize agent manager.

        Args:
            config: Agent configuration dict
            state_mgr: Optional ApplicationStateManager
            llm_service: Optional LLM service for agent LLM needs
        """
        self.config = config
        self.state_mgr = state_mgr
        self.llm_service = llm_service

        self._agents: Dict[str, Any] = {}
        self._agent_info: Dict[str, AgentInfo] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._lock = threading.Lock()

    async def initialize(self) -> None:
        """Initialize agent manager and all configured agents."""
        # Would load agent configs from config manager
        # For now, create default agents if configured
        await self._create_default_agents()
        self._broadcast_state()

    async def shutdown(self) -> None:
        """Shutdown all agents gracefully."""
        agent_ids = list(self._agents.keys())
        for agent_id in agent_ids:
            try:
                await self.stop_agent(agent_id)
                await self._shutdown_agent(agent_id)
            except Exception as e:
                print(f"Error shutting down agent {agent_id}: {e}")

        self._agents.clear()
        self._agent_info.clear()

    def create_agent(self, config: AgentConfig) -> str:
        """
        Create a new agent.

        Args:
            config: Agent configuration

        Returns:
            Agent ID

        Raises:
            ValueError: If agent ID already exists
        """
        with self._lock:
            if config.agent_id in self._agents:
                raise ValueError(f"Agent {config.agent_id} already exists")

            # Create agent instance based on type
            agent = self._create_agent_instance(config)
            self._agents[config.agent_id] = agent
            self._agent_configs[config.agent_id] = config

            # Create agent info
            info = AgentInfo(
                agent_id=config.agent_id,
                name=config.name,
                agent_type=config.agent_type,
                status=AgentStatus.INITIALIZING,
                personality=config.personality,
                created_at=time.time(),
                last_activity=time.time()
            )
            self._agent_info[config.agent_id] = info

            return config.agent_id

    async def start_agent(self, agent_id: str) -> bool:
        """
        Start an agent.

        Args:
            agent_id: Agent to start

        Returns:
            True if started successfully, False otherwise
        """
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        info = self._agent_info[agent_id]

        try:
            if hasattr(agent, 'start'):
                await agent.start()
            info.status = AgentStatus.RUNNING
            info.last_activity = time.time()
            self._broadcast_agent_state(agent_id)
            return True
        except Exception as e:
            info.status = AgentStatus.ERROR
            info.error_count += 1
            info.last_error = str(e)
            print(f"Failed to start agent {agent_id}: {e}")
            return False

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop an agent.

        Args:
            agent_id: Agent to stop

        Returns:
            True if stopped successfully
        """
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        info = self._agent_info[agent_id]

        try:
            if hasattr(agent, 'stop'):
                await agent.stop()
            info.status = AgentStatus.READY
            info.last_activity = time.time()
            self._broadcast_agent_state(agent_id)
            return True
        except Exception as e:
            info.status = AgentStatus.ERROR
            info.last_error = str(e)
            print(f"Failed to stop agent {agent_id}: {e}")
            return False

    async def pause_agent(self, agent_id: str) -> bool:
        """Pause an agent (temporary halt)."""
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        info = self._agent_info[agent_id]

        try:
            if hasattr(agent, 'pause'):
                await agent.pause()
            info.status = AgentStatus.PAUSED
            info.last_activity = time.time()
            self._broadcast_agent_state(agent_id)
            return True
        except Exception as e:
            print(f"Failed to pause agent {agent_id}: {e}")
            return False

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a paused agent."""
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        info = self._agent_info[agent_id]

        try:
            if hasattr(agent, 'resume'):
                await agent.resume()
            info.status = AgentStatus.RUNNING
            info.last_activity = time.time()
            self._broadcast_agent_state(agent_id)
            return True
        except Exception as e:
            print(f"Failed to resume agent {agent_id}: {e}")
            return False

    def get_agent(self, agent_id: str) -> Optional[Any]:
        """Get agent instance by ID."""
        return self._agents.get(agent_id)

    def get_agent_info(self, agent_id: str) -> Optional[AgentInfo]:
        """Get agent information."""
        info = self._agent_info.get(agent_id)
        return info.copy() if info else None

    def list_agents(self) -> List[AgentInfo]:
        """List all agents."""
        return [info.copy() for info in self._agent_info.values()]

    def get_agents_by_type(self, agent_type: AgentType) -> List[AgentInfo]:
        """Get all agents of a specific type."""
        return [
            info.copy()
            for info in self._agent_info.values()
            if info.agent_type == agent_type
        ]

    def is_agent_running(self, agent_id: str) -> bool:
        """Check if an agent is currently running."""
        info = self._agent_info.get(agent_id)
        return info is not None and info.status == AgentStatus.RUNNING

    def set_agent_personality(self, agent_id: str, personality: str) -> bool:
        """
        Hot-swap agent personality.

        Args:
            agent_id: Agent to modify
            personality: New personality name

        Returns:
            True if personality changed successfully
        """
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        info = self._agent_info[agent_id]

        try:
            if hasattr(agent, 'set_personality'):
                agent.set_personality(personality)
            info.personality = personality
            info.last_activity = time.time()
            self._broadcast_agent_state(agent_id)
            return True
        except Exception as e:
            print(f"Failed to set personality for agent {agent_id}: {e}")
            return False

    def restart_agent(self, agent_id: str) -> bool:
        """Restart an agent (stop then start)."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(self.stop_agent(agent_id))
            loop.run_until_complete(self._shutdown_agent(agent_id))
            # Recreate agent
            config = self._agent_configs[agent_id]
            agent = self._create_agent_instance(config)
            self._agents[agent_id] = agent
            loop.run_until_complete(self.start_agent(agent_id))
            return True
        except Exception as e:
            print(f"Failed to restart agent {agent_id}: {e}")
            return False
        finally:
            loop.close()

    def _create_agent_instance(self, config: AgentConfig) -> Any:
        """Create agent instance based on type."""
        if config.agent_type == AgentType.CREATIVE:
            from vjlive3.agents.creative_partner import CreativePartner
            return CreativePartner(
                agent_id=config.agent_id,
                name=config.name,
                personality=config.personality,
                llm_service=self.llm_service
            )

        elif config.agent_type == AgentType.PERFORMANCE:
            from vjlive3.agents.performance_agent import PerformanceAgent
            return PerformanceAgent(
                agent_id=config.agent_id,
                name=config.name,
                config=config.resource_limit
            )

        elif config.agent_type == AgentType.ANALYSIS:
            from vjlive3.agents.crowd_analyzer import CrowdAnalyzer
            return CrowdAnalyzer(
                agent_id=config.agent_id,
                name=config.name
            )

        elif config.agent_type == AgentType.SUGGESTION:
            from vjlive3.ai.suggestion_engine import AISuggestionEngine
            return AISuggestionEngine(
                agent_id=config.agent_id,
                config=config.resource_limit,
                llm_service=self.llm_service
            )

        elif config.agent_type == AgentType.ORCHESTRATOR:
            from vjlive3.agents.orchestrator import AgentOrchestrator
            return AgentOrchestrator(
                agent_id=config.agent_id,
                name=config.name,
                agent_manager=self
            )

        else:
            raise ValueError(f"Unknown agent type: {config.agent_type}")

    async def _shutdown_agent(self, agent_id: str) -> None:
        """Shutdown a specific agent."""
        if agent_id in self._agents:
            agent = self._agents[agent_id]
            if hasattr(agent, 'shutdown'):
                await agent.shutdown()

    def _broadcast_agent_state(self, agent_id: str) -> None:
        """Broadcast agent state change."""
        if not self.state_mgr or agent_id not in self._agent_info:
            return

        info = self._agent_info[agent_id]
        state = {
            'agent_id': info.agent_id,
            'name': info.name,
            'type': info.agent_type.value,
            'status': info.status.value,
            'personality': info.personality,
            'last_activity': info.last_activity
        }

        self.state_mgr.set(
            category=StateCategory.SYSTEM,
            key=f"agent.{agent_id}",
            value=state
        )

    def _broadcast_state(self) -> None:
        """Broadcast overall agent manager state."""
        if not self.state_mgr:
            return

        agents_state = {
            agent_id: info.status.value
            for agent_id, info in self._agent_info.items()
        }

        self.state_mgr.set(
            category=StateCategory.SYSTEM,
            key="agent_manager",
            value={
                'agent_count': len(self._agents),
                'agents': agents_state
            }
        )

    async def _create_default_agents(self) -> None:
        """Create default agents from configuration."""
        # Would load from config manager
        default_agents = [
            AgentConfig(
                agent_id="creative_partner_1",
                name="Creative Partner",
                agent_type=AgentType.CREATIVE,
                personality="helpful"
            ),
            AgentConfig(
                agent_id="performance_agent_1",
                name="Performance Assistant",
                agent_type=AgentType.PERFORMANCE,
                personality="balanced"
            )
        ]

        for config in default_agents:
            self.create_agent(config)
```

---

## Implementation Plan

### Day 1: Core Structure
- Create `src/vjlive3/agents/agent_manager.py`
- Implement `AgentManager` with lifecycle management
- Define enums and dataclasses
- Add agent creation and tracking
- Write unit tests for agent registry

### Day 2: Agent Types
- Implement agent factory for different agent types
- Create base agent interface
- Implement CreativePartner agent
- Implement PerformanceAgent agent
- Write tests for agent creation

### Day 3: Lifecycle & State
- Implement start/stop/pause/resume operations
- Add state broadcasting via ApplicationStateManager
- Implement agent info tracking
- Add error handling and recovery
- Write integration tests

### Day 4: Advanced Features
- Implement personality hot-swapping
- Add agent collaboration framework
- Implement resource monitoring
- Add agent health checks
- Write tests for personality and collaboration

### Day 5: Integration & Polish
- Integrate with AIIntegration (P1-AI1)
- Integrate with AgentOrchestrator (P1-AI3)
- Comprehensive test suite (≥80% coverage)
- Documentation and examples
- Performance optimization

---

## Test Strategy

**Unit Tests:**
- Agent creation and registration
- Lifecycle operations (start, stop, pause, resume)
- Agent info tracking
- Personality hot-swapping
- Agent listing and filtering by type
- Error handling and recovery

**Integration Tests:**
- Full agent lifecycle with state broadcasting
- Integration with ApplicationStateManager
- Agent collaboration scenarios
- Resource limit enforcement
- Health check monitoring

**Performance Tests:**
- Agent startup time (<1s per agent)
- Memory usage per agent (<100MB typical)
- State broadcast latency (<10ms)

---

## Performance Requirements

- **Agent Startup:** <1 second per agent
- **Memory:** <100MB per agent (typical)
- **State Broadcast:** <10ms latency
- **Health Check:** <50ms per agent

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** Agent errors logged and broadcast
- **Rail 8 (Resource Leak Prevention):** Agents properly shutdown; resources released
- **Rail 10 (Security):** Agent operations sandboxed; no arbitrary code execution

---

## Dependencies

- **P1-C1:** ApplicationStateManager — for state broadcasting
- **P1-AI1:** AIIntegration — will manage this subsystem
- **P1-AI3:** AgentOrchestrator — for advanced coordination
- **Blocking:** P1-AI1 (AIIntegration) for overall management
- **Blocked By:** None (can be implemented independently)

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md`
- `WORKSPACE/SAFETY_RAILS.md`
- Legacy: `vjlive/agent_manager.py`, `VJlive-2/creative_hive.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*