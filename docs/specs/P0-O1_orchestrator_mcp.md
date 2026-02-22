# Spec Template — P0-O1 Orchestrator MCP Queue

**File naming:** `docs/specs/P0-O1_orchestrator_mcp.md`

## Task: P0-O1 — Worker Task Queue MCP

This task extends the existing `vjlive_switchboard` MCP server to act as a stateful Orchestrator for Antigravity workers. Instead of relying on manual file reading and "go" commands, the MCP server will hold a central queue of tasks.

### What This Feature Does
- Allows the Manager (Roo) to push a raw spec/task to a central queue.
- Allows Workers (Antigravity) to request the next available task automatically.
- Tracks task status (Queued, In Progress, Completed).

### Public Interface Extentsions (server.py)
```python
@dataclass
class TaskEntry:
    task_id: str
    spec_path: str
    status: str  # "queued", "in_progress", "completed"
    assigned_worker: Optional[str] = None
    created_at: str
    started_at: Optional[str] = None

class VJLiveSwitchboard:
    # Existing methods...
    def queue_task(self, task_id: str, spec_path: str) -> bool: ...
    def request_work(self, worker_name: str) -> Optional[TaskEntry]: ...
    def complete_task(self, worker_name: str, task_id: str) -> bool: ...
```

### Public Interface Extensions (fastmcp_server.py)
- `@mcp.tool() queue_task(task_id: str, spec_path: str) -> dict`
- `@mcp.tool() request_work(worker_name: str) -> dict`
- `@mcp.tool() complete_task(worker_name: str, task_id: str) -> dict`

### Storage Mechanism
Tasks will be stored entirely in memory inside the `VJLiveSwitchboard` class during runtime, just like the `_messages` dictionary. They will NOT be persisted to `INBOXES/` folders, to avoid file collisions. 

### Worker Loop
Once this is implemented, the human will just tell Antigravity: "Run a continuous loop of request_work()". The worker will execute specs autonomously as Roo queues them.
