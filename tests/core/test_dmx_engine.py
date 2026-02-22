"""Tests for the DMX512 Core Engine (Phase 2 P2-D1)."""

import pytest

from src.vjlive3.core.dmx import DMXController, DMXFixture


def test_dmx_fixture_channel_clamping():
    """Verify values passed to set_channel are clamped to 0-255."""
    fixture = DMXFixture("TestClamping", start_channel=1, channel_count=3)
    
    # Under boundary
    fixture.set_channel(0, -50)
    assert fixture.get_values()[0] == 0
    
    # Over boundary
    fixture.set_channel(1, 300)
    assert fixture.get_values()[1] == 255
    
    # Valid
    fixture.set_channel(2, 128)
    assert fixture.get_values()[2] == 128
    
    # Verify RGB helper clamping
    fixture.set_rgb(-10, 200, 900)
    assert fixture.get_values() == [0, 200, 255]


def test_dmx_controller_mock_mode():
    """Controller starts and stops cleanly without pyartnet running."""
    controller = DMXController()
    # Force Mock mode manually in case test env has it randomly installed
    controller._mock_mode = True
    
    controller.start()
    assert controller._running is True
    assert controller._transmit_thread is None  # Mock mode shouldn't spin up threads
    
    controller.stop()
    assert controller._running is False


def test_dmx_add_and_retrieve_fixture():
    """Fixtures are correctly stored and updated via the controller."""
    controller = DMXController()
    controller._mock_mode = True
    
    controller.add_fixture("Strobe1", 1, 1)
    controller.add_fixture("Wash1", 2, 4)
    
    assert "Strobe1" in controller.fixtures
    assert "Wash1" in controller.fixtures
    
    controller.set_channel("Strobe1", 0, 255)
    controller.set_rgb("Wash1", 255, 128, 0)
    controller.set_channel("Wash1", 3, 50)  # Master dim on wash
    
    assert controller.fixtures["Strobe1"].get_values() == [255]
    assert controller.fixtures["Wash1"].get_values() == [255, 128, 0, 50]
    
    # Universe data should be populated (since Pyartnet isn't pulling we verify manually
    # or rely on the mock mode eagerly triggering it)
    assert controller._universe_data[0] == 255
    assert controller._universe_data[1:5] == [255, 128, 0, 50]


def test_dmx_out_of_bounds_channel():
    """Adding a fixture with invalid channel raises ValueError."""
    controller = DMXController()
    controller._mock_mode = True
    
    # Test 0 or negative start channel
    with pytest.raises(ValueError, match="Start channel 0 must be between 1 and 512"):
        controller.add_fixture("BadStart", 0, 1)
        
    with pytest.raises(ValueError, match="Start channel -5 must be between 1 and 512"):
        # Fixture direct call
        DMXFixture("BadStart", -5, 1)
        
    # Test exceeding universe max
    with pytest.raises(ValueError, match="exceed universe 512 length max"):
        controller.add_fixture("TooBig", 500, 20)


def test_fps_simulation_load():
    """Simulate ticking the controller rapidly 10,000 times without failing."""
    controller = DMXController()
    controller._mock_mode = True
    controller.start()
    
    fixture = controller.add_fixture("PerformanceLight", 1, 3)
    
    for i in range(10_000):
        # Sine wave modulation style logic to stress CPU cycle minimally
        val = i % 255
        controller.set_rgb("PerformanceLight", val, val, val)
        
    controller.stop()
    assert fixture.get_values() == [9, 9, 9]  # 9,999 % 255
