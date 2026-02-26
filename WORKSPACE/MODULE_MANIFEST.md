# VJLive3 Module Manifest

This document provides an inventory of all modules in the VJLive3 project, their purpose, and their relationships.

## Module Inventory

### Core Modules (`vjlive3.core`)

| Module | Purpose | Dependencies | Test Coverage |
|--------|---------|--------------|---------------|
| `pipeline.py` | Main video processing pipeline orchestrator | numpy, effects, sources | Required: 90%+ |
| `frame.py` | Frame abstraction and utilities | numpy, OpenCV | Required: 90%+ |
| `timing.py` | Timing, BPM detection, timecode sync | numpy, scipy | Required: 85%+ |
| `state.py` | State management and persistence | pydantic, yaml | Required: 85%+ |
| `config.py` | Configuration loading and validation | pydantic, yaml | Required: 90%+ |

**Critical**: These modules form the backbone of the system. Changes require extensive review.

### Effect Modules (`vjlive3.effects`)

| Module | Effect Type | Dependencies | Test Coverage |
|--------|-------------|--------------|---------------|
| `base.py` | Abstract base classes | numpy | Required: 95%+ |
| `blur.py` | Blur effects (gaussian, box, median) | numpy, OpenCV | Required: 90%+ |
| `color.py` | Color correction, grading, LUTs | numpy, OpenCV | Required: 90%+ |
| `distort.py` | Distortion, warping, displacement | numpy, scipy | Required: 85%+ |
| `generative/` | Procedural patterns | numpy, noise libraries | Required: 80%+ |
| `transitions/` | Scene transitions | numpy, OpenCV | Required: 85%+ |
| `audio_reactive/` | Audio-driven effects | numpy, audio libraries | Required: 80%+ |

**Note**: New effects should follow the pattern established in `base.py`.

### Source Modules (`vjlive3.sources`)

| Module | Source Type | Dependencies | Test Coverage |
|--------|-------------|--------------|---------------|
| `base.py` | Abstract base classes | numpy | Required: 95%+ |
| `file_source.py` | Video file playback | OpenCV, FFmpeg | Required: 90%+ |
| `camera_source.py` | Live camera capture | OpenCV, GStreamer | Required: 85%+ |
| `generator.py` | Procedural sources | numpy, PIL | Required: 80%+ |
| `network.py` | Network sources (NDI, Syphon) | NDI SDK, Spout | Required: 80%+ |

**Note**: Platform-specific code should be isolated and well-documented.

### UI Modules (`vjlive3.ui`)

| Module | Interface | Dependencies | Test Coverage |
|--------|-----------|--------------|---------------|
| `desktop.py` | Qt-based desktop GUI | PyQt6/PySide6 | Required: 70%+ |
| `web.py` | Web-based interface | FastAPI, WebSockets | Required: 80%+ |
| `cli.py` | Command-line interface | click, rich | Required: 85%+ |
| `controllers/` | Hardware controllers (OSC/MIDI) | python-osc, mido | Required: 75%+ |

**Note**: UI tests are challenging; focus on integration tests.

### Utility Modules (`vjlive3.utils`)

| Module | Purpose | Dependencies | Test Coverage |
|--------|---------|--------------|---------------|
| `logging.py` | Logging configuration | loguru | Required: 80%+ |
| `image.py` | Image processing utilities | numpy, OpenCV, PIL | Required: 85%+ |
| `perf.py` | Performance monitoring | psutil, time | Required: 75%+ |
| `security.py` | Security utilities | secrets, hashlib | Required: 80%+ |
| `validation.py` | Input validation | pydantic | Required: 85%+ |

### Plugin System (`vjlive3.plugins`)

| Module | Purpose | Dependencies | Test Coverage |
|--------|---------|--------------|---------------|
| `loader.py` | Dynamic plugin loading | importlib, pkgutil | Required: 85%+ |
| `registry.py` | Plugin registration and discovery | typing | Required: 90%+ |
| `manifest.py` | Plugin manifest parsing | yaml, pydantic | Required: 85%+ |

## Module Dependencies Graph

```
vjlive3
├── core (no internal deps)
├── effects → core
├── sources → core
├── ui → core, effects, sources
├── utils (no internal deps)
└── plugins → core, effects, sources
```

**Rule**: Lower-level modules (core, utils) must not depend on higher-level modules (ui, plugins).

## Module Quality Standards

### Required Coverage by Module Type

| Module Type | Coverage Requirement | Reason |
|-------------|---------------------|--------|
| Core | 90%+ | Critical infrastructure |
| Effects | 85%+ | Business logic |
| Sources | 85%+ | I/O handling |
| UI | 70%+ | Hard to test, integration focus |
| Utils | 80%+ | Support code |
| Plugins | 85%+ | Dynamic loading |

### Additional Quality Gates

- **Type hints**: 100% of public APIs
- **Docstrings**: 100% of public APIs (Google style)
- **No print()**: 0 instances
- **No eval()**: 0 instances
- **Security scan**: 0 high/medium vulnerabilities

## Module Evolution

### Adding New Modules

1. Create module file in appropriate package
2. Add to `__init__.py` exports
3. Write comprehensive tests (target coverage ≥ 80%)
4. Document with docstrings and examples
5. Update this manifest
6. Consider ADR if architectural impact

### Deprecating Modules

1. Mark as deprecated in docstring
2. Add `DeprecationWarning` in code
3. Update documentation
4. Provide migration path
5. Schedule removal (at least 2 major versions)
6. Update this manifest

### Module Renaming

1. Create new module with desired name
2. Keep old module as thin wrapper with deprecation warning
3. Update all imports gradually
4. Remove old module after deprecation period

## Module Responsibilities

### Core Module Responsibilities

- **Pipeline**: Orchestrate video flow
- **Frame**: Frame representation and manipulation
- **Timing**: Time management, sync, BPM
- **State**: Centralized state management
- **Config**: Configuration loading/validation

### Effect Module Responsibilities

- **Base**: Abstract interfaces
- **Implementation**: Specific effect algorithms
- **Parameters**: Effect configuration
- **Serialization**: Save/load effect state

### Source Module Responsibilities

- **Base**: Abstract source interface
- **Implementation**: Specific source types
- **Connection**: Handle connection lifecycle
- **Recovery**: Error handling and reconnection

### UI Module Responsibilities

- **Desktop**: Full-featured desktop application
- **Web**: Browser-based control interface
- **CLI**: Scripting and automation
- **Controllers**: Hardware integration

### Utils Module Responsibilities

- **Logging**: Centralized logging setup
- **Image**: Common image operations
- **Perf**: Performance metrics
- **Security**: Security utilities
- **Validation**: Input validation helpers

### Plugin Module Responsibilities

- **Loader**: Dynamic module loading
- **Registry**: Plugin discovery and management
- **Manifest**: Plugin metadata parsing

## Module Interfaces

### Public vs Private

- **Public**: Names without leading underscore, documented in `__all__`
- **Private**: Names with leading underscore, internal use only
- **Protected**: Names with single underscore, subclass use

### API Stability

- **Stable**: Public APIs in core modules (semantic versioning)
- **Experimental**: New features, may change
- **Deprecated**: Scheduled for removal

## Module Testing Strategy

Each module should have:

1. **Unit tests**: Test all public functions/classes
2. **Edge case tests**: Boundary conditions, error cases
3. **Integration tests**: Interaction with other modules
4. **Performance tests**: If performance-critical

Test files should mirror module structure:

```
vjlive3/effects/blur.py
tests/unit/effects/test_blur.py
```

## Module Documentation Requirements

Every module must have:

1. **Module docstring**: Purpose and overview
2. **Public API docs**: All classes/functions documented
3. **Examples**: Usage examples in docstrings
4. **Type hints**: Complete type annotations
5. **Cross-references**: Link to related modules

Example:

```python
"""Blur effects implementation.

This module provides various blur effects for video processing.
All effects inherit from the base Effect class.

Example:
    >>> from vjlive3.effects import BlurEffect
    >>> effect = BlurEffect(kernel_size=5)
    >>> frame = np.zeros((100, 100, 3))
    >>> result = effect.apply(frame, 0.0)

See also:
    - vjlive3.effects.base: Abstract base classes
    - vjlive3.core.pipeline: Pipeline orchestration
"""

__all__ = ["BlurEffect", "GaussianBlur", "BoxBlur"]
```

## Module Metrics

Track these metrics per module:

- **Lines of code** (excluding tests/comments)
- **Cyclomatic complexity** (target: < 10 per function)
- **Test coverage** (targets per module type above)
- **Number of imports** (minimize dependencies)
- **Public API size** (keep interfaces small)

## Module Review Checklist

When reviewing a module:

- [ ] Does it have a clear, single responsibility?
- [ ] Are dependencies minimal and appropriate?
- [ ] Is the interface well-designed and documented?
- [ ] Are there comprehensive tests?
- [ ] Does it meet coverage requirements?
- [ ] Are there any circular dependencies?
- [ ] Is error handling appropriate?
- [ ] Are there performance concerns?
- [ ] Is it secure?
- [ ] Does it follow the style guide?

---

**Maintenance**: This manifest should be updated whenever modules are added, removed, or significantly changed. It serves as the authoritative source for module organization and quality standards.