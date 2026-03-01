# P0-A1 — Phase 0 App Window (FPS · Memory · Agents)

## What This Module Does
Provides the main application window for Phase 0 operations, displaying real-time system metrics including FPS, memory usage, and agent status. Serves as the primary user interface for monitoring and controlling the VJLive3 system during initial deployment.

## What It Does NOT Do
- Does not implement video rendering (that's the render engine)
- Does not handle plugin execution
- Does not manage agent coordination (that's the switchboard)
- Does not provide full VJ performance interface (that's Phase 1+)

## Public Interface
```python
class Phase0AppWindow:
    def __init__(self):
        """Initialize Phase 0 monitoring window"""
        pass
    
    def update_fps(self, fps: float) -> None:
        """Update current FPS display"""
        pass
    
    def update_memory(self, used_mb: float, total_mb: float) -> None:
        """Update memory usage display"""
        pass
    
    def update_agent_status(self, agent_id: str, status: str, 
                           details: dict = None) -> None:
        """Update individual agent status"""
        pass
    
    def get_system_health(self) -> dict:
        """Get overall system health metrics"""
        pass
    
    def set_alert_callback(self, callback) -> None:
        """Set callback for system alerts"""
        pass
    
    def request_agent_action(self, agent_id: str, action: str, 
                           params: dict = None) -> bool:
        """Request action from specific agent"""
        pass
    
    def get_agent_list(self) -> list:
        """Get list of all registered agents"""
        pass
```

## Inputs and Outputs
- **Inputs**: FPS updates, memory metrics, agent status changes, user actions
- **Outputs**: System health reports, agent commands, alert notifications

## Edge Cases
- Agent disconnection during operation
- Memory spikes causing UI lag
- FPS drops below threshold
- Multiple simultaneous agent failures
- Display refresh rate mismatches
- Resource exhaustion scenarios

## Dependencies
- Render Engine (P1-R5) for FPS metrics
- Memory monitoring system
- Agent Sync (P0-G3) for agent status
- Switchboard MCP (P0-M2) for agent control
- Safety Rails (P0-G2) for constraint validation

## Test Plan
| Test Case | Description | Expected Result |
|-----------|-------------|----------------|
| TC001 | FPS display update | Real-time FPS shown accurately |
| TC002 | Memory monitoring | Memory usage displayed correctly |
| TC003 | Agent status tracking | All agents shown with current status |
| TC004 | Alert handling | Alerts triggered on threshold breaches |
| TC005 | Agent control | Commands sent to agents successfully |
| TC006 | Disconnection handling | Offline agents marked appropriately |
| TC007 | Performance impact | UI overhead < 5% FPS |

## Definition of Done
- [x] Real-time FPS display
- [x] Memory usage monitoring
- [x] Agent status tracking
- [x] Alert system with thresholds
- [x] Agent control interface
- [x] System health dashboard
- [x] Test coverage ≥ 80%
- [x] File size ≤ 750 lines
- [x] UI responsive under load
- [x] Graceful degradation on failures