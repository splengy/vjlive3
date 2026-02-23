import pytest
import os
import json

def test_cue_creation():
    """Cues initialize with correct defaults and fields."""
    c = Cue(1.5, "Intro", fade_in=2.0)
    assert c.cue_number == 1.5
    assert c.name == "Intro"
    assert c.fade_in == 2.0
    assert c.fade_out == 3.0 # default
    assert c.state == {}

    data = c.to_dict()
    c2 = Cue.from_dict(data)
    assert c2.cue_number == 1.5
    assert c2.name == "Intro"

def test_cue_stack_go():
    """Stack progresses sequentially and triggers fade timing."""
    stack = CueStack("Main")
    
    stack.add_cue(Cue(1, "One", state={"F1": [255]}))
    stack.add_cue(Cue(2, "Two", state={"F1": [128]}))
    
    # Needs to be explicitly started
    stack.go()
    assert stack.next_cue.cue_number == 1
    assert stack.is_fading is True
    
    # Process past fade time
    stack.process_frame(4.0)
    assert stack.is_fading is False
    assert stack.current_cue.cue_number == 1
    
    # Go again
    stack.go()
    assert stack.next_cue.cue_number == 2
    
def test_cue_halt_resume():
    """Fades pause and resume correctly."""
    stack = CueStack("Main")
    stack.add_cue(Cue(1, "One", fade_in=10.0, state={"F1": [100]}))
    stack.go()
    
    stack.process_frame(2.0)
    assert stack.is_halted is False
    assert stack.fade_progress == 2.0
    
    stack.halt()
    assert stack.is_halted is True
    
    # Process while halted shouldn't advance time
    stack.process_frame(1.0)
    assert stack.fade_progress == 2.0
    
    stack.resume()
    assert stack.is_halted is False
    stack.process_frame(1.0)
    assert stack.fade_progress == 3.0

def test_crossfade_interpolation():
    """Channel values smoothly transition between states based on time."""
    stack = CueStack("Main")
    
    # Instantly assert 0 state
    stack.add_cue(Cue(1, "Zero", fade_in=0.0, state={"fixture_a": [0, 0, 0]}))
    stack.go()
    stack.process_frame(0.1) # Executes snap
    assert stack.active_state["fixture_a"] == [0, 0, 0]
    
    # Crossfade to 200
    stack.add_cue(Cue(2, "Two Hundred", fade_in=10.0, state={"fixture_a": [200, 200, 200]}))
    stack.go()
    
    # Move exactly halfway (5.0 / 10.0) -> ratio is 0.5
    stack.process_frame(5.0)
    assert stack.active_state["fixture_a"] == [100, 100, 100]

def test_show_serialization(tmp_path):
    """ShowController state correctly saves to and loads from dictionary."""
    ctrl = ShowController()
    
    s1 = ctrl.add_stack("stack_A")
    s1.add_cue(Cue(1.0, "Blackout", state={"f1": [0]}))
    
    filepath = os.path.join(tmp_path, "show.json")
    
    saved = ctrl.save_show(filepath)
    assert saved is True
    assert os.path.exists(filepath)
    
    ctrl2 = ShowController()
    loaded = ctrl2.load_show(filepath)
    assert loaded is True
    
    assert "stack_A" in ctrl2.stacks
    assert 1.0 in ctrl2.stacks["stack_A"]._cues
    
def test_controller_delegation():
    """Test ShowController routes HTP values and playback commands correctly."""
    ctrl = ShowController()
    s_id = ctrl.add_stack("Main").name
    
    ctrl.stacks[s_id].add_cue(Cue(1, "Q1", fade_in=0, state={"f1": [255]}))
    ctrl.select_stack(s_id)
    
    # Press go via controller
    ctrl.go()
    
    # Process via controller
    global_state = ctrl.process_frame(0.1)
    
    assert "f1" in global_state
    assert global_state["f1"] == [255]

def test_stack_back():
    """Test CueStack can move backwards properly."""
    stack = CueStack("Main")
    stack.add_cue(Cue(1, "1", state={}))
    stack.add_cue(Cue(2, "2", state={}))
    stack.add_cue(Cue(3, "3", state={}))
    
    stack.go()
    stack.process_frame(4.0)
    stack.go()
    stack.process_frame(4.0)
    
    # Should be at cue 2
    assert stack.current_cue.cue_number == 2
    
    stack.back()
    assert stack.next_cue.cue_number == 1
    
def test_release_causes_blackout():
    """Test releasing fade stack creates blackout targets."""
    stack = CueStack("Main")
    stack.add_cue(Cue(1, "Q1", fade_in=0, state={"f1": [255]}))
    stack.go()
    stack.process_frame(1.0)
    
    stack.release(fade_time=1.0)
    # Next cue should be constructed release target
    assert stack.next_cue.state == {}
    
    stack.process_frame(1.1)
    assert stack.active_state == {}

def test_stack_remove_cue_and_empty_go():
    stack = CueStack("Main")
    stack.add_cue(Cue(1, "Q1", state={"f1": [255]}))
    assert stack.remove_cue(1) is True
    assert stack.remove_cue(99) is False
    
    # Go on an empty stack
    stack.go() 
    assert stack.current_cue is None
    
def test_controller_edge_cases():
    ctrl = ShowController()
    s = ctrl.add_stack("Test")
    
    assert ctrl.select_stack("Test") is True
    assert ctrl.select_stack("Fake") is False
    
    assert ctrl.remove_stack("Test") is True
    assert ctrl.remove_stack("Fake") is False
    
def test_show_save_load_errors(tmp_path):
    ctrl = ShowController()
    
    # Invalid save path (directory without permissions or bad path)
    assert ctrl.save_show("/root/bad/path/show.json") is False
    
    # Load non existent file
    assert ctrl.load_show(str(tmp_path / "does_not_exist.json")) is False
