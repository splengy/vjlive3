import pytest
import glfw
from unittest.mock import patch, MagicMock

from vjlive3.plugins.gamepad import GamepadPlugin, GamepadState
from vjlive3.plugins.api import PluginContext

def test_gamepad_headless_fallback():
    """Instantiating the plugin without an active GLFW context falls back cleanly and doesn't throw exceptions."""
    with patch('glfw.init', return_value=False):
        plugin = GamepadPlugin()
        context = MagicMock(spec=PluginContext)
        plugin.initialize(context)
        
        assert plugin._glfw_initialized is False
        
        # Processing should do nothing but not crash
        plugin.process()
        
        # Cleanup should not crash
        plugin.cleanup()


@patch('glfw.init', return_value=True)
@patch('glfw.set_joystick_callback')
@patch('glfw.joystick_present')
@patch('glfw.get_joystick_name')
def test_gamepad_discovery(mock_name, mock_present, mock_cb, mock_init):
    # Simulate Joystick 1 is present
    def side_effect_present(jid):
        return jid == glfw.JOYSTICK_1
    mock_present.side_effect = side_effect_present
    mock_name.return_value = b'Xbox Controller'
    
    plugin = GamepadPlugin()
    context = MagicMock(spec=PluginContext)
    plugin.initialize(context)
    
    assert plugin._glfw_initialized is True
    assert glfw.JOYSTICK_1 in plugin.gamepads
    assert plugin.gamepads[glfw.JOYSTICK_1].name == "Xbox Controller"
    
    # Test getting state
    state = plugin.get_gamepad_state(glfw.JOYSTICK_1)
    assert state is not None
    assert state.connected is True
    
    plugin.cleanup()


@patch('glfw.init', return_value=True)
@patch('glfw.joystick_present', return_value=True)
@patch('glfw.get_joystick_name', return_value=b'Generic')
@patch('glfw.get_joystick_axes')
@patch('glfw.get_joystick_buttons')
def test_gamepad_deadzone(mock_buttons, mock_axes, mock_name, mock_present, mock_init):
    plugin = GamepadPlugin()
    context = MagicMock(spec=PluginContext)
    plugin.initialize(context)
    
    # Provide small inputs within deadzone (default 0.1), and one outside
    mock_axes.return_value = [0.05, -0.09, 0.5, -0.8]
    mock_buttons.return_value = [1, 0]
    
    plugin.process()
    
    state = plugin.get_gamepad_state(glfw.JOYSTICK_1)
    assert list(state.axes) == [0.0, 0.0, 0.5, -0.8]
    assert list(state.buttons) == [1, 0]
    
    # Verify values were mapped to context
    context.set_parameter.assert_any_call(f"gamepad.{glfw.JOYSTICK_1}.axis.0", 0.0)
    context.set_parameter.assert_any_call(f"gamepad.{glfw.JOYSTICK_1}.axis.2", 0.5)
    context.set_parameter.assert_any_call(f"gamepad.{glfw.JOYSTICK_1}.button.0", 1)


@patch('glfw.init', return_value=True)
@patch('glfw.joystick_present', return_value=True)
@patch('glfw.get_joystick_name', return_value=b'TestPad')
def test_gamepad_hotplugging(mock_name, mock_present, mock_init):
    plugin = GamepadPlugin()
    context = MagicMock(spec=PluginContext)
    plugin.initialize(context)
    
    # Disconnect simulation
    plugin._joystick_callback(glfw.JOYSTICK_1, glfw.DISCONNECTED)
    assert glfw.JOYSTICK_1 not in plugin.gamepads
    
    # Reconnect simulation
    plugin._joystick_callback(glfw.JOYSTICK_1, glfw.CONNECTED)
    assert glfw.JOYSTICK_1 in plugin.gamepads
    
    # Process when suddenly device is no longer present via polling
    mock_present.return_value = False
    plugin.process()
    assert glfw.JOYSTICK_1 not in plugin.gamepads
