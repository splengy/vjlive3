# Technical Specification: P2-D1 DMX512 Core Engine + Fixture Profiles

## 1. What this module does
This module provides a pure-Python, hardware-independent state engine for managing DMX512 universes. It defines `FixtureProfile` mappings (e.g., RGB, RGBW, Dimmer) that translate human-readable colors or intensities into raw 0-255 DMX channel data. The core engine holds the 512-byte arrays for each universe, updating them efficiently in a continuous loop or tick cycle without performing any network transmission.

## 2. Public Interface

```python
from enum import Enum
from typing import Dict, List

class FixtureProfile(Enum):
    DIMMER = "dimmer"  # 1 channel (intensity)
    RGB = "rgb"        # 3 channels (r, g, b)
    RGBW = "rgbw"      # 4 channels (r, g, b, w)

class DMXFixture:
    """Represents a DMX physical light and its channel mapping."""
    def __init__(self, name: str, start_channel: int, profile: FixtureProfile):
        self.name: str
        self.start_channel: int
        self.profile: FixtureProfile
        self.channel_count: int
        self.values: List[int] # Current channel values 0-255
        
    def set_channel(self, offset_index: int, value: int) -> None:
        """Sets a specific 0-indexed channel offset."""
        pass

    def set_color(self, r: int, g: int, b: int, w: int = 0) -> None:
        """Helper to set colors based on the fixture's profile type."""
        pass

class DMXUniverse:
    """Holds the 512-byte data buffer for a single universe."""
    def __init__(self, universe_id: int):
        self.universe_id: int
        self.data: bytearray # Fixed size 512
        self.fixtures: Dict[str, DMXFixture]
        
    def add_fixture(self, fixture: DMXFixture) -> None:
        """Adds a fixture, checking for channel bounds and overlaps."""
        pass
        
    def update_buffer(self) -> None:
        """Applies all fixture states to the raw 512-byte array."""
        pass

class DMXEngine:
    """Core manager for multiple universes."""
    def __init__(self):
        self.universes: Dict[int, DMXUniverse]
        
    def get_universe(self, universe_id: int) -> DMXUniverse:
        """Retrieves or creates a new DMXUniverse."""
        pass
        
    def tick(self, dt: float) -> None:
        """Called every frame. Triggers buffer updates for all universes."""
        pass
```

## 3. Inputs and Outputs
*   **Inputs:**
    *   `start_channel`: Integer between 1 and 512.
    *   Channel values: Integer clamped strictly between 0 and 255.
    *   `FixtureProfile`: Determines how `set_color()` maps RGB values.
*   **Outputs:**
    *   A 512-byte `bytearray` per universe (`DMXUniverse.data`), ready for consumption by external network protocols.
*   **Edge Cases Managed:**
    *   *Out-of-bounds:* Adding a fixture where `start_channel + channel_count - 1 > 512` throws a clear `ValueError`.
    *   *Overlaps:* Adding a fixture that overlaps an existing fixture logs a `WARNING` (sometimes overlaps are intentional in VJing, but we warn).
    *   *Channel Clamping:* Values passed to `set_channel` must be automatically clamped to `0 <= x <= 255` before assignment to prevent byte overflow errors.

## 4. What it does NOT do
*   **Network Output:** It does NOT send Art-Net, sACN, or serial data. This is strictly the logical data structure. Network output is handled by `P2-D2_artnet_output`.
*   **Effect Generation:** It does NOT generate chases, sine waves, or strobe effects. That is handled by the `P2-D3_dmx_fx` engine, which will call `set_channel` on the fixtures managed by this engine.
*   **Background Threads:** It does NOT run its own asyncio loop or thread. It expects to be ticked synchronously from the main engine loop or a designated manager, ensuring thread safety for the 512-byte arrays.

## 5. Test Plan
*   `test_fixture_color_mapping`: Verify that calling `set_color(255, 128, 0)` correctly sets channels 1, 2, and 3 on an RGB profile, but channels 1, 2, 3, and 4 on an RGBW profile.
*   `test_universe_buffer_update`: Verify that `DMXUniverse.update_buffer()` writes the correct fixture values into the exact expected byte offsets (e.g., start_channel 1 -> index 0).
*   `test_channel_bounds`: Ensure `start_channel=510` for an RGBW (4 ch) fixture raises an error.
*   `test_value_clamping`: Provide negative numbers and numbers > 255 to `set_channel`, verify they are clamped cleanly.
*   `test_no_memory_leak`: Run `engine.tick(0.016)` 10,000 times, ensure memory does not grow monotonically.