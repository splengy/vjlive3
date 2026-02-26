# VJLive3 Architecture

This document provides a high-level overview of the VJLive3 system architecture.

## System Overview

VJLive3 is a real-time visual performance system built on a modular, plugin-based architecture. It processes video streams through a configurable pipeline of effects, allowing for live manipulation and performance.

## Core Components

### 1. Video Pipeline

The central component that orchestrates video flow:

```
[Video Source] → [Pre-processor] → [Effect Chain] → [Output]
```

- **Video Source**: Captures or provides video frames (camera, file, generator)
- **Pre-processor**: Normalizes frames (resolution, format, color space)
- **Effect Chain**: Sequential application of effects
- **Output**: Displays or streams processed video

### 2. Effect System

Effects are modular, reusable components:

```python
class Effect(ABC):
    @abstractmethod
    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply effect to a frame."""
        pass

    @abstractmethod
    def get_parameters(self) -> Dict[str, Any]:
        """Get effect parameters."""
        pass

    @abstractmethod
    def set_parameter(self, name: str, value: Any) -> None:
        """Set effect parameter."""
        pass
```

Effects can be:
- **Image processing**: Blur, sharpen, color correction
- **Generative**: Patterns, particles, fractals
- **Transform**: Rotate, scale, warp
- **Mix/Blend**: Combine multiple sources
- **Custom**: User-defined via shaders or Python

### 3. Source System

Pluggable video sources:

- **File Source**: Load video files (MP4, MOV, AVI, etc.)
- **Camera Source**: Capture from webcam/PCIe capture card
- **Generator Source**: Procedurally generated content
- **Network Source**: Receive via NDI, Syphon, Spout, or custom protocol
- **Composite Source**: Combine multiple sources

### 4. UI Layer

Multiple interface options:

- **Desktop GUI**: Qt-based interface for desktop use
- **Web UI**: Browser-based control interface
- **CLI**: Command-line for scripting/automation
- **OSC/MIDI**: Hardware controller support
- **Python API**: Direct programmatic control

### 5. State Management

Centralized state with:

- **Configuration**: YAML/JSON config files
- **Runtime state**: Current pipeline, parameters, presets
- **Persistence**: Save/load presets and project files
- **Undo/Redo**: Action history for non-destructive editing

## Data Flow

### Frame Processing

```
1. Source provides frame (numpy array: HxWxC, RGB)
2. Pre-processor normalizes (resize, convert, etc.)
3. Each effect in chain processes sequentially
4. Post-processor applies final adjustments
5. Output renders to display/stream
```

### Parameter Updates

```
1. UI/API receives parameter change
2. Validation against schema
3. Update effect parameter
4. (Optional) Recalculate dependent parameters
5. Emit change event for UI updates
```

## Module Structure

```
vjlive3/
├── __init__.py
├── main.py              # Application entry point
├── core/
│   ├── __init__.py
│   ├── pipeline.py      # VideoPipeline orchestrator
│   └── security/        # Security modules (rate limiting, RBAC)
├── effects/
│   ├── __init__.py
│   ├── base.py          # Abstract Effect base class
│   ├── blur.py          # Blur effect
│   ├── color.py         # Color correction
│   └── distort.py       # Distortion effects
├── sources/
│   ├── __init__.py
│   ├── base.py          # Abstract Source base class
│   └── generator.py     # Procedural generators
└── utils/
    ├── __init__.py
    ├── image.py         # Image processing utilities
    ├── logging.py       # Logging configuration
    ├── perf.py          # Performance monitoring
    └── security.py      # Security utilities
```

## Key Design Patterns

### 1. Pipeline Pattern

Video processing follows a pipeline where each stage transforms the data:

```python
class VideoPipeline:
    def __init__(self, source: Source, effects: List[Effect], output: Output):
        self.source = source
        self.effects = effects
        self.output = output

    def run(self):
        for frame in self.source.stream():
            processed = frame
            for effect in self.effects:
                processed = effect.apply(processed)
            self.output.render(processed)
```

### 2. Strategy Pattern

Effects and sources use strategy pattern for interchangeable algorithms:

```python
class BlurEffect(Effect):
    def __init__(self, algorithm: BlurAlgorithm):
        self.algorithm = algorithm  # Gaussian, Box, Median, etc.

    def apply(self, frame, timestamp):
        return self.algorithm.blur(frame)
```

### 3. Observer Pattern

State changes notify observers (UI updates):

```python
class StateManager:
    def __init__(self):
        self._observers: List[Callable] = []

    def add_observer(self, callback: Callable):
        self._observers.append(callback)

    def notify(self, event: str, data: Any):
        for observer in self._observers:
            observer(event, data)
```

### 4. Factory Pattern

Create effects and sources from configuration:

```python
class EffectFactory:
    @staticmethod
    def create(config: Dict[str, Any]) -> Effect:
        effect_type = config["type"]
        if effect_type == "blur":
            return BlurEffect(**config["params"])
        elif effect_type == "color":
            return ColorCorrectionEffect(**config["params"])
        else:
            raise ValueError(f"Unknown effect: {effect_type}")
```

### 5. Command Pattern

For undo/redo functionality:

```python
class Command(ABC):
    def execute(self) -> None:
        pass

    def undo(self) -> None:
        pass

class SetParameterCommand(Command):
    def __init__(self, effect: Effect, param: str, new_value: Any):
        self.effect = effect
        self.param = param
        self.new_value = new_value
        self.old_value = effect.get_parameter(param)

    def execute(self):
        self.effect.set_parameter(self.param, self.new_value)

    def undo(self):
        self.effect.set_parameter(self.param, self.old_value)
```

## Performance Considerations

### Frame Processing

- **Zero-copy where possible**: Avoid unnecessary copies
- **Batch processing**: Process multiple frames together when possible
- **GPU acceleration**: Use CUDA/OpenCL for heavy operations
- **Threading**: Parallelize independent operations
- **Memory pooling**: Reuse buffers to reduce allocation overhead

### Real-time Requirements

- **Frame rate consistency**: Must maintain target FPS
- **Low latency**: Minimize pipeline delay (< 1 frame ideal)
- **Predictable timing**: Avoid GC pauses and dynamic allocation

### Optimization Strategy

1. Profile to identify bottlenecks
2. Optimize hot paths (Cython/Numba/CUDA if needed)
3. Cache computed results
4. Use appropriate data structures (numpy arrays, not lists)
5. Consider JIT compilation for critical loops

## Extensibility

### Adding New Effects

1. Create class inheriting from `Effect` base class
2. Implement required methods (`apply`, `get_parameters`, `set_parameter`)
3. Add parameter validation
4. Write comprehensive tests
5. Document with examples
6. Register in effect registry

### Adding New Sources

1. Create class inheriting from `Source` base class
2. Implement `stream()` generator method
3. Handle connection lifecycle
4. Implement error recovery
5. Write tests
6. Document usage

### Plugin System

External plugins can be discovered and loaded:

```python
# In plugin file (my_plugin.py)
from vjlive3.plugins import register_effect

@register_effect("my_custom_effect")
class MyCustomEffect(Effect):
    ...

# Plugin discovery
plugin_loader.load_plugins_from_directory("plugins/")
```

## Security Considerations

- **Input validation**: All external data validated
- **Sandboxing**: Untrusted plugins run in restricted environment
- **Resource limits**: Prevent DoS via resource exhaustion
- **Code signing**: Verify plugin authenticity (optional)
- **Secrets management**: Never hardcode credentials

## Error Handling

- **Graceful degradation**: Continue with reduced functionality
- **Clear error messages**: Help users understand issues
- **Recovery**: Automatic retry for transient failures
- **Logging**: Comprehensive logging for debugging
- **Monitoring**: Track errors and performance metrics

## Future Considerations

- **Multi-GPU support**: For 4K+ real-time processing
- **Distributed processing**: Networked effect nodes
- **Machine learning integration**: Real-time ML models
- **VR/AR support**: Immersive visual performance
- **Cloud deployment**: Scalable cloud rendering

## References

- [Design Patterns](https://refactoring.guru/design-patterns)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
- [Real-time Video Processing](https://docs.opencv.org/)
- [Plugin Architecture](https://pluginbase.readthedocs.io/)

---

**Note**: This architecture is a living document. As the project evolves, this document will be updated to reflect current practices and decisions.