# P1-AI1: AIIntegration — AI Subsystem Management Layer

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3 integrates multiple AI subsystems (LLM, neural networks, computer vision, agent systems) that need:
- Centralized lifecycle management (initialization, shutdown, health monitoring)
- Resource coordination (GPU memory, model loading, inference scheduling)
- Configuration and model management
- Error handling and fallback strategies
- Integration with the main application state
- Performance monitoring and optimization

The legacy codebases have AI components scattered without unified management.

---

## Proposed Solution

Implement `AIIntegration` as a facade layer that:

1. **Manages All AI Subsystems** — LLMService, NeuralEngine, AgentManager, etc.
2. **Resource Coordination** — GPU/CPU allocation, model caching, memory management
3. **Lifecycle Management** — init, start, stop, health checks
4. **Configuration** — unified AI configuration (models, providers, timeouts)
5. **Error Handling** — graceful degradation, fallback models, circuit breakers
6. **State Integration** — broadcast AI system status via ApplicationStateManager
7. **Performance Monitoring** — inference latency, throughput, resource usage

---

## API/Interface Definition

```python
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

class AIStatus(Enum):
    """Status of an AI subsystem."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    DISABLED = "disabled"

class AISubsystem(Enum):
    """AI subsystems managed by AIIntegration."""
    LLM = "llm"
    NEURAL = "neural"
    AGENT = "agent"
    VISION = "vision"
    SUGGESTION = "suggestion"
    INTEGRATION = "integration"  # This subsystem

@dataclass
class AISubsystemInfo:
    """Information about an AI subsystem."""
    name: AISubsystem
    status: AIStatus
    last_health_check: float
    error_count: int = 0
    last_error: Optional[str] = None
    resource_usage: Dict[str, float] = field(default_factory=dict)

@dataclass
class AIConfig:
    """Global AI configuration."""
    enabled: bool = True
    default_llm_provider: str = "ollama"
    default_llm_model: str = "llama2"
    max_concurrent_inferences: int = 4
    gpu_memory_limit_mb: int = 4096
    inference_timeout_sec: float = 30.0
    enable_caching: bool = True
    cache_size: int = 1000
    fallback_enabled: bool = True
    health_check_interval_sec: float = 60.0

class AIIntegration:
    """
    Centralized AI subsystem management.

    Usage:
        ai_integration = AIIntegration(
            config=ai_config,
            state_mgr=app_state_mgr
        )

        # Initialize all subsystems
        await ai_integration.initialize()

        # Get subsystem instance
        llm_service = ai_integration.get_subsystem(AISubsystem.LLM)

        # Check health
        health = ai_integration.health_check()

        # Shutdown
        await ai_integration.shutdown()
    """

    def __init__(
        self,
        config: AIConfig,
        state_mgr: Optional['ApplicationStateManager'] = None
    ):
        """
        Initialize AI integration layer.

        Args:
            config: AI configuration
            state_mgr: Optional ApplicationStateManager for status broadcasting
        """
        self.config = config
        self.state_mgr = state_mgr

        self._subsystems: Dict[AISubsystem, Any] = {}
        self._subsystem_info: Dict[AISubsystem, AISubsystemInfo] = {}
        self._health_check_timer = None
        self._lock = threading.Lock()

        # Initialize subsystem info
        for subsystem in AISubsystem:
            self._subsystem_info[subsystem] = AISubsystemInfo(
                name=subsystem,
                status=AIStatus.INITIALIZING,
                last_health_check=time.time()
            )

    async def initialize(self) -> None:
        """Initialize all AI subsystems."""
        if not self.config.enabled:
            for info in self._subsystem_info.values():
                info.status = AIStatus.DISABLED
            return

        # Initialize subsystems in dependency order
        init_order = [
            AISubsystem.INTEGRATION,  # Self
            AISubsystem.LLM,
            AISubsystem.NEURAL,
            AISubsystem.VISION,
            AISubsystem.SUGGESTION,
            AISubsystem.AGENT
        ]

        for subsystem in init_order:
            try:
                await self._initialize_subsystem(subsystem)
            except Exception as e:
                print(f"Failed to initialize {subsystem}: {e}")
                self._subsystem_info[subsystem].status = AIStatus.ERROR
                self._subsystem_info[subsystem].error_count += 1
                self._subsystem_info[subsystem].last_error = str(e)

        # Start health check timer
        self._start_health_checks()

        # Broadcast initial state
        self._broadcast_state()

    async def shutdown(self) -> None:
        """Shutdown all AI subsystems gracefully."""
        # Stop health check timer
        self._stop_health_checks()

        # Shutdown subsystems in reverse order
        shutdown_order = [
            AISubsystem.AGENT,
            AISubsystem.SUGGESTION,
            AISubsystem.VISION,
            AISubsystem.NEURAL,
            AISubsystem.LLM,
            AISubsystem.INTEGRATION
        ]

        for subsystem in shutdown_order:
            try:
                await self._shutdown_subsystem(subsystem)
            except Exception as e:
                print(f"Error shutting down {subsystem}: {e}")

        self._subsystems.clear()

    def get_subsystem(self, subsystem: AISubsystem) -> Any:
        """
        Get an AI subsystem instance.

        Args:
            subsystem: Subsystem to retrieve

        Returns:
            Subsystem instance

        Raises:
            RuntimeError: If subsystem not initialized or in error state
        """
        info = self._subsystem_info[subsystem]
        if info.status == AIStatus.ERROR:
            raise RuntimeError(f"Subsystem {subsystem} is in error state: {info.last_error}")
        if subsystem not in self._subsystems:
            raise RuntimeError(f"Subsystem {subsystem} not initialized")
        return self._subsystems[subsystem]

    def is_subsystem_ready(self, subsystem: AISubsystem) -> bool:
        """Check if a subsystem is ready for use."""
        info = self._subsystem_info[subsystem]
        return info.status == AIStatus.READY

    def get_subsystem_info(self, subsystem: AISubsystem) -> AISubsystemInfo:
        """Get information about a subsystem."""
        return self._subsystem_info[subsystem].copy()

    def get_all_subsystem_info(self) -> Dict[AISubsystem, AISubsystemInfo]:
        """Get information about all subsystems."""
        return {k: v.copy() for k, v in self._subsystem_info.items()}

    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all subsystems.

        Returns:
            Dict with health status summary
        """
        healthy = True
        results = {}

        for subsystem, info in self._subsystem_info.items():
            if subsystem not in self._subsystems:
                continue

            try:
                # Call subsystem health check if available
                subsystem_instance = self._subsystems[subsystem]
                if hasattr(subsystem_instance, 'health_check'):
                    result = subsystem_instance.health_check()
                    results[subsystem.value] = result
                    if not result.get('healthy', True):
                        healthy = False
                else:
                    results[subsystem.value] = {'healthy': True}
            except Exception as e:
                results[subsystem.value] = {
                    'healthy': False,
                    'error': str(e)
                }
                healthy = False
                info.error_count += 1
                info.last_error = str(e)

        return {
            'timestamp': time.time(),
            'healthy': healthy,
            'subsystems': results
        }

    def restart_subsystem(self, subsystem: AISubsystem) -> bool:
        """
        Restart a failed subsystem.

        Args:
            subsystem: Subsystem to restart

        Returns:
            True if restart successful, False otherwise
        """
        try:
            # Shutdown existing
            if subsystem in self._subsystems:
                self._shutdown_subsystem(subsystem)

            # Reinitialize
            self._initialize_subsystem(subsystem)
            return True
        except Exception as e:
            print(f"Failed to restart {subsystem}: {e}")
            return False

    async def _initialize_subsystem(self, subsystem: AISubsystem) -> None:
        """Initialize a specific subsystem."""
        info = self._subsystem_info[subsystem]

        try:
            if subsystem == AISubsystem.LLM:
                from vjlive3.ai.llm_service import LLMService
                llm_config = self._load_llm_config()
                self._subsystems[subsystem] = LLMService(llm_config)
                await self._subsystems[subsystem].initialize()

            elif subsystem == AISubsystem.NEURAL:
                from vjlive3.ai.neural_engine import NeuralEngine
                neural_config = self._load_neural_config()
                self._subsystems[subsystem] = NeuralEngine(neural_config)
                await self._subsystems[subsystem].initialize()

            elif subsystem == AISubsystem.AGENT:
                from vjlive3.agents.agent_manager import AgentManager
                agent_config = self._load_agent_config()
                self._subsystems[subsystem] = AgentManager(
                    agent_config,
                    llm_service=self._subsystems.get(AISubsystem.LLM)
                )
                await self._subsystems[subsystem].initialize()

            elif subsystem == AISubsystem.VISION:
                from vjlive3.ai.vision_service import VisionService
                vision_config = self._load_vision_config()
                self._subsystems[subsystem] = VisionService(vision_config)
                await self._subsystems[subsystem].initialize()

            elif subsystem == AISubsystem.SUGGESTION:
                from vjlive3.ai.suggestion_engine import AISuggestionEngine
                suggestion_config = self._load_suggestion_config()
                self._subsystems[subsystem] = AISuggestionEngine(
                    suggestion_config,
                    llm_service=self._subsystems.get(AISubsystem.LLM)
                )
                await self._subsystems[subsystem].initialize()

            elif subsystem == AISubsystem.INTEGRATION:
                # Self — already initialized
                pass

            info.status = AIStatus.READY
            info.last_health_check = time.time()
            info.error_count = 0
            info.last_error = None

        except Exception as e:
            info.status = AIStatus.ERROR
            info.last_error = str(e)
            raise

    async def _shutdown_subsystem(self, subsystem: AISubsystem) -> None:
        """Shutdown a specific subsystem."""
        if subsystem in self._subsystems:
            instance = self._subsystems[subsystem]
            if hasattr(instance, 'shutdown'):
                await instance.shutdown()
            del self._subsystems[subsystem]

        info = self._subsystem_info[subsystem]
        info.status = AIStatus.INITIALIZING

    def _load_llm_config(self) -> Dict:
        """Load LLM-specific configuration."""
        # Would load from ConfigManager
        return {
            'provider': self.config.default_llm_provider,
            'model': self.config.default_llm_model,
            'timeout': self.config.inference_timeout_sec,
            'max_concurrent': self.config.max_concurrent_inferences
        }

    def _load_neural_config(self) -> Dict:
        """Load neural engine configuration."""
        return {
            'gpu_memory_limit_mb': self.config.gpu_memory_limit_mb,
            'enable_caching': self.config.enable_caching,
            'cache_size': self.config.cache_size
        }

    def _load_agent_config(self) -> Dict:
        """Load agent configuration."""
        return {
            'max_agents': 10,
            'enable_autonomous': True,
            'llm_timeout': self.config.inference_timeout_sec
        }

    def _load_vision_config(self) -> Dict:
        """Load vision service configuration."""
        return {
            'model': 'clip',
            'gpu_memory_mb': self.config.gpu_memory_limit_mb // 2
        }

    def _load_suggestion_config(self) -> Dict:
        """Load suggestion engine configuration."""
        return {
            'enable_suggestions': True,
            'suggestion_rate': 1.0,  # per second
            'llm_timeout': self.config.inference_timeout_sec
        }

    def _start_health_checks(self) -> None:
        """Start periodic health checks."""
        # Would use threading.Timer or integrate with main loop
        pass

    def _stop_health_checks(self) -> None:
        """Stop health check timer."""
        if self._health_check_timer:
            self._health_check_timer.cancel()
            self._health_check_timer = None

    def _broadcast_state(self) -> None:
        """Broadcast AI integration state via ApplicationStateManager."""
        if not self.state_mgr:
            return

        state = {
            'enabled': self.config.enabled,
            'subsystems': {
                s.value: info.status.value
                for s, info in self._subsystem_info.items()
            }
        }

        self.state_mgr.set(
            category=StateCategory.SYSTEM,
            key="ai_integration",
            value=state
        )

    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current AI resource usage.

        Returns:
            Dict with GPU/CPU memory usage, inference counts, etc.
        """
        usage = {
            'gpu_memory_mb': 0.0,
            'cpu_percent': 0.0,
            'active_inferences': 0,
            'cache_hit_rate': 0.0
        }

        for subsystem, info in self._subsystem_info.items():
            usage['gpu_memory_mb'] += info.resource_usage.get('gpu_memory_mb', 0)
            usage['cpu_percent'] += info.resource_usage.get('cpu_percent', 0)
            usage['active_inferences'] += info.resource_usage.get('active_inferences', 0)

        return usage
```

---

## Implementation Plan

### Day 1: Core Structure
- Create `src/vjlive3/ai/ai_integration.py`
- Implement `AIIntegration` class with subsystem registry
- Define enums (AISubsystem, AIStatus) and dataclasses (AISubsystemInfo, AIConfig)
- Add basic get/set and status tracking
- Write unit tests for subsystem management

### Day 2: Subsystem Integration
- Implement initialization order and dependency management
- Add LLMService integration (P1-AI6)
- Add NeuralEngine integration (P1-AI8)
- Add error handling and status updates
- Write integration tests with mock subsystems

### Day 3: Agent & Suggestion Integration
- Add AgentManager integration (P1-AI2)
- Add AISuggestionEngine integration (P1-AI7)
- Implement health check framework
- Add resource usage tracking
- Write tests for agent/suggestion integration

### Day 4: Vision & Advanced Features
- Add VisionService integration (P1-AI5)
- Implement resource coordination (GPU memory limits)
- Add caching and inference scheduling
- Implement fallback strategies
- Write tests for vision and resource management

### Day 5: State Integration & Polish
- Integrate with ApplicationStateManager (P1-C1)
- Add health check timer and monitoring
- Implement graceful shutdown
- Comprehensive test suite (≥80% coverage)
- Documentation and performance tuning

---

## Test Strategy

**Unit Tests:**
- Subsystem registration and initialization
- Status tracking and transitions
- Health check execution
- Resource usage aggregation
- Error handling and recovery
- Configuration loading

**Integration Tests:**
- Full initialization sequence with all subsystems
- State broadcasting to ApplicationStateManager
- Health check monitoring
- Graceful shutdown
- Resource limit enforcement

**Performance Tests:**
- Initialization time (<5s for all subsystems)
- Health check overhead (<1% CPU)
- Memory usage (<100MB for integration layer)

---

## Performance Requirements

- **Initialization:** <5 seconds for all subsystems
- **Health Check:** <100ms per subsystem, <1% CPU overhead
- **Memory:** <100MB for integration layer itself
- **State Broadcast:** <1ms per update

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** All subsystem errors logged and broadcast
- **Rail 8 (Resource Leak Prevention):** Subsystems properly shutdown; resources released
- **Rail 10 (Security):** No security implications beyond subsystems themselves

---

## Dependencies

- **P1-C1:** ApplicationStateManager — for state broadcasting
- **P1-AI2:** AgentManager — subsystem dependency
- **P1-AI5:** CreativeHive/VisionService — subsystem dependency
- **P1-AI6:** LLMService — subsystem dependency
- **P1-AI7:** AISuggestionEngine — subsystem dependency
- **P1-AI8:** NeuralEngine — subsystem dependency
- **Blocking:** All P1-AI* subsystems must have specs created
- **Blocked By:** None (can be implemented first, subsystems later)

---

## Open Questions

1. Should AIIntegration manage model loading/caching? (Yes, centralize)
2. How to handle subsystem-specific configuration? (Each subsystem loads its own)
3. Do we need inference queueing? (Yes, for concurrency limits)
4. Should health checks be async? (Yes, non-blocking)

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md`
- `WORKSPACE/SAFETY_RAILS.md`
- Legacy: `vjlive/ai_integration.py`, `VJlive-2/neural_engine.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*