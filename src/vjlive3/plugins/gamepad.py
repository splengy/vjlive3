"""
P2-H6: Gamepad Input (GLFW Backend)
Provides Gamepad/Joystick input via GLFW, handling hot-plugging
and enforcing deadzones. Safely falls back if GLFW context is absent.
"""
import logging
import glfw
from typing import List, Optional, Dict

from vjlive3.plugins.api import PluginBase, PluginContext

_logger = logging.getLogger("vjlive3.plugins.gamepad")

class GamepadState:
    """Snapshot of a controller's current axes and buttons."""
    def __init__(self, jid: int, name: str) -> None:
        self.jid = jid
        self.name = name
        self.axes: List[float] = []
        self.buttons: List[int] = []
        self.connected: bool = True


class GamepadPlugin(PluginBase):
    """Plugin wrapping GLFW joystick input."""
    
    name = "Gamepad Input"
    version = "1.0.0"
    
    def __init__(self) -> None:
        super().__init__()
        self.gamepads: Dict[int, GamepadState] = {}
        self.deadzone = 0.1
        self._glfw_initialized = False
        
    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        # Check if GLFW is actually initialized by the core engine
        if not glfw.init():
            _logger.warning("Failed to initialize GLFW. Gamepad plugin running in degraded/mock mode.")
            return
            
        self._glfw_initialized = True
        
        # We can't guarantee a window context exists here, but glfw.joystick_present
        # technically works as long as glfw is init.
        glfw.set_joystick_callback(self._joystick_callback)
        self._scan_joysticks()
        _logger.info("GamepadPlugin initialized via GLFW.")

    def _joystick_callback(self, jid: int, event: int) -> None:
        if event == glfw.CONNECTED:
            name = glfw.get_joystick_name(jid)
            if name:
                name_str = name.decode('utf-8') if isinstance(name, bytes) else str(name)
                self.gamepads[jid] = GamepadState(jid, name_str)
                _logger.info("Gamepad %d connected: %s", jid, name_str)
        elif event == glfw.DISCONNECTED:
            if jid in self.gamepads:
                self.gamepads[jid].connected = False
                _logger.info("Gamepad %d disconnected.", jid)
                del self.gamepads[jid]

    def _scan_joysticks(self) -> None:
        if not self._glfw_initialized:
            return
            
        for jid in range(glfw.JOYSTICK_1, glfw.JOYSTICK_LAST + 1):
            if glfw.joystick_present(jid):
                name = glfw.get_joystick_name(jid)
                name_str = name.decode('utf-8') if isinstance(name, bytes) else str(name)
                if name_str:
                    self.gamepads[jid] = GamepadState(jid, name_str)

    def process(self) -> None:
        """Poll the gamepad state every frame and update context parameters."""
        if not self._glfw_initialized or not self.context:
            return

        for jid, state in list(self.gamepads.items()):
            if not glfw.joystick_present(jid):
                self._joystick_callback(jid, glfw.DISCONNECTED)
                continue
                
            axes = glfw.get_joystick_axes(jid)
            if axes:
                # Apply deadzone
                state.axes = [
                    0.0 if abs(val) < self.deadzone else val 
                    for val in axes
                ]
            else:
                state.axes = []
                
            buttons = glfw.get_joystick_buttons(jid)
            state.buttons = list(buttons) if buttons else []
            
            # Map values to the matrix context so other nodes can use them
            prefix = f"gamepad.{jid}"
            
            for i, axis_val in enumerate(state.axes):
                self.context.set_parameter(f"{prefix}.axis.{i}", axis_val)
                
            for i, btn_val in enumerate(state.buttons):
                self.context.set_parameter(f"{prefix}.button.{i}", btn_val)

    def get_gamepad_state(self, jid: int) -> Optional[GamepadState]:
        return self.gamepads.get(jid)

    def cleanup(self) -> None:
        super().cleanup()
        if self._glfw_initialized:
            glfw.set_joystick_callback(None)
        self.gamepads.clear()
