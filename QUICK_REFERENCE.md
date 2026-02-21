# VJLive3 Quick Reference Card

## Essential Commands

```bash
# Setup
make install              # Install dependencies and set up hooks
./setup.sh               # Alternative setup script

# Development
make run                 # Run the application
make run-debug           # Run with debug logging
make format              # Auto-format code
make quality             # Run all quality checks

# Testing
make test               # Run all tests with coverage
make test-unit          # Unit tests only
make test-integration   # Integration tests
make test-e2e           # End-to-end tests
make test-performance   # Performance tests

# Quality Gates
make lint               # Run linters (ruff, black, isort)
make type-check         # Type checking (mypy)
make security           # Security scans (bandit, safety)
make check-all          # Check for print() and eval()

# Build & Clean
make build              # Build distribution packages
make clean              # Clean build artifacts
make coverage-report    # Generate HTML coverage report

# Utilities
make check-print-statements  # Find print() calls
make check-eval              # Find eval() calls
make benchmark              # Run performance benchmarks
```

## Project Structure

```
VJLive3_The_Reckoning/
├── src/vjlive3/          # Main package
│   ├── core/            # Core (pipeline, timing, state, config)
│   ├── effects/         # Visual effects (blur, color, distort)
│   ├── sources/         # Video sources (generators, files, cameras)
│   ├── utils/           # Utilities (logging, image, perf, security)
│   └── main.py          # Entry point
├── tests/               # Test suites
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   ├── e2e/            # End-to-end tests
│   └── performance/    # Performance tests
├── docs/               # Documentation
│   └── decisions/      # Architecture Decision Records (ADRs)
├── config/             # Configuration files
├── scripts/            # Utility scripts
└── .github/workflows/  # CI/CD pipelines
```

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration, dependencies, tool settings |
| `Makefile` | Build and development automation |
| `.pre-commit-config.yaml` | Pre-commit hooks configuration |
| `.editorconfig` | Editor settings (indentation, line endings) |
| `.gitignore` | Files to ignore in Git |
| `README.md` | Project overview and quick start |
| `GETTING_STARTED.md` | Detailed setup and development guide |
| `CONTRIBUTING.md` | Contribution guidelines |
| `STYLE_GUIDE.md` | Coding standards |
| `TESTING_STRATEGY.md` | Testing approach |
| `ARCHITECTURE.md` | System architecture |
| `SECURITY.md` | Security policies |
| `DEFINITION_OF_DONE.md` | Quality criteria |
| `CODE_OF_CONDUCT.md` | Community standards |

## Development Workflow

1. **Setup**: `make install` (one-time)
2. **Branch**: `git checkout -b feature/your-feature`
3. **Code**: Write code following STYLE_GUIDE.md
4. **Test**: Write tests and ensure coverage ≥ 80%
5. **Quality**: `make quality` (all checks must pass)
6. **Commit**: `git commit -m "feat: description"`
7. **Push**: `git push origin feature/your-feature`
8. **PR**: Open Pull Request on GitHub

## Code Quality Standards

- **Line length**: 88 characters (Black)
- **Import order**: Standard → third-party → local (isort)
- **Type hints**: Required for all public APIs
- **Docstrings**: Google style for all public APIs
- **No print()**: Use logging instead
- **No eval()**: Strictly forbidden
- **Coverage**: ≥ 80% overall, ≥ 90% for core modules

## Testing Guidelines

```python
# Test file naming: test_<module>.py
# Test class naming: Test<ClassName>
# Test function naming: test_<behavior>

import pytest

class TestMyClass:
    def test_method_returns_expected_value(self) -> None:
        """Test description."""
        result = my_function()
        assert result == expected

    @pytest.mark.parametrize("input,expected", [
        (1, 2),
        (2, 4),
    ])
    def test_with_params(self, input: int, expected: int) -> None:
        """Parametrized test."""
        assert process(input) == expected
```

## Architecture Patterns

- **Pipeline**: Video frames flow Source → Effects → Output
- **Strategy**: Effects and sources use interchangeable algorithms
- **Observer**: State changes notify observers (UI updates)
- **Factory**: Create components from configuration
- **Command**: For undo/redo functionality

## Effect Development

```python
from vjlive3.effects.base import Effect

class MyEffect(Effect):
    def __init__(self, param1: float = 1.0):
        self.param1 = param1

    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        # Apply effect to frame
        return processed_frame

    def get_parameters(self) -> Dict[str, Any]:
        return {"param1": self.param1}

    def set_parameter(self, name: str, value: Any) -> None:
        if name == "param1":
            self.param1 = value
```

## Source Development

```python
from vjlive3.sources.base import Source

class MySource(Source):
    def stream(self) -> Iterator[np.ndarray]:
        while True:
            frame = generate_frame()
            yield frame

    def get_info(self) -> Dict[str, Any]:
        return {
            "type": "MySource",
            "width": 1920,
            "height": 1080,
            "fps": 30.0,
        }
```

## Commit Message Format

```
type(scope): subject

body

footer
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`

**Example**:
```
feat(effects): add kaleidoscope effect

- Implement kaleidoscope shader
- Add configuration for segments
- Add tests for edge cases

Closes #123
```

## ADR Creation

```bash
# Copy template
cp docs/decisions/ADR_000_TEMPLATE.md docs/decisions/ADR_002_my-decision.md

# Edit and fill in all sections
# Update index in docs/decisions/README.md
# Include in your PR
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | `pip install -e .` |
| Test failures | `pytest -v --log-cli-level=DEBUG` |
| Lint errors | `make format` or `black src/ && isort src/` |
| Type errors | `mypy src/` |
| Pre-commit fails | `pre-commit run --all-files` |
| Coverage low | `pytest --cov=src/vjlive3 --cov-report=html` |

## Useful Resources

- **Project README**: `README.md`
- **Getting Started**: `GETTING_STARTED.md`
- **Style Guide**: `STYLE_GUIDE.md`
- **Testing Strategy**: `TESTING_STRATEGY.md`
- **Architecture**: `ARCHITECTURE.md`
- **Contributing**: `CONTRIBUTING.md`
- **Security**: `SECURITY.md`
- **ADRs**: `docs/decisions/README.md`

## Contact

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Security**: security@vjlive.com

---

**Version**: 0.1.0
**Last Updated**: 2026-02-20