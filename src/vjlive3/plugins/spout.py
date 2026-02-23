import sys
import logging
import numpy as np
from typing import Optional, List

logger = logging.getLogger(__name__)

# Determine active OS and attempt import
IS_WINDOWS = sys.platform.startswith('win')
HAS_SPOUT = False

if IS_WINDOWS:
    try:
        import SpoutGL # type: ignore
        HAS_SPOUT = True
    except ImportError:
        logger.warning("SpoutGL library not found on Windows. Falling back to Mock Spout implementation.")
else:
    logger.info("Non-Windows OS detected. Using Mock Spout implementation.")


class SpoutSender:
    """Sends textures via Spout to other applications."""
    def __init__(self, name: str = "VJLive3 Spout Output") -> None:
        self.name = name
        self._sender = None
        self._mock_mode = not HAS_SPOUT

        if not self._mock_mode:
            try:
                self._sender = SpoutGL.SpoutSender()
                self._sender.setSenderName(name)
            except Exception as e:
                logger.error(f"Failed to initialize SpoutSender '{name}': {e}")
                self._mock_mode = True

    def send_texture(self, texture_id: int, width: int, height: int) -> bool:
        if self._mock_mode:
            return True
            
        if self._sender:
            try:
                # Assuming standard SpoutGL py library signatures: sendTexture(texID, GL_TEXTURE_2D, w, h, invert, 0)
                # But often simple wrappers just take (id, w, h)
                return self._sender.sendTexture(texture_id, width, height)
            except Exception as e:
                logger.error(f"Spout send_texture failed: {e}")
        return False

    def send_image(self, frame_bgra: np.ndarray) -> bool:
        if self._mock_mode:
            return True
            
        if self._sender and frame_bgra is not None:
            try:
                height, width = frame_bgra.shape[:2]
                return self._sender.sendImage(frame_bgra.tobytes(), width, height, 0x8031, False, 0) # 0x8031 is GL_BGRA
            except Exception as e:
                logger.error(f"Spout send_image failed: {e}")
        return False

    def destroy(self) -> None:
        if not self._mock_mode and self._sender:
            try:
                self._sender.releaseSender()
            except Exception:
                pass
            self._sender = None


class SpoutReceiver:
    """Receives textures via Spout from other applications."""
    def __init__(self, sender_name: str) -> None:
        self.sender_name = sender_name
        self._receiver = None
        self._mock_mode = not HAS_SPOUT
        
        if not self._mock_mode:
            try:
                self._receiver = SpoutGL.SpoutReceiver()
                self._receiver.setReceiverName(sender_name)
            except Exception as e:
                logger.error(f"Failed to initialize SpoutReceiver for '{sender_name}': {e}")
                self._mock_mode = True

    def receive_texture(self, target_texture_id: int) -> bool:
        if self._mock_mode:
            return True
            
        if self._receiver:
            try:
                # Often takes texture ID and returns width/height
                width = 0
                height = 0
                result = self._receiver.receiveTexture(target_texture_id, width, height)
                return bool(result)
            except Exception as e:
                logger.error(f"Spout receive_texture failed: {e}")
        return False

    def receive_image(self) -> Optional[np.ndarray]:
        if self._mock_mode:
            return None
            
        if self._receiver:
            try:
                # Requires allocating buffer in advance in py-spout usually
                width = self._receiver.getSenderWidth()
                height = self._receiver.getSenderHeight()
                if width > 0 and height > 0:
                    buffer = np.zeros((height, width, 4), dtype=np.uint8)
                    if self._receiver.receiveImage(buffer.ctypes.data, width, height):
                        return buffer
            except Exception as e:
                logger.error(f"Spout receive_image failed: {e}")
        return None

    def destroy(self) -> None:
        if not self._mock_mode and self._receiver:
            try:
                self._receiver.releaseReceiver()
            except Exception:
                pass
            self._receiver = None


class SpoutManager:
    """Manages Spout context and discovery."""
    def __init__(self) -> None:
        self._mock_mode = not HAS_SPOUT
        self._spout = None
        
        if not self._mock_mode:
            try:
                self._spout = SpoutGL.Spout()
            except Exception as e:
                logger.warning(f"Could not initialize SpoutManager: {e}")
                self._mock_mode = True

    def get_senders(self) -> List[str]:
        if self._mock_mode:
            return []
            
        senders = []
        if self._spout:
            count = self._spout.getSenderCount()
            for i in range(count):
                name = self._spout.getSenderName(i)
                if name:
                    senders.append(name)
        return senders


class SpoutPlugin(object):
    """Exposes Spout capability to the VJLive3 Plugin API."""
    
    name = "Spout Integration"
    version = "1.0.0"
    
    def __init__(self) -> None:
        super().__init__()
        self.manager: Optional[SpoutManager] = None
        self.active_senders: List[SpoutSender] = []
        self.active_receivers: List[SpoutReceiver] = []
    
    def initialize(self, context) -> None:
        super().initialize(context)
        self.manager = SpoutManager()
        
    def create_sender(self, name: str) -> SpoutSender:
        sender = SpoutSender(name)
        self.active_senders.append(sender)
        return sender
        
    def create_receiver(self, name: str) -> SpoutReceiver:
        receiver = SpoutReceiver(name)
        self.active_receivers.append(receiver)
        return receiver
        
    def cleanup(self) -> None:
        super().cleanup()
        for s in self.active_senders:
            s.destroy()
        for r in self.active_receivers:
            r.destroy()
        self.active_senders.clear()
        self.active_receivers.clear()
        self.manager = None
