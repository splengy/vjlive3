# P4-COR020: AgentAvatarEffect (agent_avatar)

## Description

The `AgentAvatarEffect` (from `VJlive-2/core/extensions/agents/agent_avatar.py`) is a specialized OpenGL Fragment Shader overlay that visually represents the active AI Agent. It draws a reactive geometric core (spinning hexagon/triangles) that changes its fragmentation, glow, and color based on the AI's internal state (thinking, confident, overwhelmed).

## Public Interface Requirements

```python
from vjlive3.plugins.base import EffectNode

class AgentAvatarEffect(EffectNode):
    """
    Renders a reactive 2D/3D geometric avatar representing the AI Agent.
    """
    METADATA = {
        "id": "AgentAvatarEffect",
        "type": "overlay",
        "version": "1.0.0",
        "legacy_ref": "agent_avatar (AgentAvatarEffect)"
    }

    def __init__(self):
        super().__init__()
        self.avatar_scale = 0.15
        
    def update_from_agent_state(self, state: dict) -> None:
        """Parses the Agent's mood vector into shader uniforms (spin_speed, fragmentation)."""
        pass
```

## Implementation Notes

- **Decoupling hardware:** The legacy code had hardcoded logic for Surface IR Cameras (`SurfaceIRSource`) and OpenCV face tracking. In VJLive3, this MUST be stripped out of the shader node. Face tracking data (`gaze_x`, `shadow_mask`) must be provided generically via the `StateManager`.
- **Shader Porting:** Convert the `AVATAR_FRAGMENT_SHADER` string to a standalone `.glsl` file in `src/vjlive3/shaders/` and load it via the `ResourceManager`.

## Test Plan

- **Pytest:** Set the simulated agent state to "overwhelmed" and process it. Assert that the underlying `fragmentation` uniform value spikes above `0.8`.
- Coverage must exceed 80%.
