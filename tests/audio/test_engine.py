import pytest
import time
import numpy as np

from vjlive3.audio.config import AudioSourceType, AudioDeviceConfig
from vjlive3.audio.engine import AudioEngine
from vjlive3.audio.source import DummySource

@pytest.fixture(autouse=True)
def reset_audio_engine_singleton():
    AudioEngine._instance = None
    yield
    if AudioEngine._instance:
        AudioEngine._instance.cleanup()
        AudioEngine._instance = None

def test_audio_engine_singleton():
    engine1 = AudioEngine()
    engine2 = AudioEngine()
    assert engine1 is engine2

def test_audio_engine_add_remove_source():
    engine = AudioEngine()
    dev_cfg = AudioDeviceConfig(source_type=AudioSourceType.DUMMY)
    
    source = engine.add_source("dummy_src", dev_cfg)
    assert source is not None
    assert "dummy_src" in engine.sources
    
    source_dup = engine.add_source("dummy_src", dev_cfg)
    assert source_dup is source # returns existing
    
    engine.remove_source("dummy_src")
    assert "dummy_src" not in engine.sources

def test_audio_engine_lifecycle_and_analysis():
    engine = AudioEngine()
    dev_cfg = AudioDeviceConfig(source_type=AudioSourceType.DUMMY)
    
    source = engine.add_source("dummy_src", dev_cfg)
    
    # We test the pure processing without the background thread race conditions
    engine._is_running = True
    source.is_active = True
    
    # manually pump signal
    test_signal = np.sin(np.linspace(0, 2 * np.pi, engine.config.buffer_size)).astype(np.float32)
    source._push_chunk(test_signal)
    
    # Manually pop the chunk and run analysis (simulating the thread loop)
    chunk = source.read_chunk()
    features = engine.analyzer.analyze(chunk)
    engine._latest_features["dummy_src"] = features
    
    fetched_features = engine.get_features("dummy_src")
    assert fetched_features is not None
    assert fetched_features.rms > 0.0
    assert len(fetched_features.spectrum) == 128
    
    engine.stop()
    assert engine._is_running is False
    assert source.is_active is False

def test_audio_engine_event_bus():
    from vjlive3.core.event_bus import EventBus
    
    # Reset singleton just in case
    EventBus._instance = None
    event_bus = EventBus()
    
    events_received = []
    
    def on_features_updated(payload):
        events_received.append(("AudioFeaturesUpdated", payload["source_id"]))
        
    def on_beat_detected(payload):
        events_received.append(("BeatDetected", payload["source_id"]))
        
    event_bus.subscribe("AudioFeaturesUpdated", on_features_updated)
    event_bus.subscribe("BeatDetected", on_beat_detected)
    
    engine = AudioEngine(event_bus=event_bus)
    dev_cfg = AudioDeviceConfig(source_type=AudioSourceType.DUMMY)
    source = engine.add_source("dummy_src", dev_cfg)
    
    engine.start()
    
    # Mock a beat by feeding strong sine wave
    test_signal = np.sin(np.linspace(0, 2 * np.pi, engine.config.buffer_size)).astype(np.float32)
    
    # Fill up the beat history first
    for i in range(20):
        source._push_chunk(test_signal * 0.1)
        time.sleep(0.02) # let processing loop catch it
        
    time.sleep(0.2) # Bypass 150ms debounce
    
    # Cause spike
    for _ in range(3):
        source._push_chunk(test_signal * 2.0)
        time.sleep(0.02)
    
    time.sleep(0.1)
    engine.stop()
    
    # We should have received events
    assert len(events_received) > 0
    feature_events = [e for e in events_received if e[0] == "AudioFeaturesUpdated"]
    beat_events = [e for e in events_received if e[0] == "BeatDetected"]
    
    assert len(feature_events) > 0
    assert feature_events[0][1] == "dummy_src"
    assert len(beat_events) > 0
    assert beat_events[0][1] == "dummy_src"
