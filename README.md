# VJLive3 (The Reckoning)

> **Professional Live Visual Performance System for VJs**

VJLive3 is a **real-time GPU-accelerated visual performance engine** designed specifically for:
- **VJs (Video Jockeys)** performing at clubs, festivals, and events
- **Live coders** creating visuals through code
- **Digital artists** exploring generative and audio-reactive art
- **AI-human collaborative performances**

Built on OpenGL 4.6 with a strict 60 FPS engine, VJLive3 provides:
- **Real-time GPU rendering** with custom shader support
- **Audio reactivity** with FFT analysis and beat detection
- **Live coding** with hot-reload shaders and Python scripts
- **Hardware integration** (MIDI, OSC, DMX, depth cameras)
- **Plugin architecture** for extensible effects and sources
- **Video streaming** via NDI/Spout for professional workflows
- **Node-based graph** for complex visual routing
- **Health monitoring** and fault tolerance for live shows

## Features

### Core Engine
- **60 FPS Guaranteed**: Strict synchronous loop with no blocking I/O in hot path
- **OpenGL 4.6 Rendering**: GPU-accelerated graphics with custom shader support
- **Real-time Audio Analysis**: FFT, beat detection, onset detection, frequency bands
- **Live Coding**: Hot-reload shaders and Python scripts without restart
- **Node-Based Graph**: Unified Matrix for flexible visual routing and mixing

### Hardware Integration
- **MIDI Controllers**: Full MIDI mapping with learn mode (python-rtmidi)
- **OSC Support**: Open Sound Control for device communication
- **DMX Lighting**: Control stage lighting directly from visuals
- **Depth Cameras**: Astra/OpenNI support for 3D effects
- **Gamepad Support**: Xbox/PlayStation controller input

### Video I/O
- **NDI Output**: Network Device Interface for streaming to other apps
- **Spout/Syphon**: Texture sharing on Windows/macOS
- **Multiple Sources**: Camera, video files, generators, network streams
- **Recording**: FFmpeg-based recording to disk

### Effects & Creativity
- **100+ Built-in Effects**: From classic blurs to quantum datamoshing
- **Shader Hot-Reload**: Edit GLSL shaders and see changes instantly
- **Audio Modulation**: Map audio features to any effect parameter
- **LFOs & Envelopes**: Low-frequency oscillators for parameter animation
- **Particle Systems**: 3D particles with audio reactivity
- **ML Effects**: Neural style transfer, segmentation, depth estimation

### Collaboration & AI
- **Multi-User Editing**: Real-time collaborative parameter editing
- **AI Assistant**: LLM-powered shader generation and suggestions
- **Agent System**: Autonomous creative agents that jam with you
- **Version Control**: Undo/redo with full history

### Reliability
- **Health Monitoring**: Circuit breakers, heartbeats, auto-recovery
- **Fault Tolerance**: Graceful degradation when components fail
- **Performance Profiling**: Frame time, GPU/CPU usage tracking
- **Configuration Validation**: Pydantic-validated settings

### Developer Experience
- **Plugin System**: Hot-reloadable plugins with sandboxing
- **Type Safety**: Full mypy coverage, Pydantic V2 configs
- **Testing**: 80%+ coverage, performance benchmarks
- **Documentation**: Comprehensive guides, API reference, examples

## Quick Start

### Prerequisites

- **Python 3.9+** (3.10+ recommended for full feature support)
- **Dedicated GPU** (OpenGL 4.6 required for real-time rendering)
- **Audio Interface** (optional, for audio-reactive features)
- **Git**
- **Virtual environment tool** (venv, conda, etc.)

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| GPU | OpenGL 4.0 | OpenGL 4.6 |
| RAM | 8GB | 16GB+ |
| CPU | 4 cores | 8+ cores |
| Audio | None | ASIO/WDM/ASIO4ALL |

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd VJLive3_The_Reckoning
```

2. **Set up development environment:**
```bash
make install
```

This will:
- Create a virtual environment
- Install all dependencies (including OpenGL, audio, hardware)
- Set up pre-commit hooks
- Configure the project

3. **Configure your hardware:**
```bash
# For MIDI controllers
sudo usermod -aG audio,dialout $USER

# For depth cameras (Astra)
# Note: Astra camera setup requires manual configuration
```

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd VJLive3_The_Reckoning
```

2. Set up development environment:
```bash
make install
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up pre-commit hooks
- Configure the project

### Running the Application

```bash
# Run with default settings
make run

# Run with debug logging
make run-debug

# Run with audio input
AUDIO_SOURCE=1 make run

# Run with MIDI controller
MIDI_DEVICE=1 make run

# Run with depth camera
DEPTH_CAMERA=1 make run

# Run with custom config
CONFIG_PATH=config/my_setup.yaml make run
```

### Running Tests

```bash
# Run all tests with coverage
make test

# Run specific test suite
make test-unit
make test-integration
make test-e2e
make test-performance
```

### Code Quality

```bash
# Check code quality (lint, type-check, security)
make quality

# Auto-format code
make format

# Check for print() statements and eval() calls
make check-all
```

## Project Structure

```
VJLive3_The_Reckoning/
├── src/vjlive3/          # Main source code
│   ├── core/            # Core functionality
│   ├── effects/         # Visual effects
│   ├── sources/         # Video sources
│   └── utils/           # Utilities
├── tests/               # Test suites
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   ├── e2e/            # End-to-end tests
│   └── performance/    # Performance tests
├── docs/               # Documentation
│   ├── decisions/      # Architecture decision records (ADRs)
│   └── api/            # API documentation
├── config/             # Configuration files
├── scripts/            # Utility scripts
├── pyproject.toml      # Project configuration
├── Makefile            # Build and task automation
└── .github/workflows/  # CI/CD pipelines
```

## Development Workflow

1. **Create a feature branch**:
```bash
git checkout -b feature/my-feature
```

2. **Make your changes** and write tests for them.

3. **Run pre-commit hooks** (automatic on commit) or manually:
```bash
pre-commit run --all-files
```

4. **Ensure all quality gates pass**:
```bash
make quality
```

5. **Commit and push**:
```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/my-feature
```

6. **Create a Pull Request** with a clear description.

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Architecture

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Decision Records

Important architectural decisions are documented in [docs/decisions/](docs/decisions/). See [docs/decisions/README.md](docs/decisions/README.md) for how to write ADRs.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](<issues-url>)
- **Discussions**: [GitHub Discussions](<discussions-url>)
- **Discord**: [Join our community](<discord-url>)

## Acknowledgments

Built with love by the VJLive Team and contributors.

---

**Note**: This project is in active development. APIs may change before v1.0 release.