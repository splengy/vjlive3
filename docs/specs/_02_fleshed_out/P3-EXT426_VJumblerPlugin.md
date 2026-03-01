# P3-EXT426: Make Noise Jumbler

## Task: P3-EXT426 — Make Noise Jumbler

**What This Module Does**

The VJumblerPlugin is a chaotic signal routing and mutation processor that emulates the Make Noise Jumbler Eurorack module. It creates complex, evolving audio textures through analog-style signal routing, voltage-controlled chaos generation, and dynamic signal mutation. The module processes audio and CV signals through a network of interconnected processing stages that create unpredictable yet musically useful results.

**What This Module Does NOT Do**

- Does not implement traditional delay or reverb effects
- Does not provide standard filter or distortion processing
- Does not support MIDI or OSC control interfaces
- Does not include preset management or patch storage
- Does not perform real-time pitch shifting or time stretching

## Public Interface

```python
class VJumblerPlugin(EffectNode):
    """
    Software virtualization of Make Noise Jumbler - chaotic signal routing and mutation processor.
    
    Creates complex, evolving audio textures through analog-style signal routing and voltage-controlled chaos.
    """
    
    def __init__(self) -> None:
        super().__init__("jumbler")
        
        # Core processing parameters (0-10 scale)
        self.set_parameter("chaos_amount", 5.0)           # Overall chaos intensity
        self.set_parameter("mutation_rate", 3.0)          # Signal mutation frequency
        self.set_parameter("routing_complexity", 4.0)     # Signal path complexity
        self.set_parameter("feedback_amount", 2.0)        # Internal feedback level
        self.set_parameter("modulation_depth", 3.0)       # Modulation intensity
        self.set_parameter("random_seed", 0.0)            # Chaos seed (0-10)
        self.set_parameter("smoothing_time", 2.0)         # Signal smoothing duration
        self.set_parameter("threshold_level", 4.0)        # Signal threshold for mutation
        
        # Input/output configuration
        self.set_input("audio_in", AudioInput())         # Main audio input
        self.set_input("cv_control", CVInput())          # Control voltage input
        self.set_output("audio_out", AudioOutput())      # Processed audio output
        self.set_output("chaos_out", CVOutput())         # Chaos signal output
        
        # Internal state
        self._chaos_generator = ChaosGenerator()
        self._signal_router = SignalRouter()
        self._mutation_engine = MutationEngine()
        self._feedback_buffer = CircularBuffer(size=4096)
        self._random_state = np.random.RandomState()
```

## Inputs and Outputs

| Name | Type | Description | Constraints |
|------|------|-------------|-------------|
| `audio_in` | `AudioInput` | Main audio signal input | 44.1kHz-192kHz, 16-32 bit |
| `cv_control` | `CVInput` | Control voltage modulation input | -10V to +10V range |
| `audio_out` | `AudioOutput` | Processed audio output | Same format as input |
| `chaos_out` | `CVOutput` | Generated chaos signal | 0V to +10V range |

## Core Processing Architecture

### Chaos Generation System
```python
class ChaosGenerator:
    """Generates chaotic signals using mathematical chaos algorithms."""
    
    def generate_chaos(self, amount: float, seed: int) -> np.ndarray:
        """
        Generate chaotic signal using logistic map and other chaos algorithms.
        
        Parameters:
        - amount: Chaos intensity (0.0-1.0)
        - seed: Random seed for reproducibility
        
        Returns:
        - np.ndarray: Chaotic signal buffer
        """
        # Logistic map chaos: x[n+1] = r * x[n] * (1 - x[n])
        r = 3.57 + (amount * 0.43)  # Chaos threshold (3.57-4.0)
        x = np.random.rand(buffer_size)
        
        for i in range(100):  # Warm up iterations
            x = r * x * (1 - x)
        
        # Add other chaos sources
        if amount > 0.7:
            # Lorenz attractor for high chaos
            x += self._lorenz_attractor(seed, amount)
        
        if amount > 0.9:
            # Rossler attractor for extreme chaos
            x += self._rossler_attractor(seed, amount)
        
        return x * amount
```

### Signal Routing Network
```python
class SignalRouter:
    """Analog-style signal routing with voltage-controlled paths."""
    
    def route_signals(self, input_signal: np.ndarray, 
                     complexity: float, 
                     chaos: np.ndarray) -> np.ndarray:
        """
        Route signals through complex network with voltage-controlled paths.
        
        Parameters:
        - input_signal: Input audio signal
        - complexity: Routing complexity (0.0-1.0)
        - chaos: Chaos control signal
        
        Returns:
        - np.ndarray: Routed output signal
        """
        # Create routing matrix based on complexity
        matrix_size = int(4 + (complexity * 8))  # 4-12 routing nodes
        routing_matrix = self._generate_routing_matrix(matrix_size, complexity)
        
        # Apply chaos modulation to routing
        chaos_modulated = chaos[:matrix_size] * complexity
        routing_matrix += chaos_modulated[:, np.newaxis]
        
        # Process through routing network
        output = np.zeros_like(input_signal)
        for i in range(matrix_size):
            gain = 1.0 / matrix_size
            output += input_signal * routing_matrix[i] * gain
        
        return output
```

### Mutation Engine
```python
class MutationEngine:
    """Applies various signal mutations based on control parameters."""
    
    def mutate_signal(self, signal: np.ndarray, 
                     rate: float, 
                     depth: float, 
                     threshold: float) -> np.ndarray:
        """
        Apply signal mutations including bit crushing, sample rate reduction,
        and dynamic distortion.
        
        Parameters:
        - signal: Input signal to mutate
        - rate: Mutation rate (0.0-1.0)
        - depth: Mutation depth (0.0-1.0)
        - threshold: Signal threshold for mutation activation
        
        Returns:
        - np.ndarray: Mutated signal
        """
        # Bit crushing
        if rate > 0.3:
            bit_depth = 16 - int(rate * 12)
            signal = self._bit_crush(signal, bit_depth)
        
        # Sample rate reduction
        if rate > 0.6:
            reduction_factor = 1.0 + (rate * 4.0)
            signal = self._sample_rate_reduce(signal, reduction_factor)
        
        # Dynamic distortion
        if depth > 0.4:
            drive = depth * 10.0
            signal = self._soft_clip(signal, drive)
        
        # Threshold-based mutation
        signal = np.where(np.abs(signal) > threshold * 0.1,
                         signal * (1.0 + depth * 0.5),
                         signal)
        
        return signal
```

## Mathematical Processing Details

### Chaos Signal Generation
- **Logistic Map**: x[n+1] = r * x[n] * (1 - x[n]) where r ∈ [3.57, 4.0]
- **Lyapunov Exponent**: Measures chaos intensity, calculated as λ = lim(n→∞) (1/n) ∑ log|f'(x[i])|
- **Frequency Spectrum**: Chaos signals contain broadband noise with 1/f characteristics

### Signal Processing
- **Sample Rate**: 44.1kHz, 48kHz, 96kHz, or 192kHz depending on input
- **Bit Depth**: 16, 24, or 32-bit floating point processing
- **Buffer Size**: 512 or 1024 samples for real-time processing
- **Latency**: <10ms total processing latency

### Routing Algorithms
- **Matrix Routing**: NxN routing matrix with voltage-controlled gains
- **Feedback Paths**: Multiple feedback loops with variable delay times
- **Cross-Modulation**: Non-linear mixing of routed signals

## Edge Cases and Error Handling

### Parameter Edge Cases
- **chaos_amount = 0**: Pure signal routing without chaos (deterministic behavior)
- **chaos_amount = 10**: Maximum chaos (fully unpredictable output)
- **mutation_rate = 0**: No signal mutation (clean processing)
- **mutation_rate = 10**: Maximum mutation (extreme signal degradation)
- **routing_complexity = 0**: Direct signal path (no routing)
- **routing_complexity = 10**: Maximum routing complexity (12-node network)

### Error Scenarios
- **Missing Audio Input**: Generates silence with chaos signal only
- **Invalid Sample Rate**: Resamples to nearest supported rate
- **Memory Overflow**: Reduces buffer size and complexity automatically
- **CPU Overload**: Simplifies processing chain to maintain real-time performance

## Dependencies

### Internal Dependencies
- **Base Class**: `EffectNode` (provides core effect functionality)
- **Audio Processing**: `AudioInput`, `AudioOutput` for signal I/O
- **CV Processing**: `CVInput`, `CVOutput` for control voltage I/O
- **Math Libraries**: `numpy` for array operations and signal processing
- **Random Generation**: `numpy.random` for chaos generation

### External Dependencies
- **NumPy**: For efficient array operations and mathematical functions
- **SciPy**: Optional for advanced signal processing (if available)
- **SoundCard Drivers**: For audio I/O functionality

## Test Plan

### Unit Tests
```python
def test_jumbler_initialization():
    """Verify VJumblerPlugin initializes correctly."""
    plugin = VJumblerPlugin()
    assert plugin.parameters['chaos_amount'] == 5.0
    assert plugin.parameters['mutation_rate'] == 3.0
    assert plugin.parameters['routing_complexity'] == 4.0
    assert plugin.parameters['feedback_amount'] == 2.0
    assert plugin.parameters['modulation_depth'] == 3.0
    assert plugin.parameters['random_seed'] == 0.0
    assert plugin.parameters['smoothing_time'] == 2.0
    assert plugin.parameters['threshold_level'] == 4.0
    
    # Verify I/O configuration
    assert len(plugin.inputs) == 2
    assert len(plugin.outputs) == 2


def test_chaos_generation():
    """Verify chaos generation produces expected results."""
    generator = ChaosGenerator()
    
    # Test different chaos levels
    low_chaos = generator.generate_chaos(0.3, 42)
    high_chaos = generator.generate_chaos(0.9, 42)
    
    # Verify chaos intensity
    assert np.std(low_chaos) < np.std(high_chaos)
    assert np.mean(np.abs(low_chaos)) < np.mean(np.abs(high_chaos))


def test_signal_routing():
    """Verify signal routing produces expected results."""
    router = SignalRouter()
    
    # Test different complexity levels
    simple_route = router.route_signals(test_signal, 0.2, test_chaos)
    complex_route = router.route_signals(test_signal, 0.8, test_chaos)
    
    # Verify routing complexity
    assert np.std(simple_route) < np.std(complex_route)
    assert len(np.unique(simple_route)) < len(np.unique(complex_route))
```

### Integration Tests
```python
def test_full_processing_chain():
    """Verify complete processing chain works correctly."""
    plugin = VJumblerPlugin()
    
    # Test with various parameter combinations
    for chaos in [0.0, 5.0, 10.0]:
        for mutation in [0.0, 5.0, 10.0]:
            for routing in [0.0, 5.0, 10.0]:
                # Set parameters
                plugin.parameters['chaos_amount'] = chaos
                plugin.parameters['mutation_rate'] = mutation
                plugin.parameters['routing_complexity'] = routing
                
                # Process test signal
                output = plugin.process(test_audio)
                
                # Verify output is valid
                assert output is not None
                assert output.shape == test_audio.shape
                assert np.issubdtype(output.dtype, np.floating)


def test_performance_60fps():
    """Verify effect maintains 60 FPS minimum."""
    plugin = VJumblerPlugin()
    
    for _ in range(100):  # 100 frames test
        start_time = time.time()
        plugin.process(test_audio)
        render_time = time.time() - start_time
        
        # Verify 60 FPS minimum (16.67ms per frame)
        assert render_time <= 0.01667
```

### Audio Quality Tests
```python
def test_audio_quality():
    """Verify audio quality meets standards."""
    plugin = VJumblerPlugin()
    
    # Test with various input signals
    for test_signal in [sine_wave, square_wave, noise, music_clip]:
        output = plugin.process(test_signal)
        
        # Verify no clipping
        assert np.max(np.abs(output)) <= 1.0
        
        # Verify frequency response
        freq_response = np.abs(np.fft.fft(output))
        assert np.mean(freq_response) > 0.01  # Not silent


def test_chaos_consistency():
    """Verify chaos generation is reproducible with same seed."""
    generator = ChaosGenerator()
    
    # Generate with same seed
    chaos1 = generator.generate_chaos(0.7, 42)
    chaos2 = generator.generate_chaos(0.7, 42)
    
    # Should be identical with same seed
    assert np.allclose(chaos1, chaos2, atol=1e-5)
    
    # Different seed should produce different results
    chaos3 = generator.generate_chaos(0.7, 43)
    assert not np.allclose(chaos1, chaos3, atol=1e-5)
```

## Definition of Done

- [ ] Spec reviewed and approved by Manager
- [ ] All unit tests pass (logic, chaos generation, signal routing)
- [ ] All integration tests pass (full processing chain, performance)
- [ ] Audio quality tests pass (no clipping, valid frequency response)
- [ ] Performance verified at 60 FPS minimum
- [ ] No file over 750 lines
- [ ] No stubs in code
- [ ] Comprehensive documentation completed
- [ ] Test coverage ≥80%
- [ ] Git commit with `[P3-EXT426] Make Noise Jumbler: chaotic signal processor`
- [ ] BOARD.md updated
- [ ] Lock released
- [ ] AGENT_SYNC.md handoff note written
- [ ] 🎁 **Easter Egg Reward**: THANK YOU for your rigorous work! As a reward for reaching Phase 2, please invent a highly creative, secret "easter egg" specifically for this module, and submit it to `WORKSPACE/EASTEREGG_COUNCIL.md` before picking up your next task.

## LEGACY CODE REFERENCES  
Use these to fill in the spec. These are the REAL implementations:

### vjlive/plugins/make_noise/jumbler.py (L1-20)  
```python
"""
Make Noise Jumbler - Chaotic Signal Routing and Mutation Processor

Creates complex, evolving audio textures through analog-style signal routing and voltage-controlled chaos.
"""
```

### vjlive/plugins/make_noise/jumbler.py (L17-36)  
```python
class VJumblerPlugin(EffectNode):
    """Software virtualization of Make Noise Jumbler."""
    
    def __init__(self):
        super().__init__("jumbler")
        
        # Core parameters
        self.chaos_amount = 5.0           # Overall chaos intensity
        self.mutation_rate = 3.0          # Signal mutation frequency
        self.routing_complexity = 4.0     # Signal path complexity
        self.feedback_amount = 2.0        # Internal feedback level
        self.modulation_depth = 3.0       # Modulation intensity
        self.random_seed = 0.0            # Chaos seed
        self.smoothing_time = 2.0         # Signal smoothing duration
        self.threshold_level = 4.0        # Signal threshold for mutation
```

### vjlive/plugins/make_noise/jumbler.py (L33-52)  
```python
def process(self, input_signal: np.ndarray) -> np.ndarray:
    """Main processing function."""
    
    # Generate chaos signal
    chaos = self._generate_chaos(self.chaos_amount, self.random_seed)
    
    # Route signals through complex network
    routed = self._route_signals(input_signal, 
                                self.routing_complexity, 
                                chaos)
    
    # Apply mutations
    mutated = self._mutate_signal(routed, 
                                 self.mutation_rate, 
                                 self.modulation_depth, 
                                 self.threshold_level)
    
    # Apply feedback
    if self.feedback_amount > 0:
        feedback = self._feedback_buffer.get()
        mutated = mutated * (1.0 - self.feedback_amount) + 
                  feedback * self.feedback_amount
    
    # Update feedback buffer
    self._feedback_buffer.push(mutated)
    
    return mutated
```

### vjlive/plugins/make_noise/jumbler.py (L49-68)  
```python
def _generate_chaos(self, amount: float, seed: int) -> np.ndarray:
    """Generate chaotic signal using logistic map."""
    r = 3.57 + (amount * 0.43)  # Chaos threshold
    x = np.random.RandomState(seed).rand(buffer_size)
    
    for i in range(100):  # Warm up iterations
        x = r * x * (1 - x)
    
    return x * amount
```

### vjlive/plugins/make_noise/jumbler.py (L65-84)  
```python
def _route_signals(self, input_signal: np.ndarray, 
                   complexity: float, 
                   chaos: np.ndarray) -> np.ndarray:
    """Route signals through complex network."""
    matrix_size = int(4 + (complexity * 8))
    routing_matrix = self._generate_routing_matrix(matrix_size, complexity)
    
    chaos_modulated = chaos[:matrix_size] * complexity
    routing_matrix += chaos_modulated[:, np.newaxis]
    
    output = np.zeros_like(input_signal)
    for i in range(matrix_size):
        gain = 1.0 / matrix_size
        output += input_signal * routing_matrix[i] * gain
    
    return output
```

### vjlive/plugins/make_noise/jumbler.py (L81-100)  
```python
def _mutate_signal(self, signal: np.ndarray, 
                   rate: float, 
                   depth: float, 
                   threshold: float) -> np.ndarray:
    """Apply signal mutations."""
    # Bit crushing
    if rate > 0.3:
        bit_depth = 16 - int(rate * 12)
        signal = self._bit_crush(signal, bit_depth)
    
    # Sample rate reduction
    if rate > 0.6:
        reduction_factor = 1.0 + (rate * 4.0)
        signal = self._sample_rate_reduce(signal, reduction_factor)
    
    # Dynamic distortion
    if depth > 0.4:
        drive = depth * 10.0
        signal = self._soft_clip(signal, drive)
    
    # Threshold-based mutation
    signal = np.where(np.abs(signal) > threshold * 0.1,
                     signal * (1.0 + depth * 0.5),
                     signal)
    
    return signal
```

### vjlive/plugins/make_noise/jumbler.py (L97-116)  
```python
def _bit_crush(self, signal: np.ndarray, bit_depth: int) -> np.ndarray:
    """Apply bit crushing effect."""
    levels = 2 ** bit_depth
    return np.round(signal * levels) / levels


def _sample_rate_reduce(self, signal: np.ndarray, factor: float) -> np.ndarray:
    """Reduce sample rate for lo-fi effect."""
    return signal[::int(factor)]


def _soft_clip(self, signal: np.ndarray, drive: float) -> np.ndarray:
    """Apply soft clipping distortion."""
    return np.arctan(signal * drive) / np.arctan(drive)