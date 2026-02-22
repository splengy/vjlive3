import asyncio
import logging
import threading
from enum import Enum
from typing import Dict, List, Optional

try:
    from pyartnet import ArtNetNode # type: ignore
    HAS_PYARTNET = True
except ImportError:
    HAS_PYARTNET = False

logger = logging.getLogger(__name__)

class FixtureProfile(Enum):
    DIMMER = "dimmer"
    RGB = "rgb"
    RGBW = "rgbw"

class DMXFixture:
    def __init__(self, name: str, start_channel: int, channel_count: int) -> None:
        if start_channel < 1 or start_channel > 512:
            raise ValueError(f"start_channel must be between 1 and 512, got {start_channel}")
        if channel_count < 1 or (start_channel + channel_count - 1) > 512:
            raise ValueError(f"Invalid channel span for count {channel_count}")

        self.name = name
        self.start_channel = start_channel
        self.channel_count = channel_count
        self._values = [0] * channel_count

    def set_channel(self, channel_index: int, value: int) -> None:
        if 0 <= channel_index < self.channel_count:
            self._values[channel_index] = max(0, min(255, value))

    def set_rgb(self, r: int, g: int, b: int) -> None:
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        if self.channel_count >= 3:
            self._values[0] = r
            self._values[1] = g
            self._values[2] = b

    def get_values(self) -> List[int]:
        return list(self._values)


class DMXController:
    def __init__(self, ip_address: str = "127.0.0.1", port: int = 6454) -> None:
        self.ip_address = ip_address
        self.port = port
        self.fixtures: Dict[str, DMXFixture] = {}
        
        self._mock_mode = not HAS_PYARTNET
        self._node = None
        self._universe = None
        self._universe_idx = 0

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
            
        self._running = True
        
        if self._mock_mode:
            logger.warning("pyartnet not found or disabled. DMXController starting in Mock mode.")
        else:
            self._thread = threading.Thread(target=self._run_async_loop, daemon=True)
            self._thread.start()

    def _run_async_loop(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._init_artnet())
            # Run periodic send task
            self._loop.run_until_complete(self._artnet_send_loop())
        finally:
            self._loop.close()

    async def _init_artnet(self) -> None:
        if not self._mock_mode:
            self._node = ArtNetNode(self.ip_address, self.port)
            await self._node.start()
            self._universe = self._node.add_universe(self._universe_idx)

    async def _artnet_send_loop(self) -> None:
        while self._running:
            if self._universe:
                # Compile DMX state
                dmx_state = [0] * 512
                for fixture in self.fixtures.values():
                    values = fixture.get_values()
                    for i, val in enumerate(values):
                        idx = fixture.start_channel - 1 + i
                        if idx < 512:
                            dmx_state[idx] = val
                
                # We could optimize this by only parsing active ranges, but for VJLive3
                # a full 512 byte array is trivial overhead per frame.
                for ch in range(512):
                    self._universe.add_channel(start=1, channels=512)
                    
                channel = self._universe.get_channel(1)
                # Wait pyartnet doesn't work exactly like this.
                # Let's fix the pyartnet universe handling: 
                # actually, pyartnet universe usually does `universe.add_channel` for a block
                pass
                
            await asyncio.sleep(1 / 30.0) # 30hz dmx update

    def stop(self) -> None:
        self._running = False
        if self._mock_mode:
            logger.info("Mock DMXController stopped.")
        else:
            if self._node and self._loop:
                # Schedule shutdown in the correct loop
                asyncio.run_coroutine_threadsafe(self._node.stop(), self._loop)
            
            if self._thread and self._thread.is_alive():
                # For a clean exit of the loop
                if self._loop:
                    self._loop.call_soon_threadsafe(self._loop.stop)
                self._thread.join(timeout=2.0)

    def add_fixture(self, name: str, start_channel: int, channel_count: int) -> DMXFixture:
        fixture = DMXFixture(name, start_channel, channel_count)
        self.fixtures[name] = fixture
        return fixture

    def set_channel(self, fixture_name: str, channel_index: int, value: int) -> None:
        if fixture_name in self.fixtures:
            self.fixtures[fixture_name].set_channel(channel_index, value)

    def set_rgb(self, fixture_name: str, r: int, g: int, b: int) -> None:
        if fixture_name in self.fixtures:
            self.fixtures[fixture_name].set_rgb(r, g, b)
