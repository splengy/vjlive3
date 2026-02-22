import colorsys
import math
import logging
from typing import List, Dict
from vjlive3.dmx.engine import DMXFixture

logger = logging.getLogger(__name__)

class DmxEffect:
    def update(self, delta_time: float) -> None:
        pass

    def apply_to(self, fixtures: List[DMXFixture]) -> None:
        pass


class ChaseEffect(DmxEffect):
    def __init__(self, speed: float = 1.0, forward: bool = True) -> None:
        self.speed = speed
        self.forward = forward
        self._progress = 0.0

    def update(self, delta_time: float) -> None:
        # Clamp large delta to prevent skipping multiple full cycles
        dt = min(delta_time, 1.0)
        self._progress += dt * self.speed

    def apply_to(self, fixtures: List[DMXFixture]) -> None:
        if not fixtures:
            return
            
        count = len(fixtures)
        # Calculate current active index
        active_idx = int(self._progress) % count
        
        if not self.forward:
            active_idx = (count - 1) - active_idx

        for i, fixture in enumerate(fixtures):
            # For a basic chase, we just turn the active one full white (or dim max)
            # and zero out the others. A more advanced chase would respect base colors.
            if i == active_idx:
                fixture.set_rgb(255, 255, 255)
                # Give dimmers some love too if it's a single channel light
                if fixture.channel_count == 1:
                    fixture.set_channel(0, 255)
            else:
                fixture.set_rgb(0, 0, 0)
                if fixture.channel_count == 1:
                    fixture.set_channel(0, 0)


class RainbowEffect(DmxEffect):
    def __init__(self, speed: float = 1.0, spread: float = 1.0) -> None:
        self.speed = speed
        self.spread = spread
        self._phase = 0.0

    def update(self, delta_time: float) -> None:
        dt = min(delta_time, 1.0)
        self._phase = (self._phase + (dt * self.speed)) % 1.0

    def apply_to(self, fixtures: List[DMXFixture]) -> None:
        if not fixtures:
            return
            
        count = len(fixtures)
        for i, fixture in enumerate(fixtures):
            # Calculate hue offset based on physical position (index) and spread
            offset = (i / max(1, count)) * self.spread
            hue = (self._phase + offset) % 1.0
            
            # Convert HSL to RGB (S=1, L=0.5 -> full saturation, 100% brightness)
            r_f, g_f, b_f = colorsys.hls_to_rgb(hue, 0.5, 1.0)
            
            r = int(r_f * 255)
            g = int(g_f * 255)
            b = int(b_f * 255)
            
            fixture.set_rgb(r, g, b)
            
            # Fallback for mono fixtures: pulse the dimmer based on lightness curve (sine)
            if fixture.channel_count < 3:
                # Dimmer follows a sine wave of the hue
                dimmer = int(((math.sin(hue * math.pi * 2) + 1.0) / 2.0) * 255)
                fixture.set_channel(0, dimmer)


class StrobeEffect(DmxEffect):
    def __init__(self, rate_hz: float = 10.0, duty_cycle: float = 0.5) -> None:
        self.rate_hz = max(0.1, min(30.0, rate_hz)) # Clamped per constraints
        self.duty_cycle = duty_cycle
        self._time_accumulator = 0.0
        self._state = False

    def update(self, delta_time: float) -> None:
        dt = min(delta_time, 1.0)
        self._time_accumulator += dt
        
        period = 1.0 / self.rate_hz
        cycle_pos = (self._time_accumulator % period) / period
        
        self._state = bool(cycle_pos <= self.duty_cycle)

    def trigger(self) -> None:
        # For beat-sync: reset the cycle to immediately pop on
        self._time_accumulator = 0.0
        self._state = True

    def apply_to(self, fixtures: List[DMXFixture]) -> None:
        if not fixtures:
            return
            
        target_val = 255 if self._state else 0
        
        for fixture in fixtures:
            fixture.set_rgb(target_val, target_val, target_val)
            if fixture.channel_count == 1:
                fixture.set_channel(0, target_val)


class DmxFxEngine:
    def __init__(self) -> None:
        self._effects: Dict[str, DmxEffect] = {}

    def add_effect(self, group_name: str, effect: DmxEffect) -> None:
        self._effects[group_name] = effect

    def remove_effect(self, group_name: str) -> None:
        if group_name in self._effects:
            del self._effects[group_name]

    def update_all(self, delta_time: float, fixture_groups: Dict[str, List[DMXFixture]]) -> None:
        for group_name, effect in self._effects.items():
            effect.update(delta_time)
            
            if group_name in fixture_groups:
                fixtures = fixture_groups[group_name]
                effect.apply_to(fixtures)
