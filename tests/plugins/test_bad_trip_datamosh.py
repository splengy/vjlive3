import pytest
from unittest.mock import MagicMock
from vjlive3.plugins.bad_trip_datamosh import BadTripDatamoshEffect

@pytest.fixture
def effect():
    # Setup
    e = BadTripDatamoshEffect()
    # Mock set_uniform since we don't have a real GL context during unit test generally, 
    # unless Effect base class handles it gracefully without a context.
    e.set_uniform = MagicMock()
    return e

def test_initialization(effect):
    assert effect.name == 'bad_trip_datamosh'
    assert len(effect.params) == 12
    assert effect.params['anxiety'] == 6.0
    assert effect.params['doom'] == 4.0

def test_map_param(effect):
    # Test valid range
    effect.params['anxiety'] = 5.0
    assert effect._map_param('anxiety', 0.0, 10.0) == 5.0
    
    # Test min clamp
    effect.params['anxiety'] = -5.0
    assert effect._map_param('anxiety', 0.0, 10.0) == 0.0
    
    # Test max clamp
    effect.params['anxiety'] = 15.0
    assert effect._map_param('anxiety', 0.0, 10.0) == 10.0
    
    # Test 0-1 mapping
    effect.params['demon_face'] = 5.0
    assert effect._map_param('demon_face', 0.0, 1.0) == 0.5

def test_load_preset(effect):
    # Set to some random values
    effect.params['anxiety'] = 1.0
    effect.params['demon_face'] = 1.0
    
    # Load preset
    effect.load_preset('arachnophobia')
    
    # Verify exact preset values applied
    assert effect.params['insect_crawl'] == 10.0
    assert effect.params['shadow_people'] == 8.0
    assert effect.params['anxiety'] == 8.0
    assert effect.params['demon_face'] == 2.0
    
    # Verify others are zeroed out as per merge behavior
    assert effect.params['void_gaze'] == 0.0
    
    # Load unknown preset does nothing
    effect.load_preset('unknown_preset')
    assert effect.params['anxiety'] == 8.0

def test_apply_uniforms_no_audio(effect):
    effect.apply_uniforms(time=1.0, resolution=(1920, 1080))
    
    # Check that 12 uniforms were set
    assert effect.set_uniform.call_count == 12
    
    # Check specific calls
    # Note: MagicMock records arguments as tuples.
    # We can inspect the calls
    calls = {call[0][0]: call[0][1] for call in effect.set_uniform.call_args_list}
    
    assert calls['u_anxiety'] == 6.0
    assert calls['u_demon_face'] == 0.4
    assert calls['u_doom'] == 0.4

def test_apply_uniforms_with_audio(effect):
    mock_audio = MagicMock()
    mock_audio.get_energy.return_value = 1.0
    mock_audio.get_band.return_value = 1.0
    
    effect.apply_uniforms(time=1.0, resolution=(1920, 1080), audio_reactor=mock_audio)
    
    calls = {call[0][0]: call[0][1] for call in effect.set_uniform.call_args_list}
    
    # Anxiety (6.0) * (1.0 + 1.0 * 0.5) = 6.0 * 1.5 = 9.0
    assert calls['u_anxiety'] == 9.0
    
    # Demon Face (0.4) * (1.0 + 1.0 * 0.5) = 0.4 * 1.5 = 0.6
    assert calls['u_demon_face'] == 0.6

def test_apply_uniforms_audio_error_handling(effect):
    mock_audio = MagicMock()
    # Force an exception to test the try/except block
    mock_audio.get_energy.side_effect = Exception("Audio failure")
    
    # Should not crash
    effect.apply_uniforms(time=1.0, resolution=(1920, 1080), audio_reactor=mock_audio)
    
    calls = {call[0][0]: call[0][1] for call in effect.set_uniform.call_args_list}
    
    # Should fall back to base mapped values
    assert calls['u_anxiety'] == 6.0

def test_get_state(effect):
    state = effect.get_state()
    assert state['name'] == 'bad_trip_datamosh'
    assert 'anxiety' in state['params']
    assert state['params']['anxiety'] == 6.0
    
    # Modify params and check if returned state reflects it
    effect.params['anxiety'] = 10.0
    state2 = effect.get_state()
    assert state2['params']['anxiety'] == 10.0

def test_shader_string(effect):
    shader = effect.get_fragment_shader()
    assert "u_anxiety" in shader
    assert "u_demon_face" in shader
    assert "hasDual" in shader
    assert "u_time_loop" in shader
