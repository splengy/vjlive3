# Spec Template — Focus on Technical Accuracy

**File naming:** `docs/specs/P3-EXT137_QuantumState.md`
**Rule:** This file must exist and be reviewed BEFORE writing any code for this task.

---

## Task: P3-EXT137 — Quantum State Management

**What This Module Does**

Implements a quantum state simulation and visualization system that brings quantum mechanics concepts into VJLive3's visual effects ecosystem. The Quantum State module enables superposition, entanglement, wave function collapse, and quantum tunneling effects that can be applied to visual parameters, creating mind-bending, consciousness-expanding visual experiences. This module serves as both a standalone effect engine and a foundation for quantum-enhanced audio reactivity, allowing creators to explore the intersection of quantum physics and visual art.

---

## Architecture Decisions

- **Pattern:** Quantum Circuit Simulation with Real-Time Visualization
- **Rationale:** Quantum state manipulation requires a mathematically rigorous foundation based on quantum mechanics principles. Using a circuit-based approach allows for composable quantum operations that can be combined to create complex visual effects. Real-time visualization bridges the abstract mathematical concepts with tangible visual outputs that can be integrated into VJLive's effect chain.
- **Constraints:**
  - Must accurately simulate quantum mechanics (unitary evolution, measurement collapse)
  - Must support real-time operation at 60 FPS for visual effects
  - Must integrate with existing parameter system (0-10 signal rail)
  - Must provide audio reactivity through quantum-enhanced analysis
  - Must support multi-qubit systems (up to 10 qubits for performance)
  - Must implement proper quantum state normalization and evolution
  - Must provide visualization data for rendering quantum phenomena
  - Must support MIDI/OSC control for live performance
  - Must include preset system for common quantum configurations
  - Must maintain deterministic behavior for reproducible results
  - Must handle state serialization for saving/loading quantum configurations

---

## Public Interface

```python
class QuantumStateManager:
    """Manages quantum state simulation and visualization."""
    
    def __init__(self, config: QuantumConfig):
        self.config = config
        self.circuits = {}  # circuit_name -> QuantumCircuit
        self.statevector_simulator = StatevectorSimulator()
        self.measurement_results = {}
        self.visualization_data = {}
        self.audio_reactor = None
        self.consciousness_level = 5.0  # 0-10 scale
        self.entanglement_metrics = {}
        
    def create_circuit(self, name: str, num_qubits: int) -> bool:
        """Create a new quantum circuit."""
        if name in self.circuits:
            return False
            
        circuit = QuantumCircuit(num_qubits)
        self.circuits[name] = circuit
        return True
        
    def add_gate(self, circuit_name: str, gate_type: str, qubits: List[int], params: Dict = None) -> bool:
        """Add a quantum gate to a circuit."""
        if circuit_name not in self.circuits:
            return False
            
        circuit = self.circuits[circuit_name]
        
        # Create gate based on type
        if gate_type == "h":
            gate = HadamardGate(qubits[0])
        elif gate_type == "x":
            gate = XGate(qubits[0])
        elif gate_type == "y":
            gate = YGate(qubits[0])
        elif gate_type == "z":
            gate = ZGate(qubits[0])
        elif gate_type == "rx":
            gate = RotationXGate(qubits[0], params.get('theta', 0))
        elif gate_type == "ry":
            gate = RotationYGate(qubits[0], params.get('theta', 0))
        elif gate_type == "rz":
            gate = RotationZGate(qubits[0], params.get('theta', 0))
        elif gate_type == "cx":
            gate = CNOTGate(qubits[0], qubits[1])
        elif gate_type == "cz":
            gate = CZGate(qubits[0], qubits[1])
        else:
            return False
            
        circuit.add_gate(gate)
        return True
        
    def run_simulation(self, circuit_name: str) -> Dict:
        """Run quantum simulation for specified circuit."""
        if circuit_name not in self.circuits:
            return {}
            
        circuit = self.circuits[circuit_name]
        
        # Simulate circuit
        statevector = self.statevector_simulator.simulate(circuit)
        
        # Get measurement probabilities
        probabilities = self._calculate_probabilities(statevector)
        
        # Perform measurement (collapse)
        measured_state = self.statevector_simulator.measure(statevector)
        
        # Store results
        self.measurement_results[circuit_name] = measured_state
        self.state_vectors[circuit_name] = statevector
        
        # Compute entanglement metrics
        self.entanglement_metrics[circuit_name] = {
            'entropy': self._calculate_entanglement_entropy(statevector),
            'purity': self._calculate_purity(statevector),
            'coherence': self._calculate_coherence(statevector)
        }
        
        return {
            'statevector': statevector,
            'probabilities': probabilities,
            'measurement': measured_state,
            'metrics': self.entanglement_metrics[circuit_name]
        }
        
    def get_visualization_data(self, circuit_name: str) -> Dict:
        """Get data formatted for visualization."""
        if circuit_name not in self.measurement_results:
            self.run_simulation(circuit_name)
            
        counts = self.measurement_results[circuit_name]
        statevector = self.state_vectors[circuit_name]
        
        return {
            'measurement_counts': counts,
            'statevector_magnitudes': [abs(amplitude) for amplitude in statevector],
            'statevector_phases': [np.angle(amplitude) for amplitude in statevector],
            'entanglement_metrics': self.entanglement_metrics[circuit_name],
            'consciousness_level': self.consciousness_level
        }
        
    def set_consciousness_level(self, level: float):
        """Set consciousness level (0-10) affecting visualization."""
        self.consciousness_level = max(0.0, min(10.0, level))
        
    def set_audio_reactor(self, reactor: AudioReactor):
        """Connect audio reactor for quantum audio reactivity."""
        self.audio_reactor = reactor
        
    def get_parameter_value(self, param_name: str) -> float:
        """Get quantum-influenced parameter value for VJLive integration."""
        # Map quantum state to parameter value
        if param_name == 'quantum_coherence':
            return self.entanglement_metrics.get('default', {}).get('coherence', 0.5)
        elif param_name == 'consciousness_level':
            return self.consciousness_level
        elif param_name == 'quantum_entropy':
            return self.entanglement_metrics.get('default', {}).get('entropy', 0.0)
        return 0.0
```

---

## Core Components

### 1. QuantumCircuit

Represents a quantum circuit with qubits and gates.

```python
class QuantumCircuit:
    """Quantum circuit representation."""
    
    def __init__(self, num_qubits: int):
        self.num_qubits = num_qubits
        self.gates = []
        self.initial_state = '0' * num_qubits
        
    def add_gate(self, gate: QuantumGate):
        """Add a gate to the circuit."""
        self.gates.append(gate)
        
    def get_unitary_matrix(self) -> np.ndarray:
        """Compute the unitary matrix for the entire circuit."""
        # Start with identity matrix
        unitary = np.eye(2**self.num_qubits, dtype=complex)
        
        # Apply each gate
        for gate in self.gates:
            gate_matrix = gate.get_matrix()
            unitary = gate_matrix @ unitary
            
        return unitary
```

### 2. StatevectorSimulator

Simulates quantum state evolution.

```python
class StatevectorSimulator:
    """Simulates quantum state evolution."""
    
    def simulate(self, circuit: QuantumCircuit) -> np.ndarray:
        """Simulate circuit and return final statevector."""
        # Initialize statevector
        statevector = np.zeros(2**circuit.num_qubits, dtype=complex)
        statevector[0] = 1.0  # Start in |0⟩ state
        
        # Apply each gate
        for gate in circuit.gates:
            gate_matrix = gate.get_matrix()
            statevector = gate_matrix @ statevector
            
        # Normalize
        norm = np.linalg.norm(statevector)
        if norm > 0:
            statevector = statevector / norm
            
        return statevector
        
    def measure(self, statevector: np.ndarray) -> Dict[str, int]:
        """Perform measurement on statevector."""
        # Calculate probabilities
        probabilities = np.abs(statevector)**2
        
        # Sample from distribution
        outcome = np.random.choice(len(statevector), p=probabilities)
        
        # Create measurement result (collapsed state)
        result = np.zeros_like(statevector)
        result[outcome] = 1.0
        
        # Convert to bitstring
        num_qubits = int(np.log2(len(statevector)))
        bitstring = format(outcome, f'0{num_qubits}b')
        
        return {bitstring: 1}
```

### 3. QuantumGate Base Class

Base class for all quantum gates.

```python
class QuantumGate:
    """Base class for quantum gates."""
    
    def __init__(self, qubits: List[int]):
        self.qubits = qubits
        
    def get_matrix(self) -> np.ndarray:
        """Return the unitary matrix for this gate."""
        raise NotImplementedError
        
class HadamardGate(QuantumGate):
    """Hadamard gate for superposition."""
    
    def __init__(self, qubit: int):
        super().__init__([qubit])
        
    def get_matrix(self) -> np.ndarray:
        H = np.array([[1, 1], [1, -1]]) / np.sqrt(2)
        return H
        
class XGate(QuantumGate):
    """Pauli-X (NOT) gate."""
    
    def __init__(self, qubit: int):
        super().__init__([qubit])
        
    def get_matrix(self) -> np.ndarray:
        return np.array([[0, 1], [1, 0]], dtype=complex)
        
class CNOTGate(QuantumGate):
    """Controlled-NOT gate for entanglement."""
    
    def __init__(self, control: int, target: int):
        super().__init__([control, target])
        
    def get_matrix(self) -> np.ndarray:
        return np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0]
        ], dtype=complex)
```

---

## Integration with Existing Systems

### Audio Reactivity Integration

```python
class QuantumAudioReactor:
    """Quantum-enhanced audio reactivity."""
    
    def __init__(self, quantum_manager: QuantumStateManager):
        self.quantum_manager = quantum_manager
        self.audio_analyzer = None
        
    def set_audio_analyzer(self, analyzer: AudioAnalyzer):
        """Connect audio analyzer."""
        self.audio_analyzer = analyzer
        
    def update_quantum_circuit(self, circuit_name: str):
        """Update quantum circuit based on audio features."""
        if not self.audio_analyzer:
            return
            
        # Get audio features
        bass = self.audio_analyzer.get_feature_value(AudioFeature.BASS)
        mid = self.audio_analyzer.get_feature_value(AudioFeature.MID)
        treble = self.audio_analyzer.get_feature_value(AudioFeature.TREBLE)
        volume = self.audio_analyzer.get_feature_value(AudioFeature.VOLUME)
        
        # Map audio to quantum parameters
        # Bass controls superposition depth
        # Mid controls entanglement
        # Treble controls rotation angles
        # Volume controls measurement probability
        
        # Example: Add Hadamard gates based on bass
        if bass > 0.7:
            self.quantum_manager.add_gate(circuit_name, 'h', [0])
            
    def get_quantum_parameters(self) -> Dict[str, float]:
        """Get quantum-influenced parameters for effects."""
        return {
            'coherence': self.quantum_manager.get_parameter_value('quantum_coherence'),
            'consciousness': self.quantum_manager.consciousness_level,
            'entropy': self.quantum_manager.get_parameter_value('quantum_entropy'),
            'superposition': self._calculate_superposition_strength()
        }
```

### Parameter System Integration

```python
class QuantumParameterSource:
    """Provides quantum-derived parameters to VJLive's parameter system."""
    
    def __init__(self, quantum_manager: QuantumStateManager):
        self.quantum_manager = quantum_manager
        self.parameter_cache = {}
        
    def update(self):
        """Update all quantum-influenced parameters."""
        viz_data = self.quantum_manager.get_visualization_data('default')
        
        self.parameter_cache = {
            'quantum_coherence': viz_data['entanglement_metrics']['coherence'],
            'consciousness_level': viz_data['consciousness_level'],
            'quantum_entropy': viz_data['entanglement_metrics']['entropy'],
            'superposition_strength': self._calculate_superposition(viz_data),
            'entanglement_factor': self._calculate_entanglement(viz_data)
        }
        
    def get_parameter(self, name: str) -> float:
        """Get current value of quantum parameter."""
        return self.parameter_cache.get(name, 0.0)
```

---

## Performance Requirements

- **Simulation Speed:** < 5ms for 5-qubit circuit with 20 gates
- **Visualization Update:** 60 FPS for quantum state rendering
- **Memory Usage:** < 20MB for quantum state data
- **CPU Usage:** < 5% on Orange Pi 5 for typical circuits
- **Latency:** < 10ms from parameter change to visual update
- **Circuit Complexity:** Support up to 10 qubits and 50 gates
- **Preset Loading:** < 100ms for complex quantum presets
- **Audio Reactivity:** < 2ms audio-to-quantum update latency
- **State Serialization:** < 50ms for save/load operations
- **Multi-Circuit:** Support 10+ simultaneous circuits

---

## Testing Strategy

### Unit Tests

```python
def test_quantum_circuit_creation():
    """Test creating a quantum circuit."""
    circuit = QuantumCircuit(3)
    assert circuit.num_qubits == 3
    assert len(circuit.gates) == 0
    
def test_hadamard_gate():
    """Test Hadamard gate creates superposition."""
    circuit = QuantumCircuit(1)
    circuit.add_gate(HadamardGate(0))
    
    simulator = StatevectorSimulator()
    statevector = simulator.simulate(circuit)
    
    # Should be equal superposition
    expected = np.array([1/np.sqrt(2), 1/np.sqrt(2)], dtype=complex)
    assert np.allclose(np.abs(statevector), np.abs(expected))
    
def test_cnot_entanglement():
    """Test CNOT creates entanglement."""
    circuit = QuantumCircuit(2)
    circuit.add_gate(HadamardGate(0))
    circuit.add_gate(CNOTGate(0, 1))
    
    simulator = StatevectorSimulator()
    statevector = simulator.simulate(circuit)
    
    # Should be Bell state: (|00⟩ + |11⟩)/√2
    expected = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)
    assert np.allclose(np.abs(statevector), np.abs(expected))
    
def test_measurement_collapse():
    """Test measurement collapses state."""
    circuit = QuantumCircuit(1)
    circuit.add_gate(HadamardGate(0))
    
    simulator = StatevectorSimulator()
    statevector = simulator.simulate(circuit)
    
    # Measure multiple times
    results = [simulator.measure(statevector) for _ in range(100)]
    
    # Should get roughly 50% |0⟩ and 50% |1⟩
    zeros = sum(1 for r in results if '0' in r)
    ones = sum(1 for r in results if '1' in r)
    
    assert 40 < zeros < 60  # Within statistical variation
    assert 40 < ones < 60
    
def test_entanglement_entropy():
    """Test entanglement entropy calculation."""
    # Bell state has max entropy of 1
    bell_state = np.array([1/np.sqrt(2), 0, 0, 1/np.sqrt(2)], dtype=complex)
    
    entropy = _calculate_entanglement_entropy(bell_state)
    assert np.isclose(entropy, 1.0, atol=0.01)
```

### Integration Tests

```python
def test_quantum_manager_integration():
    """Test complete quantum manager workflow."""
    config = QuantumConfig()
    manager = QuantumStateManager(config)
    
    # Create circuit
    manager.create_circuit('test', 2)
    
    # Add gates
    manager.add_gate('test', 'h', [0])
    manager.add_gate('test', 'cx', [0, 1])
    
    # Run simulation
    result = manager.run_simulation('test')
    
    assert 'statevector' in result
    assert 'probabilities' in result
    assert 'measurement' in result
    assert 'metrics' in result
    
def test_audio_reactivity():
    """Test audio-driven quantum updates."""
    manager = QuantumStateManager(QuantumConfig())
    reactor = QuantumAudioReactor(manager)
    
    # Mock audio analyzer
    mock_analyzer = MockAudioAnalyzer()
    mock_analyzer.bass = 0.8
    reactor.set_audio_analyzer(mock_analyzer)
    
    # Update circuit based on audio
    manager.create_circuit('audio_test', 2)
    reactor.update_quantum_circuit('audio_test')
    
    # Should have added gates based on audio
    assert len(manager.circuits['audio_test'].gates) > 0
    
def test_consciousness_level_mapping():
    """Test consciousness level affects visualization."""
    manager = QuantumStateManager(QuantumConfig())
    
    # Test different levels
    for level in [0.0, 5.0, 10.0]:
        manager.set_consciousness_level(level)
        viz_data = manager.get_visualization_data('default')
        
        assert viz_data['consciousness_level'] == level
```

### Performance Tests

```python
def test_simulation_latency():
    """Test simulation meets latency requirements."""
    manager = QuantumStateManager(QuantumConfig())
    manager.create_circuit('perf_test', 5)
    
    # Add complex circuit
    for i in range(20):
        manager.add_gate('perf_test', 'h', [i % 5])
        manager.add_gate('perf_test', 'cx', [i % 5, (i+1) % 5])
        
    # Measure simulation time
    import time
    start = time.perf_counter()
    
    for _ in range(100):
        manager.run_simulation('perf_test')
        
    elapsed = time.perf_counter() - start
    avg_time = elapsed / 100
    
    assert avg_time < 0.005, f"Average simulation time {avg_time*1000:.1f}ms > 5ms"
    
def test_memory_usage():
    """Test memory usage stays within budget."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    # Create many quantum managers
    managers = []
    for _ in range(10):
        manager = QuantumStateManager(QuantumConfig())
        manager.create_circuit('test', 5)
        for i in range(10):
            manager.add_gate('test', 'h', [i % 5])
        managers.append(manager)
        
    mem_after = process.memory_info().rss / 1024 / 1024  # MB
    mem_delta = mem_after - mem_before
    
    assert mem_delta < 20, f"Memory increase {mem_delta:.1f}MB > 20MB budget"
```

---

## Implementation Roadmap

1. **Week 1:** Implement core quantum circuit and gate classes
2. **Week 2:** Build statevector simulator with proper quantum mechanics
3. **Week 3:** Add visualization data extraction and formatting
4. **Week 4:** Implement audio reactivity integration
5. **Week 5:** Develop consciousness level system and parameter mapping
6. **Week 6:** Performance optimization and comprehensive testing

---
-

## References

- `CELEBRATION.md` (to be referenced)
- `PRODUCTION_HARDENING_AUDIT.md` (to be referenced)
- `QUANTUM_CONSCIOUSNESS_EXPLORER.md` (to be referenced)
- `VJlive-2/demos/demo_quantum_consciousness_explorer.py` (to be referenced)
- `VJlive-2/docs/QUANTUM_AUDIO_REACTIVITY.md` (to be referenced)
- `VJlive-2/test_quantum_simple.py` (to be referenced)
- `core/quantum/quantum_state_simulator.py` (to be referenced)
- `numpy` (for linear algebra operations)
- `scipy` (for advanced quantum operations)
- `OpenGL` (for quantum state visualization)

---

## Conclusion

The Quantum State Management module transforms VJLive3 into a tool for exploring the fascinating intersection of quantum mechanics and visual art. By providing accurate quantum simulation with real-time visualization and audio reactivity, this module enables creators to produce truly mind-bending visual experiences that reflect the strange and beautiful nature of quantum reality. Its robust architecture, mathematical rigor, and seamless integration with existing systems make it a powerful addition to VJLive's effect library, opening new creative possibilities for artists seeking to push the boundaries of visual expression.

---
