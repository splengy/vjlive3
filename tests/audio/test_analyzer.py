import pytest
import numpy as np

from vjlive3.audio.analyzer import AudioAnalyzer
from vjlive3.audio.config import AudioConfig

def test_audio_analyzer_features():
    config = AudioConfig(fft_resolution=1024, sample_rate=48000, buffer_size=1024)
    analyzer = AudioAnalyzer(config=config)
    
    # 1. Test empty buffer
    empty_features = analyzer.analyze(np.array([], dtype=np.float32))
    assert empty_features.rms == 0.0
    
    # 2. Test sine wave
    t = np.linspace(0, 1.0, 1024, endpoint=False)
    buffer = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
    
    features = analyzer.analyze(buffer)
    assert features.rms > 0.6  # approx 0.707
    assert len(features.spectrum) == 128  # decimation output size
    
    # 3. Test Beat Detection
    # Initialize history with low amplitudes
    for i in range(20):
        analyzer.analyze(buffer * 0.1)
        
    # Wait enough time to bypass the 150ms beat debounce
    import time
    time.sleep(0.2)
        
    # Sudden energy spike should trigger a beat
    beat_features = analyzer.analyze(buffer * 2.0)
    assert beat_features.is_beat is True
    
    # Next frame same high energy shouldn't be a new beat
    no_beat_features = analyzer.analyze(buffer * 2.0)
    assert no_beat_features.is_beat is False
