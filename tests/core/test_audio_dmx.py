import pytest
from vjlive3.core.dmx.audio_dmx import AudioDmxLink

def test_beat_trigger_mapping():
    link = AudioDmxLink()
    trigger_called = False
    
    def on_beat():
        nonlocal trigger_called
        trigger_called = True
        
    link.map_beat(on_beat)
    
    # Audio data with no beat
    link.update({"bands": [], "is_beat": False}, 0.1)
    assert not trigger_called
    
    # Audio data with beat
    link.update({"bands": [], "is_beat": True}, 0.1)
    assert trigger_called


def test_frequency_band_mapping():
    link = AudioDmxLink()
    
    # Map bass frequency to dimmer
    link.map_frequency_band(20.0, 80.0, "dimmer")
    
    # No audio data initially
    assert link.target_values["dimmer"] == 0.0
    
    # Audio data dict approach
    audio_data = {
        "bands": [
            {"low": 20.0, "high": 80.0, "amp": 0.75},
            {"low": 80.0, "high": 250.0, "amp": 0.2}
        ],
        "is_beat": False
    }
    
    link.update(audio_data, 0.1)
    assert link.target_values["dimmer"] == 0.75
    
    
def test_audio_dropout_decay():
    link = AudioDmxLink()
    
    link.map_frequency_band(20.0, 80.0, "color_intensity")
    
    # Send some active audio
    audio_data = {
        "bands": [
            {"low": 20.0, "high": 80.0, "amp": 1.0}
        ]
    }
    link.update(audio_data, 0.1)
    assert link.target_values["color_intensity"] == 1.0
    
    # Now simulate dropout (empty bands or no bands) with 0.5s delta time
    link.update({"bands": []}, 0.5)
    
    # With decay_rate of 1.0 unit per second, delta = 0.5 should reduce it by 0.5
    assert link.target_values["color_intensity"] == 0.5
    
    # Another 0.6s should clamp it to 0.0
    link.update({}, 0.6)
    assert link.target_values["color_intensity"] == 0.0


def test_clear_mappings():
    link = AudioDmxLink()
    link.map_frequency_band(20.0, 80.0, "dimmer")
    link.map_beat(lambda: None)
    
    assert len(link._band_mappings) == 1
    assert len(link._beat_mappings) == 1
    assert len(link.target_values) == 1
    
    link.clear_mappings()
    assert len(link._band_mappings) == 0
    assert len(link._beat_mappings) == 0
    assert len(link.target_values) == 0


def test_beat_exception_handling(caplog):
    link = AudioDmxLink()
    
    def failing_action():
        raise RuntimeError("Effect crashed")
        
    link.map_beat(failing_action)
    
    # Should catch exception and log, not crash update loop
    link.update({"is_beat": True}, 0.1)
    
    assert "Error in mapped beat action" in caplog.text
    assert "Effect crashed" in caplog.text
