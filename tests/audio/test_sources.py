import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from vjlive3.audio.config import AudioSourceType, AudioConfig, AudioDeviceConfig
from vjlive3.audio.source import DummySource, MicrophoneSource

def test_audio_config_defaults():
    config = AudioConfig()
    assert config.sample_rate == 48000
    assert config.buffer_size == 2048
    assert config.fft_resolution == 2048

def test_dummy_source_initialization():
    global_cfg = AudioConfig()
    dev_cfg = AudioDeviceConfig(device_name="MyDummy", source_type=AudioSourceType.DUMMY)
    source = DummySource("dummy_1", dev_cfg, global_cfg)
    assert source.id == "dummy_1"
    assert source.config.device_name == "MyDummy"
    assert source.config.source_type == AudioSourceType.DUMMY
    assert not source.is_active
    assert source.volume == 1.0

def test_dummy_source_volume():
    global_cfg = AudioConfig()
    dev_cfg = AudioDeviceConfig(source_type=AudioSourceType.DUMMY)
    source = DummySource("dummy_1", dev_cfg, global_cfg)
    
    source.volume = 0.5
    assert source.volume == 0.5
    source.volume = 1.5
    assert source.volume == 1.5
    source.volume = -0.5
    assert source.volume == 0.0

def test_dummy_source_lifecycle():
    global_cfg = AudioConfig(buffer_size=1024)
    dev_cfg = AudioDeviceConfig(source_type=AudioSourceType.DUMMY)
    source = DummySource("dummy_1", dev_cfg, global_cfg)
    
    assert source.read_chunk() is None
    
    assert source.start() is True
    assert source.is_active is True
    
    # Simulate a chunk pushed by the internal thread wrapper
    fake_chunk = np.zeros(1024, dtype=np.float32)
    source._push_chunk(fake_chunk)
    
    buf = source.read_chunk()
    assert buf is not None
    assert len(buf) == 1024
    assert np.all(buf == 0.0)
    
    source.stop()
    assert source.is_active is False

@patch("vjlive3.audio.source.pyaudio")
def test_microphone_source_lifecycle(mock_pyaudio):
    global_cfg = AudioConfig(buffer_size=512)
    dev_cfg = AudioDeviceConfig(source_type=AudioSourceType.MICROPHONE, device_id=0)
    
    mock_pa_instance = MagicMock()
    mock_stream = MagicMock()
    mock_pa_instance.open.return_value = mock_stream
    
    source = MicrophoneSource("mic_1", dev_cfg, global_cfg, mock_pa_instance)
    assert not source.is_active
    
    # Test audio callback putting data
    fake_data = np.ones(512, dtype=np.float32)
    in_bytes = fake_data.tobytes()
    source._audio_callback(in_bytes, 512, None, 0) # status 0
    
    # Check read retrieves the data put by callback
    buf = source.read_chunk()
    assert len(buf) == 512
    assert np.all(buf == 1.0)
    
    success = source.start()
    assert success is True
    assert source.is_active is True
    mock_stream.start_stream.assert_called_once()
    
    source.stop()
    assert source.is_active is False
    mock_stream.stop_stream.assert_called_once()
    mock_stream.close.assert_called_once()
