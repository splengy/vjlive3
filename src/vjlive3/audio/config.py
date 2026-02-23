"""
Audio Configuration
VJLive3 audio engine configuration definitions using Pydantic.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class AudioSourceType(str, Enum):
    """Types of audio sources supported by the engine."""
    MICROPHONE = "microphone"
    LINE_IN = "line_in"
    FILE = "file"
    NETWORK = "network"
    DUMMY = "dummy"

class AudioDeviceConfig(BaseModel):
    """Configuration for a specific audio device."""
    device_id: Optional[int] = Field(None, description="PyAudio device index (if known)")
    device_name: Optional[str] = Field(None, description="Partial or full name to match against")
    source_type: AudioSourceType = Field(AudioSourceType.MICROPHONE, description="Type of source")
    volume: float = Field(1.0, ge=0.0, le=2.0, description="Input gain/volume multiplier")
    enabled: bool = Field(True, description="Whether this source starts enabled")
    # For file or network sources:
    uri: Optional[str] = Field(None, description="File path or stream URL")

class AudioConfig(BaseModel):
    """Global configuration for the AudioEngine."""
    sample_rate: int = Field(48000, description="Internal sample rate (Hz)")
    buffer_size: int = Field(2048, description="Frames per buffer for capture")
    
    # Analysis Configuration
    fft_resolution: int = Field(2048, description="Number of bins for FFT")
    enable_beat_detection: bool = Field(True, description="Run onset detection algorithms")
    
    # Frequency bands for reactivity (Hz)
    bass_range: tuple[float, float] = Field((20.0, 250.0), description="Bass band frequency range")
    mid_range: tuple[float, float] = Field((250.0, 4000.0), description="Mid band frequency range")
    high_range: tuple[float, float] = Field((4000.0, 20000.0), description="Treble band frequency range")
    
    # Defaults and limits
    max_sources: int = Field(8, description="Maximum concurrent audio sources allowed")
    master_volume: float = Field(1.0, ge=0.0, le=2.0, description="Global volume multiplier")
    
    devices: List[AudioDeviceConfig] = Field(
        default_factory=list, 
        description="List of configured audio sources"
    )
