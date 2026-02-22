"""DMX512 Core Engine implementation."""

import asyncio
import logging
import threading
from enum import Enum
from typing import Dict, List, Optional

try:
    import pyartnet
except ImportError:
    pyartnet = None


logger = logging.getLogger(__name__)


class FixtureProfile(Enum):
    """Supported fixture profiles."""
    DIMMER = "dimmer"
    RGB = "rgb"
    RGBW = "rgbw"


class DMXFixture:
    """Represents a DMX fixture mapped to specific channels."""

    def __init__(self, name: str, start_channel: int, channel_count: int) -> None:
        """Initialize a new DMX fixture.

        Args:
            name: Human-readable name of the fixture.
            start_channel: 1-indexed start channel (1-512).
            channel_count: Number of channels this fixture occupies.

        Raises:
            ValueError: If start channel is out of bounds.
        """
        if not (1 <= start_channel <= 512):
            raise ValueError(f"Start channel {start_channel} must be between 1 and 512.")
        
        self.name = name
        self.start_channel = start_channel
        self.channel_count = channel_count
        # Channel values are internal 0-indexed memory representation (0-255)
        self._values: List[int] = [0] * channel_count

    def _clamp(self, value: int) -> int:
        """Clamp value to 0-255."""
        return max(0, min(255, value))

    def set_channel(self, channel_index: int, value: int) -> None:
        """Set a value for a specific channel on this fixture.

        Args:
            channel_index: Zero-based index relative to the start channel.
            value: Int DMX value (clamped to 0-255).
        """
        if 0 <= channel_index < self.channel_count:
            self._values[channel_index] = self._clamp(value)
        else:
            logger.warning(
                f"Ignored out-of-bounds channel_index {channel_index} "
                f"for fixture {self.name} (has {self.channel_count} channels)."
            )

    def set_rgb(self, r: int, g: int, b: int) -> None:
        """Helper to set RGB values. Assumes RGB are the first 3 channels.
        
        Args:
            r, g, b: RGB values (clamped to 0-255).
        """
        if self.channel_count >= 3:
            self._values[0] = self._clamp(r)
            self._values[1] = self._clamp(g)
            self._values[2] = self._clamp(b)
        else:
            logger.warning(f"Fixture {self.name} has too few channels for RGB.")

    def get_values(self) -> List[int]:
        """Return exactly the internally maintained channel values."""
        return list(self._values)


class DMXController:
    """Manages DMX fixtures and state transmission via Art-Net or fallback."""

    def __init__(self, ip_address: str = "127.0.0.1", port: int = 6454) -> None:
        """Initialize the DMX controller.

        Args:
            ip_address: Destination IP for Art-Net transmission.
            port: Destination port.
        """
        self.ip_address = ip_address
        self.port = port
        self.fixtures: Dict[str, DMXFixture] = {}
        
        # Internal transmission states and tasks
        self._running = False
        self._transmit_thread: Optional[threading.Thread] = None
        self._asyncio_loop: Optional[asyncio.AbstractEventLoop] = None
        self._pyartnet_node = None
        self._pyartnet_universe = None
        
        # Fallback to mock mode if pyartnet isn't installed
        self._mock_mode = (pyartnet is None)
        
        # Maintain internal single universe map (1-512)
        # Note: 0-indexed internally, mapped to channels 1-512.
        self._universe_data: List[int] = [0] * 512

    def start(self) -> None:
        """Start the DMX engine in a background thread."""
        if self._running:
            return

        self._running = True
        logger.info(f"Starting DMX Controller (Target {self.ip_address}:{self.port})")

        if self._mock_mode:
            logger.warning("pyartnet not found. DMX Controller running in Mock mode.")
            return

        # Start true transmission
        self._transmit_thread = threading.Thread(
            target=self._run_transmit_loop, daemon=True, name="DMXTransmit"
        )
        self._transmit_thread.start()

    def _run_transmit_loop(self) -> None:
        """Asyncio transmission loop, designed to run in a separate thread."""
        try:
            self._asyncio_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._asyncio_loop)
            self._asyncio_loop.run_until_complete(self._init_pyartnet())
            
            while self._running:
                self._update_universe_data()
                if self._pyartnet_universe:
                    # Update internal universe data to artnet node
                    for i, val in enumerate(self._universe_data):
                        self._pyartnet_universe[i].set_value(val)
                # Cap transmit rate slightly below standard DMX ~44Hz update rate to simulate properly
                self._asyncio_loop.run_until_complete(asyncio.sleep(1 / 44.0))

        except Exception as e:
            logger.error(f"DMX transmission thread aborted: {e}")
        finally:
            if self._asyncio_loop:
                self._asyncio_loop.close()

    async def _init_pyartnet(self) -> None:
        """Initialize pyartnet components asynchronously."""
        try:
            self._pyartnet_node = pyartnet.ArtNetNode(
                ip=self.ip_address, port=self.port, max_fps=44
            )
            self._pyartnet_universe = self._pyartnet_node.add_universe(0)
            
            # Pre-add 512 channels
            for i in range(512):
                self._pyartnet_universe.add_channel(start=i+1, width=1)
            
            await self._pyartnet_node.start()
        except Exception as e:
            logger.error(f"Failed to bind pyartnet node: {e}")
            self._mock_mode = True  # Fallback smoothly if bind fails

    def _update_universe_data(self) -> None:
        """Gather values from all fixtures into the global DMX buffer."""
        for fixture in self.fixtures.values():
            start = fixture.start_channel - 1  # Map 1-based to 0-based
            count = fixture.channel_count
            vals = fixture.get_values()
            
            for i in range(count):
                if start + i < 512:
                    self._universe_data[start + i] = vals[i]

    def stop(self) -> None:
        """Stop DMX transmission cleanly."""
        if not self._running:
            return

        logger.info("Stopping DMX Controller.")
        self._running = False

        if not self._mock_mode and self._transmit_thread:
            self._transmit_thread.join(timeout=2.0)

    def add_fixture(self, name: str, start_channel: int, channel_count: int) -> DMXFixture:
        """Create and track a DMX fixture.

        Args:
            name: Unique name identifier.
            start_channel: 1-indexed channel (must fit within 512).
            channel_count: Number of DMX slots required.

        Returns:
            The spawned DMXFixture object.

        Raises:
            ValueError: If fixture breaches max boundaries or channel start < 1.
        """
        if name in self.fixtures:
            logger.warning(f"Overwriting existing fixture definition for {name}")

        if start_channel + channel_count - 1 > 512:
            raise ValueError(
                f"Fixture {name} bounds ({start_channel} to "
                f"{start_channel + channel_count - 1}) exceed universe 512 length max."
            )
            
        fixture = DMXFixture(name, start_channel, channel_count)
        self.fixtures[name] = fixture
        return fixture

    def set_channel(self, fixture_name: str, channel_index: int, value: int) -> None:
        """Shortcut to set a channel directly through the controller.

        Args:
            fixture_name: Target fixture.
            channel_index: Zero-indexed local channel on that fixture.
            value: Integer value (0-255).
        """
        if fixture_name in self.fixtures:
            self.fixtures[fixture_name].set_channel(channel_index, value)
            if self._mock_mode:
                # Eagerly update universe buffer in mock mode for faster assertions
                self._update_universe_data()
        else:
            logger.warning(f"Attempted to access non-existent fixture: {fixture_name}")

    def set_rgb(self, fixture_name: str, r: int, g: int, b: int) -> None:
        """Shortcut to set an RGB value directly through the controller.

        Args:
            fixture_name: Target fixture.
            r, g, b: Component values (0-255).
        """
        if fixture_name in self.fixtures:
            self.fixtures[fixture_name].set_rgb(r, g, b)
            if self._mock_mode:
                 self._update_universe_data()
        else:
            logger.warning(f"Attempted to access non-existent fixture: {fixture_name}")
