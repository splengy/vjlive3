# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P2-D4_show_control.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P2-D4 — Show Control

**What This Module Does**

Implements a comprehensive show control system for VJLive3 that provides professional-level timeline management, cue stacking, and show synchronization capabilities. The Show Control module enables users to create, edit, and execute complex visual shows with precise timing, automation, and integration with external show control protocols (Art-Net, sACN, MIDI, etc.). It serves as the central orchestration layer for live performances, allowing seamless coordination of multiple visual elements, effects, and lighting controls across time.

---

## Architecture Decisions

- **Pattern:** Timeline-Based Cue Engine with Quantum-Enhanced Automation
- **Rationale:** Show control requires precise temporal coordination of multiple parameters. A timeline-based approach with keyframes provides fine-grained control over parameter evolution over time. The quantum-enhanced features (entangled keyframes, superposition states) enable advanced creative workflows like probabilistic parameter selection and AI-assisted timeline generation. The cue stack system allows for non-linear, improvisational performance control.
- **Constraints:**
  - Must support timeline durations up to 24 hours
  - Must handle 1000+ keyframes per parameter without performance degradation
  - Must provide sub-millisecond timing accuracy for cue triggering
  - Must support real-time parameter interpolation during playback
  - Must integrate with Art-Net, sACN, MIDI, and OSC protocols
  - Must enable collaborative multi-user editing
  - Must support show recording and playback
  - Must provide AI-powered timeline suggestions
  - Must export to professional show control formats
  - Must maintain 60 FPS during timeline playback

---

## Legacy References

| Codebase | File | Class/Function | Status |
|----------|------|----------------|--------|
| VJlive-2 | `core/timeline/quantum_timeline.py` (L1-20) | QuantumTimeline class | Port — main timeline engine |
| VJlive-2 | `core/timeline/quantum_timeline.py` (L417-436) | export_to_show_control | Port — export functionality |
| VJlive-2 | `core/timeline/quantum_timeline_api.py` (L209-228) | handle_get_ai_suggestions | Reference — AI integration |
| VJlive-2 | `core/timeline/quantum_timeline_api.py` (L225-244) | handle_export | Reference — export API |
| VJlive-2 | `DEVELOPER_PROMPTS/12_LASER_SYSTEM_FRAMEWORK.md` (L1-20) | Laser control framework | Reference — show control concepts |
| VJlive-2 | `WORKER_25_HARDWARE_INTEGRATION.md` (L33-52) | Hardware integration | Reference — controller support |

---

## Public Interface

```python
class ShowController:
    """Main show control orchestrator."""
    
    def __init__(self, config: ShowControlConfig) -> None:...
    def start(self) -> bool:...
    def stop(self) -> None:...
    def load_show(self, show_path: str) -> bool:...
    def save_show(self, show_path: str) -> bool:...
    def play(self) -> None:...
    def pause(self) -> None:...
    def stop_playback(self) -> None:...
    def seek(self, time: float) -> None:...
    def get_current_time(self) -> float:...
    def get_duration(self) -> float:...
    def add_cue(self, cue: Cue) -> str:...
    def remove_cue(self, cue_id: str) -> bool:...
    def update_cue(self, cue_id: str, updates: dict) -> bool:...
    def get_cue(self, cue_id: str) -> Optional[Cue]:...
    def get_all_cues(self) -> List[Cue]:...
    def trigger_cue(self, cue_id: str) -> bool:...
    def get_cue_stack(self) -> CueStack:...
    def set_cue_stack(self, stack: CueStack) -> None:...
    def export_to_show_control(self, format: str) -> dict:...
    def get_ai_suggestions(self, count: int = 10) -> List[TimelineSuggestion]:...
    def subscribe(self, event: str, callback: Callable) -> None:...
    def unsubscribe(self, event: str, callback: Callable) -> None:...
    def get_stats(self) -> dict:...

class Cue:
    """Individual cue in the show."""
    
    def __init__(self,
                 cue_id: str,
                 name: str,
                 time: float,
                 duration: float,
                 parameters: Dict[str, Any],
                 quantum_state: Optional[QuantumState] = None,
                 pre_wait: float = 0.0,
                 post_wait: float = 0.0,
                 tags: List[str] = None) -> None:...
    def to_dict(self) -> dict:...
    @staticmethod
    def from_dict(data: dict) -> 'Cue':...

class CueStack:
    """Stack of cues for sequential or triggered playback."""
    
    def __init__(self) -> None:...
    def add_cue(self, cue: Cue, position: Optional[int] = None) -> None:...
    def remove_cue(self, cue_id: str) -> bool:...
    def move_cue(self, cue_id: str, new_position: int) -> bool:...
    def get_cue_at(self, position: int) -> Optional[Cue]:...
    def get_position(self, cue_id: str) -> Optional[int]:...
    def clear(self) -> None:...
    def to_list(self) -> List[Cue]:...
    def from_list(self, cues: List[Cue]) -> None:...

class QuantumTimeline:
    """Quantum-enhanced timeline with entangled keyframes."""
    
    def __init__(self) -> None:...
    def add_parameter(self, param_path: str) -> None:...
    def remove_parameter(self, param_path: str) -> None:...
    def add_keyframe(self, param_path: str, time: float, value: Any, 
                    interpolation: InterpolationType = InterpolationType.LINEAR,
                    quantum_state: Optional[QuantumState] = None) -> str:...
    def remove_keyframe(self, param_path: str, keyframe_id: str) -> bool:...
    def update_keyframe(self, param_path: str, keyframe_id: str, 
                       updates: dict) -> bool:...
    def get_keyframes(self, param_path: str) -> List[Keyframe]:...
    def get_value_at(self, param_path: str, time: float) -> Any:...
    def get_derivative_at(self, param_path: str, time: float) -> float:...
    def entangle_keyframes(self, keyframe_ids: List[str]) -> str:...
    def entangle_parameters(self, param_paths: List[str]) -> str:...
    def get_entanglement(self, entanglement_id: str) -> Entanglement:...
    def remove_entanglement(self, entanglement_id: str) -> bool:...
    def get_ai_suggestions(self, count: int = 10) -> List[TimelineSuggestion]:...
    def record_parameter(self, param_path: str, duration: float) -> None:...
    def stop_recording(self) -> List[Keyframe]:...
    def export_to_dict(self) -> dict:...
    def import_from_dict(self, data: dict) -> None:...
```

---

## Core Components

### 1. ShowController

The central orchestrator that manages the entire show control system. It coordinates timeline playback, cue execution, parameter updates, and external protocol integration.

```python
class ShowController:
    """Main show control orchestrator."""
    
    def __init__(self, config: ShowControlConfig):
        self.config = config
        self.timeline = QuantumTimeline()
        self.cue_stack = CueStack()
        self.current_time = 0.0
        self.duration = 0.0
        self.state = ShowState.STOPPED
        self.playback_speed = 1.0
        self.loop_enabled = False
        self.quantum_seed = random.randint(0, 2**32 - 1)
        self.quantum_entanglement: Dict[str, Entanglement] = {}
        self.subscribers: Dict[str, List[Callable]] = {
            'time_update': [],
            'cue_triggered': [],
            'state_change': [],
            'parameter_change': []
        }
        self.recording_thread = None
        self.recording = False
        self.ai_suggestion_engine = AISuggestionEngine()
        
    def play(self) -> None:
        """Start or resume playback."""
        if self.state == ShowState.PLAYING:
            return
            
        self.state = ShowState.PLAYING
        self._start_playback_thread()
        self._notify_subscribers('state_change', {'state': self.state})
        
    def pause(self) -> None:
        """Pause playback."""
        if self.state != ShowState.PLAYING:
            return
            
        self.state = ShowState.PAUSED
        self._notify_subscribers('state_change', {'state': self.state})
        
    def stop_playback(self) -> None:
        """Stop playback and reset to beginning."""
        self.state = ShowState.STOPPED
        self.current_time = 0.0
        self._notify_subscribers('state_change', {'state': self.state})
        
    def seek(self, time: float) -> None:
        """Seek to specific time in show."""
        time = max(0.0, min(time, self.duration))
        self.current_time = time
        self._update_parameters_at_time(time)
        self._notify_subscribers('time_update', {'time': time})
        
    def _start_playback_thread(self) -> None:
        """Start the playback thread."""
        self.playback_thread = threading.Thread(
            target=self._playback_loop,
            daemon=True
        )
        self.playback_thread.start()
        
    def _playback_loop(self) -> None:
        """Main playback loop."""
        last_update = time.time()
        
        while self.state == ShowState.PLAYING:
            current_time = time.time()
            delta = (current_time - last_update) * self.playback_speed
            last_update = current_time
            
            # Update current time
            self.current_time += delta
            
            # Check for loop
            if self.current_time >= self.duration:
                if self.loop_enabled:
                    self.current_time %= self.duration
                else:
                    self.current_time = self.duration
                    self.state = ShowState.FINISHED
                    self._notify_subscribers('state_change', {'state': self.state})
                    break
                    
            # Update parameters based on timeline
            self._update_parameters_at_time(self.current_time)
            
            # Check for cue triggers
            self._check_cue_triggers(self.current_time)
            
            # Notify time update
            self._notify_subscribers('time_update', {'time': self.current_time})
            
            # Sleep to maintain frame rate
            time.sleep(1.0 / 60.0)  # 60 FPS
            
    def _update_parameters_at_time(self, time: float) -> None:
        """Update all parameters to their values at the given time."""
        for param_path in self.timeline.get_all_parameters():
            value = self.timeline.get_value_at(param_path, time)
            self._apply_parameter_value(param_path, value)
            
    def _apply_parameter_value(self, param_path: str, value: Any) -> None:
        """Apply a parameter value to the system."""
        # This would interface with the parameter system
        # For now, just notify subscribers
        self._notify_subscribers('parameter_change', {
            'path': param_path,
            'value': value,
            'time': self.current_time
        })
        
    def _check_cue_triggers(self, time: float) -> None:
        """Check if any cues should be triggered at this time."""
        for cue in self.cue_stack.to_list():
            if abs(cue.time - time) < 0.01:  # Within 10ms
                self._trigger_cue(cue)
                
    def _trigger_cue(self, cue: Cue) -> None:
        """Execute a cue."""
        # Apply cue parameters
        for param_path, value in cue.parameters.items():
            self._apply_parameter_value(param_path, value)
            
        # Notify subscribers
        self._notify_subscribers('cue_triggered', {
            'cue_id': cue.cue_id,
            'cue_name': cue.name,
            'time': self.current_time
        })
        
    def _notify_subscribers(self, event: str, data: dict) -> None:
        """Notify all subscribers of an event."""
        for callback in self.subscribers.get(event, []):
            try:
                callback(data)
            except Exception as e:
                logger.error(f"Error in subscriber callback for {event}: {e}")
```

### 2. QuantumTimeline

The quantum-enhanced timeline system that manages parameter keyframes, interpolation, and quantum entanglements.

```python
class QuantumTimeline:
    """Quantum-enhanced timeline with entangled keyframes."""
    
    def __init__(self):
        self.parameters: Dict[str, ParameterTrack] = {}
        self.entanglements: Dict[str, Entanglement] = {}
        self.quantum_seed = random.randint(0, 2**32 - 1)
        self.ai_engine = AISuggestionEngine()
        
    def add_parameter(self, param_path: str) -> None:
        """Add a parameter track to the timeline."""
        if param_path not in self.parameters:
            self.parameters[param_path] = ParameterTrack(param_path)
            
    def add_keyframe(self, param_path: str, time: float, value: Any,
                    interpolation: InterpolationType = InterpolationType.LINEAR,
                    quantum_state: Optional[QuantumState] = None) -> str:
        """Add a keyframe to a parameter track."""
        if param_path not in self.parameters:
            self.add_parameter(param_path)
            
        keyframe = Keyframe(
            keyframe_id=str(uuid.uuid4()),
            time=time,
            value=value,
            interpolation=interpolation,
            quantum_state=quantum_state or QuantumState.DETERMINISTIC
        )
        
        self.parameters[param_path].add_keyframe(keyframe)
        return keyframe.keyframe_id
    
    def get_value_at(self, param_path: str, time: float) -> Any:
        """Get interpolated value of a parameter at given time."""
        if param_path not in self.parameters:
            return None
            
        track = self.parameters[param_path]
        keyframes = track.get_keyframes_at_time(time)
        
        if not keyframes:
            return track.get_default_value()
            
        if len(keyframes) == 1:
            return keyframes[0].value
            
        # Find surrounding keyframes for interpolation
        kf_before, kf_after = self._find_surrounding_keyframes(keyframes, time)
        
        if kf_before is None:
            return kf_after.value
        if kf_after is None:
            return kf_before.value
            
        # Apply interpolation
        return self._interpolate(kf_before, kf_after, time)
    
    def _interpolate(self, kf1: Keyframe, kf2: Keyframe, time: float) -> Any:
        """Interpolate between two keyframes."""
        t = (time - kf1.time) / (kf2.time - kf1.time)
        
        # Apply interpolation curve
        if kf1.interpolation == InterpolationType.LINEAR:
            t_curve = t
        elif kf1.interpolation == InterpolationType.EASE_IN:
            t_curve = t * t
        elif kf1.interpolation == InterpolationType.EASE_OUT:
            t_curve = 1.0 - (1.0 - t) * (1.0 - t)
        elif kf1.interpolation == InterpolationType.EASE_IN_OUT:
            t_curve = 3 * t * t - 2 * t * t * t
        elif kf1.interpolation == InterpolationType.STEP:
            t_curve = 0.0 if t < 0.5 else 1.0
        else:
            t_curve = t
            
        # Handle quantum states
        if kf1.quantum_state == QuantumState.SUPERPOSITION:
            # Collapse superposition based on time
            if t < 0.5:
                return kf1.value
            else:
                return kf2.value
        elif kf1.quantum_state == QuantumState.ENTANGLED:
            # Value depends on entanglement
            return self._resolve_entangled_value(kf1, kf2, t)
        else:
            # Standard interpolation
            return self._lerp(kf1.value, kf2.value, t_curve)
    
    def _lerp(self, v1: Any, v2: Any, t: float) -> Any:
        """Linear interpolation between two values."""
        if isinstance(v1, (int, float)):
            return v1 + (v2 - v1) * t
        elif isinstance(v1, (tuple, list)) and len(v1) == len(v2):
            return type(v1)(a + (b - a) * t for a, b in zip(v1, v2))
        else:
            # For non-numeric types, use step interpolation
            return v1 if t < 0.5 else v2
```

### 3. Cue and CueStack

Cues represent discrete events or parameter snapshots, while cue stacks manage sequences of cues.

```python
class Cue:
    """Individual cue in the show."""
    
    def __init__(self,
                 cue_id: str,
                 name: str,
                 time: float,
                 duration: float,
                 parameters: Dict[str, Any],
                 quantum_state: Optional[QuantumState] = None,
                 pre_wait: float = 0.0,
                 post_wait: float = 0.0,
                 tags: List[str] = None):
        self.cue_id = cue_id
        self.name = name
        self.time = time
        self.duration = duration
        self.parameters = parameters.copy()
        self.quantum_state = quantum_state or QuantumState.DETERMINISTIC
        self.pre_wait = pre_wait
        self.post_wait = post_wait
        self.tags = tags or []
        
    def to_dict(self) -> dict:
        """Convert cue to dictionary for serialization."""
        return {
            'cue_id': self.cue_id,
            'name': self.name,
            'time': self.time,
            'duration': self.duration,
            'parameters': self.parameters,
            'quantum_state': self.quantum_state.value if self.quantum_state else None,
            'pre_wait': self.pre_wait,
            'post_wait': self.post_wait,
            'tags': self.tags
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'Cue':
        """Create cue from dictionary."""
        return Cue(
            cue_id=data['cue_id'],
            name=data['name'],
            time=data['time'],
            duration=data['duration'],
            parameters=data['parameters'],
            quantum_state=QuantumState(data['quantum_state']) if data.get('quantum_state') else None,
            pre_wait=data.get('pre_wait', 0.0),
            post_wait=data.get('post_wait', 0.0),
            tags=data.get('tags', [])
        )

class CueStack:
    """Stack of cues for sequential or triggered playback."""
    
    def __init__(self):
        self.cues: List[Cue] = []
        self.current_index = 0
        
    def add_cue(self, cue: Cue, position: Optional[int] = None) -> None:
        """Add a cue to the stack."""
        if position is not None:
            self.cues.insert(position, cue)
        else:
            self.cues.append(cue)
        self._sort_by_time()
        
    def _sort_by_time(self) -> None:
        """Sort cues by time."""
        self.cues.sort(key=lambda c: c.time)
        
    def get_next_cue(self, current_time: float) -> Optional[Cue]:
        """Get the next cue to be triggered."""
        for cue in self.cues:
            if cue.time > current_time:
                return cue
        return None
    
    def get_cue_at_time(self, time: float) -> List[Cue]:
        """Get all cues scheduled at a specific time."""
        return [cue for cue in self.cues if abs(cue.time - time) < 0.01]
```

### 4. Quantum Entanglement

The quantum entanglement system allows keyframes and parameters to be linked in superposition states, enabling advanced creative workflows.

```python
class Entanglement:
    """Quantum entanglement between keyframes or parameters."""
    
    def __init__(self,
                 entanglement_id: str,
                 members: List[str],
                 entanglement_type: EntanglementType,
                 seed: Optional[int] = None):
        self.entanglement_id = entanglement_id
        self.members = members  # List of keyframe IDs or parameter paths
        self.entanglement_type = entanglement_type
        self.seed = seed or random.randint(0, 2**32 - 1)
        self.collapsed = False
        self.collapsed_state = None
        
    def collapse(self, trigger_member: str) -> Dict[str, Any]:
        """Collapse the entanglement based on a trigger."""
        if self.collapsed:
            return {member: self.collapsed_state.get(member) for member in self.members}
            
        # Deterministic pseudo-random based on seed and trigger
        rng = random.Random(self.seed + hash(trigger_member))
        
        if self.entanglement_type == EntanglementType.SUPERPOSITION:
            # All members take same value
            value = rng.random()
            self.collapsed_state = {member: value for member in self.members}
        elif self.entanglement_type == EntanglementType.ENTANGLED:
            # Members have correlated but different values
            base = rng.random()
            self.collapsed_state = {
                member: (base + i * 0.1) % 1.0
                for i, member in enumerate(self.members)
            }
        elif self.entanglement_type == EntanglementType.BIPARTITE:
            # Split into two groups with opposite values
            mid = len(self.members) // 2
            value1 = rng.random()
            value2 = 1.0 - value1
            self.collapsed_state = {
                member: (value1 if i < mid else value2)
                for i, member in enumerate(self.members)
            }
            
        self.collapsed = True
        return self.collapsed_state.copy()
```

---

## Integration with External Protocols

### Art-Net Export

```python
def export_to_artnet(self, timeline: QuantumTimeline) -> dict:
    """Export timeline to Art-Net show control format."""
    artnet_data = {
        'universe': self.config.artnet_universe,
        'fps': self.config.fps,
        'frames': []
    }
    
    # Convert timeline to frames
    total_frames = int(self.duration * self.config.fps)
    for frame in range(total_frames):
        time = frame / self.config.fps
        frame_data = {
            'frame': frame,
            'time': time,
            'channels': {}
        }
        
        # Get all parameter values at this frame
        for param_path in timeline.get_all_parameters():
            value = timeline.get_value_at(param_path, time)
            # Map parameter to DMX channel
            channel = self._param_to_channel(param_path)
            frame_data['channels'][channel] = self._value_to_dmx(value)
            
        artnet_data['frames'].append(frame_data)
        
    return artnet_data
```

### sACN Export

```python
def export_to_sacn(self, timeline: QuantumTimeline) -> dict:
    """Export timeline to sACN (Streaming ACN) format."""
    sacn_data = {
        'universe': self.config.sacn_universe,
        'priority': self.config.sacn_priority,
        'sync': True,
        'preview': False,
        'data': []
    }
    
    # Similar to Art-Net but with sACN-specific fields
    # ...
    
    return sacn_data
```

### MIDI Show Control

```python
def export_to_midi(self, timeline: QuantumTimeline) -> dict:
    """Export timeline to MIDI Show Control format."""
    midi_data = {
        'format': 'MSC',
        'version': '1.0',
        'cue_list': []
    }
    
    # Convert cues to MIDI cues
    for cue in self.cue_stack.to_list():
        midi_cue = {
            'cue_number': cue.cue_id,
            'cue_name': cue.name,
            'time': cue.time,
            'midi_messages': self._parameters_to_midi(cue.parameters)
        }
        midi_data['cue_list'].append(midi_cue)
        
    return midi_data
```

---

## AI-Powered Timeline Suggestions

The system includes an AI engine that can suggest timeline improvements, auto-complete partial timelines, and generate creative parameter variations.

```python
class AISuggestionEngine:
    """AI engine for timeline suggestions."""
    
    def __init__(self):
        self.model = None  # Would load a trained model
        self.suggestion_history = []
        
    def get_suggestions(self, timeline: QuantumTimeline, count: int = 10) -> List[TimelineSuggestion]:
        """Get AI suggestions for timeline improvements."""
        suggestions = []
        
        # Analyze current timeline
        analysis = self._analyze_timeline(timeline)
        
        # Generate suggestions based on analysis
        if analysis['gaps']:
            suggestions.append(self._suggest_fill_gaps(timeline, analysis))
            
        if analysis['repetitive']:
            suggestions.append(self._suggest_variation(timeline, analysis))
            
        if analysis['timing_issues']:
            suggestions.append(self._suggest_timing_improvements(timeline, analysis))
            
        # Return top N suggestions
        return suggestions[:count]
    
    def _analyze_timeline(self, timeline: QuantumTimeline) -> dict:
        """Analyze timeline for potential improvements."""
        analysis = {
            'gaps': [],
            'repetitive': False,
            'timing_issues': [],
            'complexity': 0.0
        }
        
        # Check for gaps in parameter coverage
        for param_path in timeline.get_all_parameters():
            keyframes = timeline.get_keyframes(param_path)
            if len(keyframes) < 2:
                analysis['gaps'].append(param_path)
                
        # Check for repetitive patterns
        # ...
        
        return analysis
    
    def suggest_keyframe_insertion(self, param_path: str, time: float) -> TimelineSuggestion:
        """Suggest where to insert a keyframe."""
        # Analyze surrounding keyframes
        # Suggest interpolation type and value
        # Return suggestion with confidence score
        pass
```

---

## Performance Requirements

- **Timeline Duration:** Support up to 24 hours (86,400 seconds)
- **Keyframe Count:** Handle 1000+ keyframes per parameter without slowdown
- **Playback Timing:** Sub-millisecond accuracy for cue triggering
- **Parameter Interpolation:** < 1ms per parameter update during playback
- **Memory:** < 100MB for typical show (100 parameters, 1000 keyframes each)
- **AI Suggestions:** Generate suggestions in < 5 seconds
- **Export:** Export to Art-Net/sACN in < 10 seconds for typical show
- **Collaboration:** Support 5+ simultaneous editors with conflict resolution

---

## Testing Strategy

### Unit Tests

```python
def test_cue_creation():
    """Test creating a cue."""
    cue = Cue(
        cue_id='test_cue_1',
        name='Test Cue',
        time=10.5,
        duration=2.0,
        parameters={'intensity': 0.8, 'color': (1.0, 0.5, 0.0)}
    )
    
    assert cue.cue_id == 'test_cue_1'
    assert cue.name == 'Test Cue'
    assert cue.time == 10.5
    assert cue.duration == 2.0
    assert cue.parameters['intensity'] == 0.8

def test_cue_serialization():
    """Test cue serialization."""
    cue = Cue(
        cue_id='test_cue',
        name='Test',
        time=5.0,
        duration=1.0,
        parameters={'param': 0.5}
    )
    
    data = cue.to_dict()
    restored = Cue.from_dict(data)
    
    assert restored.cue_id == cue.cue_id
    assert restored.name == cue.name
    assert restored.time == cue.time
    assert restored.parameters == cue.parameters

def test_cue_stack_operations():
    """Test cue stack operations."""
    stack = CueStack()
    
    cue1 = Cue('c1', 'First', 0.0, 1.0, {})
    cue2 = Cue('c2', 'Second', 5.0, 1.0, {})
    cue3 = Cue('c3', 'Third', 2.5, 1.0, {})
    
    stack.add_cue(cue1)
    stack.add_cue(cue2)
    stack.add_cue(cue3)
    
    # Should be sorted by time
    assert stack.cues[0].cue_id == 'c1'
    assert stack.cues[1].cue_id == 'c3'
    assert stack.cues[2].cue_id == 'c2'
    
    # Test retrieval
    next_cue = stack.get_next_cue(1.0)
    assert next_cue.cue_id == 'c3'
```

### Integration Tests

```python
def test_timeline_playback():
    """Test complete timeline playback."""
    controller = ShowController(ShowControlConfig())
    
    # Add parameter
    controller.timeline.add_parameter('effect.intensity')
    
    # Add keyframes
    controller.timeline.add_keyframe('effect.intensity', 0.0, 0.0)
    controller.timeline.add_keyframe('effect.intensity', 5.0, 1.0)
    controller.timeline.add_keyframe('effect.intensity', 10.0, 0.5)
    
    # Set duration
    controller.duration = 15.0
    
    # Test value retrieval at various times
    assert controller.timeline.get_value_at('effect.intensity', 0.0) == 0.0
    assert controller.timeline.get_value_at('effect.intensity', 2.5) == 0.5
    assert controller.timeline.get_value_at('effect.intensity', 5.0) == 1.0
    assert controller.timeline.get_value_at('effect.intensity', 7.5) == 0.75
    assert controller.timeline.get_value_at('effect.intensity', 10.0) == 0.5

def test_cue_triggering():
    """Test cue triggering during playback."""
    controller = ShowController(ShowControlConfig())
    controller.duration = 30.0
    
    # Add cue
    cue = Cue(
        cue_id='test_cue',
        name='Test',
        time=5.0,
        duration=1.0,
        parameters={'intensity': 1.0}
    )
    controller.cue_stack.add_cue(cue)
    
    # Simulate playback to cue time
    controller.current_time = 4.9
    controller._check_cue_triggers(4.9)  # Should not trigger
    controller._check_cue_triggers(5.0)   # Should trigger
    
    # Verify cue was triggered (would need to track this)
    # ...

def test_export_to_artnet():
    """Test Art-Net export."""
    controller = ShowController(ShowControlConfig(
        artnet_universe=0,
        fps=30
    ))
    
    # Build timeline with some parameters
    controller.timeline.add_parameter('channel.1')
    controller.timeline.add_keyframe('channel.1', 0.0, 0)
    controller.timeline.add_keyframe('channel.1', 1.0, 255)
    controller.duration = 2.0
    
    # Export
    export_data = controller.export_to_show_control('artnet')
    
    assert 'universe' in export_data
    assert 'fps' in export_data
    assert 'frames' in export_data
    assert len(export_data['frames']) == 60  # 2 seconds * 30 fps
```

### Performance Tests

```python
def test_large_timeline_performance():
    """Test performance with large timeline."""
    controller = ShowController(ShowControlConfig())
    
    # Add many parameters
    for i in range(100):
        param = f'param.{i}'
        controller.timeline.add_parameter(param)
        
        # Add many keyframes
        for j in range(100):
            time = j * 0.1
            value = (i + j) % 256
            controller.timeline.add_keyframe(param, time, value)
            
    # Measure query performance
    import time
    start = time.time()
    
    for _ in range(1000):
        param = f'param.{random.randint(0, 99)}'
        time_point = random.uniform(0, 10.0)
        controller.timeline.get_value_at(param, time_point)
        
    elapsed = time.time() - start
    avg_latency = elapsed / 1000 * 1000
    
    assert avg_latency < 1.0, f"Average query latency {avg_latency:.2f}ms > 1ms budget"

def test_playback_timing_accuracy():
    """Test playback timing accuracy."""
    controller = ShowController(ShowControlConfig())
    controller.duration = 10.0
    
    # Add cue at specific time
    cue_time = 2.5
    cue = Cue('test', 'Test', cue_time, 0.1, {})
    controller.cue_stack.add_cue(cue)
    
    # Start playback
    controller.play()
    
    # Monitor time updates
    times = []
    def on_time_update(data):
        times.append(data['time'])
        
    controller.subscribe('time_update', on_time_update)
    
    # Let it run for a bit
    time.sleep(0.5)
    controller.stop_playback()
    
    # Check that cue was triggered near expected time
    triggered_times = [t for t in times if t >= cue_time and t < cue_time + 0.1]
    assert len(triggered_times) > 0, "Cue was not triggered"
```

---

## Hardware Considerations

### Real-Time Playback

- Use high-resolution timers for accurate timing
- Implement frame pacing to maintain consistent 60 FPS
- Use separate thread for playback to avoid blocking UI
- Implement jitter compensation for timing drift

```python
def _playback_loop(self) -> None:
    """Main playback loop with precise timing."""
    import time
    
    target_frame_time = 1.0 / 60.0  # 60 FPS
    last_frame_time = time.perf_counter()
    
    while self.state == ShowState.PLAYING:
        # Calculate delta time
        current_time = time.perf_counter()
        delta = current_time - last_frame_time
        last_frame_time = current_time
        
        # Update playback time
        self.current_time += delta * self.playback_speed
        
        # Process frame
        self._update_parameters_at_time(self.current_time)
        self._check_cue_triggers(self.current_time)
        
        # Sleep to maintain frame rate
        elapsed = time.perf_counter() - current_time
        sleep_time = max(0, target_frame_time - elapsed)
        time.sleep(sleep_time)
```

### Memory Management

- Use object pooling for keyframes and cues
- Implement lazy loading for large shows
- Compress stored show data
- Use memory-mapped files for very large shows

---

## Error Handling

### Graceful Degradation

```python
class ShowController:
    def __init__(self, config):
        # ...
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        
    def play(self) -> None:
        """Start playback with error handling."""
        try:
            self._validate_playback_readiness()
            super().play()
        except Exception as e:
            self.error_state = True
            self.last_error = str(e)
            logger.error(f"Failed to start playback: {e}")
            self._notify_subscribers('error', {'type': 'playback_start', 'error': str(e)})
            
    def _validate_playback_readiness(self) -> None:
        """Validate that show is ready for playback."""
        if not self.timeline.get_all_parameters():
            raise ShowControlError("No parameters in timeline")
            
        if self.duration <= 0:
            raise ShowControlError("Invalid show duration")
            
        # Check for orphaned keyframes
        # ...
```

### Recovery Mechanisms

```python
def recover_from_error(self) -> bool:
    """Attempt to recover from error state."""
    if not self.error_state:
        return True
        
    try:
        # Reset to safe state
        self.stop_playback()
        self.current_time = 0.0
        
        # Clear any corrupted state
        if self.recording:
            self._stop_recording()
            
        self.error_state = False
        self.last_error = None
        self.recovery_attempts = 0
        
        logger.info("Successfully recovered from error state")
        return True
        
    except Exception as e:
        self.recovery_attempts += 1
        if self.recovery_attempts > 3:
            logger.error(f"Recovery failed after {self.recovery_attempts} attempts")
            return False
        time.sleep(0.5 * self.recovery_attempts)
        return self.recover_from_error()
```

---

## Configuration System

### JSON Configuration

```json
{
  "show_control": {
    "enabled": true,
    "default_duration": 300.0,
    "default_fps": 60,
    "loop_enabled": false,
    "quantum_enabled": true,
    "ai_suggestions_enabled": true,
    "auto_save_interval": 60.0,
    "max_undo_steps": 100,
    "collaboration": {
      "enabled": true,
      "max_collaborators": 5,
      "conflict_resolution": "merge"
    },
    "export": {
      "artnet": {
        "enabled": true,
        "universe": 0,
        "priority": 100
      },
      "sacn": {
        "enabled": false,
        "universe": 1,
        "priority": 100
      },
      "midi": {
        "enabled": false,
        "port": "virtual"
      }
    }
  }
}
```

---

## Implementation Tips

1. **Start with Core Timeline**: Implement basic keyframe interpolation before adding quantum features
2. **Use Data Classes**: For keyframes, cues, and configuration to ensure type safety
3. **Implement Proper Cleanup**: Handle resource cleanup on show unload
4. **Add Debug Visualization**: Provide timeline editor UI with real-time preview
5. **Test Edge Cases**: Handle overlapping cues, circular entanglements, large shows
6. **Profile Early**: Measure performance with realistic show sizes
7. **Use Dependency Injection**: Make AI engine and export modules injectable
8. **Implement Undo/Redo**: Use command pattern for all user actions
9. **Add Monitoring**: Track playback timing, cue latency, memory usage
10. **Document Quantum Features**: Clearly explain superposition and entanglement concepts

---

## Performance Optimization Checklist

- [ ] Use spatial indexing for keyframe queries (R-tree or similar)
- [ ] Pre-calculate interpolation curves for smooth playback
- [ ] Cache computed values for frequently accessed times
- [ ] Use lock-free data structures for playback thread
- [ ] Implement incremental save for large shows
- [ ] Use memory pooling for keyframe objects
- [ ] Optimize AI suggestion engine with caching
- [ ] Profile hot paths with realistic workloads
- [ ] Use SIMD for bulk parameter calculations
- [ ] Implement lazy loading for show components

---

## Testing Checklist

- [ ] All unit tests pass with 100% coverage
- [ ] Integration tests verify complete show lifecycle
- [ ] Performance tests meet all latency and memory budgets
- [ ] Stress tests with maximum keyframes and parameters
- [ ] Edge case testing (empty shows, circular references, etc.)
- [ ] Hardware validation on target systems
- [ ] CI/CD pipeline runs all tests on every commit
- [ ] No memory leaks detected with valgrind
- [ ] No performance regressions compared to baseline
- [ ] AI suggestions are relevant and helpful
- [ ] Export formats are compatible with target systems
- [ ] Collaborative editing works with multiple users

---

## Definition of Done

- [ ] Spec reviewed (by Manager or User before code starts)
- [ ] All 20 tests implemented and passing
- [ ] Test coverage >= 90%
- [ ] Performance budget met on target hardware
- [ ] Timeline playback accuracy < 1ms verified
- [ ] Export compatibility verified with Art-Net and sACN
- [ ] AI suggestions quality validated
- [ ] Collaborative editing tested with 3+ users
- [ ] CI/CD pipeline runs tests on every commit
- [ ] No file over 500 lines
- [ ] No stubs in code
- [ ] Verification checkpoint box checked
- [ ] Git commit with `[Phase-2] P2-D4: Show Control` message
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written

---

## LEGACY CODE REFERENCES  

Use these to fill in the spec. These are the REAL implementations:

### core/timeline/quantum_timeline.py (L1-20) [VJlive (Original)]
```python
"""
QuantumTimeline - Revolutionary timeline system with AI collaboration and quantum-enhanced automation

Features:
- Entangled keyframes (quantum superposition of parameter states)
- AI-powered timeline suggestions and auto-completion
- Collaborative multi-user timeline editing
- Performance recording and quantum looping
- Real-time Socket.IO integration
- Export to professional show control protocols
"""

import logging
import time
import threading
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy
import numpy as np
```

This shows the overall architecture and features of the quantum timeline system.

### core/timeline/quantum_timeline.py (L417-436) [VJlive (Original)]
```python
    def export_to_show_control(self, format: str = "artnet") -> Dict[str, Any]:
        """Export timeline to professional show control protocols"""
        export_data = {
            "timeline": {
                "duration": self.current_time,
                "parameters": {},
                "quantum_properties": {
                    "seed": self.quantum_seed,
                    "entanglements": self.quantum_entanglement
                }
            }
        }
        
        for path, param in self.parameters.items():
            export_data["timeline"]["parameters"][path] = {
                "keyframes": [{
```

This shows the export interface for show control protocols.

### core/timeline/quantum_timeline_api.py (L209-228) [VJlive (Original)]
```python
        @self.socketio.on('timeline_get_ai_suggestions')
        def handle_get_ai_suggestions(data):
            """Get AI suggestions for timeline"""
            try:
                count = data.get('count', 10) if data else 10
                suggestions = self.quantum_timeline.get_ai_suggestions(count)
                emit('timeline_ai_suggestions', {'suggestions': suggestions})
            except Exception as e:
                logger.error("Error getting AI suggestions: %s", str(e))
                emit('timeline_error', {'error': str(e)})
```

This shows the AI suggestions API integration.

### core/timeline/quantum_timeline_api.py (L225-244) [VJlive (Original)]
```python
        @self.socketio.on('timeline_export')
        def handle_export(data):
            """Export timeline to show control format"""
            try:
                format = data.get('format', 'artnet')
                export_data = self.quantum_timeline.export_to_show_control(format)
                emit('timeline_export_data', {'data': export_data})
            except Exception as e:
                logger.error("Error exporting timeline: %s", str(e))
                emit('timeline_error', {'error': str(e)})
```

This shows the export API integration.

---

## Notes for Implementers

1. **Quantum Features**: Implement superposition and entanglement as creative tools, not just technical features
2. **Timeline Performance**: Use efficient data structures for keyframe queries (interval trees, R-trees)
3. **AI Integration**: Start with rule-based suggestions before implementing ML models
4. **Export Formats**: Focus on Art-Net and sACN first; MIDI show control can be added later
5. **Collaboration**: Use operational transformation or CRDTs for multi-user editing
6. **Recording**: Implement parameter recording with configurable sample rate
7. **Cue Stack**: Support both time-based and manual trigger modes
8. **Interpolation**: Provide multiple interpolation curves (linear, ease, bezier)
9. **Validation**: Validate timeline integrity (no gaps, no orphaned keyframes)
10. **Documentation**: Provide clear examples for common show control workflows

---

## Implementation Roadmap

1. **Week 1**: Design timeline data structures and keyframe system
2. **Week 2**: Implement basic timeline with linear interpolation
3. **Week 3**: Add cue stack and basic playback engine
4. **Week 4**: Implement quantum features (superposition, entanglement)
5. **Week 5**: Add AI suggestion engine (rule-based initially)
6. **Week 6**: Implement export formats (Art-Net, sACN)
7. **Week 7**: Add collaborative editing and recording
8. [ ] **Week 8**: Performance optimization and final testing

---

## Easter Egg Idea

If exactly 42 keyframes are added to a single parameter track, and the times of these keyframes form a Fibonacci sequence (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368, 75025, 121393, 196418, 317811, 514229, 832040, 1346269, 2178309, 3524578, 5702887, 9227465, 14930352, 24157817, 39088169, 63245986, 102334155, 165580141, 267914296), the ShowController enters "Golden Timeline Mode" where all parameter values automatically resolve to the golden ratio (1.618) at every keyframe, and the plugin bus broadcasts a hidden message "The timeline is in harmony" encoded in the quantum seed value, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `core/timeline/quantum_timeline.py` (to be implemented)
- `core/timeline/quantum_timeline_api.py` (to be implemented)
- `core/show_control.py` (to be implemented)
- `lib/artnet.py` (for Art-Net export)
- `lib/sacn.py` (for sACN export)
- `lib/midi.py` (for MIDI show control)
- Open Lighting Architecture (OLA)
- QLab show control software
- Timecode synchronization standards (SMPTE, LTC)
- Quantum computing concepts (superposition, entanglement)
- AI-powered creative assistance systems

---

## Conclusion

The Show Control module is the orchestration heart of VJLive3, providing professional-grade timeline management, cue control, and show synchronization capabilities. Its quantum-enhanced features enable unprecedented creative workflows, while its robust export capabilities ensure compatibility with professional lighting and show control systems. By implementing precise timing, AI-assisted timeline creation, and collaborative editing, this module will empower VJs and lighting designers to create and execute complex, synchronized visual shows with confidence and creativity.

---
>>>>>>> REPLACE