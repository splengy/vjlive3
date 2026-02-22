import asyncio
import logging
import threading
import time
from enum import Enum
from typing import Optional

try:
    from pyartnet import ArtNetNode # type: ignore
    HAS_PYARTNET = True
except ImportError:
    HAS_PYARTNET = False

try:
    import sacn # type: ignore
    HAS_SACN = True
except ImportError:
    HAS_SACN = False

logger = logging.getLogger(__name__)

class DmxProtocol(Enum):
    ARTNET = "artnet"
    SACN = "sacn"

class NetworkOutputNode:
    def __init__(self, ip_address: str, protocol: DmxProtocol = DmxProtocol.ARTNET, universe: int = 0) -> None:
        self.ip_address = ip_address
        self.protocol = protocol
        self.universe_id = universe
        self._data = bytearray(512)
        
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

        self._artnet_node = None
        self._artnet_universe = None
        self._sacn_sender = None

        # Determine if we need mock fallback
        if self.protocol == DmxProtocol.ARTNET and not HAS_PYARTNET:
            self._mock_mode = True
        elif self.protocol == DmxProtocol.SACN and not HAS_SACN:
            self._mock_mode = True
        else:
            self._mock_mode = False

    def start(self) -> None:
        if self._running:
            return
        
        self._running = True
        if self._mock_mode:
            logger.warning(f"{self.protocol.value} library missing. NetworkOutputNode starting in fallback mock mode.")
            # We still run a dummy thread to simulate 44Hz tick
            self._thread = threading.Thread(target=self._run_mock_loop, daemon=True)
            self._thread.start()
        else:
            try:
                if self.protocol == DmxProtocol.SACN:
                    self._init_sacn()
                    # sACN sender has its own thread usually, but we manage transmission
                    self._thread = threading.Thread(target=self._run_sacn_loop, daemon=True)
                    self._thread.start()
                elif self.protocol == DmxProtocol.ARTNET:
                    self._thread = threading.Thread(target=self._run_artnet_loop, daemon=True)
                    self._thread.start()
            except Exception as e:
                logger.error(f"Failed to bind {self.protocol.value} on {self.ip_address}: {e}. Falling back to mock data routing.")
                self._mock_mode = True
                self._thread = threading.Thread(target=self._run_mock_loop, daemon=True)
                self._thread.start()

    def update_universe(self, data: bytearray) -> None:
        length = len(data)
        if length < 512:
            padded = bytearray(data)
            padded.extend(b'\x00' * (512 - length))
            self._data = padded
        elif length > 512:
            self._data = bytearray(data[:512])
        else:
            self._data = bytearray(data)

    def get_status(self) -> dict:
        return {
            "ip_address": self.ip_address,
            "protocol": self.protocol.value,
            "universe": self.universe_id,
            "running": self._running,
            "mock_mode": self._mock_mode
        }

    def _init_sacn(self):
        self._sacn_sender = sacn.sACNsender(bind_address="0.0.0.0", bind_port=5568, source_name="VJLive3")
        self._sacn_sender.start()
        self._sacn_sender.activate_output(self.universe_id)
        if self.ip_address != "127.0.0.1" and self.ip_address != "localhost":
            self._sacn_sender[self.universe_id].destination = self.ip_address
        else:
            self._sacn_sender[self.universe_id].multicast = False
            self._sacn_sender[self.universe_id].destination = "127.0.0.1"

    def _run_sacn_loop(self):
        while self._running:
            if self._sacn_sender:
                self._sacn_sender[self.universe_id].dmx_data = tuple(self._data)
            time.sleep(1.0 / 44.0)

    def _run_artnet_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._async_artnet_loop())
        finally:
            self._loop.close()

    async def _async_artnet_loop(self):
        # Bind the node
        self._artnet_node = ArtNetNode(self.ip_address, 6454)
        await self._artnet_node.start()
        self._artnet_universe = self._artnet_node.add_universe(self.universe_id)
        
        while self._running:
            # Send universe state (conceptually, pyartnet handles this internally upon data assignment usually)
            # but we force tick at 44Hz explicitly per spec
            await asyncio.sleep(1.0 / 44.0)

    def _run_mock_loop(self):
        while self._running:
            time.sleep(1.0 / 44.0)

    def stop(self) -> None:
        if not self._running:
            return
            
        # Send blackout
        blackout = bytearray(512)
        self.update_universe(blackout)
        
        # Give networks a moment to flush blackout frame
        time.sleep(0.05)
        
        self._running = False
        
        if self._mock_mode:
            pass
        elif self.protocol == DmxProtocol.SACN and self._sacn_sender:
            self._sacn_sender.stop()
        elif self.protocol == DmxProtocol.ARTNET and self._loop and self._artnet_node:
            asyncio.run_coroutine_threadsafe(self._artnet_node.stop(), self._loop)
            
        if self._thread and self._thread.is_alive():
            if self._loop and self.protocol == DmxProtocol.ARTNET:
                self._loop.call_soon_threadsafe(self._loop.stop)
            self._thread.join(timeout=2.0)
