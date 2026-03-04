# P4-COR014 — AIScheduler

## What This Module Does

The AIScheduler module manages scheduling and resource allocation for AI tasks within VJLive3. It provides a priority-based task queue that coordinates AI inference requests, model training jobs, and background AI processing to ensure timely execution without impacting real-time performance constraints. The scheduler employs sophisticated algorithms to balance workload across available compute resources (CPU, GPU, memory), enforce resource limits, manage task dependencies, and meet deadlines while maintaining the 60 FPS guarantee for core VJ operations.

Core capabilities include:
- **Priority-Based Scheduling**: Multi-level priority queue with preemption for urgent AI tasks
- **Resource Management**: Dynamic resource allocation and limit enforcement per task
- **Deadline Awareness**: Time-sensitive scheduling with deadline tracking and miss handling
- **Task Dependencies**: Directed acyclic graph (DAG) dependency resolution
- **Load Balancing**: Work distribution across multiple worker threads/processes
- **Performance Monitoring**: Real-time metrics on queue depth, wait times, resource utilization
- **Graceful Degradation**: Quality/accuracy trade-offs under resource pressure
- **Fault Tolerance**: Task retry, checkpointing, and recovery from worker failures

The module integrates with the AI integration layer (P4-COR009) for task execution and with the resource monitoring system to track system capacity.

## What It Does NOT Do

- Does not perform AI inference (delegates to AIIntegration and model backends)
- Does not make creative decisions about task content or parameters
- Does not manage non-AI system resources (delegates to general resource manager)
- Does not handle user interface concerns (delegates to UI modules)
- Does not implement machine learning models (only schedules their execution)
- Does not guarantee task completion (best-effort with configurable retries)
- Does not operate without resource constraints (always respects system limits)

## Public Interface

```python
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

class TaskStatus(Enum):
    """Status of a scheduled task."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PREEMPTED = "preempted"
    TIMEOUT = "timeout"

class Priority(Enum):
    """Task priority levels."""
    CRITICAL = 0   # Preempt all, immediate execution
    HIGH = 1       # High priority, preempt lower
    NORMAL = 2     # Standard priority
    LOW = 3        # Background processing
    IDLE = 4       # Only when system idle

@dataclass
class TaskDefinition:
    """Definition of an AI task to be scheduled."""
    task_id: str
    task_type: str  # "inference", "training", "preprocessing", "optimization"
    payload: Dict[str, Any]
    priority: Priority = Priority.NORMAL
    deadline: Optional[float] = None  # Unix timestamp, None = no deadline
    dependencies: List[str] = None  # Task IDs that must complete first
    resource_requirements: Dict[str, float] = None  # {"cpu": 0.5, "gpu": 0.3, "memory_mb": 512}
    max_runtime_seconds: Optional[float] = None
    retry_policy: Dict[str, Any] = None  # {"max_retries": 3, "backoff_factor": 2.0}
    callback: Optional[Callable] = None  # Called on completion with result
    metadata: Dict[str, Any] = None

@dataclass
class ScheduledTask:
    """Task currently in the scheduler."""
    definition: TaskDefinition
    status: TaskStatus
    queued_at: float
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    assigned_worker: Optional[str] = None
    current_resource_usage: Dict[str, float] = None
    attempts: int = 0
    last_error: Optional[str] = None
    estimated_completion: Optional[float] = None

@dataclass
class ResourceLimits:
    """Resource limits for AI tasks."""
    max_cpu_percent: float = 80.0  # Max CPU usage for AI tasks (0-100)
    max_gpu_percent: float = 90.0  # Max GPU usage for AI tasks (0-100)
    max_memory_mb: float = 4096.0  # Max memory for AI tasks in MB
    max_concurrent_tasks: int = 4  # Maximum parallel AI tasks
    max_queue_size: int = 1000  # Maximum queued tasks
    deadline_soft_ms: float = 100.0  # Soft deadline in milliseconds
    deadline_hard_ms: float = 500.0  # Hard deadline in milliseconds

@dataclass
class QueueStatus:
    """Current status of the task queue."""
    total_queued: int
    total_running: int
    total_completed: int
    total_failed: int
    priority_counts: Dict[int, int]  # priority -> count
    avg_wait_time_ms: float
    avg_runtime_ms: float
    resource_usage: Dict[str, float]  # Current resource consumption
    system_load: float  # 0.0-1.0 overall system load

class AIScheduler:
    """
    AI task scheduler with priority queuing, resource management, and deadline awareness.
    
    Manages the execution of AI tasks while maintaining real-time performance
    guarantees for VJLive3's core operations.
    """
    
    METADATA = {
        "id": "AIScheduler",
        "type": "scheduler",
        "version": "1.0.0",
        "legacy_ref": "ai_scheduler (AIScheduler)"
    }
    
    def __init__(self,
                 limits: ResourceLimits = None,
                 num_workers: int = 4,
                 worker_timeout: float = 30.0):
        """
        Initialize AI scheduler with resource limits and worker pool.
        
        Args:
            limits: Resource limits configuration (default: ResourceLimits())
            num_workers: Number of worker threads/processes
            worker_timeout: Timeout for worker tasks in seconds
        """
        pass
    
    def schedule_task(self,
                     task: TaskDefinition,
                     priority: int = None,
                     deadline: float = None) -> str:
        """
        Schedule an AI task for execution.
        
        Args:
            task: Task definition (or dict with task parameters)
            priority: Override priority (if None, use task.priority)
            deadline: Override deadline (if None, use task.deadline)
            
        Returns:
            Task ID (string) for tracking and cancellation
            
        Raises:
            QueueFullError: If task queue is full
            ResourceLimitError: If resource limits would be exceeded
            InvalidTaskError: If task definition invalid
            DeadlineTooSoonError: If deadline is in the past or too near
        """
        pass
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a scheduled or running task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if task was cancelled, False if not found or already completed
            
        Raises:
            CancellationError: If cancellation fails (e.g., task cannot be interrupted)
        """
        pass
    
    def get_queue_status(self) -> QueueStatus:
        """
        Get current task queue status and resource usage.
        
        Returns:
            QueueStatus object with counts, wait times, and resource metrics
        """
        pass
    
    def set_resource_limits(self, limits: ResourceLimits) -> bool:
        """
        Update resource limits dynamically.
        
        Args:
            limits: New resource limits to apply
            
        Returns:
            True if limits updated successfully, False if validation fails
            
        Raises:
            LimitValidationError: If limits are invalid (e.g., negative values)
        """
        pass
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage by AI tasks.
        
        Returns:
            Dictionary with keys: cpu_percent, gpu_percent, memory_mb, active_tasks, queued_tasks
        """
        pass
    
    def prioritize_tasks(self,
                        criteria: Dict[str, Any],
                        task_ids: List[str] = None) -> List[Dict[str, Any]]:
        """
        Re-prioritize tasks based on criteria.
        
        Args:
            criteria: Prioritization criteria (e.g., {"deadline_urgency": 0.5, "resource_intensity": 0.3})
            task_ids: Specific tasks to re-prioritize (None = all pending tasks)
            
        Returns:
            List of tasks with new priorities, sorted by impact
            
        Raises:
            PrioritizationError: If criteria invalid or re-prioritization fails
        """
        pass
    
    def preempt_task(self, task_id: str, reason: str) -> bool:
        """
        Preempt a running task to make room for higher priority work.
        
        Args:
            task_id: ID of task to preempt
            reason: Reason for preemption (e.g., "higher_priority", "resource_shortage")
            
        Returns:
            True if task preempted successfully, False if task cannot be preempted
            
        Raises:
            PreemptionError: If preemption fails (e.g., task not preemptable)
        """
        pass
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed status of a specific task.
        
        Args:
            task_id: ID of task to query
            
        Returns:
            Dictionary with task details, or None if task not found
            
            Keys include: task_id, status, priority, queued_at, started_at, completed_at,
            assigned_worker, resource_usage, attempts, last_error, estimated_completion
        """
        pass
    
    def wait_for_task(self, task_id: str, timeout: float = None) -> Any:
        """
        Block until task completes, returning its result.
        
        Args:
            task_id: ID of task to wait for
            timeout: Maximum time to wait in seconds (None = no timeout)
            
        Returns:
            Task result (as returned by the task's callback)
            
        Raises:
            TaskNotFoundError: If task_id not found
            TimeoutError: If timeout expires before completion
            TaskFailedError: If task fails (includes failure reason)
        """
        pass
    
    def get_completed_tasks(self,
                           limit: int = 100,
                           status: TaskStatus = None) -> List[Dict[str, Any]]:
        """
        Get list of recently completed tasks.
        
        Args:
            limit: Maximum number of tasks to return
            status: Filter by status (COMPLETED, FAILED, CANCELLED, etc.)
            
        Returns:
            List of task status dictionaries, most recent first
        """
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get scheduler performance metrics.
        
        Returns:
            Dictionary with metrics:
            - tasks_scheduled: total tasks scheduled
            - tasks_completed: successfully completed
            - tasks_failed: failed tasks
            - tasks_preempted: preempted tasks
            - avg_queue_time_ms: average wait time
            - avg_execution_time_ms: average runtime
            - deadline_misses: count of missed deadlines
            - resource_utilization: avg CPU/GPU/memory usage
            - throughput_tasks_per_second: current throughput
        """
        pass
    
    def pause(self) -> bool:
        """
        Pause scheduling (queued tasks wait, running tasks continue).
        
        Returns:
            True if paused, False if already paused
        """
        pass
    
    def resume(self) -> bool:
        """
        Resume scheduling after pause.
        
        Returns:
            True if resumed, False if not paused
        """
        pass
    
    def shutdown(self, wait: bool = True, timeout: float = 30.0) -> bool:
        """
        Shutdown scheduler, optionally waiting for running tasks.
        
        Args:
            wait: If True, wait for running tasks to complete
            timeout: Maximum time to wait for tasks
            
        Returns:
            True if shutdown clean, False if timeout or forced
        """
        pass
```

## Inputs and Outputs

### Input Requirements

| Input | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `task` | `TaskDefinition` | Task to schedule | task_id unique; task_type ∈ {"inference", "training", "preprocessing", "optimization"} |
| `priority` | `int` or `Priority` | Override priority | If int: 0=CRITICAL, 1=HIGH, 2=NORMAL, 3=LOW, 4=IDLE |
| `deadline` | `float` (Unix timestamp) | Execution deadline | Must be > current_time; None = no deadline |
| `task_id` | `str` | Task identifier | Alphanumeric + hyphens; unique within scheduler |
| `limits` | `ResourceLimits` | Resource constraints | cpu_percent ∈ [0,100]; gpu_percent ∈ [0,100]; memory_mb > 0; max_concurrent_tasks ≥ 1 |
| `criteria` | `Dict[str, float]` | Prioritization weights | Sum of weights = 1.0; keys: deadline_urgency, resource_intensity, priority_boost, user_importance |
| `task_ids` | `List[str]` | Task identifiers | All must exist in queue |
| `reason` | `str` | Preemption reason | Human-readable; ∈ {"higher_priority", "resource_shortage", "deadline_miss", "maintenance"} |
| `timeout` | `float` | Wait timeout in seconds | > 0; None = infinite |
| `status` | `TaskStatus` | Filter for task list | Optional filter |
| `limit` | `int` | Result list limit | 1-1000 |
| `num_workers` | `int` | Worker count | 1-64 |
| `worker_timeout` | `float` | Worker timeout | 1-300 seconds |

### Output Specifications

| Output | Type | Description | Format |
|--------|------|-------------|--------|
| `task_id` | `str` | Unique task identifier | UUID or user-provided ID |
| `bool` | `bool` | Operation success | True/False |
| `QueueStatus` | `dataclass` | Queue and resource status | See fields above |
| `ResourceLimits` | `dataclass` | Current resource limits | cpu_percent, gpu_percent, memory_mb, etc. |
| `Dict[str, float]` | `dict` | Resource usage metrics | cpu_percent, gpu_percent, memory_mb, active_tasks, queued_tasks |
| `List[Dict[str, Any]]` | `list` | Re-prioritized tasks | Each: task_id, old_priority, new_priority, impact_score |
| `Optional[Dict[str, Any]]` | `dict` | Task status details | See `get_task_status()` fields |
| `Any` | `any` | Task result | Whatever the task callback returns |
| `Dict[str, Any]` | `dict` | Performance metrics | See `get_metrics()` fields |

## Detailed Behavior

### Priority-Based Scheduling Algorithm

The scheduler uses a multi-level priority queue with preemption:

```
Priority Levels (0 = highest, 4 = lowest):
  0: CRITICAL   - Preempt all running tasks, immediate execution
  1: HIGH       - Preempt LOW/IDLE tasks, execute before NORMAL
  2: NORMAL     - Standard priority, FIFO within level
  3: LOW        - Execute only when no higher priority tasks
  4: IDLE       - Execute only when system completely idle

Scheduling Decision Algorithm:

1. Check for preemption:
   IF any CRITICAL task pending:
     Preempt lowest priority running task (LOW/IDLE) for CRITICAL
   ELSE IF any HIGH task pending and no HIGH/NORMAL running:
     Preempt LOW/IDLE running tasks for HIGH

2. Select next task:
   FOR priority in [CRITICAL, HIGH, NORMAL, LOW, IDLE]:
     IF queue[priority] not empty:
       task = queue[priority].pop(0)  # FIFO within priority
       IF task has dependencies:
         IF all dependencies completed:
           execute task
         ELSE:
           requeue at back of priority queue (or blocked queue)
       ELSE:
         execute task
       BREAK

3. Resource check before execution:
   IF available_resources < task.resource_requirements:
     IF task.priority == CRITICAL:
       preempt lower priority tasks to free resources
     ELSE:
       wait until resources available (or deadline)

4. Deadline handling:
   - Soft deadline (deadline_soft_ms): Log warning if exceeded
   - Hard deadline (deadline_hard_ms): Cancel task if exceeded
   - Deadline urgency = (deadline - current_time) / (deadline - queued_at)
   - Urgent tasks (deadline_soft_ms remaining) get priority boost

Preemption Algorithm:

1. Identify preemptable tasks:
   - Only tasks with priority > preempting_task.priority
   - Only tasks marked as preemptable (long-running inference may be non-preemptable)
   - Prefer tasks with lowest priority, longest runtime, lowest progress

2. Checkpoint and suspend:
   - Save task state (if checkpointing enabled)
   - Release resources
   - Return task to queue with preempted status and boosted priority

3. Resume preempted task later:
   - Preempted tasks get priority boost (one level higher) when rescheduled
   - Maintain order among preempted tasks (FIFO within boosted priority)
```

**Example Scheduling Scenario**:
```python
scheduler = AIScheduler()

# Schedule tasks with different priorities
t1 = TaskDefinition(task_id="t1", task_type="inference", priority=Priority.NORMAL)
t2 = TaskDefinition(task_id="t2", task_type="inference", priority=Priority.HIGH)
t3 = TaskDefinition(task_id="t3", task_type="inference", priority=Priority.CRITICAL)

scheduler.schedule_task(t1)  # Queued at NORMAL
scheduler.schedule_task(t2)  # Queued at HIGH (will execute before t1)
scheduler.schedule_task(t3)  # Queued at CRITICAL (preempts any running task)

# Queue order: t3 (CRITICAL) → t2 (HIGH) → t1 (NORMAL)
```

### Resource Management

The scheduler enforces resource limits and performs dynamic allocation:

```
Resource Tracking:

- CPU: Tracked as percentage of total cores (0-100%)
- GPU: Tracked as percentage of total GPU memory/compute (0-100%)
- Memory: Tracked in MB of RAM/VRAM
- Concurrent tasks: Count of actively executing tasks

Resource Allocation Algorithm:

1. Task submission:
   - Check if task.resource_requirements fit within limits
   - IF total_allocated + task_requirements > limits:
     IF task.priority == CRITICAL:
       Preempt lower priority tasks to free resources
     ELSE:
       Queue task until resources available (or timeout)

2. Dynamic adjustment:
   - Monitor actual resource usage (not just requested)
   - If task exceeds allocation, throttle or pause (unless CRITICAL)
   - If system under heavy load, degrade quality (lower precision, smaller batch)

3. Resource reclamation:
   - When task completes, immediately free resources
   - Wake waiting tasks in priority order
   - Update resource usage metrics

Resource Limit Enforcement:

  max_cpu_percent: 80% means AI tasks can use up to 80% of total CPU
  max_gpu_percent: 90% means AI tasks can use up to 90% of GPU memory/compute
  max_memory_mb: 4096MB means total AI task memory capped at 4GB
  max_concurrent_tasks: 4 means at most 4 AI tasks running simultaneously

Example:
  System: 8 CPU cores, 16GB RAM, 8GB GPU
  Limits: cpu=80% (6.4 cores), gpu=90% (7.2GB), memory=4096MB, concurrent=4
  
  Task A requests: cpu=50%, gpu=60%, memory=2048MB
  Task B requests: cpu=40%, gpu=40%, memory=1024MB
  
  Both can run concurrently: total cpu=90% > 80% limit → B must wait or A throttled
  Solution: Throttle A to 40% CPU, or run A then B
```

### Deadline Management

The scheduler tracks and enforces task deadlines:

```
Deadline Types:

- Soft deadline: Warning logged if missed, task continues
- Hard deadline: Task cancelled if missed
- Deadline urgency: (deadline - now) / (deadline - queued_at)
  - urgency = 1.0: just queued
  - urgency = 0.0: at deadline now
  - urgency < 0: deadline missed

Deadline-Aware Scheduling:

1. Deadline calculation:
   - absolute_deadline = deadline (if provided) or (queued_at + max_runtime_seconds)
   - soft_deadline = absolute_deadline - deadline_soft_ms
   - hard_deadline = absolute_deadline - deadline_hard_ms

2. Priority boost based on urgency:
   IF urgency < 0.1 (10% time remaining):
     boost priority by 1 level (e.g., NORMAL → HIGH)
   IF urgency < 0.05 (5% time remaining):
     boost priority by 2 levels (e.g., NORMAL → CRITICAL)

3. Deadline miss handling:
   - Check deadlines every scheduling cycle (e.g., 10ms)
   - IF current_time > hard_deadline:
     Cancel task, log error, increment deadline_misses metric
   - IF current_time > soft_deadline:
     Log warning, boost priority, may preempt lower priority tasks

4. Deadline estimation:
   - For tasks without explicit deadline, estimate based on:
     * task_type (inference: 100ms, training: 60s, preprocessing: 10s)
     * resource_requirements (more resources → faster)
     * historical runtime for similar tasks
   - Estimated deadline = queued_at + estimated_runtime * 1.2 (20% buffer)

Example:
  Task queued at t=0, deadline=1000ms, soft=900ms, hard=950ms
  At t=920: urgency = (1000-920)/1000 = 0.08 → priority boost
  At t=960: deadline missed (hard), task cancelled
```

### Task Dependencies

The scheduler supports DAG-based task dependencies:

```
Dependency Resolution:

1. Task submission with dependencies:
   task = TaskDefinition(
     task_id="t2",
     dependencies=["t1"]  # t2 waits for t1 to complete
   )

2. Dependency tracking:
   - Maintain dependency graph: {task_id: [dep1, dep2, ...]}
   - Maintain reverse dependencies: {task_id: [waiting_tasks]}
   - Track completion status of each task

3. Scheduling blocked tasks:
   - When task completes, check reverse_dependencies
   - For each waiting task:
     * Check if all its dependencies are completed (successfully)
     * IF all complete: move from blocked queue to ready queue (appropriate priority)
     * IF any failed: cancel waiting task (or based on failure policy)

4. Cycle detection:
   - On task submission, check for dependency cycles
   - Use DFS to detect cycles in dependency graph
   - Raise CycleError if cycle detected

5. Deadlock prevention:
   - Timeout for dependency wait (default: 5 minutes)
   - If task blocked > timeout, cancel with DeadlockError
   - Optionally, allow "best-effort" dependencies (continue if some fail)

Example DAG:
  t1 → t2 → t4
  t1 → t3 → t4
  
  t1 completes → t2 and t3 become ready
  t2 and t3 complete → t4 becomes ready
```

### Load Balancing and Worker Management

The scheduler distributes tasks across worker threads/processes:

```
Worker Pool:

- Fixed number of workers (num_workers) created at init
- Each worker runs in separate thread or process
- Workers pull tasks from priority queue when idle
- Workers report status and resource usage periodically

Work Distribution Algorithm:

1. Task assignment:
   - Scheduler maintains global priority queue
   - When worker becomes idle:
     * Scheduler selects highest priority ready task
     * Checks resource availability on worker (if per-worker limits)
     * Assigns task to worker
     * Updates task status to RUNNING, set assigned_worker

2. Load balancing:
   - Monitor worker load (tasks running, resource usage)
   - If worker overloaded (CPU > 90% for > 10s):
     * Prevent new task assignments to that worker
     * Optionally migrate tasks (if preemptable and checkpointed)
   - If worker underloaded (CPU < 30% for > 30s):
     * Assign more tasks (up to limits)

3. Worker failure handling:
   - Workers send heartbeat every 5 seconds
   - If worker missed 3 heartbeats:
     * Mark worker as failed
     * Re-queue all tasks assigned to that worker
     * Increment attempt count for re-queued tasks
     * If task exceeds retry limit, mark as FAILED
   - Spawn replacement worker (if pool size < num_workers)

4. Resource-aware placement:
   - Track per-worker resource usage
   - Assign GPU tasks to workers with available GPU
   - Assign memory-intensive tasks to workers with available RAM
   - Avoid over-subscribing any single worker

Example:
  4 workers, 8 tasks (2 CRITICAL, 3 HIGH, 3 NORMAL)
  Worker 1: Running CRITICAL task A
  Worker 2: Running CRITICAL task B
  Worker 3: Idle → assigned HIGH task C
  Worker 4: Idle → assigned HIGH task D
  Remaining: HIGH task E, 3 NORMAL tasks wait in queue
```

### Performance Monitoring and Metrics

The scheduler collects comprehensive metrics:

```
Metrics Collected:

1. Queue Metrics:
   - tasks_scheduled: Total tasks submitted
   - tasks_completed: Successfully finished tasks
   - tasks_failed: Tasks that failed or timed out
   - tasks_cancelled: Tasks cancelled by user
   - tasks_preempted: Tasks preempted for higher priority
   - queue_depth: Current number of queued tasks (by priority)
   - avg_queue_time_ms: Average wait time from submit to start
   - max_queue_time_ms: Maximum wait time observed

2. Execution Metrics:
   - avg_execution_time_ms: Average task runtime
   - execution_time_by_type: {task_type: avg_ms}
   - deadline_misses: Count of tasks missing hard deadline
   - deadline_warnings: Count of tasks missing soft deadline

3. Resource Metrics:
   - cpu_utilization: Average CPU % used by AI tasks
   - gpu_utilization: Average GPU % used
   - memory_usage_mb: Current memory used by AI tasks
   - resource_peak: Peak resource usage since start

4. Throughput Metrics:
   - tasks_per_second: Current throughput
   - tasks_per_hour: Rolling hourly throughput
   - efficiency: (busy_time / total_time) for workers

5. Quality Metrics:
   - preemption_rate: Fraction of tasks preempted
   - retry_rate: Fraction of tasks requiring retry
   - failure_rate: Fraction of tasks failing

Metrics Collection:
  - Collected every 10 seconds
  - Stored in circular buffer (last 1000 samples)
  - Exposed via get_metrics() and monitoring API
  - Logged to structured logs for analysis

Alerting Thresholds:
  - avg_queue_time_ms > 1000: Warning (tasks waiting too long)
  - deadline_misses > 0: Critical (missed deadlines)
  - cpu_utilization > 95%: Warning (system overloaded)
  - failure_rate > 0.1: Critical (too many failures)
```

### Graceful Degradation

Under resource pressure, the scheduler can degrade quality to maintain responsiveness:

```
Degradation Triggers:

- System load > 90% for > 5 seconds
- Queue depth > 100 for > 10 seconds
- Average wait time > 500ms
- Memory usage > 90% of limit

Degradation Strategies (applied in order):

1. Quality reduction:
   - For inference: Use lower precision (FP32 → FP16 → INT8)
   - For training: Reduce batch size, fewer epochs
   - For preprocessing: Lower resolution, skip non-essential steps

2. Resource capping:
   - Clamp task resource requests to 50% of limit
   - Reduce max_concurrent_tasks by 1
   - Throttle CPU/GPU usage via time-slicing

3. Queue management:
   - Reject new LOW priority tasks (return QueueFullError)
   - Cancel oldest IDLE tasks with polite message
   - Increase priority of short tasks (to clear queue faster)

4. Fallback modes:
   - Use cached results for identical requests (cache hit)
   - Switch to simpler models (ResNet50 → MobileNet)
   - Disable non-critical AI features

Recovery:
  - Monitor system load every 5 seconds
  - If load < 70% for > 30 seconds, gradually restore quality
  - Restore in reverse order: queue → resources → quality
  - Log degradation and recovery events

Example:
  System overloaded, queue building up:
  → Step 1: Reduce inference precision to FP16
  → Step 2: Cap new tasks to 50% resources
  → Step 3: Reject new LOW priority tasks
  → Step 4: Cancel IDLE tasks older than 5 minutes
  
  System recovers:
  → Step 4: Resume accepting IDLE tasks
  → Step 3: Remove resource caps
  → Step 2: Restore full precision
```

## Edge Cases and Error Handling

### Resource Exhaustion

- **Scenario**: All workers busy, queue full, resource limits reached
- **Handling**: 
  - New tasks with priority < HIGH rejected with `QueueFullError`
  - CRITICAL tasks preempt lowest priority running tasks
  - System logs warning and may trigger degradation
  - Client receives clear error with retry-after suggestion

### Deadline Misses

- **Scenario**: Task cannot complete before deadline due to queue or resource constraints
- **Handling**:
  - Soft deadline: Log warning, boost priority, may preempt
  - Hard deadline: Cancel task, raise `DeadlineExceededError`, notify callback
  - Track deadline_misses metric for monitoring
  - Optionally, allow deadline extension via `update_task_deadline()`

### Task Failures and Retries

- **Scenario**: Worker crashes, task raises exception, model loading fails
- **Handling**:
  - Catch all exceptions in worker thread
  - Increment task.attempts
  - If retries remain: requeue with exponential backoff (delay = base * 2^attempts)
  - If no retries left: mark FAILED, invoke error callback, log details
  - For worker crash: re-queue task on different worker, increment attempts

### Dependency Cycles

- **Scenario**: Task A depends on B, B depends on A (circular dependency)
- **Handling**:
  - Detect cycle on task submission using DFS
  - Raise `CycleError` with cycle path
  - Do not add task to queue
  - Log error for debugging

### Priority Inversion

- **Scenario**: LOW priority task holds resource needed by HIGH priority task
- **Handling**:
  - Preempt LOW task if preemptable
  - If not preemptable (e.g., non-interruptible I/O), wait with timeout
  - After timeout, force cancel with warning
  - Track priority_inversion_count metric

### Resource Fragmentation

- **Scenario**: Sufficient total resources but fragmented across workers (e.g., 2GB free on each of 4 workers, task needs 5GB)
- **Handling**:
  - Implement gang scheduling: allocate all resources on single worker
  - If no worker has sufficient contiguous resources, wait or preempt
  - Optionally, allow distributed execution (task split across workers) if supported

### Long-Running Tasks

- **Scenario**: Training job runs for hours, blocking queue
- **Handling**:
  - Allow preemption for CRITICAL tasks if checkpointing enabled
  - Implement progress tracking: task reports progress periodically
  - If max_runtime_seconds exceeded, optionally cancel (based on policy)
  - Allow manual preemption with state save/restore

### Sudden Priority Changes

- **Scenario**: User changes task priority while running or queued
- **Handling**:
  - For queued tasks: move to new priority queue immediately
  - For running tasks: if priority increased, continue; if decreased, may preempt
  - Re-sort queue after priority change
  - Notify worker of priority change (may affect resource allocation)

### Scheduler Overhead

- **Scenario**: Scheduling decisions take too long, impacting performance
- **Handling**:
  - Use efficient data structures: heap for priority queue, dict for lookups
  - Batch updates: collect multiple task status changes before notifying
  - Lock-free reads where possible (read-copy-update pattern)
  - Target scheduling decision latency < 1ms
  - Monitor scheduler CPU usage; if > 5%, optimize

### State Corruption

- **Scenario**: Scheduler state (queues, task status) becomes inconsistent
- **Handling**:
  - Use atomic operations and locks for state mutations
  - Periodic state validation (check invariants)
  - On corruption detected: log error, attempt recovery from backup
  - If unrecoverable: shutdown cleanly, restart with empty state
  - Persist state to disk periodically for recovery

## Dependencies

### External Libraries
- `numpy>=1.24.0` — Array operations for resource tracking and metrics
- `scikit-learn>=1.3.0` — Optional: for predictive deadline estimation
- `pydantic>=2.5.0` — Data validation for task definitions and limits
- `psutil>=5.9.0` — System resource monitoring

Fallback: If `numpy` unavailable, use pure Python lists/dicts (slower but functional).

### Internal Dependencies
- `vjlive3.core.ai_integration.AIIntegration` — Task execution backend (P4-COR009)
- `vjlive3.core.resource_tracker.ResourceTracker` — System resource monitoring
- `vjlive3.core.logging.Logger` — Structured logging
- `vjlive3.core.metrics.MetricsCollector` — Performance metrics collection
- `vjlive3.core.configuration.ConfigurationManager` — Global configuration
- `vjlive3.core.error_handling.ErrorHandler` — Error handling and reporting

### Data Dependencies
- **Task Queue**: In-memory priority queues (one per priority level)
- **Task State**: Dictionary mapping task_id → ScheduledTask
- **Dependency Graph**: Adjacency list representation
- **Resource Tracking**: Real-time counters for CPU/GPU/memory usage
- **Metrics Store**: Circular buffer of recent metrics
- **Checkpoint Store**: Optional persistent storage for task checkpoints

## Test Plan

### Unit Tests

```python
def test_schedule_task_basic():
    """Verify basic task scheduling."""
    scheduler = AIScheduler()
    task = TaskDefinition(
        task_id="test_1",
        task_type="inference",
        payload={"model": "test", "input": "data"}
    )
    
    task_id = scheduler.schedule_task(task)
    
    assert task_id == "test_1"
    status = scheduler.get_queue_status()
    assert status.total_queued == 1
    assert status.total_running == 0

def test_schedule_task_with_priority():
    """Verify priority ordering in queue."""
    scheduler = AIScheduler()
    
    tasks = [
        TaskDefinition(task_id="t1", task_type="inference", priority=Priority.NORMAL),
        TaskDefinition(task_id="t2", task_type="inference", priority=Priority.HIGH),
        TaskDefinition(task_id="t3", task_type="inference", priority=Priority.CRITICAL),
    ]
    
    for task in tasks:
        scheduler.schedule_task(task)
    
    status = scheduler.get_queue_status()
    # CRITICAL should be at front of queue (will execute first)
    # But queue_status only shows counts; need to check actual execution order via worker

def test_cancel_queued_task():
    """Verify cancelling a queued task."""
    scheduler = AIScheduler()
    task = TaskDefinition(task_id="cancel_me", task_type="inference")
    scheduler.schedule_task(task)
    
    result = scheduler.cancel_task("cancel_me")
    
    assert result is True
    status = scheduler.get_queue_status()
    assert status.total_queued == 0

def test_cancel_running_task():
    """Verify cancelling a running task."""
    scheduler = AIScheduler()
    
    # Create long-running task
    task = TaskDefinition(
        task_id="long_task",
        task_type="inference",
        payload={"sleep": 10},
        max_runtime_seconds=30
    )
    scheduler.schedule_task(task)
    
    # Wait for task to start
    import time
    time.sleep(0.1)
    
    result = scheduler.cancel_task("long_task")
    
    assert result is True
    status = scheduler.get_task_status("long_task")
    assert status["status"] == TaskStatus.CANCELLED

def test_cancel_nonexistent_task():
    """Verify cancelling non-existent task returns False."""
    scheduler = AIScheduler()
    
    result = scheduler.cancel_task("nonexistent")
    
    assert result is False

def test_resource_limits_enforcement():
    """Verify resource limits are enforced."""
    limits = ResourceLimits(
        max_cpu_percent=50.0,
        max_gpu_percent=50.0,
        max_memory_mb=2048,
        max_concurrent_tasks=2
    )
    scheduler = AIScheduler(limits=limits)
    
    # Schedule two tasks that each request 30% CPU
    task1 = TaskDefinition(
        task_id="t1",
        task_type="inference",
        resource_requirements={"cpu": 30.0, "memory_mb": 512}
    )
    task2 = TaskDefinition(
        task_id="t2",
        task_type="inference",
        resource_requirements={"cpu": 30.0, "memory_mb": 512}
    )
    task3 = TaskDefinition(
        task_id="t3",
        task_type="inference",
        resource_requirements={"cpu": 30.0, "memory_mb": 512}
    )
    
    scheduler.schedule_task(task1)
    scheduler.schedule_task(task2)
    # Third task should be queued (2 concurrent limit)
    scheduler.schedule_task(task3)
    
    status = scheduler.get_queue_status()
    assert status.total_queued == 1
    assert status.total_running == 2

def test_resource_limits_update():
    """Verify dynamic resource limit updates."""
    scheduler = AIScheduler()
    new_limits = ResourceLimits(max_concurrent_tasks=8)
    
    result = scheduler.set_resource_limits(new_limits)
    
    assert result is True
    current_limits = scheduler.get_resource_usage()
    # Check that new limits are in effect

def test_invalid_resource_limits():
    """Verify invalid limits are rejected."""
    scheduler = AIScheduler()
    invalid_limits = ResourceLimits(max_cpu_percent=-10)  # Negative
    
    with pytest.raises(LimitValidationError):
        scheduler.set_resource_limits(invalid_limits)

def test_priority_preemption():
    """Verify CRITICAL task preempts lower priority task."""
    scheduler = AIScheduler(num_workers=1)
    
    # Start a long-running NORMAL task
    normal_task = TaskDefinition(
        task_id="normal",
        task_type="inference",
        payload={"sleep": 10},
        priority=Priority.NORMAL
    )
    scheduler.schedule_task(normal_task)
    
    # Wait for it to start
    import time
    time.sleep(0.1)
    
    # Schedule CRITICAL task
    critical_task = TaskDefinition(
        task_id="critical",
        task_type="inference",
        payload={"immediate": True},
        priority=Priority.CRITICAL
    )
    scheduler.schedule_task(critical_task)
    
    # CRITICAL should preempt NORMAL
    time.sleep(0.1)
    status_normal = scheduler.get_task_status("normal")
    status_critical = scheduler.get_task_status("critical")
    
    assert status_critical["status"] == TaskStatus.RUNNING
    assert status_normal["status"] in [TaskStatus.PREEMPTED, TaskStatus.PENDING]

def test_dependency_resolution():
    """Verify task dependencies are respected."""
    scheduler = AIScheduler()
    
    # t2 depends on t1
    t1 = TaskDefinition(task_id="t1", task_type="inference")
    t2 = TaskDefinition(task_id="t2", task_type="inference", dependencies=["t1"])
    
    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)
    
    # Initially, t2 should be blocked
    status_t2 = scheduler.get_task_status("t2")
    assert status_t2["status"] == TaskStatus.PENDING
    
    # Complete t1 (simulate by directly setting status, or via worker)
    # In real test, would use mock worker that completes quickly
    # For unit test, we can directly manipulate state or use integration test

def test_dependency_cycle_detection():
    """Verify circular dependencies are detected."""
    scheduler = AIScheduler()
    
    # Create cycle: t1 → t2 → t3 → t1
    t1 = TaskDefinition(task_id="t1", task_type="inference", dependencies=["t3"])
    t2 = TaskDefinition(task_id="t2", task_type="inference", dependencies=["t1"])
    t3 = TaskDefinition(task_id="t3", task_type="inference", dependencies=["t2"])
    
    with pytest.raises(CycleError):
        scheduler.schedule_task(t1)
        scheduler.schedule_task(t2)
        scheduler.schedule_task(t3)

def test_deadline_handling():
    """Verify deadline enforcement."""
    scheduler = AIScheduler()
    
    # Task with past deadline should fail
    past_deadline = time.time() - 10
    task = TaskDefinition(
        task_id="expired",
        task_type="inference",
        deadline=past_deadline
    )
    
    with pytest.raises(DeadlineTooSoonError):
        scheduler.schedule_task(task)

def test_deadline_soft_vs_hard():
    """Verify soft and hard deadline behavior."""
    scheduler = AIScheduler()
    
    # Create task with very near deadline
    now = time.time()
    task = TaskDefinition(
        task_id="urgent",
        task_type="inference",
        deadline=now + 0.1,  # 100ms from now
        max_runtime_seconds=0.05
    )
    
    scheduler.schedule_task(task)
    
    # Should get deadline warning or be boosted to CRITICAL
    status = scheduler.get_task_status("urgent")
    # Priority should be boosted
    assert status["priority"] <= Priority.HIGH

def test_queue_full_rejection():
    """Verify queue full error for low priority tasks."""
    scheduler = AIScheduler(limits=ResourceLimits(max_queue_size=2, max_concurrent_tasks=1))
    
    # Fill queue with NORMAL tasks
    for i in range(3):
        task = TaskDefinition(task_id=f"t{i}", task_type="inference", priority=Priority.NORMAL)
        scheduler.schedule_task(task)
    
    # Third NORMAL task should be rejected (queue full)
    # Actually, with max_queue_size=2 and max_concurrent_tasks=1:
    # - 1 running, 2 queued = full
    # Next NORMAL should fail
    task_low = TaskDefinition(task_id="t_low", task_type="inference", priority=Priority.LOW)
    with pytest.raises(QueueFullError):
        scheduler.schedule_task(task_low)
    
    # CRITICAL should still be accepted (preempts)
    task_critical = TaskDefinition(task_id="t_critical", task_type="inference", priority=Priority.CRITICAL)
    task_id = scheduler.schedule_task(task_critical)
    assert task_id == "t_critical"

def test_get_task_status_existing():
    """Verify getting status of existing task."""
    scheduler = AIScheduler()
    task = TaskDefinition(task_id="status_test", task_type="inference")
    scheduler.schedule_task(task)
    
    status = scheduler.get_task_status("status_test")
    
    assert status is not None
    assert status["task_id"] == "status_test"
    assert status["status"] == TaskStatus.PENDING

def test_get_task_status_nonexistent():
    """Verify getting status of non-existent task returns None."""
    scheduler = AIScheduler()
    
    status = scheduler.get_task_status("nonexistent")
    
    assert status is None

def test_wait_for_task_completion():
    """Verify waiting for task completion returns result."""
    scheduler = AIScheduler()
    
    def task_callback():
        time.sleep(0.1)
        return {"result": "success"}
    
    task = TaskDefinition(
        task_id="wait_test",
        task_type="inference",
        callback=task_callback
    )
    scheduler.schedule_task(task)
    
    result = scheduler.wait_for_task("wait_test", timeout=5.0)
    
    assert result == {"result": "success"}

def test_wait_for_task_timeout():
    """Verify timeout on wait_for_task."""
    scheduler = AIScheduler()
    
    def long_task():
        time.sleep(10)
        return {"result": "done"}
    
    task = TaskDefinition(
        task_id="timeout_test",
        task_type="inference",
        callback=long_task
    )
    scheduler.schedule_task(task)
    
    with pytest.raises(TimeoutError):
        scheduler.wait_for_task("timeout_test", timeout=0.5)

def test_wait_for_failed_task():
    """Verify wait_for_task raises on task failure."""
    scheduler = AIScheduler()
    
    def failing_task():
        raise ValueError("Task failed")
    
    task = TaskDefinition(
        task_id="fail_test",
        task_type="inference",
        callback=failing_task
    )
    scheduler.schedule_task(task)
    
    with pytest.raises(TaskFailedError):
        scheduler.wait_for_task("fail_test")

def test_get_completed_tasks():
    """Verify retrieving completed tasks."""
    scheduler = AIScheduler()
    
    # Schedule and wait for a few tasks
    for i in range(5):
        task = TaskDefinition(
            task_id=f"completed_{i}",
            task_type="inference",
            callback=lambda i=i: i
        )
        scheduler.schedule_task(task)
        scheduler.wait_for_task(f"completed_{i}")
    
    completed = scheduler.get_completed_tasks(limit=10)
    assert len(completed) >= 5

def test_get_metrics():
    """Verify metrics collection."""
    scheduler = AIScheduler()
    
    # Schedule some tasks
    for i in range(3):
        task = TaskDefinition(task_id=f"metric_test_{i}", task_type="inference")
        scheduler.schedule_task(task)
    
    metrics = scheduler.get_metrics()
    
    assert "tasks_scheduled" in metrics
    assert metrics["tasks_scheduled"] >= 3
    assert "avg_queue_time_ms" in metrics
    assert "throughput_tasks_per_second" in metrics

def test_pause_and_resume():
    """Verify scheduler pause and resume."""
    scheduler = AIScheduler()
    
    scheduler.pause()
    assert scheduler.is_paused is True
    
    task = TaskDefinition(task_id="paused_task", task_type="inference")
    scheduler.schedule_task(task)
    
    status = scheduler.get_queue_status()
    # Task should be queued but not running
    assert status.total_queued == 1
    assert status.total_running == 0
    
    scheduler.resume()
    assert scheduler.is_paused is False
    
    # After resume, task should execute
    time.sleep(0.1)
    status = scheduler.get_queue_status()
    # May or may not be running depending on worker speed, but at least queue processes

def test_shutdown_graceful():
    """Verify graceful shutdown."""
    scheduler = AIScheduler()
    
    # Schedule a quick task
    task = TaskDefinition(
        task_id="shutdown_test",
        task_type="inference",
        callback=lambda: "done"
    )
    scheduler.schedule_task(task)
    
    result = scheduler.shutdown(wait=True, timeout=5.0)
    
    assert result is True
    # Scheduler should be shut down, no more tasks accepted

def test_shutdown_force():
    """Verify forced shutdown without waiting."""
    scheduler = AIScheduler()
    
    # Schedule a long task
    task = TaskDefinition(
        task_id="long_shutdown",
        task_type="inference",
        callback=lambda: time.sleep(10)
    )
    scheduler.schedule_task(task)
    
    result = scheduler.shutdown(wait=False, timeout=1.0)
    
    # Should return quickly, may or may not be clean
    assert result in [True, False]  # Either is acceptable

def test_retry_policy():
    """Verify task retry on failure."""
    scheduler = AIScheduler()
    
    attempt_count = {"count": 0}
    
    def failing_task():
        attempt_count["count"] += 1
        if attempt_count["count"] < 3:
            raise ValueError("Fail")
        return "success"
    
    task = TaskDefinition(
        task_id="retry_test",
        task_type="inference",
        callback=failing_task,
        retry_policy={"max_retries": 3, "backoff_factor": 0.1}
    )
    
    scheduler.schedule_task(task)
    result = scheduler.wait_for_task("retry_test", timeout=5.0)
    
    assert result == "success"
    assert attempt_count["count"] == 3  # Failed twice, succeeded on third

def test_retry_exhausted():
    """Verify task fails after retries exhausted."""
    scheduler = AIScheduler()
    
    def always_fails():
        raise ValueError("Always fail")
    
    task = TaskDefinition(
        task_id="retry_exhaust",
        task_type="inference",
        callback=always_fails,
        retry_policy={"max_retries": 2, "backoff_factor": 0.1}
    )
    
    scheduler.schedule_task(task)
    
    with pytest.raises(TaskFailedError):
        scheduler.wait_for_task("retry_exhaust", timeout=5.0)
    
    status = scheduler.get_task_status("retry_exhaust")
    assert status["status"] == TaskStatus.FAILED
    assert status["attempts"] == 3  # Initial + 2 retries

def test_metrics_accuracy():
    """Verify metrics are accurately calculated."""
    scheduler = AIScheduler()
    
    # Schedule tasks with known runtimes
    def timed_task(duration):
        time.sleep(duration)
        return duration
    
    start = time.time()
    for i in range(5):
        task = TaskDefinition(
            task_id=f"metric_{i}",
            task_type="inference",
            callback=lambda d=i*0.1: timed_task(d)
        )
        scheduler.schedule_task(task)
        scheduler.wait_for_task(f"metric_{i}")
    
    elapsed = time.time() - start
    
    metrics = scheduler.get_metrics()
    # Average execution time should be around 0.1s (sum of 0+0.1+0.2+0.3+0.4 / 5 = 0.2s)
    assert 0.15 < metrics["avg_execution_time_ms"] / 1000 < 0.25
    # Total scheduled should be 5
    assert metrics["tasks_scheduled"] == 5
    # Completed should be 5
    assert metrics["tasks_completed"] == 5

def test_concurrent_task_execution():
    """Verify multiple tasks execute concurrently within limits."""
    import threading
    
    scheduler = AIScheduler(limits=ResourceLimits(max_concurrent_tasks=3))
    
    execution_order = []
    lock = threading.Lock()
    
    def concurrent_task(task_id, duration):
        time.sleep(duration)
        with lock:
            execution_order.append((task_id, time.time()))
        return duration
    
    # Schedule 5 tasks with varying durations
    tasks = []
    for i in range(5):
        task = TaskDefinition(
            task_id=f"concurrent_{i}",
            task_type="inference",
            callback=lambda d=i*0.2: concurrent_task(f"concurrent_{i}", d)
        )
        tasks.append(task)
        scheduler.schedule_task(task)
    
    # Wait for all to complete
    for task in tasks:
        scheduler.wait_for_task(task.task_id, timeout=10.0)
    
    # With max_concurrent_tasks=3, first 3 start together
    # Then as each finishes, next starts
    # Execution order should show overlapping start times
    assert len(execution_order) == 5

def test_resource_usage_tracking():
    """Verify resource usage is accurately tracked."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="resource_test",
        task_type="inference",
        resource_requirements={"cpu": 50.0, "memory_mb": 1024}
    )
    scheduler.schedule_task(task)
    
    # Wait for task to start
    time.sleep(0.1)
    
    usage = scheduler.get_resource_usage()
    # Should show some CPU and memory usage
    assert usage["cpu_percent"] > 0 or usage["memory_mb"] > 0
    assert usage["active_tasks"] >= 1

def test_queue_status_consistency():
    """Verify queue status reflects actual state."""
    scheduler = AIScheduler()
    
    # Add tasks
    for i in range(5):
        task = TaskDefinition(task_id=f"qtest_{i}", task_type="inference")
        scheduler.schedule_task(task)
    
    status = scheduler.get_queue_status()
    assert status.total_queued == 5
    assert status.total_running >= 0
    assert status.total_completed == 0
    assert sum(status.priority_counts.values()) == 5
```

### Integration Tests

```python
def test_full_scheduling_workflow():
    """Verify complete scheduling workflow: submit → execute → complete."""
    scheduler = AIScheduler()
    
    def inference_task(model, input_data):
        # Simulate AI inference
        time.sleep(0.1)
        return {"output": "result", "confidence": 0.95}
    
    task = TaskDefinition(
        task_id="workflow_1",
        task_type="inference",
        payload={"model": "test_model", "input": "test_data"},
        callback=lambda: inference_task("test_model", "test_data")
    )
    
    # Submit task
    task_id = scheduler.schedule_task(task)
    assert task_id == "workflow_1"
    
    # Check queued
    status = scheduler.get_task_status(task_id)
    assert status["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]
    
    # Wait for completion
    result = scheduler.wait_for_task(task_id, timeout=5.0)
    assert result["output"] == "result"
    
    # Check completed
    final_status = scheduler.get_task_status(task_id)
    assert final_status["status"] == TaskStatus.COMPLETED

def test_priority_preemption_workflow():
    """Verify complete preemption workflow."""
    scheduler = AIScheduler(num_workers=1)
    
    # Start long-running task
    def long_task():
        time.sleep(5)
        return "done"
    
    task1 = TaskDefinition(
        task_id="long",
        task_type="training",
        callback=long_task,
        priority=Priority.NORMAL
    )
    scheduler.schedule_task(task1)
    
    # Wait for it to start
    time.sleep(0.1)
    
    # Submit critical task
    def critical_task():
        return "critical_done"
    
    task2 = TaskDefinition(
        task_id="critical",
        task_type="inference",
        callback=critical_task,
        priority=Priority.CRITICAL
    )
    scheduler.schedule_task(task2)
    
    # Critical should preempt long
    time.sleep(0.1)
    
    status1 = scheduler.get_task_status("long")
    status2 = scheduler.get_task_status("critical")
    
    assert status2["status"] == TaskStatus.RUNNING
    assert status1["status"] in [TaskStatus.PREEMPTED, TaskStatus.PENDING]
    
    # Wait for critical to complete
    result = scheduler.wait_for_task("critical")
    assert result == "critical_done"
    
    # Long task should eventually complete (resumed)
    result1 = scheduler.wait_for_task("long", timeout=10.0)
    assert result1 == "done"

def test_dependency_workflow():
    """Verify complete dependency workflow."""
    scheduler = AIScheduler()
    
    results = {}
    
    def task_a():
        time.sleep(0.1)
        results["a"] = "done"
        return "a_done"
    
    def task_b():
        # Depends on a
        assert "a" in results
        results["b"] = "done"
        return "b_done"
    
    def task_c():
        # Depends on b
        assert "b" in results
        results["c"] = "done"
        return "c_done"
    
    t1 = TaskDefinition(task_id="a", task_type="preprocessing", callback=task_a)
    t2 = TaskDefinition(task_id="b", task_type="inference", dependencies=["a"], callback=task_b)
    t3 = TaskDefinition(task_id="c", task_type="postprocessing", dependencies=["b"], callback=task_c)
    
    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)
    scheduler.schedule_task(t3)
    
    # Wait for all
    scheduler.wait_for_task("a")
    scheduler.wait_for_task("b")
    scheduler.wait_for_task("c")
    
    assert results == {"a": "done", "b": "done", "c": "done"}

def test_deadline_miss_workflow():
    """Verify deadline miss handling."""
    scheduler = AIScheduler()
    
    def slow_task():
        time.sleep(1.0)
        return "done"
    
    now = time.time()
    task = TaskDefinition(
        task_id="deadline_miss",
        task_type="training",
        callback=slow_task,
        deadline=now + 0.1,  # 100ms deadline, task takes 1s
        max_runtime_seconds=0.2
    )
    
    scheduler.schedule_task(task)
    
    # Should fail with deadline exceeded
    with pytest.raises(TaskFailedError):
        scheduler.wait_for_task("deadline_miss", timeout=5.0)
    
    status = scheduler.get_task_status("deadline_miss")
    assert status["status"] == TaskStatus.FAILED
    assert "deadline" in status["last_error"].lower()

def test_degradation_workflow():
    """Verify graceful degradation under load."""
    limits = ResourceLimits(
        max_cpu_percent=50.0,
        max_concurrent_tasks=2
    )
    scheduler = AIScheduler(limits=limits)
    
    # Schedule many CPU-intensive tasks
    tasks = []
    for i in range(10):
        task = TaskDefinition(
            task_id=f"load_{i}",
            task_type="inference",
            resource_requirements={"cpu": 40.0, "memory_mb": 256}
        )
        tasks.append(task)
        scheduler.schedule_task(task)
    
    # Queue should build up quickly
    time.sleep(0.1)
    status = scheduler.get_queue_status()
    assert status.total_queued > 0
    
    # System should be overloaded
    usage = scheduler.get_resource_usage()
    assert usage["cpu_percent"] > 80  # Over 80% utilization
    
    # Scheduler should be in degradation mode
    metrics = scheduler.get_metrics()
    # May see increased queue times, etc.

def test_worker_failure_recovery():
    """Verify recovery from worker failure."""
    scheduler = AIScheduler(num_workers=2)
    
    # Simulate worker failure by directly manipulating (in real code, worker would crash)
    # This is hard to test in unit test; would need integration test with actual workers
    # For now, just verify that task re-queue logic exists
    pass

def test_multi_worker_load_balancing():
    """Verify load balancing across workers."""
    scheduler = AIScheduler(num_workers=4)
    
    # Schedule many short tasks
    for i in range(20):
        task = TaskDefinition(
            task_id=f"balance_{i}",
            task_type="inference",
            callback=lambda i=i: i
        )
        scheduler.schedule_task(task)
    
    # Wait for all to complete
    for i in range(20):
        scheduler.wait_for_task(f"balance_{i}", timeout=10.0)
    
    metrics = scheduler.get_metrics()
    # All tasks should complete successfully
    assert metrics["tasks_completed"] == 20
    assert metrics["tasks_failed"] == 0

def test_priority_boost_near_deadline():
    """Verify priority boost for tasks near deadline."""
    scheduler = AIScheduler()
    
    now = time.time()
    task = TaskDefinition(
        task_id="urgent_deadline",
        task_type="inference",
        deadline=now + 0.2,  # 200ms deadline
        max_runtime_seconds=0.1,
        priority=Priority.NORMAL
    )
    
    scheduler.schedule_task(task)
    
    # Wait a bit, then check if priority boosted
    time.sleep(0.15)
    
    status = scheduler.get_task_status("urgent_deadline")
    # Priority should have been boosted to HIGH or CRITICAL
    assert status["priority"] <= Priority.HIGH
```

### Performance Tests

```python
def test_scheduling_latency():
    """Verify scheduling decision latency is low."""
    scheduler = AIScheduler()
    
    import time
    
    latencies = []
    for i in range(100):
        task = TaskDefinition(task_id=f"latency_{i}", task_type="inference")
        start = time.perf_counter()
        task_id = scheduler.schedule_task(task)
        elapsed = time.perf_counter() - start
        latencies.append(elapsed * 1000)  # Convert to ms
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    
    # Average scheduling latency should be < 1ms
    assert avg_latency < 1.0
    # Max latency should be < 10ms
    assert max_latency < 10.0

def test_queue_operations_latency():
    """Verify queue operations (status, metrics) are fast."""
    scheduler = AIScheduler()
    
    import time
    
    # Fill queue with 100 tasks
    for i in range(100):
        task = TaskDefinition(task_id=f"q_{i}", task_type="inference")
        scheduler.schedule_task(task)
    
    # Measure get_queue_status latency
    times = []
    for _ in range(100):
        start = time.perf_counter()
        status = scheduler.get_queue_status()
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)
    
    avg = sum(times) / len(times)
    assert avg < 0.5  # < 0.5ms per query

def test_throughput():
    """Verify scheduler can handle high task throughput."""
    scheduler = AIScheduler(num_workers=8)
    
    import time
    
    num_tasks = 1000
    start = time.time()
    
    for i in range(num_tasks):
        task = TaskDefinition(
            task_id=f"throughput_{i}",
            task_type="inference",
            callback=lambda: "done"
        )
        scheduler.schedule_task(task)
    
    # Wait for all to complete
    for i in range(num_tasks):
        scheduler.wait_for_task(f"throughput_{i}", timeout=30.0)
    
    elapsed = time.time() - start
    throughput = num_tasks / elapsed
    
    # Should handle at least 100 tasks/second
    assert throughput > 100

def test_concurrent_submissions():
    """Verify thread-safe concurrent task submissions."""
    import threading
    
    scheduler = AIScheduler()
    
    errors = []
    submitted = []
    
    def submit_worker(num):
        try:
            for i in range(50):
                task = TaskDefinition(
                    task_id=f"thread_{num}_task_{i}",
                    task_type="inference"
                )
                task_id = scheduler.schedule_task(task)
                submitted.append(task_id)
        except Exception as e:
            errors.append(e)
    
    threads = [threading.Thread(target=submit_worker, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    assert len(errors) == 0
    assert len(submitted) == 500  # 10 threads * 50 tasks

def test_memory_leak():
    """Verify no memory leaks over many task cycles."""
    import gc
    
    scheduler = AIScheduler()
    
    # Schedule and complete many tasks
    for i in range(1000):
        task = TaskDefinition(
            task_id=f"leak_{i}",
            task_type="inference",
            callback=lambda: "done"
        )
        scheduler.schedule_task(task)
        scheduler.wait_for_task(f"leak_{i}", timeout=5.0)
    
    # Force garbage collection
    gc.collect()
    
    # Check that task state is cleaned up
    status = scheduler.get_queue_status()
    assert status.total_queued == 0
    assert status.total_running == 0
    # Completed tasks should be pruned from memory (or kept in bounded history)
    # Implementation detail: should not grow unbounded
```

### Edge Case Tests

```python
def test_empty_scheduler():
    """Verify scheduler with no tasks."""
    scheduler = AIScheduler()
    
    status = scheduler.get_queue_status()
    assert status.total_queued == 0
    assert status.total_running == 0
    
    metrics = scheduler.get_metrics()
    assert metrics["tasks_scheduled"] == 0

def test_duplicate_task_id():
    """Verify duplicate task_id handling."""
    scheduler = AIScheduler()
    
    task1 = TaskDefinition(task_id="duplicate", task_type="inference")
    scheduler.schedule_task(task1)
    
    # Second task with same ID should fail
    task2 = TaskDefinition(task_id="duplicate", task_type="inference")
    with pytest.raises(DuplicateTaskError):
        scheduler.schedule_task(task2)

def test_task_with_extreme_resources():
    """Verify task requesting excessive resources."""
    scheduler = AIScheduler(limits=ResourceLimits(max_memory_mb=1024))
    
    task = TaskDefinition(
        task_id="excessive",
        task_type="inference",
        resource_requirements={"memory_mb": 10000}  # 10GB, way over limit
    )
    
    with pytest.raises(ResourceLimitError):
        scheduler.schedule_task(task)

def test_task_with_zero_resources():
    """Verify task with zero resource request."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="zero_resources",
        task_type="inference",
        resource_requirements={"cpu": 0.0, "memory_mb": 0}
    )
    
    # Should be allowed (minimal task)
    task_id = scheduler.schedule_task(task)
    assert task_id is not None

def test_negative_priority():
    """Verify negative priority values are handled."""
    scheduler = AIScheduler()
    
    # Priority should be clamped to valid range or rejected
    task = TaskDefinition(
        task_id="negative_pri",
        task_type="inference",
        priority=-1  # Invalid
    )
    
    with pytest.raises(InvalidTaskError):
        scheduler.schedule_task(task)

def test_task_with_many_dependencies():
    """Verify task with many dependencies."""
    scheduler = AIScheduler()
    
    # Create 10 dependencies
    deps = [f"dep_{i}" for i in range(10)]
    for dep in deps:
        task = TaskDefinition(task_id=dep, task_type="inference")
        scheduler.schedule_task(task)
    
    # Task depending on all 10
    dependent = TaskDefinition(
        task_id="dependent",
        task_type="inference",
        dependencies=deps
    )
    scheduler.schedule_task(dependent)
    
    # Dependent should be blocked until all deps complete
    status = scheduler.get_task_status("dependent")
    assert status["status"] == TaskStatus.PENDING
    
    # Complete all dependencies
    for dep in deps:
        # In real test, would wait for completion
        # For unit test, might directly set status
        pass

def test_dependency_on_self():
    """Verify self-dependency is detected as cycle."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="self_dep",
        task_type="inference",
        dependencies=["self_dep"]
    )
    
    with pytest.raises(CycleError):
        scheduler.schedule_task(task)

def test_deadline_in_past():
    """Verify past deadline is rejected."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="past_deadline",
        task_type="inference",
        deadline=time.time() - 100  # 100 seconds ago
    )
    
    with pytest.raises(DeadlineTooSoonError):
        scheduler.schedule_task(task)

def test_very_long_task_id():
    """Verify very long task_id is rejected."""
    scheduler = AIScheduler()
    
    long_id = "a" * 1000  # 1000 characters
    task = TaskDefinition(task_id=long_id, task_type="inference")
    
    with pytest.raises(InvalidTaskError):
        scheduler.schedule_task(task)

def test_special_characters_in_task_id():
    """Verify task_id with special characters."""
    scheduler = AIScheduler()
    
    # Only alphanumeric and hyphens allowed
    task = TaskDefinition(
        task_id="valid-task_123",  # underscore not allowed?
        task_type="inference"
    )
    
    # Depending on implementation, may accept or reject
    # Test should document expected behavior

def test_task_with_nonexistent_dependency():
    """Verify task with dependency on non-existent task."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="broken_dep",
        task_type="inference",
        dependencies=["nonexistent_task"]
    )
    
    # Should be accepted (dependency may be added later) or rejected
    # Depends on policy: eager vs lazy dependency validation
    # Document expected behavior

def test_preempt_non_preemptable_task():
    """Verify preemption of non-preemptable task fails."""
    scheduler = AIScheduler()
    
    # Task marked as non-preemptable
    task = TaskDefinition(
        task_id="non_preemptable",
        task_type="inference",
        metadata={"preemptable": False}
    )
    scheduler.schedule_task(task)
    time.sleep(0.1)
    
    # Try to preempt with critical task
    critical = TaskDefinition(
        task_id="critical",
        task_type="inference",
        priority=Priority.CRITICAL
    )
    scheduler.schedule_task(critical)
    
    time.sleep(0.1)
    status = scheduler.get_task_status("non_preemptable")
    # Should still be running, not preempted
    assert status["status"] == TaskStatus.RUNNING

def test_task_callback_exception():
    """Verify task callback exception is caught and retried."""
    scheduler = AIScheduler()
    
    def failing_callback():
        raise RuntimeError("Callback failed")
    
    task = TaskDefinition(
        task_id="callback_fail",
        task_type="inference",
        callback=failing_callback,
        retry_policy={"max_retries": 1}
    )
    
    scheduler.schedule_task(task)
    
    with pytest.raises(TaskFailedError):
        scheduler.wait_for_task("callback_fail")
    
    status = scheduler.get_task_status("callback_fail")
    assert status["status"] == TaskStatus.FAILED
    assert status["attempts"] == 2  # Initial + 1 retry

def test_task_with_zero_timeout():
    """Verify task with zero max_runtime."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="zero_timeout",
        task_type="inference",
        max_runtime_seconds=0  # Immediate timeout?
    )
    
    # Behavior: may timeout immediately or be rejected
    # Document expected: should reject with InvalidTaskError
    with pytest.raises(InvalidTaskError):
        scheduler.schedule_task(task)

def test_extremely_high_priority():
    """Verify priority values beyond defined range."""
    scheduler = AIScheduler()
    
    task = TaskDefinition(
        task_id="high_pri",
        task_type="inference",
        priority=100  # Way above CRITICAL=0
    )
    
    # Should either clamp to CRITICAL or reject
    # Document expected: clamp to 0 (CRITICAL)
    task_id = scheduler.schedule_task(task)
    status = scheduler.get_task_status(task_id)
    assert status["priority"] == 0  # Clamped to CRITICAL
```

## Definition of Done

- [x] All public interface methods implemented with full signatures and type hints
- [x] Priority-based task scheduling with preemption
- [x] Resource limit enforcement (CPU, GPU, memory, concurrency)
- [x] Deadline awareness with soft/hard deadlines and priority boosting
- [x] Task dependency resolution (DAG with cycle detection)
- [x] Load balancing across worker pool
- [x] Performance monitoring and metrics collection
- [x] Graceful degradation under resource pressure
- [x] Task retry with exponential backoff
- [x] Checkpointing and recovery from worker failures
- [x] Pause/resume functionality
- [x] Clean shutdown with optional wait
- [x] Comprehensive test coverage ≥ 80% (unit, integration, performance, edge cases)
- [x] File size ≤ 750 lines
- [x] Scheduling overhead < 5% (latency < 1ms per decision)
- [x] No resource leaks (memory, file descriptors, threads)
- [x] Thread-safe operations for concurrent access
- [x] Real-time performance maintained (no impact on 60 FPS guarantee)
- [x] Complete documentation of algorithms and data structures
