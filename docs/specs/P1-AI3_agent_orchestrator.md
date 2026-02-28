# P1-AI3: AgentOrchestrator — LangGraph Orchestration for VJLive Agents

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3's autonomous agents need sophisticated orchestration to:
- Coordinate multiple agents working together on complex tasks
- Manage conversation state and context between agents
- Route tasks to appropriate agents based on capabilities
- Handle agent collaboration patterns (sequential, parallel, consensus)
- Integrate with LangGraph for stateful, multi-actor workflows
- Provide visual feedback on agent activities
- Support the Consciousness Symphony and Hive Mind patterns

The legacy codebases have agent orchestration scattered and not using modern frameworks.

---

## Proposed Solution

Implement `AgentOrchestrator` using LangGraph patterns with:

1. **Stateful Workflows** — maintain conversation state across multiple agents
2. **Agent Routing** — intelligent routing based on task type and agent capabilities
3. **Collaboration Patterns** — support various multi-agent coordination strategies
4. **Hive Mind Integration** — collective intelligence decision making
5. **Consciousness Symphony** — orchestrate the 4-movement symphony
6. **Visual Feedback** — broadcast orchestration state for UI overlay
7. **Error Recovery** — graceful handling of agent failures

---

## API/Interface Definition

```python
from typing import Dict, Any, Optional, List, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum
import time

class OrchestrationState(Enum):
    """States of the orchestration system."""
    IDLE = "idle"
    PROCESSING = "processing"
    COLLABORATING = "collaborating"
    SYNCHRONIZING = "synchronizing"
    ERROR = "error"

class TaskType(Enum):
    """Types of tasks that can be orchestrated."""
    CREATIVE = "creative"  # Visual creation, style transfer
    ANALYSIS = "analysis"  # Crowd analysis, sentiment
    PERFORMANCE = "performance"  # Show control, transitions
    SUGGESTION = "suggestion"  # Parameter suggestions
    ORCHESTRATION = "orchestration"  # Multi-agent coordination

@dataclass
class AgentTask:
    """A task assigned to an agent."""
    task_id: str
    task_type: TaskType
    description: str
    input_data: Dict[str, Any]
    assigned_agent: Optional[str] = None
    status: str = "pending"
    result: Optional[Dict] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None

@dataclass
class CollaborationPattern:
    """Pattern for multi-agent collaboration."""
    pattern_id: str
    name: str
    description: str
    agents_required: List[str]
    coordination_type: str  # "sequential", "parallel", "consensus", "voting"
    timeout_sec: float = 30.0

class AgentOrchestrator:
    """
    Orchestrates multiple agents using LangGraph patterns.

    Usage:
        orchestrator = AgentOrchestrator(
            agent_manager=agent_mgr,
            state_mgr=app_state_mgr
        )

        await orchestrator.initialize()

        # Submit task
        task_id = orchestrator.submit_task(
            task_type=TaskType.CREATIVE,
            description="Generate visual for drop",
            input_data={"bpm": 128, "energy": 0.8}
        )

        # Wait for result
        result = await orchestrator.wait_for_task(task_id)
    """

    def __init__(
        self,
        agent_manager: 'AgentManager',
        state_mgr: Optional['ApplicationStateManager'] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize agent orchestrator.

        Args:
            agent_manager: AgentManager instance
            state_mgr: Optional ApplicationStateManager
            config: Optional configuration dict
        """
        self.agent_manager = agent_manager
        self.state_mgr = state_mgr
        self.config = config or {}

        self._tasks: Dict[str, AgentTask] = {}
        self._task_queue: List[str] = []
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._collaboration_patterns: Dict[str, CollaborationPattern] = {}
        self._state = OrchestrationState.IDLE
        self._lock = threading.Lock()
        self._task_counter = 0

        # Register default collaboration patterns
        self._register_default_patterns()

    async def initialize(self) -> None:
        """Initialize orchestrator."""
        # Would load patterns from config
        self._broadcast_state()

    async def shutdown(self) -> None:
        """Shutdown orchestrator gracefully."""
        # Cancel all active tasks
        for task in self._active_tasks.values():
            task.cancel()

        self._state = OrchestrationState.IDLE

    def submit_task(
        self,
        task_type: TaskType,
        description: str,
        input_data: Dict[str, Any],
        assigned_agent: Optional[str] = None,
        collaboration_pattern: Optional[str] = None
    ) -> str:
        """
        Submit a task for orchestration.

        Args:
            task_type: Type of task
            description: Human-readable description
            input_data: Task input data
            assigned_agent: Optional specific agent ID; if None, auto-route
            collaboration_pattern: Optional collaboration pattern to use

        Returns:
            Task ID for tracking
        """
        with self._lock:
            task_id = f"task_{self._task_counter}"
            self._task_counter += 1

            task = AgentTask(
                task_id=task_id,
                task_type=task_type,
                description=description,
                input_data=input_data,
                assigned_agent=assigned_agent
            )
            self._tasks[task_id] = task
            self._task_queue.append(task_id)

            # Start processing if idle
            if self._state == OrchestrationState.IDLE:
                self._start_processing()

            self._broadcast_task_state(task_id)
            return task_id

    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Wait for task completion.

        Args:
            task_id: Task to wait for
            timeout: Optional timeout in seconds

        Returns:
            Task result dict, or None if timeout/failed
        """
        import asyncio

        start_time = time.time()
        while True:
            task = self._tasks.get(task_id)
            if not task:
                return None

            if task.status == "completed":
                return task.result
            if task.status == "error":
                return None

            if timeout and (time.time() - start_time) > timeout:
                return None

            await asyncio.sleep(0.1)

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """Get current status of a task."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        return {
            'task_id': task.task_id,
            'status': task.status,
            'assigned_agent': task.assigned_agent,
            'created_at': task.created_at,
            'started_at': task.started_at,
            'completed_at': task.completed_at
        }

    def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[TaskType] = None
    ) -> List[Dict]:
        """
        List tasks with optional filtering.

        Args:
            status: Filter by task status
            task_type: Filter by task type

        Returns:
            List of task status dicts
        """
        tasks = []
        for task in self._tasks.values():
            if status and task.status != status:
                continue
            if task_type and task.task_type != task_type:
                continue

            tasks.append({
                'task_id': task.task_id,
                'type': task.task_type.value,
                'description': task.description,
                'status': task.status,
                'assigned_agent': task.assigned_agent,
                'created_at': task.created_at
            })

        return tasks

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.

        Args:
            task_id: Task to cancel

        Returns:
            True if cancelled successfully
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if task.status in ["pending", "running"]:
                task.status = "cancelled"
                if task_id in self._task_queue:
                    self._task_queue.remove(task_id)
                if task_id in self._active_tasks:
                    self._active_tasks[task_id].cancel()
                    del self._active_tasks[task_id]

                self._broadcast_task_state(task_id)
                return True

            return False

    def register_collaboration_pattern(
        self,
        pattern: CollaborationPattern
    ) -> None:
        """
        Register a collaboration pattern.

        Args:
            pattern: Collaboration pattern definition
        """
        self._collaboration_patterns[pattern.pattern_id] = pattern

    def get_collaboration_pattern(
        self,
        pattern_id: str
    ) -> Optional[CollaborationPattern]:
        """Get a collaboration pattern by ID."""
        return self._collaboration_patterns.get(pattern_id)

    def _register_default_patterns(self) -> None:
        """Register default collaboration patterns."""
        # Creative collaboration: Creative Partner + Performance Agent
        creative_pattern = CollaborationPattern(
            pattern_id="creative_jam",
            name="Creative Jam",
            description="Creative partner and performance agent collaborate",
            agents_required=["creative_partner_1", "performance_agent_1"],
            coordination_type="parallel"
        )
        self._collaboration_patterns["creative_jam"] = creative_pattern

        # Analysis pattern: Crowd analyzer + suggestion engine
        analysis_pattern = CollaborationPattern(
            pattern_id="crowd_analysis",
            name="Crowd Analysis",
            description="Analyze crowd and generate suggestions",
            agents_required=["crowd_analyzer_1", "suggestion_engine_1"],
            coordination_type="sequential"
        )
        self._collaboration_patterns["crowd_analysis"] = analysis_pattern

    def _start_processing(self) -> None:
        """Start processing the task queue."""
        if not self._task_queue:
            self._state = OrchestrationState.IDLE
            return

        self._state = OrchestrationState.PROCESSING
        task_id = self._task_queue.pop(0)
        self._process_task(task_id)

    def _process_task(self, task_id: str) -> None:
        """Process a single task (runs in background)."""
        import asyncio

        task = self._tasks[task_id]
        task.status = "running"
        task.started_at = time.time()
        self._broadcast_task_state(task_id)

        # Determine agent assignment
        if task.assigned_agent:
            agent_id = task.assigned_agent
        else:
            agent_id = self._route_task(task)

        if not agent_id:
            task.status = "error"
            task.result = {"error": "No suitable agent found"}
            self._broadcast_task_state(task_id)
            self._continue_processing()
            return

        # Execute task on agent
        async def execute():
            try:
                agent = self.agent_manager.get_agent(agent_id)
                if not agent:
                    raise RuntimeError(f"Agent {agent_id} not found")

                # Call agent's process method
                if hasattr(agent, 'process_task'):
                    result = await agent.process_task(task)
                else:
                    result = await self._default_task_execution(agent, task)

                task.status = "completed"
                task.result = result
                task.completed_at = time.time()

            except Exception as e:
                task.status = "error"
                task.result = {"error": str(e)}
                print(f"Task {task_id} failed: {e}")

            finally:
                self._broadcast_task_state(task_id)
                self._continue_processing()

        # Run async task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            self._active_tasks[task_id] = loop.create_task(execute())
            loop.run_until_complete(self._active_tasks[task_id])
        finally:
            loop.close()
            if task_id in self._active_tasks:
                del self._active_tasks[task_id]

    def _route_task(self, task: AgentTask) -> Optional[str]:
        """
        Route task to appropriate agent.

        Args:
            task: Task to route

        Returns:
            Agent ID, or None if no suitable agent
        """
        # Simple routing based on task type
        available_agents = self.agent_manager.list_agents()

        if task.task_type == TaskType.CREATIVE:
            creative_agents = [
                a for a in available_agents
                if a.agent_type == AgentType.CREATIVE and a.status == AgentStatus.READY
            ]
            return creative_agents[0].agent_id if creative_agents else None

        elif task.task_type == TaskType.ANALYSIS:
            analysis_agents = [
                a for a in available_agents
                if a.agent_type == AgentType.ANALYSIS and a.status == AgentStatus.READY
            ]
            return analysis_agents[0].agent_id if analysis_agents else None

        elif task.task_type == TaskType.PERFORMANCE:
            performance_agents = [
                a for a in available_agents
                if a.agent_type == AgentType.PERFORMANCE and a.status == AgentStatus.READY
            ]
            return performance_agents[0].agent_id if performance_agents else None

        elif task.task_type == TaskType.SUGGESTION:
            suggestion_agents = [
                a for a in available_agents
                if a.agent_type == AgentType.SUGGESTION and a.status == AgentStatus.READY
            ]
            return suggestion_agents[0].agent_id if suggestion_agents else None

        return None

    async def _default_task_execution(
        self,
        agent: Any,
        task: AgentTask
    ) -> Dict:
        """Default task execution if agent doesn't have process_task."""
        # Generic execution: call agent's main method with task data
        if hasattr(agent, 'process'):
            return await agent.process(task.input_data)
        else:
            raise RuntimeError(f"Agent {agent.agent_id} cannot process tasks")

    def _continue_processing(self) -> None:
        """Continue processing the task queue."""
        if self._task_queue:
            self._start_processing()
        else:
            self._state = OrchestrationState.IDLE
            self._broadcast_state()

    def _broadcast_task_state(self, task_id: str) -> None:
        """Broadcast task state change."""
        if not self.state_mgr or task_id not in self._tasks:
            return

        task = self._tasks[task_id]
        state = {
            'task_id': task.task_id,
            'type': task.task_type.value,
            'status': task.status,
            'assigned_agent': task.assigned_agent,
            'created_at': task.created_at
        }

        self.state_mgr.set(
            category=StateCategory.SYSTEM,
            key=f"orchestration.task.{task_id}",
            value=state
        )

    def _broadcast_state(self) -> None:
        """Broadcast overall orchestration state."""
        if not self.state_mgr:
            return

        self.state_mgr.set(
            category=StateCategory.SYSTEM,
            key="agent_orchestrator",
            value={
                'state': self._state.value,
                'queue_length': len(self._task_queue),
                'active_tasks': len(self._active_tasks),
                'total_tasks': len(self._tasks)
            }
        )
```

---

## Implementation Plan

### Day 1: Core Structure
- Create `src/vjlive3/agents/agent_orchestrator.py`
- Implement `AgentOrchestrator` with task queue
- Define enums and dataclasses
- Add task submission and tracking
- Write unit tests for task management

### Day 2: Agent Routing
- Implement intelligent task routing
- Add agent capability matching
- Implement routing strategies (round-robin, capability-based, load-based)
- Add agent health consideration in routing
- Write tests for routing logic

### Day 3: Collaboration Patterns
- Implement collaboration pattern framework
- Add sequential and parallel patterns
- Implement consensus and voting patterns
- Add pattern selection logic
- Write tests for collaboration patterns

### Day 4: LangGraph Integration
- Integrate LangGraph for stateful workflows
- Implement conversation state management
- Add graph-based task dependencies
- Implement checkpoint and recovery
- Write tests for LangGraph integration

### Day 5: Integration & Polish
- Integrate with AgentManager (P1-AI2)
- Integrate with AIIntegration (P1-AI1)
- Add Consciousness Symphony coordination
- Comprehensive test suite (≥80% coverage)
- Documentation and examples

---

## Test Strategy

**Unit Tests:**
- Task submission and queuing
- Task routing logic
- Collaboration pattern matching
- Agent assignment and tracking
- Task cancellation
- State transitions

**Integration Tests:**
- Full task lifecycle with real agents
- AgentManager integration
- State broadcasting
- Collaboration pattern execution
- Error recovery scenarios

**Performance Tests:**
- Task queuing latency (<10ms)
- Routing decision time (<5ms)
- Memory per task (<1MB)

---

## Performance Requirements

- **Task Submission:** <10ms
- **Routing Decision:** <5ms
- **Queue Processing:** <100ms per task
- **Memory:** <1MB per active task

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** Task failures logged and broadcast
- **Rail 8 (Resource Leak Prevention):** Tasks properly cancelled; async resources cleaned
- **Rail 10 (Security):** Task input validated; no arbitrary code execution

---

## Dependencies

- **P1-AI1:** AIIntegration — overall AI management
- **P1-AI2:** AgentManager — agent lifecycle
- **P1-C1:** ApplicationStateManager — state broadcasting
- **Blocking:** P1-AI2 (AgentManager)
- **Blocked By:** None

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md`
- `WORKSPACE/SAFETY_RAILS.md`
- Legacy: `vjlive/agent_orchestrator.py`, `VJlive-2/consciousness_symphony.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*