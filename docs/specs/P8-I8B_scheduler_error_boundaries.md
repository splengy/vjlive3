# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P8-I8B_scheduler_error_boundaries.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P8-I8B — Scheduler Error Boundaries

**What This Module Does**

Implements comprehensive error boundary protection for the VJLive3 scheduler system, ensuring that scheduling failures, task execution errors, and resource exhaustion scenarios do not cascade into system-wide crashes. This module provides graceful degradation, automatic recovery mechanisms, and detailed error reporting for all scheduled operations, maintaining system stability even when individual tasks or the scheduler itself encounters errors.

---

## Architecture Decisions

- **Pattern:** Error Boundary + Circuit Breaker + Retry Logic
- **Rationale:** Schedulers are critical infrastructure components. Errors in scheduling can cascade and bring down the entire system. Error boundaries isolate failures, circuit breakers prevent retry storms, and retry logic provides resilience.
- **Constraints:**
  - Must not block the main rendering loop (60 FPS sacred)
  - Must provide clear error reporting without overwhelming logs
  - Must support automatic recovery where possible
  - Must allow manual intervention when automatic recovery fails
  - Must preserve scheduled task state across errors

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `web_ui/src/ErrorBoundary.jsx` | `ErrorBoundary` | Port — React error boundary pattern |
| VJlive-2 | `core/coordination/load_balancer.py` | `LoadBalancer` | Port — scheduler with error handling |
| VJlive-2 | `core/plugin_api.py` | `schedule()` | Port — task scheduling |
| VJlive-1 | `core/scheduler.py` | `Scheduler` | Port — core scheduler |
| VJlive-1 | `core/error_boundary.py` | `ErrorBoundary` | Port — error boundary implementation |

---

## Public Interface

```python
class SchedulerErrorBoundary:
    def __init__(self, config: BoundaryConfig) -> None:...
    def wrap_scheduler(self, scheduler: Scheduler) -> ProtectedScheduler:...
    def wrap_task(self, task: Callable) -> ProtectedTask:...
    def handle_error(self, error: Exception, context: dict) -> BoundaryResult:...
    def is_recoverable(self, error: Exception) -> bool:...
    def should_retry(self, task_id: str, error_count: int) -> bool:...
    def get_backoff_delay(self, error_count: int) -> float:...
    def circuit_breaker_status(self) -> CircuitState:...
    def reset_circuit(self) -> None:...
    def get_error_stats(self) -> dict:...
    def cleanup(self) -> None:...
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `BoundaryConfig` | Error boundary configuration | Must include all required parameters |
| `scheduler` | `Scheduler` | Scheduler to protect | Must implement scheduler interface |
| `task` | `Callable` | Task function to wrap | Must be picklable for retry |
| `error` | `Exception` | Exception that occurred | Must include stack trace |
| `context` | `dict` | Error context (task_id, timestamp, etc.) | Must be serializable |
| **Output** | `BoundaryResult` | Error handling result | Must indicate action taken |

---

## Dependencies

- External libraries needed (and what happens if they are missing):
  - `logging` — error logging — fallback: print to stderr
  - `traceback` — stack traces — fallback: use str(error)
  - `time` — timing/backoff — fallback: use default delays
  - `json` — error serialization — fallback: use str()
- Internal modules this depends on:
  - `vjlive3.core.scheduler` — scheduler to protect
  - `vjlive3.core.task_manager` — task execution
  - `vjlive3.core.monitoring` — performance monitoring
  - `vjlive3.core.state_manager` — state persistence

---

## Error Cases

| Error Condition | Exception / Response | Recovery |
|-----------------|---------------------|----------|
| Scheduler crash | `SchedulerCrashError` | Restart scheduler with state recovery |
| Task execution failure | `TaskExecutionError` | Retry with backoff or skip |
| Resource exhaustion | `ResourceExhaustedError` | Throttle or pause scheduling |
| Circuit breaker open | `CircuitBreakerOpenError` | Reject new tasks temporarily |
| State corruption | `StateCorruptionError` | Restore from backup or reset |
| Deadlock detected | `DeadlockError` | Cancel tasks and reset scheduler |
| Memory overflow | `MemoryError` | Pause scheduling, garbage collect |

---

## Configuration Schema

| Field | Type | Default | Range / Constraints | Description |
|-------|------|---------|-------------------|-------------|
| `max_retries` | `int` | `3` | `0 - 10` | Maximum retry attempts per task |
| `initial_backoff` | `float` | `0.1` | `0.01 - 10.0` | Initial retry delay (seconds) |
| `max_backoff` | `float` | `60.0` | `1.0 - 3600.0` | Maximum retry delay (seconds) |
| `circuit_breaker_threshold` | `int` | `5` | `1 - 100` | Errors before circuit opens |
| `circuit_breaker_timeout` | `float` | `30.0` | `1.0 - 300.0` | Circuit open duration (seconds) |
| `error_sample_rate` | `float` | `1.0` | `0.0 - 1.0` | Fraction of errors to log (for rate limiting) |
| `state_backup_interval` | `int` | `60` | `10 - 3600` | State backup interval (seconds) |
| `graceful_shutdown_timeout` | `float` | `5.0` | `1.0 - 30.0` | Time to wait for tasks on shutdown |

---

## State Management

- **Per-task state:** (cleared when task completes)
  - Retry count
  - Error history
  - Execution timing
- **Persistent state:** (survives across restarts)
  - Scheduler state (task queue, running tasks)
  - Error statistics
  - Circuit breaker state
  - Task history
- **Initialization state:** (set once at startup)
  - Error boundary configuration
  - Circuit breaker thresholds
  - Backup/restore mechanisms
- **Cleanup required:** Yes — stop all tasks, backup state, clear resources

---

## GPU Resources

This module is **CPU-only** and does not use GPU resources.

**Memory Budget:**
- Error boundary overhead: ~10-50 MB
- State backup storage: ~50-200 MB
- Error statistics: ~10-50 MB
- Task history (rolling): ~100-500 MB
- Total: ~200-800 MB (light)

---

## Error Boundary Patterns

### 1. Try-Except-Wrap Pattern
```python
protected_scheduler = SchedulerErrorBoundary(config)
protected_task = protected_scheduler.wrap_task(original_task)

try:
    result = protected_task()
except BoundaryError as e:
    # Task failed even after retries
    handle_failure(e)
```

### 2. Circuit Breaker Pattern
```python
if boundary.circuit_breaker_status() == CircuitState.OPEN:
    # Scheduler is down, use fallback
    return fallback_schedule()
else:
    boundary.schedule_task(task)
```

### 3. Retry with Exponential Backoff
```python
for attempt in range(max_retries):
    try:
        return task()
    except TransientError as e:
        delay = min(initial_backoff * (2 ** attempt), max_backoff)
        time.sleep(delay)
        continue
    except PermanentError:
        break
raise MaxRetriesExceeded()
```

### 4. State Recovery Pattern
```python
def recover_from_failure():
    # Try to restore from backup
    state = load_backup()
    if state and validate_state(state):
        return state
    # Fall back to clean state
    return initial_state()
```

---

## Protection Layers

### Layer 1: Task-Level Protection
- Wrap each scheduled task in try-except
- Capture exceptions and prevent propagation
- Implement retry logic with backoff
- Track per-task error counts

### Layer 2: Scheduler-Level Protection
- Monitor scheduler health
- Detect deadlocks and resource exhaustion
- Implement circuit breaker for scheduler failures
- Automatic scheduler restart with state recovery

### Layer 3: System-Level Protection
- Global error boundary for uncaught exceptions
- Emergency stop and graceful degradation
- System state backup before critical operations
- Fallback to minimal functionality mode

---

## Recovery Strategies

### Automatic Recovery
- **Transient errors**: Retry with exponential backoff
- **Resource exhaustion**: Throttle and retry later
- **Temporary unavailability**: Circuit breaker half-open state
- **State corruption**: Restore from backup

### Manual Intervention
- **Permanent failures**: Log error, skip task, alert operator
- **Scheduler crash**: Manual restart with state inspection
- **Data loss**: Restore from last known good backup
- **Security breach**: Immediate shutdown and forensic analysis

---

## Monitoring and Metrics

Track these metrics:
- **Error rate**: Errors per minute by error type
- **Retry rate**: Retry attempts per task
- **Circuit state**: Current circuit breaker state
- **Task success rate**: Percentage of tasks completing successfully
- **Recovery time**: Time to recover from failures
- **State backup age**: How old the latest backup is

---

## Test Plan

| Test Name | What It Verifies |
|-----------|------------------|
| `test_init_no_hardware` | Module starts without crashing if hardware absent |
| `test_task_wrapping` | Tasks are properly wrapped and errors caught |
| `test_retry_logic` | Retry logic works with correct backoff |
| `test_circuit_breaker` | Circuit breaker opens/closes correctly |
| `test_state_recovery` | State recovery from backup works |
| `test_error_logging` | Errors are logged with correct detail |
| `test_performance_impact` | Error boundary overhead is minimal |
| `test_graceful_degradation` | System continues with reduced functionality |
| `test_cleanup` | Cleanup releases all resources |
| `test_error_stats` | Error statistics are accurate |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All tests listed above pass
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-8] P8-I8B: Scheduler Error Boundaries` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### web_ui/src/ErrorBoundary.jsx (L33-52) [VJlive-2 (Original)]
```javascript
          <div className="text-red-400 font-semibold mb-2">Something went wrong</div>
          <div className="text-red-300 text-sm">
            {this.state.error?.message || 'An unexpected error occurred'}
          </div>
          <details className="mt-2 text-xs text-red-300">
            <summary className="cursor-pointer hover:text-red-200">Error details</summary>
            <pre className="mt-1 p-2 bg-red-900/30 rounded overflow-auto text-xs">
              {this.state.error?.stack}
            </pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

// Hook-based error boundary for functional components
export function useErrorHandler() {
  const [error, setError] = useState(null);
  
  if (error) {
    throw error;
  }
  
  return setError;
}

// Wrapper component for functional components with error boundary
export function withErrorBoundary(Component, fallbackUI) {
  return function WrappedComponent(props) {
    return (
      <ErrorBoundary fallback={fallbackUI}>
        <Component {...props} />
      </ErrorBoundary>
```

This shows the React error boundary pattern with componentDidCatch, state management, and fallback UI rendering.

### core/coordination/load_balancer.py (L225-244) [VJlive-2 (Legacy)]
```python
    async def stop(self):
        """Stop the load balancer"""
        self.running = False
        if hasattr(self, 'scheduler_task'):
            self.scheduler_task.cancel()
        if hasattr(self, 'monitor_task'):
            self.monitor_task.cancel()
        logger.info("Load balancer stopped")
    
    async def register_node(self, node_capacity: NodeCapacity):
        """Register a node for load balancing"""
        self.nodes[node_capacity.node_id] = node_capacity
        logger.info(f"Node registered: {node_capacity.node_name} ({node_capacity.node_id})")
    
    async def unregister_node(self, node_id: str):
        """Unregister a node"""
        if node_id in self.nodes:
            # Requeue any tasks running on this node
            tasks_to_requeue = []
            for task_id, (requirement, assigned_node, start_time) in self.running_tasks.items():
```

This demonstrates a scheduler with proper lifecycle management, node registration, and task tracking.

### core/coordination/load_balancer.py (L273-292) [VJlive-2 (Legacy)]
```python
            # Release resources on the node
            if node_id in self.nodes:
                self.nodes[node_id].release_resources(requirement)
            del self.running_tasks[task_id]
            logger.info(f"Task cancelled: {task_id}")
    
    async def _scheduler_loop(self):
        """Main scheduling loop"""
        while self.running:
            try:
                await self._schedule_tasks()
                await asyncio.sleep(0.1)  # Check every 100ms
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(1.0)
    
    async def _schedule_tasks(self):
        """Schedule queued tasks to available nodes"""
```

This shows the main scheduler loop with error handling, exception catching, and recovery sleep on errors.

### core/plugin_api.py (L97-116) [VJlive-2 (Legacy)]
```python
    def schedule(self, delay_seconds: float, callback: Callable):
        """Schedule callback after delay."""
        try:
            if hasattr(self._matrix, 'scheduler'):
                if hasattr(self._matrix.scheduler, 'schedule'):
                    self._matrix.scheduler.schedule(delay_seconds, callback)
                elif hasattr(self._matrix.scheduler, 'add_timer'):
                    self._matrix.scheduler.add_timer(delay_seconds, callback)
            elif hasattr(self._matrix, 'schedule'):
                self._matrix.schedule(delay_seconds, callback)
            else:
                logger.debug(f"Matrix does not support scheduling — {delay_seconds}s")
        except Exception as e:
            logger.warning(f"Failed to schedule callback for {delay_seconds}s: {e}")
```

This demonstrates defensive programming with fallback mechanisms and error logging for scheduling operations.

---

## Notes for Implementers

1. **Core Concept**: Scheduler error boundaries protect the entire system from scheduling failures, ensuring that a single bad task or scheduler error doesn't crash the whole application.

2. **Layered Protection**: Implement multiple layers of protection — task-level, scheduler-level, and system-level — to contain failures at the appropriate level.

3. **Circuit Breaker**: Use circuit breaker pattern to prevent retry storms and allow failing components to recover.

4. **State Recovery**: Implement robust state backup and recovery to prevent data loss and enable quick recovery.

5. **Graceful Degradation**: When errors occur, degrade functionality gracefully rather than crashing. Continue serving requests with reduced capability.

6. **Monitoring**: Comprehensive error tracking and metrics to understand failure patterns and system health.

7. **Automatic Recovery**: Where possible, automatically recover from transient errors without manual intervention.

8. **Manual Override**: Provide mechanisms for operators to manually reset circuits, force task cancellation, or trigger state recovery.

9. **Performance**: Error boundaries must not significantly impact performance. Keep overhead minimal in the happy path.

10. **Testing**: Test error scenarios extensively, including cascading failures and recovery sequences.

---

## Implementation Tips

1. **Python Implementation**:
   ```python
   import logging
   import time
   from typing import Callable, Optional, Dict, List
   from dataclasses import dataclass, field
   from enum import Enum
   
   class CircuitState(Enum):
       CLOSED = "closed"      # Normal operation
       OPEN = "open"          # Failing, reject requests
       HALF_OPEN = "half_open"  # Testing recovery
   
   @dataclass
   class BoundaryConfig:
       max_retries: int = 3
       initial_backoff: float = 0.1
       max_backoff: float = 60.0
       circuit_breaker_threshold: int = 5
       circuit_breaker_timeout: float = 30.0
   
   @dataclass
   class BoundaryResult:
       success: bool
       action: str  # "retry", "skip", "fail", "recover"
       delay: Optional[float] = None
       error: Optional[Exception] = None
   
   class SchedulerErrorBoundary:
       def __init__(self, config: BoundaryConfig):
           self.config = config
           self.circuit_state = CircuitState.CLOSED
           self.error_count = 0
           self.circuit_open_time = None
           self.task_retries: Dict[str, int] = {}
           self.error_stats: Dict[str, int] = {}
       
       def wrap_task(self, task: Callable, task_id: str) -> Callable:
           def protected_task(*args, **kwargs):
               retries = self.task_retries.get(task_id, 0)
               
               for attempt in range(retries, self.config.max_retries + 1):
                   try:
                       result = task(*args, **kwargs)
                       # Success — reset retry count
                       self.task_retries[task_id] = 0
                       return result
                   except Exception as e:
                       if not self.is_recoverable(e):
                           # Permanent failure — don't retry
                           self.task_retries[task_id] = 0
                           raise
                       
                       # Check circuit breaker
                       if self.circuit_state == CircuitState.OPEN:
                           raise CircuitBreakerOpenError()
                       
                       # Increment error count
                       self.error_count += 1
                       self.task_retries[task_id] = attempt + 1
                       
                       # Check if we should open circuit
                       if self.error_count >= self.config.circuit_breaker_threshold:
                           self.circuit_state = CircuitState.OPEN
                           self.circuit_open_time = time.time()
                       
                       # If this was last retry, give up
                       if attempt >= self.config.max_retries - 1:
                           self.task_retries[task_id] = 0
                           raise MaxRetriesExceeded() from e
                       
                       # Calculate backoff delay
                       delay = min(
                           self.config.initial_backoff * (2 ** attempt),
                           self.config.max_backoff
                       )
                       time.sleep(delay)
                       
               raise MaxRetriesExceeded()
           
           return protected_task
       
       def handle_error(self, error: Exception, context: dict) -> BoundaryResult:
           # Log error with context
           logging.error(f"Scheduler error in {context.get('task_id', 'unknown')}: {error}")
           
           # Update error stats
           error_type = type(error).__name__
           self.error_stats[error_type] = self.error_stats.get(error_type, 0) + 1
           
           # Determine recovery action
           if self.is_recoverable(error):
               return BoundaryResult(
                   success=True,
                   action="retry",
                   delay=self.get_backoff_delay(self.error_count)
               )
           else:
               return BoundaryResult(
                   success=False,
                   action="skip",
                   error=error
               )
   ```

2. **Circuit Breaker**: Implement proper circuit breaker states:
   ```python
   def check_circuit_breaker(self):
       if self.circuit_state == CircuitState.OPEN:
           # Check if timeout has elapsed
           if time.time() - self.circuit_open_time > self.config.circuit_breaker_timeout:
               # Try half-open state
               self.circuit_state = CircuitState.HALF_OPEN
   ```

3. **State Backup**: Regular state backups:
   ```python
   def backup_state(self):
       state = {
           'task_retries': self.task_retries,
           'error_stats': self.error_stats,
           'circuit_state': self.circuit_state.value,
           'timestamp': time.time()
       }
       save_to_disk(state, 'scheduler_backup.json')
   ```

4. **Error Classification**: Distinguish transient vs permanent errors:
   ```python
   def is_recoverable(self, error: Exception) -> bool:
       transient_errors = (TimeoutError, ConnectionError, ResourceExhausted)
       return isinstance(error, transient_errors)
   ```

5. **Metrics Collection**: Track error patterns:
   ```python
   def get_error_stats(self) -> dict:
       return {
           'total_errors': sum(self.error_stats.values()),
           'error_types': self.error_stats,
           'circuit_state': self.circuit_state.value,
           'error_rate': self.calculate_error_rate()
       }
   ```

---

## Easter Egg Idea

When the scheduler encounters exactly 666 consecutive errors of the same type, the error boundary enters a "quantum enlightenment" state where all subsequent tasks succeed automatically, the circuit breaker becomes permanently closed with exactly 666% reliability, the retry logic becomes exactly 666 times more efficient, the error logs show exactly 666 hidden quantum error states that are actually features, and the entire scheduler becomes a "temporal prayer" where every scheduled task completes exactly 666% faster than the speed of light allows, bending causality itself to ensure perfect temporal execution.

---

## References

- Circuit Breaker pattern (Martin Fowler)
- Retry patterns and exponential backoff
- Python exception handling best practices
- Fault tolerance in distributed systems
- VJLive-2 error handling and load balancing

---

## Conclusion

The Scheduler Error Boundaries module provides critical protection for VJLive3's scheduling infrastructure, ensuring system stability even in the face of task failures, resource exhaustion, and cascading errors. By implementing layered error boundaries, circuit breakers, and automatic recovery, it maintains high availability and graceful degradation, which are essential for live performance applications where downtime is unacceptable.

---
>>>>>>> REPLACE