import pytest
from vjlive3.dmx.fx import DmxFxEngine, ChaseEffect, RainbowEffect, StrobeEffect
from vjlive3.dmx.engine import DMXFixture

def test_chase_step_progression():
    """Chase effect moves exactly one fixture forward per interval."""
    fixtures = [
        DMXFixture("F1", 1, 3),
        DMXFixture("F2", 4, 3),
        DMXFixture("F3", 7, 3),
    ]
    
    chase = ChaseEffect(speed=1.0)
    
    # Init state (t=0)
    chase.apply_to(fixtures)
    assert fixtures[0].get_values() == [255, 255, 255]
    assert fixtures[1].get_values() == [0, 0, 0]
    
    # Progress 1 sec
    chase.update(1.0)
    chase.apply_to(fixtures)
    assert fixtures[0].get_values() == [0, 0, 0]
    assert fixtures[1].get_values() == [255, 255, 255]
    assert fixtures[2].get_values() == [0, 0, 0]

    # Progress 1 sec (wrap)
    chase.update(1.0) # idx 2
    chase.update(1.0) # idx 0 again
    chase.apply_to(fixtures)
    assert fixtures[0].get_values() == [255, 255, 255]
    assert fixtures[2].get_values() == [0, 0, 0]

def test_chase_reverse():
    fixtures = [DMXFixture("F1", 1, 3), DMXFixture("F2", 4, 3)]
    chase = ChaseEffect(speed=1.0, forward=False)
    chase.apply_to(fixtures)
    # Starts at last index
    assert fixtures[1].get_values() == [255, 255, 255]
    
def test_rainbow_color_spread():
    """Rainbow effect generates phase-shifted colors across fixtures."""
    fixtures = [
        DMXFixture("F1", 1, 3),
        DMXFixture("F2", 4, 3),
    ]
    rainbow = RainbowEffect(speed=0.0, spread=0.5) # Stationary rainbow
    
    # Force phase update
    rainbow.update(0.0)
    rainbow.apply_to(fixtures)
    
    v1 = fixtures[0].get_values()
    v2 = fixtures[1].get_values()
    
    # They should not be identical because of spread
    assert v1 != v2
    
def test_rainbow_dimmer_fallback():
    fixtures = [DMXFixture("dimmer", 1, 1)]
    rainbow = RainbowEffect()
    rainbow.update(0.0)
    rainbow.apply_to(fixtures)
    # Even on a dimmer, it should fallback to sine wave intensity mapping instead of ignoring
    assert fixtures[0].get_values()[0] > 0

def test_strobe_duty_cycle():
    """Strobe effect correctly toggles between max and min values based on time."""
    fixtures = [DMXFixture("F1", 1, 3)]
    strobe = StrobeEffect(rate_hz=10.0, duty_cycle=0.5)
    
    # Initial trigger
    strobe.trigger()
    strobe.apply_to(fixtures)
    assert fixtures[0].get_values() == [255, 255, 255]
    
    # Move exactly 0.051 seconds (just over 50% duty cycle of 10hz)
    strobe.update(0.051)
    strobe.apply_to(fixtures)
    assert fixtures[0].get_values() == [0, 0, 0]
    
def test_fx_engine_update():
    """Engine correctly routes updates to assigned fixture groups."""
    engine = DmxFxEngine()
    strobe = StrobeEffect()
    
    fixtures = [DMXFixture("F1", 1, 3)]
    groups = {"main": fixtures}
    
    engine.add_effect("main", strobe)
    strobe.trigger()
    
    # Update through engine
    engine.update_all(0.06, groups) # Will push strobe to OFF state
    
    assert fixtures[0].get_values() == [0, 0, 0]
    
    engine.remove_effect("main")
    # Empty update should not crash
    engine.update_all(0.06, groups)
    
def test_empty_apply_returns_safely():
    """Applying effects to empty lists should not throw DivisionByZero or IndexErrors."""
    chase = ChaseEffect()
    rainbow = RainbowEffect()
    strobe = StrobeEffect()
    
    chase.apply_to([])
    rainbow.apply_to([])
    strobe.apply_to([])
    assert True # Passthrough success
