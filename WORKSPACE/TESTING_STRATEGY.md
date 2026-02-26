# Testing Strategy

This document outlines the comprehensive testing strategy for VJLive3, ensuring high quality, reliability, and maintainability.

## Testing Pyramid

We follow the testing pyramid principle:

```
      /\
     /  \   E2E Tests (few, broad)
    /    \
   /      \  Integration Tests (some, focused)
  /________\
 /          \ Unit Tests (many, fast)
```

### Unit Tests (70%)

- **Scope**: Single function, class, or module
- **Speed**: < 100ms per test
- **Isolation**: No external dependencies (mocked)
- **Coverage**: All business logic, edge cases, error conditions

### Integration Tests (20%)

- **Scope**: Multiple components working together
- **Speed**: < 1s per test
- **Dependencies**: Real components (database, file system, etc.)
- **Coverage**: Component interactions, API contracts

### End-to-End Tests (5%)

- **Scope**: Complete user workflows
- **Speed**: < 5s per test
- **Environment**: Near-production environment
- **Coverage**: Critical user journeys

### Performance Tests (5%)

- **Scope**: Performance characteristics
- **Speed**: Varies (benchmark mode)
- **Metrics**: Latency, throughput, memory, CPU
- **Coverage**: Performance-critical paths

## Test Organization

```
tests/
├── unit/              # Unit tests
│   ├── core/
│   ├── effects/
│   ├── sources/
│   └── utils/
├── integration/       # Integration tests
│   ├── test_video_pipeline.py
│   ├── test_effect_chain.py
│   └── test_hardware_integration.py
├── e2e/              # End-to-end tests
│   ├── test_user_journey.py
│   ├── test_performance_mode.py
│   └── test_cli_interface.py
├── performance/      # Performance tests
│   ├── test_benchmarks.py
│   ├── test_memory_usage.py
│   └── test_rendering_speed.py
└── conftest.py       # Shared fixtures and configuration
```

## Writing Tests

### Unit Tests

```python
import numpy as np
import pytest
from vjlive3.effects import BlurEffect


class TestBlurEffect:
    """Test suite for BlurEffect."""

    def test_apply_returns_same_shape(self) -> None:
        """Test that apply returns frame with same shape."""
        effect = BlurEffect(kernel_size=5)
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.shape == frame.shape

    def test_apply_preserves_dtype(self) -> None:
        """Test that apply preserves data type."""
        effect = BlurEffect()
        frame = np.zeros((50, 50, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.dtype == frame.dtype

    @pytest.mark.parametrize("kernel_size", [3, 5, 7, 9])
    def test_different_kernel_sizes(self, kernel_size: int) -> None:
        """Test blur with various kernel sizes."""
        effect = BlurEffect(kernel_size=kernel_size)
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = effect.apply(frame, timestamp=0.0)
        assert result.shape == frame.shape

    def test_invalid_frame_raises(self) -> None:
        """Test that invalid frame raises ValueError."""
        effect = BlurEffect()
        with pytest.raises(ValueError, match="Invalid frame shape"):
            effect.apply(np.zeros((100, 100)), timestamp=0.0)  # 2D array
```

### Integration Tests

```python
import pytest
from vjlive3.core import VideoProcessor
from vjlive3.effects import BlurEffect, ColorCorrectionEffect


class TestVideoPipeline:
    """Integration tests for video processing pipeline."""

    @pytest.fixture
    def processor(self) -> VideoProcessor:
        """Create processor with multiple effects."""
        return VideoProcessor(
            effects=[
                BlurEffect(kernel_size=3),
                ColorCorrectionEffect(brightness=1.2)
            ]
        )

    def test_effects_chain_processing(self, processor: VideoProcessor) -> None:
        """Test that effects are applied in sequence."""
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = processor.process(frame, timestamp=0.0)
        assert result.shape == frame.shape
        # Verify effects were applied (frame changed)
        assert not np.array_equal(result, frame)

    def test_multiple_frames_consistent(self, processor: VideoProcessor) -> None:
        """Test that processing is consistent across frames."""
        frame = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result1 = processor.process(frame, timestamp=0.0)
        result2 = processor.process(frame, timestamp=0.0)
        assert np.array_equal(result1, result2)
```

### End-to-End Tests

```python
import pytest
from vjlive3.cli import main as cli_main


class TestCLI:
    """End-to-end tests for command-line interface."""

    def test_help_command(self) -> None:
        """Test that help command displays usage."""
        with pytest.raises(SystemExit) as exc_info:
            cli_main(["--help"])
        assert exc_info.value.code == 0

    def test_run_with_config(self, tmp_path: Path) -> None:
        """Test running with a configuration file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
        video:
          source: test.mp4
          fps: 30
        effects:
          - blur:
              kernel_size: 5
        """)
        # This would start the application (in test mode)
        # result = cli_main(["--config", str(config_file)])
        # assert result.exit_code == 0
```

### Performance Tests

```python
import pytest
from vjlive3.effects import BlurEffect


@pytest.mark.performance
class TestBlurPerformance:
    """Performance tests for BlurEffect."""

    def test_processing_speed(self) -> None:
        """Test that blur effect meets performance targets."""
        effect = BlurEffect(kernel_size=5)
        frame = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)

        # Measure time for 100 frames
        import time
        start = time.perf_counter()
        for _ in range(100):
            effect.apply(frame, timestamp=0.0)
        elapsed = time.perf_counter() - start

        # Should process 100 frames in < 1 second
        assert elapsed < 1.0, f"Too slow: {elapsed:.2f}s for 100 frames"

    def test_memory_usage(self) -> None:
        """Test that memory usage is reasonable."""
        import tracemalloc
        effect = BlurEffect()
        frame = np.random.randint(0, 255, (1920, 1080, 3), dtype=np.uint8)

        tracemalloc.start()
        effect.apply(frame, timestamp=0.0)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Should use less than 100MB peak
        assert peak < 100_000_000, f"Memory usage too high: {peak} bytes"
```

## Fixtures and Test Data

### Shared Fixtures

In `tests/conftest.py`:

```python
import numpy as np
import pytest
from vjlive3.core import VideoProcessor


@pytest.fixture
def sample_frame_1080p() -> np.ndarray:
    """Create a 1080p test frame."""
    return np.zeros((1080, 1920, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame_720p() -> np.ndarray:
    """Create a 720p test frame."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def processor() -> VideoProcessor:
    """Create a default VideoProcessor."""
    return VideoProcessor()
```

### Test Data

Store test data in `tests/data/`:

```
tests/data/
├── videos/
│   ├── short_clip.mp4
│   └── test_pattern.mp4
├── images/
│   ├── test_image.png
│   └── gradient.png
└── configs/
    └── test_config.yaml
```

## Mocking and Stubbing

Use `pytest-mock` for mocking:

```python
def test_external_api_call(mocker):
    """Test that external API is called correctly."""
    mock_api = mocker.patch("vjlive3.external.API")
    mock_api.return_value.get_data.return_value = {"key": "value"}

    result = my_function()

    mock_api.assert_called_once_with(api_key="test")
    assert result == "expected"
```

## Coverage Requirements

- **Overall coverage**: ≥ 80%
- **New code coverage**: ≥ 80%
- **Critical modules**: ≥ 90% (core, effects, sources)

### Excluding from Coverage

Mark non-critical code with `# pragma: no cover`:

```python
def __repr__(self) -> str:  # pragma: no cover
    """String representation for debugging."""
    return f"{self.__class__.__name__}({self.name})"
```

## Running Tests

```bash
# All tests with coverage
make test

# Specific test file
pytest tests/unit/test_blur_effect.py

# Specific test function
pytest tests/unit/test_blur_effect.py::test_apply_returns_same_shape

# With verbose output
pytest -v

# With debug logging
pytest --log-cli-level=DEBUG

# Performance tests only
pytest -m performance

# Parallel execution
pytest -n auto  # requires pytest-xdist
```

## CI/CD Integration

All tests run in CI/CD on every push/PR:

1. **Unit tests**: Fast feedback (< 5 min)
2. **Integration tests**: Medium speed (< 10 min)
3. **E2E tests**: Slower, run on schedule/PR only
4. **Performance tests**: Run nightly or on release candidates

## Test-Driven Development (TDD)

We encourage TDD:

1. Write a failing test
2. Write minimal code to pass
3. Refactor while keeping tests green
4. Repeat

Benefits:
- Better design (testable code)
- Complete test coverage
- Confidence to refactor
- Living documentation

## Common Pitfalls

### ❌ Bad: Testing implementation details

```python
def test_internal_state():
    obj = MyClass()
    obj._private_attribute = 42  # Manipulating internals
    assert obj._private_attribute == 42
```

### ✅ Good: Testing behavior

```python
def test_behavior():
    obj = MyClass(config={"value": 42})
    result = obj.process()
    assert result == expected_output
```

### ❌ Bad: Brittle tests

```python
def test_exact_output():
    # Ties test to exact formatting/implementation
    assert my_function() == "Exactly this string"
```

### ✅ Good: Testing essential properties

```python
def test_output_properties():
    result = my_function()
    assert isinstance(result, str)
    assert len(result) > 0
    assert "key" in result
```

## Performance Testing Guidelines

1. **Warm up**: Run once before measuring
2. **Multiple iterations**: Average over many runs
3. **Isolate**: Test one thing at a time
4. **Use appropriate hardware**: Document test environment
5. **Set thresholds**: Define acceptable performance bounds
6. **Track trends**: Monitor performance over time

## Debugging Tests

```bash
# Drop into debugger on failure
pytest --pdb

# Show local variables in traceback
pytest -l

# Run last failed tests
pytest --last-failed

# Run with print statements visible
pytest -s

# Show test durations
pytest --durations=10
```

## Test Documentation

Each test file should have a docstring explaining:

- What is being tested
- Why these tests are important
- Any special setup/teardown

```python
"""Tests for VideoProcessor.

This module tests the core video processing pipeline including:
- Frame preprocessing
- Effect application
- Output formatting
- Error handling

The tests ensure that the processor correctly handles various
input formats and maintains quality standards.
"""
```

## Continuous Improvement

- Review coverage reports regularly
- Add tests for bug fixes (regression tests)
- Refactor tests when code changes
- Remove obsolete tests
- Keep tests fast and reliable

---

**Key Principle**: Tests are not a burden—they're a safety net that enables confident development and refactoring.