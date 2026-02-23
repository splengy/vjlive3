"""
Audio Source Management for VJLive3 Audio Engine.
Handles capturing audio from different hardware devices and streams into buffers.
"""

import time
import numpy as np
import threading
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Deque
from collections import deque

from .config import AudioDeviceConfig, AudioSourceType, AudioConfig

logger = logging.getLogger(__name__)

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available. Only Dummy audio sources will work.")


class AudioFeatures:
    """Dataclass holding extracted features from an audio buffer."""
    def __init__(self):
        self.rms: float = 0.0
        self.peak: float = 0.0
        self.bass: float = 0.0
        self.mid: float = 0.0
        self.treble: float = 0.0
        self.is_beat: bool = False
        self.beat_phase: float = 0.0
        self.bpm: float = 120.0
        self.spectrum: np.ndarray = np.zeros(128, dtype=np.float32)

class AudioSource(ABC):
    """
    Base class for all audio inputs.
    Manages an internal lock-free ring buffer (deque) of audio chunks.
    """
    def __init__(self, source_id: str, config: AudioDeviceConfig, global_config: AudioConfig):
        self.id = source_id
        self.config = config
        self.global_config = global_config
        self.is_active = False
        
        # Audio feature state
        self.features = AudioFeatures()
        
        # Ring buffer for safe cross-thread read/writes
        # Keep ~0.5 seconds of audio history maximum
        max_chunks = max(4, int(global_config.sample_rate * 0.5 / global_config.buffer_size))
        self._buffer: Deque[np.ndarray] = deque(maxlen=max_chunks)
        self._lock = threading.Lock()
        
    @property
    def volume(self) -> float:
        return self.config.volume
        
    @volume.setter
    def volume(self, val: float):
        self.config.volume = max(0.0, min(val, 2.0))

    @abstractmethod
    def start(self) -> bool:
        """Begin capturing audio. Returns True if successful."""
        pass
        
    @abstractmethod
    def stop(self) -> None:
        """Stop capturing audio."""
        pass
        
    def read_chunk(self) -> Optional[np.ndarray]:
        """
        Pull the oldest chunk from the buffer for analysis.
        Returns contiguous float32 numpy array or None if empty.
        """
        try:
            return self._buffer.popleft()
        except IndexError:
            return None
            
    def _push_chunk(self, data: np.ndarray) -> None:
        """
        Push new audio data onto the right of the ring buffer.
        If buffer is full, the oldest chunk drops off the left automatically.
        """
        # Apply local source gain
        if self.config.volume != 1.0:
            data = data * self.config.volume
            
        self._buffer.append(data)

class DummySource(AudioSource):
    """Fallback source that generates a silent/mock signal."""
    
    def __init__(self, source_id: str, config: AudioDeviceConfig, global_config: AudioConfig):
        super().__init__(source_id, config, global_config)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
    def start(self) -> bool:
        if self.is_active: return True
        self.is_active = True
        self._stop_event.clear()
        
        self._thread = threading.Thread(
            target=self._mock_capture_loop, 
            name=f"AudioDummy-{self.id}",
            daemon=True
        )
        self._thread.start()
        logger.info(f"Started DummySource {self.id}")
        return True
        
    def stop(self) -> None:
        self.is_active = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
            
    def _mock_capture_loop(self):
        """Simulate realtime audio acquisition."""
        chunk_time = self.global_config.buffer_size / self.global_config.sample_rate
        
        while not self._stop_event.is_set():
            # In testing we often manually push chunks via `_push_chunk`,
            # so we only generate zeros if the buffer is empty to avoid stomping test data
            if len(self._buffer) == 0:
                chunk = np.zeros(self.global_config.buffer_size, dtype=np.float32)
                self._push_chunk(chunk)
            time.sleep(chunk_time)

class MicrophoneSource(AudioSource):
    """
    Hardware audio capture utilizing PyAudio.
    Operates a non-blocking callback stream.
    """
    
    def __init__(self, source_id: str, config: AudioDeviceConfig, global_config: AudioConfig, pa_instance: Any = None):
        super().__init__(source_id, config, global_config)
        self._pa = pa_instance
        self._stream = None
        
    def start(self) -> bool:
        if not PYAUDIO_AVAILABLE or not self._pa:
            logger.error(f"Cannot start MicrophoneSource {self.id}: PyAudio unavailable")
            return False
            
        if self.is_active: 
            return True
            
        try:
            device_idx = self.config.device_id
            
            # Auto-detect if device_id is undefined
            if device_idx is None:
                info = self._pa.get_default_input_device_info()
                device_idx = info['index']
                
            self._stream = self._pa.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.global_config.sample_rate,
                input=True,
                input_device_index=device_idx,
                frames_per_buffer=self.global_config.buffer_size,
                stream_callback=self._audio_callback
            )
            
            self._stream.start_stream()
            self.is_active = True
            logger.info(f"Started MicrophoneSource {self.id} on device index {device_idx}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to open hardware stream for source {self.id}: {e}")
            self.is_active = False
            return False
            
    def stop(self) -> None:
        if not self.is_active or not self._stream:
            return
            
        self.is_active = False
        try:
            self._stream.stop_stream()
            self._stream.close()
        except Exception as e:
            logger.error(f"Error closing audio stream {self.id}: {e}")
        finally:
            self._stream = None
            
    def _audio_callback(self, in_data, frame_count, time_info, status) -> tuple:
        """PyAudio threaded callback triggered when hardware fills the buffer."""
        try:
            # Parse PyAudio bytes to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Check for dropped frames
            if status & pyaudio.paInputOverflow:
                logger.warning(f"Audio Buffer Overflow on source {self.id}")
                
            # Submit to ring buffer
            self._push_chunk(audio_data.copy())
            
            return (in_data, pyaudio.paContinue)
        except Exception as e:
            logger.error(f"Error in audio callback {self.id}: {e}")
            return (in_data, pyaudio.paContinue)
