import pytest
from vjlive3.dmx.engine import DMXFixture, DMXController, FixtureProfile

def test_dmx_fixture_channel_clamping():
    """Values passed to set_channel are clamped to 0-255."""
    fixture = DMXFixture("test_clamp", start_channel=1, channel_count=3)
    
    # Normal assignment
    fixture.set_channel(0, 100)
    assert fixture.get_values() == [100, 0, 0]
    
    # Over 255 clamps to 255
    fixture.set_channel(1, 300)
    assert fixture.get_values() == [100, 255, 0]
    
    # Under 0 clamps to 0
    fixture.set_channel(2, -50)
    assert fixture.get_values() == [100, 255, 0]

    # Test RGB helper
    fixture.set_rgb(300, -10, 128)
    assert fixture.get_values() == [255, 0, 128]

def test_dmx_controller_mock_mode():
    """Controller starts and stops cleanly in mock mode (without pyartnet or without throwing error)."""
    # Force mock mode by faking it if pyartnet was actually found
    controller = DMXController()
    controller._mock_mode = True # Ensure mock mode for deterministic testing without binding ports
    
    # Should start cleanly
    controller.start()
    assert controller._running is True
    
    # Should stop cleanly
    controller.stop()
    assert controller._running is False

def test_dmx_add_and_retrieve_fixture():
    """Fixtures are correctly stored and updated via the controller."""
    controller = DMXController()
    fixture = controller.add_fixture("front_wash", start_channel=10, channel_count=4)
    
    assert "front_wash" in controller.fixtures
    assert controller.fixtures["front_wash"] is fixture
    
    # Set through controller
    controller.set_channel("front_wash", 0, 200)
    assert fixture.get_values()[0] == 200
    
    # Set RGB through controller
    controller.set_rgb("front_wash", 10, 20, 30)
    assert fixture.get_values()[:3] == [10, 20, 30]

def test_dmx_out_of_bounds_channel():
    """Adding a fixture with invalid channel raises ValueError."""
    # Under 1
    with pytest.raises(ValueError, match="start_channel must be between 1 and 512"):
        DMXFixture("bad", start_channel=0, channel_count=1)
        
    # Over 512
    with pytest.raises(ValueError, match="start_channel must be between 1 and 512"):
        DMXFixture("bad", start_channel=513, channel_count=1)
        
    # Valid start, but count pushes it out of bounds (510 + 4 - 1 = 513)
    with pytest.raises(ValueError, match="Invalid channel span"):
        DMXFixture("bad", start_channel=510, channel_count=4)

    # Valid start, zero count
    with pytest.raises(ValueError, match="Invalid channel span"):
        DMXFixture("bad", start_channel=1, channel_count=0)

import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

def test_dmx_controller_real_mode():
    """Test the controller starting real ArtNet threads and loops under mock injection."""
    import vjlive3.dmx.engine
    
    controller = DMXController()
    controller._mock_mode = False # Force real mode
    
    # Setup mocks
    mock_node_instance = MagicMock()
    mock_node_instance.start = AsyncMock()
    mock_node_instance.stop = AsyncMock()
    mock_universe = MagicMock()
    mock_node_instance.add_universe.return_value = mock_universe
    
    original_node = getattr(vjlive3.dmx.engine, 'ArtNetNode', None)
    vjlive3.dmx.engine.ArtNetNode = MagicMock(return_value=mock_node_instance)
    
    try:
        # We don't want the while loop to run forever, so we mock `_running` to become False quickly
        async def stop_soon():
            await asyncio.sleep(0.01)
            controller._running = False
            
        # Start controller
        controller.start()
        assert controller._running is True
        
        # Inject our quick stopper into the loop
        # Instead of call_soon_threadsafe which might fail if loop is closing, we wait:
        for _ in range(10):
            if controller._loop is not None and controller._loop.is_running():
                break
            import time
            time.sleep(0.05)
            
        if controller._loop and controller._loop.is_running():
            asyncio.run_coroutine_threadsafe(stop_soon(), controller._loop)
        else:
            controller._running = False # Fallback
        
        # Wait for thread to finish safely
        controller._thread.join(timeout=2.0)
        
        # Thread joined, which means the loop stopped
        assert controller._running is False
        mock_node_instance.start.assert_called_once()
        mock_node_instance.add_universe.assert_called_once_with(0)
    finally:
        if original_node:
            vjlive3.dmx.engine.ArtNetNode = original_node

def test_dmx_controller_stop_with_node():
    """Test the controller explicit stop method."""
    import vjlive3.dmx.engine
    controller = DMXController()
    controller._mock_mode = False
    
    mock_node_instance = MagicMock()
    mock_node_instance.start = AsyncMock()
    mock_node_instance.stop = AsyncMock()
    
    original_node = getattr(vjlive3.dmx.engine, 'ArtNetNode', None)
    vjlive3.dmx.engine.ArtNetNode = MagicMock(return_value=mock_node_instance)
    
    try:
        controller.start()
        
        # Wait briefly for thread to initialize loop
        import time
        for _ in range(10):
            if controller._loop is not None and controller._loop.is_running():
                break
            time.sleep(0.05)
        
        # Manually stop
        controller.stop()
        if controller._thread:
            controller._thread.join(timeout=2.0)
        
        assert controller._running is False
        mock_node_instance.stop.assert_called_once()
    finally:
        if original_node:
            vjlive3.dmx.engine.ArtNetNode = original_node
