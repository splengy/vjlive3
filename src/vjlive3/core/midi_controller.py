from dataclasses import dataclass
from typing import List, Callable, Optional, Dict
import logging

try:
    import mido
except ImportError:
    mido = None

logger = logging.getLogger(__name__)

@dataclass
class MidiEvent:
    type: str # 'note_on', 'note_off', 'cc'
    channel: int
    note: int
    velocity: int
    value: int # for cc

@dataclass
class MidiDeviceStatus:
    name: str
    is_connected: bool

class MidiController:
    """Manages raw MIDI hardware inputs and transforms them into VJLive events."""
    
    def __init__(self) -> None:
        self._port = None
        self._device_name: str = ""
        self._is_connected: bool = False
        self._callbacks: List[Callable[[MidiEvent], None]] = []
        
        if mido is None:
            logger.warning("mido library not found. MIDI Controller will run in dummy mode.")

    def scan_devices(self) -> List[str]:
        """Returns a list of available MIDI input device names."""
        if mido is None:
            return []
        try:
            return list(mido.get_input_names())
        except Exception as e:
            logger.error(f"Failed to scan MIDI devices: {e}")
            return []

    def connect(self, device_name: str) -> bool:
        """Connects to a distinct MIDI input port gracefully."""
        if mido is None:
            return False
            
        try:
            self._port = mido.open_input(device_name)
            self._device_name = device_name
            self._is_connected = True
            logger.info(f"Successfully connected to MIDI port: {device_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MIDI port {device_name}: {e}")
            self._is_connected = False
            self._port = None
            return False

    def disconnect(self) -> None:
        """Safely tears down the active MIDI port connection."""
        if self._port is not None:
            try:
                self._port.close()
            except Exception as e:
                logger.error(f"Error disconnecting MIDI port: {e}")
            finally:
                self._port = None
                
        self._is_connected = False
        self._device_name = ""
        logger.info("MIDI port disconnected.")

    def register_callback(self, callback: Callable[[MidiEvent], None]) -> None:
        """Registers a non-blocking receiver function for processed MidiEvents."""
        if callback not in self._callbacks:
            self._callbacks.append(callback)

    def _dispatch_event(self, event: MidiEvent) -> None:
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception as e:
                logger.error(f"Callback threw exception during MIDI dispatch: {e}")

    def poll(self) -> None:
        """Non-blocking function that drains the hardware port of active messages."""
        if not self._is_connected or self._port is None:
            return

        try:
            # Poll pending messages quickly without locking the main thread
            for msg in self._port.iter_pending():
                event = self._parse_message(msg)
                if event is not None:
                    self._dispatch_event(event)

        except Exception as e:
            # Drop connection on hardware failure (fail-graceful)
            logger.warning(f"Hardware failure polling MIDI port: {e}")
            self.disconnect()

    def _parse_message(self, msg) -> Optional[MidiEvent]:
        """Translates a raw library Mido message into our standardized system MidiEvent."""
        if msg.type == 'note_on':
            return MidiEvent(type='note_on', channel=msg.channel, note=msg.note, velocity=msg.velocity, value=0)
        elif msg.type == 'note_off':
            return MidiEvent(type='note_off', channel=msg.channel, note=msg.note, velocity=msg.velocity, value=0)
        elif msg.type == 'control_change':
            return MidiEvent(type='cc', channel=msg.channel, note=0, velocity=0, value=msg.value)
        
        return None

    def get_status(self) -> MidiDeviceStatus:
        """Returns current device status snapshot."""
        return MidiDeviceStatus(name=self._device_name, is_connected=self._is_connected)
