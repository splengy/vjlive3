"""
P2-H4: NDI Video Transport
Handles NDI sender, receiver, and hub discovery.
Safely falls back to a mock implementation if NDIlib is missing.
"""
import logging
from typing import List, Optional, Any
import numpy as np

try:
    import NDIlib as ndi
except ImportError:
    ndi = None

from vjlive3.plugins.api import PluginBase, PluginContext

_logger = logging.getLogger("vjlive3.plugins.ndi")


class NDISender:
    """Sends frames from VJLive3 to the network via NDI."""
    def __init__(self, name: str = "VJLive3 Output", mock_mode: bool = False) -> None:
        self.name = name
        self.mock_mode = mock_mode
        self._ndi_send = None
        
        if not self.mock_mode and ndi is not None:
            send_settings = ndi.SendCreate()
            send_settings.ndi_name = self.name
            send_settings.clock_video = True
            self._ndi_send = ndi.send_create(send_settings)
            
            self._video_frame = ndi.VideoFrameV2()
            self._video_frame.FourCC = ndi.FOURCC_VIDEO_TYPE_BGRA
            _logger.info("NDISender '%s' created.", self.name)
        else:
            _logger.debug("Mock NDISender '%s' initialized.", self.name)

    def send_frame(self, frame_bgra: np.ndarray) -> bool:
        """Send a BGRA numpy array frame."""
        if not isinstance(frame_bgra, np.ndarray):
            return False
            
        h, w, c = frame_bgra.shape
        if c != 4:
            _logger.warning("NDISender expects BGRA frames (4 channels). Got %d.", c)
            return False

        if self.mock_mode or ndi is None or self._ndi_send is None:
            return True

        self._video_frame.xres = w
        self._video_frame.yres = h
        self._video_frame.data = frame_bgra
        self._video_frame.line_stride_in_bytes = w * 4

        ndi.send_send_video_v2(self._ndi_send, self._video_frame)
        return True

    def destroy(self) -> None:
        """Explicitly free the NDI pointers to avoid memory leaks."""
        if self._ndi_send is not None and not self.mock_mode and ndi is not None:
            ndi.send_destroy(self._ndi_send)
            self._ndi_send = None
            _logger.info("NDISender '%s' destroyed.", self.name)


class NDIReceiver:
    """Receives frames from the network into VJLive3."""
    def __init__(self, source_name: str, mock_mode: bool = False) -> None:
        self.source_name = source_name
        self.mock_mode = mock_mode
        self._ndi_recv = None
        self._connected = False

    def connect(self) -> bool:
        """Attempt to connect to the NDI source."""
        if self.mock_mode or ndi is None:
            self._connected = True
            _logger.debug("Mock NDIReceiver connected to '%s'.", self.source_name)
            return True

        # In real usage, we'd need a valid source object from discovery.
        # For simplicity of abstraction matching standard NDI usage:
        create_settings = ndi.RecvCreateV3()
        # The source name dictates mapping
        create_settings.source_to_connect_to = ndi.Source()
        create_settings.source_to_connect_to.ndi_name = self.source_name
        create_settings.color_format = ndi.RECV_COLOR_FORMAT_BGRX_BGRA
        
        self._ndi_recv = ndi.recv_create_v3(create_settings)
        if self._ndi_recv is None:
            _logger.warning("NDIReceiver failed to create for '%s'.", self.source_name)
            return False
            
        self._connected = True
        return True

    def read_frame(self) -> Optional[np.ndarray]:
        """Read the next available frame. Non-blocking/timeout based."""
        if not self._connected:
            return None
            
        if self.mock_mode or ndi is None:
            # Return a mock blank 1080p frame
            return np.zeros((1080, 1920, 4), dtype=np.uint8)
            
        t, v, a, m = ndi.recv_capture_v2(self._ndi_recv, 0) # timeout 0ms
        
        if t == ndi.FRAME_TYPE_VIDEO:
            # We copy the buffer because we must free the NDI frame
            frame = np.copy(v.data)
            ndi.recv_free_video_v2(self._ndi_recv, v)
            return frame
            
        return None

    def disconnect(self) -> None:
        """Explicitly disconnect and free receiver."""
        if self._ndi_recv is not None and not self.mock_mode and ndi is not None:
            ndi.recv_destroy(self._ndi_recv)
            self._ndi_recv = None
        self._connected = False
        _logger.info("NDIReceiver '%s' disconnected.", self.source_name)


class NDIHub:
    """Central manager for discovery and routing of NDI streams."""
    def __init__(self) -> None:
        self.mock_mode = (ndi is None)
        self._senders: List[NDISender] = []
        self._receivers: List[NDIReceiver] = []
        self._find = None
        
        if self.mock_mode:
            _logger.warning("NDI library not found. Running in mock mode.")
        else:
            if not ndi.initialize():
                _logger.error("Failed to initialize NDIlib. Falling back to mock mode.")
                self.mock_mode = True
            else:
                find_create_desc = ndi.FindCreate()
                self._find = ndi.find_create_v2(find_create_desc)

    def get_available_sources(self) -> List[str]:
        """Discover active NDI sources on the network."""
        if self.mock_mode or ndi is None or self._find is None:
            return []
            
        # NDI find needs a moment to populate
        sources = ndi.find_get_current_sources(self._find)
        return [s.ndi_name for s in sources]

    def create_sender(self, name: str) -> NDISender:
        """Instantiate a new managed sender."""
        sender = NDISender(name, mock_mode=self.mock_mode)
        self._senders.append(sender)
        return sender

    def create_receiver(self, source_name: str) -> NDIReceiver:
        """Instantiate a new managed receiver."""
        receiver = NDIReceiver(source_name, mock_mode=self.mock_mode)
        self._receivers.append(receiver)
        return receiver

    def shutdown(self) -> None:
        """Clean up all senders, receivers, and the find instance."""
        for sender in self._senders:
            sender.destroy()
        self._senders.clear()
        
        for receiver in self._receivers:
            receiver.disconnect()
        self._receivers.clear()
        
        if self._find is not None and not self.mock_mode and ndi is not None:
            ndi.find_destroy(self._find)
            self._find = None
            ndi.destroy()
        
        _logger.info("NDIHub shut down.")


class NDIPlugin(PluginBase):
    """Plugin wrapper exposing NDI capabilities to the API and Node Graph."""
    
    name = "NDI Interface"
    version = "1.0.0"
    
    def __init__(self) -> None:
        super().__init__()
        self.hub: Optional[NDIHub] = None
        self.default_sender: Optional[NDISender] = None
        
    def initialize(self, context: PluginContext) -> None:
        super().initialize(context)
        self.hub = NDIHub()
        # Provide a default master output sender
        self.default_sender = self.hub.create_sender("VJLive3_Master")
        _logger.info("NDIPlugin initialized.")

    def process(self) -> None:
        """
        Called to process NDI routing.
        E.g., taking the context's master frames and pushing them to NDISender.
        """
        if not self.context or not self.default_sender:
            return
            
        # Example: grab a frame from the context and send it out
        master_frame = self.context.get_parameter("render.master_frame_bgra")
        if master_frame is not None:
            self.default_sender.send_frame(master_frame)
            
        # We can also poll receivers here and update context parameters

    def cleanup(self) -> None:
        super().cleanup()
        if self.hub:
            self.hub.shutdown()
            self.hub = None
