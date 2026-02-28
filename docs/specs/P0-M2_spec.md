# Spec Template — Copy this file for every new task

**File naming:** `docs/specs/<task-id>_<module-name>.md`  
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P0-M2 — vjlive-switchboard

**Phase:** Phase 0 / P0  
**Assigned To:** Agent-7  
**Spec Written By:** Agent-7  
**Date:** 2025-04-05

---

## What This Module Does

The `vjlive-switchboard` module acts as a central communication and coordination hub for the VJLive agent ecosystem. It manages hardware lock acquisition, message queuing between agents, and secure comms routing to the Knowledge Server (MCP). By implementing a port from legacy VJlive2's switchboard logic into VJLive3, this module ensures consistent access control, prevents resource conflicts via locking mechanisms, and enables reliable inter-agent messaging through a prioritized queue system.

---

## What It Does NOT Do

- It does not perform actual hardware operations (e.g., GPIO control or sensor reading).  
- It does not implement AI reasoning or content generation.  
- It does not manage long-term memory storage or concept retrieval.  
- It does not replace the Knowledge Server (`server.py`) or its tools like `get_concept()` or `log_decision()`.  
- It does not handle user interface rendering or frontend display.

---

## Public Interface

```python
class vjlive_switchboard:
    def __init__(self, config: dict) -> None:
        """
        Initializes the switchboard with configuration.
        
        Args:
            config: Dictionary containing server address, lock paths, queue settings, and comms endpoints.
        """
    
    def acquire_lock(self, resource_name: str) -> bool:
        """
        Attempts to acquire a hardware or resource lock.
        
        Args:
            resource_name: Name of the resource (e.g., "display_01", "motor_a").
            
        Returns:
            True if lock acquired; False otherwise.
        """
    
    def release_lock(self, resource_name: str) -> None:
        """
        Releases a previously acquired lock.
        
        Args:
            resource_name: Name of the resource to release.
        """
    
    def enqueue_message(self, sender: str, message: dict) -> bool:
        """
        Adds a message to the internal queue for delivery.
        
        Args:
            sender: Agent ID or name sending the message.
            message: Dictionary containing payload and metadata (e.g., priority).
            
        Returns:
            True if enqueued successfully; False if queue is full or rejected.
        """
    
    def dequeue_message(self) -> dict | None:
        """
        Retrieves the next message from the queue based on priority.
        
        Returns:
            Message dictionary, or None if no messages available.
        """
    
    def broadcast_to_agents(self, topic: str, payload: dict) -> bool:
        """
        Sends a message to all agents subscribed to a given topic.
        
        Args:
            topic: Topic name (e.g., "hardware_update", "task_assigned").
            payload: Message content.
            
        Returns:
            True if broadcast successful; False on failure or no subscribers.
        """
    
    def stop(self) -> None:
        """
        Gracefully shuts down the switchboard, releasing all locks and closing queues.
        """
```

---

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `config` | `dict` | Configuration for server endpoints, lock paths, queue size, comms settings | Must include: `server_url`, `lock_dir`, `queue_max_size`, `comms_timeout_sec` |
| `resource_name` | `str` | Identifier of hardware or shared resource to lock | Must be non-empty; must match known pattern (e.g., "display_01", "sensor_b") |
| `sender` | `str` | Agent ID sending a message | Must be valid agent name; length ≤ 32 characters |
| `message` | `dict` | Payload with keys: `content`, `priority`, `timestamp` | Priority must be one of: `"low"`, `"medium"`, `"high"` |
| `topic` | `str` | Topic to broadcast to (e.g., "task_update") | Must not exceed 64 characters; must match registered topic list |
| `payload` | `dict` | Message content to deliver | No schema enforced; must be serializable |

---

## Edge Cases and Error Handling

- What happens if hardware is missing? → Use the **NullDevice pattern**: return `False` on `acquire_lock()` and log warning in `COMMS/LOGS.md`.  
- What happens on bad input? → Raise `ValueError` with descriptive message (e.g., "Invalid resource name: 'invalid'") if `resource_name` is malformed or not in allowed list.  
- What happens when queue is full? → Return `False` from `enqueue_message()` and log a warning to `COMMS/QUEUE_STATUS.md`.  
- What happens on broadcast with no subscribers? → Return `False`, log event, but do not crash.  
- What is the cleanup path? → On `stop()`, release all locks via `release_lock()` for each held resource, close message queue, and write shutdown status to `COMMS/SWITCHBOARD_STATUS.md`.

---

## Dependencies

- External libraries needed (and what happens if they are missing):  
  - `queue` — used for inter-agent messaging — fallback: in-memory list with LIFO behavior  
  - `threading` — used for concurrent message handling — fallback: sequential processing via blocking calls  
- Internal modules this depends on:  
  - `vjlive3.knowledge_server.tools.get_concept` — to validate concept availability during task assignment  
  - `vjlive3.comms.subscriber_manager` — to manage agent subscriptions and topic routing  

---

## Test Plan

| Test Name | What It Verifies |
|-----------|-----------------|
| `test_init_no_config` | Module starts without crashing if config is missing or malformed |
| `test_acquire_lock_success` | Lock can be acquired for a valid resource name |
| `test_acquire_lock_conflict` | Lock fails to acquire when already held by another agent |
| `test_release_lock_missing` | Attempting to release an unacquired lock does not crash |
| `test_enqueue_message_full_queue` | Queue rejects message when full and returns False |
| `test_dequeue_message_empty` | Returns None when no messages in queue |
| `test_broadcast_to_no_subscribers` | Broadcast fails gracefully with no subscribers |
| `test_stop_cleanup` | All locks are released and queues closed cleanly on stop() |

**Minimum coverage:** 80% before task is marked done.

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)  
- [ ] All tests listed above pass  
- [ ] No file over 750 lines  
- [ ] No stubs in code  
- [ ] Verification checkpoint box checked  
- [ ] Git commit with `[Phase-0] P0-M2: vjlive-switchboard module for lock + comms + queue` message  
- [ ] BOARD.md updated with new switchboard-related task references  
- [ ] Lock released  
- [ ] AGENT_SYNC.md handoff note written  
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 0, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

---

## LEGACY CODE REFERENCES

### vjlive2/MCP_SETUP_GUIDE.md (L1-20)
```python
# MCP SETUP GUIDE: CONNECTING THE HIVEMIND

To get **Roo** and **Copilot** working on the VJLive Knowledge Server, follow these steps. This server acts as the "Hippocampus" (Long-Term Memory) for the project.

## 1. The Server Entry Point
The Knowledge Server is located at:
`tools/knowledge_server/src/server.py`
```

### vjlive2/MCP_SETUP_GUIDE.md (L17-36)
```python
      "args": [
        "/home/happy/Desktop/claude projects/VJlive-2/tools/knowledge_server/src/server.py"
      ]
    }
  }
}
```

### vjlive2/MCP_SETUP_GUIDE.md (L33-40)
```python
-   `search_concepts(query)`: Find relevant architectural rules.
-   `log_decision(context)`: Record architectural decisions to `COMMS/DECISIONS.md`.
```

### vjlive2/MCP_SETUP_GUIDE.md (L37-40)
```python
When a new agent joins, instruct them to:
1.  Call `get_concept("prime_directive")` (if available) or `read_file("BOARD.md")`.
2.  Claim a task from `BOARD.md`.
3.  Adhere to the **Plaits Protocol** (`tools/knowledge_server/concepts/plaits_protocol.md`).
```

### vjlive2/MCP_SETUP_GUIDE.md (L38-40)
```python
1.  Call `get_concept("prime_directive")` (if available) or `read_file("BOARD.md")`.
2.  Claim a task from `BOARD.md`.
3.  Adhere to the **Plaits Protocol** (`tools/knowledge_server/concepts/plaits_protocol.md`).
```

### vjlive