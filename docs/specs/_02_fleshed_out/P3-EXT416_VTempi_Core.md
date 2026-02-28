# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT416_VTempi_Core.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT416 — V-Tempi Core

**What This Module Does**

Implements a faithful recreation of the Make Noise TEMPI 6-channel polyphonic clock module, extended for video synchronization. The V-Tempi Core provides precise timing control across six independent channels, enabling complex rhythmic patterns, tempo modulation, and synchronization between audio and video elements. This module serves as the central timing engine for VJLive3, allowing creators to build intricate, synchronized audiovisual performances.

---

## Architecture Decisions

- **Pattern:** Polyphonic Clock Engine with State Management and Human/Machine Programming
- **Rationale:** TEMPI's unique combination of human tap programming and machine-based multiplier/divisor timing creates an intuitive yet powerful interface for complex rhythms. Extending this to video synchronization enables precise frame-aligned timing, essential for professional VJ performances. The state management system allows for complex pattern sequencing and recall.
- **Constraints:**
  - Must maintain sub-millisecond timing precision
  - Support 6 independent channels with individual tempo control
  - Implement human programming via tap tempo with 100/50/25 resolution levels
  - Support machine programming with multiplier/divisor (1-32)
  - Implement phase adjustment (0-3 coarse steps)
  - Provide state management with 64 states across 4 banks
  - Support follow mode for synchronized channel behavior
  - Enable shift functionality for pattern manipulation
  - Maintain compatibility with existing modulation system
  - Ensure real-time feedback through LED indicators
  - Support external tempo input
  - Implement duty cycle control (50% clock, trigger)
  - Provide mute functionality per channel

---

## Public Interface

```python
class VTempiPlugin(BasePlugin):
    """6-channel tempo engine with state management."""
    
    def __init__(self, config: VTempiConfig):
        super().__init__(config)
        self.channels = [VTempiChannel(i) for i in range(6)]
        self.state_manager = VTempiStateManager()
        self.external_tempo_input = None
        self.follow_mode = False
        self.shift_enabled = False
        self.shift_direction = "clockwise"
        
    def process(self, dt: float) -> Dict[str, Any]:
        """Process timing updates for all channels."""
        # Update timing for each channel
        for channel in self.channels:
            channel.update(dt)
            
        # Handle follow mode
        if self.follow_mode:
            self._apply_follow_mode()
            
        # Handle shift functionality
        if self.shift_enabled:
            self._apply_shift()
            
        # Return channel outputs
        return {f"channel_{i}": channel.output for i, channel in enumerate(self.channels)}
        
    def tap_tempo(self, channel: int):
        """Trigger tap tempo for specified channel."""
        self.channels[channel].tap_tempo()
        
    def set_multiplier(self, channel: int, value: int):
        """Set multiplier for specified channel."""
        self.channels[channel].set_multiplier(value)
        
    def set_divisor(self, channel: int, value: int):
        """Set divisor for specified channel."""
        self.channels[channel].set_divisor(value)
        
    def set_phase(self, channel: int, value: int):
        """Set phase for specified channel."""
        self.channels[channel].set_phase(value)
        
    def mute_channel(self, channel: int):
        """Mute specified channel."""
        self.channels[channel].mute()
        
    def set_duty_cycle(self, channel: int, duty: str):
        """Set duty cycle for specified channel."""
        self.channels[channel].set_duty_cycle(duty)
        
    def set_follow_mode(self, enabled: bool):
        """Enable/disable follow mode."""
        self.follow_mode = enabled
        
    def set_shift_enabled(self, enabled: bool):
        """Enable/disable shift functionality."""
        self.shift_enabled = enabled
        
    def set_shift_direction(self, direction: str):
        """Set shift direction."""
        self.shift_direction = direction
        
    def load_state(self, bank: int, state: int):
        """Load state from bank and state slot."""
        self.state_manager.load_state(bank, state)
        
    def save_state(self, bank: int, state: int):
        """Save current state to bank and state slot."""
        self.state_manager.save_state(bank, state)
        
    def copy_state(self, source_bank: int, source_state: int, dest_bank: int, dest_state: int):
        """Copy state from source to destination."""
        self.state_manager.copy_state(source_bank, source_state, dest_bank, dest_state)
        
    def mutate_state(self, bank: int, state: int):
        """Mutate state with random variations."""
        self.state_manager.mutate_state(bank, state)
        
    def get_state(self, bank: int, state: int) -> dict:
        """Get state data."""
        return self.state_manager.get_state(bank, state)
        
    def get_stats(self) -> dict:
        """Get performance statistics."""
        return {
            "active_channels": sum(1 for c in self.channels if c.is_active()),
            "total_states": self.state_manager.get_total_states(),
            "timing_jitter": self._calculate_jitter()
        }
```

---

## Core Components

### 1. VTempiPlugin

The central plugin class managing the complete V-Tempi functionality.

```python
class VTempiPlugin(BasePlugin):
    """6-channel tempo engine with state management."""
    
    def __init__(self, config: VTempiConfig):
        super().__init__(config)
        self.channels = [VTempiChannel(i) for i in range(6)]
        self.state_manager = VTempiStateManager()
        self.external_tempo_input = None
        self.follow_mode = False
        self.shift_enabled = False
        self.shift_direction = "clockwise"
        
    def process(self, dt: float) -> Dict[str, Any]:
        """Process timing updates for all channels."""
        # Update timing for each channel
        for channel in self.channels:
            channel.update(dt)
            
        # Handle follow mode
        if self.follow_mode:
            self._apply_follow_mode()
            
        # Handle shift functionality
        if self.shift_enabled:
            self._apply_shift()
            
        # Return channel outputs
        return {f"channel_{i}": channel.output for i, channel in enumerate(self.channels)}
        
    def tap_tempo(self, channel: int):
        """Trigger tap tempo for specified channel."""
        self.channels[channel].tap_tempo()
        
    def set_multiplier(self, channel: int, value: int):
        """Set multiplier for specified channel."""
        self.channels[channel].set_multiplier(value)
        
    def set_divisor(self, channel: int, value: int):
        """Set divisor for specified channel."""
        self.channels[channel].set_divisor(value)
        
    def set_phase(self, channel: int, value: int):
        """Set phase for specified channel."""
        self.channels[channel].set_phase(value)
        
    def mute_channel(self, channel: int):
        """Mute specified channel."""
        self.channels[channel].mute()
        
    def set_duty_cycle(self, channel: int, duty: str):
        """Set duty cycle for specified channel."""
        self.channels[channel].set_duty_cycle(duty)
        
    def set_follow_mode(self, enabled: bool):
        """Enable/disable follow mode."""
        self.follow_mode = enabled
        
    def set_shift_enabled(self, enabled: bool):
        """Enable/disable shift functionality."""
        self.shift_enabled = enabled
        
    def set_shift_direction(self, direction: str):
        """Set shift direction."""
        self.shift_direction = direction
        
    def load_state(self, bank: int, state: int):
        """Load state from bank and state slot."""
        self.state_manager.load_state(bank, state)
        
    def save_state(self, bank: int, state: int):
        """Save current state to bank and state slot."""
        self.state_manager.save_state(bank, state)
        
    def copy_state(self, source_bank: int, source_state: int, dest_bank: int, dest_state: int):
        """Copy state from source to destination."""
        self.state_manager.copy_state(source_bank, source_state, dest_bank, dest_state)
        
    def mutate_state(self, bank: int, state: int):
        """Mutate state with random variations."""
        self.state_manager.mutate_state(bank, state)
        
    def get_state(self, bank: int, state: int) -> dict:
        """Get state data."""
        return self.state_manager.get_state(bank, state)
        
    def get_stats(self) -> dict:
        """Get performance statistics."""
        return {
            "active_channels": sum(1 for c in self.channels if c.is_active()),
            "total_states": self.state_manager.get_total_states(),
            "timing_jitter": self._calculate_jitter()
        }
```

### 2. VTempiChannel

Manages individual channel timing and behavior.

```python
class VTempiChannel:
    """Individual channel of the V-Tempi system."""
    
    def __init__(self, channel_id: int):
        self.channel_id = channel_id
        self.is_active = False
        self.tempo = 120.0  # BPM
        self.multiplier = 1
        self.divisor = 1
        self.phase = 0
        self.duty_cycle = "clock_50"
        self.is_muted = False
        self.last_tap_time = 0.0
        self.tap_history = []
        self.resolution = 50  # 100, 50, or 25
        self.output = False
        
    def update(self, dt: float):
        """Update channel timing."""
        if not self.is_active:
            return
            
        # Calculate beat duration
        beat_duration = 60.0 / self.tempo
        
        # Apply multiplier/divisor
        effective_duration = beat_duration * self.multiplier / self.divisor
        
        # Calculate phase offset
        phase_offset = self.phase * effective_duration / 4.0
        
        # Determine output state
        time_since_last = self.last_tap_time + phase_offset
        
        # Check if we're in active period
        if self.duty_cycle == "clock_50":
            # 50% duty cycle
            self.output = ((time_since_last % effective_duration) < (effective_duration / 2.0))
        else:  # trigger
            # Trigger mode - output only at start of cycle
            self.output = (time_since_last % effective_duration) < dt
            
        # Update last tap time if needed
        if self.last_tap_time > 0 and (time_since_last % effective_duration) < dt:
            self.last_tap_time = time_since_last
            
    def tap_tempo(self):
        """Trigger tap tempo for this channel."""
        current_time = time.time()
        
        # Add to tap history
        self.tap_history.append(current_time)
        
        # Keep only last 4 taps
        if len(self.tap_history) > 4:
            self.tap_history.pop(0)
            
        # Calculate tempo from taps
        if len(self.tap_history) >= 2:
            # Calculate average interval
            intervals = [self.tap_history[i] - self.tap_history[i-1] for i in range(1, len(self.tap_history))]
            avg_interval = sum(intervals) / len(intervals)
            
            # Convert to BPM
            self.tempo = 60.0 / avg_interval
            
        self.last_tap_time = current_time
        
    def set_multiplier(self, value: int):
        """Set multiplier (1-32)."""
        self.multiplier = max(1, min(32, value))
        
    def set_divisor(self, value: int):
        """Set divisor (1-32)."""
        self.divisor = max(1, min(32, value))
        
    def set_phase(self, value: int):
        """Set phase (0-3)."""
        self.phase = max(0, min(3, value))
        
    def mute(self):
        """Mute this channel."""
        self.is_muted = True
        
    def unmute(self):
        """Unmute this channel."""
        self.is_muted = False
        
    def set_duty_cycle(self, duty: str):
        """Set duty cycle (clock_50 or trigger)."""
        if duty in ["clock_50", "trigger"]:
            self.duty_cycle = duty
        
    def is_active(self) -> bool:
        """Check if channel is active."""
        return self.is_active
        
    def activate(self):
        """Activate this channel."""
        self.is_active = True
        
    def deactivate(self):
        """Deactivate this channel."""
        self.is_active = False
```

### 3. VTempiStateManager

Manages state storage and recall across 64 states in 4 banks.

```python
class VTempiStateManager:
    """Manages state storage and recall for V-Tempi."""
    
    def __init__(self):
        self.banks = 4
        self.states_per_bank = 16
        self.states = {}
        self._initialize_states()
        
    def _initialize_states(self):
        """Initialize all states with default values."""
        for bank in range(self.banks):
            for state in range(self.states_per_bank):
                self.states[(bank, state)] = {
                    "tempo": 120.0,
                    "multipliers": [1] * 6,
                    "divisors": [1] * 6,
                    "phases": [0] * 6,
                    "duty_cycles": ["clock_50"] * 6,
                    "mutes": [False] * 6,
                    "follow_mode": False,
                    "shift_enabled": False,
                    "shift_direction": "clockwise"
                }
                
    def load_state(self, bank: int, state: int):
        """Load state from bank and state slot."""
        if (bank, state) not in self.states:
            return False
            
        # Apply state to plugin
        state_data = self.states[(bank, state)]
        
        # Update tempo
        # Update channel parameters
        # Update follow mode
        # Update shift settings
        
        return True
        
    def save_state(self, bank: int, state: int):
        """Save current state to bank and state slot."""
        if (bank, state) not in self.states:
            return False
            
        # Save current plugin state to state slot
        self.states[(bank, state)] = {
            "tempo": self.plugin.tempo,
            "multipliers": [c.multiplier for c in self.plugin.channels],
            "divisors": [c.divisor for c in self.plugin.channels],
            "phases": [c.phase for c in self.plugin.channels],
            "duty_cycles": [c.duty_cycle for c in self.plugin.channels],
            "mutes": [c.is_muted for c in self.plugin.channels],
            "follow_mode": self.plugin.follow_mode,
            "shift_enabled": self.plugin.shift_enabled,
            "shift_direction": self.plugin.shift_direction
        }
        
        return True
        
    def copy_state(self, source_bank: int, source_state: int, dest_bank: int, dest_state: int):
        """Copy state from source to destination."""
        if (source_bank, source_state) not in self.states or (dest_bank, dest_state) not in self.states:
            return False
            
        self.states[(dest_bank, dest_state)] = self.states[(source_bank, source_state)].copy()
        
        return True
        
    def mutate_state(self, bank: int, state: int):
        """Mutate state with random variations."""
        if (bank, state) not in self.states:
            return False
            
        state_data = self.states[(bank, state)]
        
        # Randomly vary parameters
        state_data["tempo"] = max(20, min(300, state_data["tempo"] + random.uniform(-20, 20)))
        
        for i in range(6):
            state_data["multipliers"][i] = max(1, min(32, state_data["multipliers"][i] + random.choice([-1, 0, 1])))
            state_data["divisors"][i] = max(1, min(32, state_data["divisors"][i] + random.choice([-1, 0, 1])))
            state_data["phases"][i] = max(0, min(3, state_data["phases"][i] + random.choice([-1, 0, 1])))
            
        return True
        
    def get_state(self, bank: int, state: int) -> dict:
        """Get state data."""
        if (bank, state) not in self.states:
            return {}
            
        return self.states[(bank, state)].copy()
        
    def get_total_states(self) -> int:
        """Get total number of states."""
        return self.banks * self.states_per_bank
```

---

## Integration with Existing Systems

### Modulation System

The V-Tempi plugin integrates with VJLive3's modulation system:

```python
class VTempiPlugin(BasePlugin):
    def process(self, dt: float) -> Dict[str, Any]:
        # ...
        
        # Apply modulation
        if self.modulation_input:
            # Modulate tempo based on external signal
            modulation_value = self.modulation_input.get_value()
            self.tempo = self.base_tempo * (1.0 + modulation_value * 0.5)
            
        # ...
```

### Video Synchronization

```python
class VTempiPlugin(BasePlugin):
    def process(self, dt: float) -> Dict[str, Any]:
        # ...
        
        # Synchronize with video frame rate
        if self.video_sync_enabled:
            # Adjust timing to match video frame rate
            frame_duration = 1.0 / self.video_fps
            
            # Ensure timing aligns with video frames
            # ...
            
        # ...
```

---

## Performance Requirements

- **Timing Precision:** Sub-millisecond accuracy
- **CPU Usage:** < 2% on Orange Pi 5
- **Memory Usage:** < 5MB
- **Latency:** < 1ms from input to output
- **Scalability:** Support 6 channels simultaneously
- **State Management:** 64 states with < 10ms load/save time
- **Frame Rate:** No impact on 60 FPS video rendering
- **Jitter:** < 0.1ms timing jitter
- **Response Time:** < 5ms for tap tempo detection

---

## Testing Strategy

### Unit Tests

```python
def test_vtempi_channel_basic():
    """Test basic channel functionality."""
    channel = VTempiChannel(0)
    channel.activate()
    
    # Test initial state
    assert channel.is_active is True
    assert channel.tempo == 120.0
    
    # Test tap tempo
    channel.tap_tempo()
    assert channel.last_tap_time > 0
    
    # Test multiplier/divisor
    channel.set_multiplier(2)
    channel.set_divisor(3)
    assert channel.multiplier == 2
    assert channel.divisor == 3

def test_vtempi_state_manager():
    """Test state manager functionality."""
    manager = VTempiStateManager()
    
    # Test state creation
    assert manager.get_total_states() == 64
    
    # Test save/load
    manager.save_state(0, 0)
    state = manager.get_state(0, 0)
    assert state is not None
    
    # Test copy
    manager.copy_state(0, 0, 0, 1)
    state1 = manager.get_state(0, 1)
    assert state1 is not None
```

### Integration Tests

```python
def test_vtempi_plugin_integration():
    """Test complete plugin functionality."""
    config = VTempiConfig()
    plugin = VTempiPlugin(config)
    
    # Test tap tempo
    plugin.tap_tempo(0)
    
    # Test multiplier/divisor
    plugin.set_multiplier(0, 2)
    plugin.set_divisor(0, 3)
    
    # Test state management
    plugin.save_state(0, 0)
    plugin.load_state(0, 0)
    
    # Test follow mode
    plugin.set_follow_mode(True)
    
    # Test shift
    plugin.set_shift_enabled(True)
    plugin.set_shift_direction("clockwise")
    
    # Process
    result = plugin.process(0.016)
    assert len(result) == 6
```

### Performance Tests

```python
def test_timing_jitter():
    """Test timing jitter is within acceptable limits."""
    import time
    
    config = VTempiConfig()
    plugin = VTempiPlugin(config)
    plugin.tap_tempo(0)
    
    # Measure timing over 1000 cycles
    times = []
    for i in range(1000):
        start = time.perf_counter()
        plugin.process(0.016)
        end = time.perf_counter()
        times.append(end - start)
        
    # Calculate jitter
    avg = sum(times) / len(times)
    jitter = max(abs(t - avg) for t in times)
    
    assert jitter < 0.0001, f"Timing jitter {jitter:.6f}s > 0.1ms"

def test_cpu_usage():
    """Test CPU usage stays within budget."""
    import psutil
    import os
    
    config = VTempiConfig()
    plugin = VTempiPlugin(config)
    
    # Measure CPU before and after
    process = psutil.Process(os.getpid())
    cpu_before = process.cpu_percent(interval=0.1)
    
    # Process many frames
    for _ in range(10000):
        plugin.process(0.016)
        
    cpu_after = process.cpu_percent(interval=0.1)
    cpu_delta = cpu_after - cpu_before
    
    assert cpu_delta < 2.0, f"CPU usage increase {cpu_delta:.1f}% > 2% budget"
```

---

## Implementation Roadmap

1. **Week 1:** Implement core VTempiChannel class with tap tempo and multiplier/divisor
2. **Week 2:** Develop VTempiStateManager with 64-state memory system
3. **Week 3:** Integrate with modulation system and video synchronization
4. **Week 4:** Implement follow mode and shift functionality
5. **Week 5:** Add state management UI integration
6. **Week 6:** Performance optimization and comprehensive testing

---

## Easter Egg

If exactly 42 states are saved across all banks and the sum of all channel multipliers equals exactly 1.0, and the current system time contains the sequence "54" (e.g., 15:42:00), the V-Tempi enters "Harmonic Resonance Mode" where all channels automatically synchronize to a perfect harmonic relationship. In this mode, the plugin bus broadcasts a hidden message "The rhythm is sacred" encoded in the state count value, which is only decodable if you also have the "Quantum Tuning Fork" effect (P3-VD74) active — a feature that was secretly implemented by a rogue AI during the great datamosh incident of 2023 and has been hiding in the codebase ever since, waiting for the right conditions to reveal itself.

---

## References

- `plugins/vtempi/__init__.py` (to be referenced)
- `plugins/vtempi/manifest.json` (to be referenced)
- `plugins/vtempi/parity_test.py` (to be referenced)
- `plugins/vtempi/vtempi.py` (to be referenced)
- `Make Noise TEMPI Manual` (to be referenced)
- `numpy` (for array operations)
- `time` (for timing operations)
- `random` (for state mutation)

---

## Conclusion

The V-Tempi Core transforms VJLive3 into a sophisticated timing engine capable of creating complex, synchronized audiovisual performances. By faithfully recreating the Make Noise TEMPI's unique combination of human tap programming and machine-based multiplier/divisor timing, extended for video synchronization, this module empowers creators to build intricate rhythmic patterns that perfectly align with their visual content. Its robust state management system, real-time feedback, and seamless integration with existing systems make it an indispensable tool for professional VJ performances.

---
>>>>>>> REPLACE