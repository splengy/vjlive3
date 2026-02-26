# VJLive3 Style Guide

This document defines the coding standards and style guidelines for the VJLive3 project.

## General Principles

1. **Readability over cleverness**: Code is read more often than written.
2. **Explicit over implicit**: Clear intent beats terse syntax.
3. **Consistency is key**: Follow existing patterns in the codebase.
4. **Type safety**: Use type hints everywhere possible.
5. **Documentation**: Document why, not what (unless it's non-obvious).

## Python Style

We follow [PEP 8](https://pep8.org/) with these specific configurations:

- **Line length**: 88 characters (Black default)
- **Indentation**: 4 spaces (no tabs)
- **String quotes**: Double quotes (`"`) for strings, single quotes (`'`) for dict keys
- **Trailing commas**: Always use for multi-line collections
- **Import ordering**: Standard library → third-party → local (isort)

### Example

```python
from typing import List, Optional

import numpy as np
from pydantic import BaseModel

from vjlive3.core import VideoProcessor
from vjlive3.effects import BlurEffect


class VideoPipeline(BaseModel):
    """Video processing pipeline configuration."""

    name: str
    effects: List[BlurEffect]
    input_source: Optional[str] = None

    def process_frame(
        self, frame: np.ndarray, timestamp: float
    ) -> np.ndarray:
        """Process a single video frame.

        Args:
            frame: Input frame as numpy array (HxWxC)
            timestamp: Current time in seconds

        Returns:
            Processed frame with all effects applied
        """
        result = frame.copy()
        for effect in self.effects:
            result = effect.apply(result, timestamp)
        return result
```

## Type Hints

**Always** use type hints for:

- Function parameters and return types
- Class attributes (when using dataclasses/pydantic)
- Variable assignments (when not immediately obvious)

**Use proper types**:

```python
# Good
def process_frames(
    frames: List[np.ndarray],
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[np.ndarray, float]:
    ...

# Bad
def process_frames(frames, metadata=None):
    ...
```

**Type aliases** for complex types:

```python
from typing import TypeAlias

Frame: TypeAlias = np.ndarray
Timestamp: TypeAlias = float
EffectChain: TypeAlias = List[Callable[[Frame, Timestamp], Frame]]
```

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Modules | `snake_case` | `video_processor.py` |
| Packages | `snake_case` | `vjlive3.core` |
| Classes | `PascalCase` | `VideoProcessor` |
| Functions | `snake_case` | `process_frame()` |
| Variables | `snake_case` | `frame_count` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_FPS = 60` |
| Methods | `snake_case` | `render()` |
| Private | `_prefix` | `_internal_method()` |
| Dunder | `__suffix__` | `__init__()` |

## Imports

Order imports with blank lines between groups:

1. **Standard library**
2. **Third-party libraries**
3. **Local application imports**

Within each group, sort alphabetically.

```python
# Standard library
import os
import sys
from pathlib import Path
from typing import List, Optional

# Third-party
import cv2
import numpy as np
from loguru import logger
from pydantic import BaseModel

# Local
from vjlive3.core import VideoProcessor
from vjlive3.effects import BlurEffect
```

## Error Handling

- **Use specific exceptions**: Don't use bare `except:`
- **Log errors**: Always log exceptions with context
- **Graceful degradation**: Handle failures appropriately

```python
# Good
try:
    frame = processor.process(frame_data)
except ProcessingError as e:
    logger.error(f"Frame processing failed: {e}")
    return fallback_frame

# Bad
try:
    frame = processor.process(frame_data)
except:
    pass  # Silent failure
```

## Logging

Use `loguru` for logging (configured in application entry point):

```python
from loguru import logger

logger.debug("Detailed information for debugging")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")
logger.critical("Critical failure")
```

**Never use `print()`** for debugging or logging.

## Docstrings

Use **Google style** docstrings:

```python
def process_frame(
    frame: np.ndarray,
    timestamp: float,
    metadata: Optional[Dict[str, Any]] = None
) -> np.ndarray:
    """Process a single video frame with optional metadata.

    Applies all registered effects in sequence to the input frame.
    The frame is processed in RGB format and returned as such.

    Args:
        frame: Input frame as HxWxC numpy array in RGB format
        timestamp: Current playback time in seconds
        metadata: Optional metadata dictionary with keys:
            - 'beat': Current beat number (float)
            - 'bpm': Current beats per minute (float)

    Returns:
        Processed frame as HxWxC numpy array in RGB format

    Raises:
        ValueError: If frame has invalid shape or dtype
        ProcessingError: If effect processing fails

    Example:
        >>> frame = np.zeros((480, 640, 3), dtype=np.uint8)
        >>> result = process_frame(frame, 1.5, {'beat': 4.0})
        >>> result.shape
        (480, 640, 3)
    """
    ...
```

## Testing

### Test File Naming

- Test files: `test_<module>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<behavior>`

### Test Structure

```python
import pytest
from vjlive3.core import VideoProcessor


class TestVideoProcessor:
    """Test suite for VideoProcessor."""

    def test_init_with_default_params(self) -> None:
        """Test initialization uses default parameters."""
        processor = VideoProcessor()
        assert processor.fps == 30.0

    def test_process_frame_returns_rgb(self) -> None:
        """Test that process_frame returns RGB frame."""
        processor = VideoProcessor()
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        result = processor.process(frame)
        assert result.shape == (100, 100, 3)

    @pytest.mark.parametrize("fps", [24, 30, 60, 120])
    def test_different_fps_values(self, fps: float) -> None:
        """Test processor works with various FPS values."""
        processor = VideoProcessor(fps=fps)
        assert processor.fps == fps
```

### Fixtures

Use fixtures for common setup:

```python
@pytest.fixture
def sample_frame() -> np.ndarray:
    """Create a sample test frame."""
    return np.zeros((480, 640, 3), dtype=np.uint8)

@pytest.fixture
def processor() -> VideoProcessor:
    """Create a VideoProcessor instance."""
    return VideoProcessor()
```

## Configuration Files

- **YAML**: Use 2-space indentation
- **JSON**: Use 2-space indentation
- **TOML**: Follow Black formatting
- **.env**: `KEY=value` format, no quotes

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding or fixing tests
- `chore`: Build/CI changes

**Example**:
```
feat(effects): add kaleidoscope effect

- Implement kaleidoscope shader
- Add configuration parameters for segments
- Add tests for edge cases

Closes #123
```

## Security Practices

1. **Never commit secrets**: Use environment variables or config files
2. **Validate inputs**: Check all external data
3. **Avoid eval/exec**: Never use these functions
4. **Use parameterized queries**: For database operations
5. **Keep dependencies updated**: Regularly update for security patches

## Performance Guidelines

1. **Profile before optimizing**: Use profiling tools
2. **Avoid premature optimization**: Write clear code first
3. **Use appropriate data structures**: Choose based on access patterns
4. **Minimize allocations**: Reuse objects when possible
5. **Consider async**: For I/O-bound operations

## Code Review Checklist

When reviewing code, check:

- [ ] Does the code follow this style guide?
- [ ] Are there print() statements?
- [ ] Are there eval() or exec() calls?
- [ ] Are type hints complete?
- [ ] Is error handling appropriate?
- [ ] Are there tests? Do they cover the changes?
- [ ] Is documentation updated?
- [ ] Are there any security concerns?
- [ ] Is the code performant?
- [ ] Are commit messages clear?

## Tools

We use these tools to enforce style:

- **Black**: Code formatting
- **isort**: Import sorting
- **ruff**: Linting
- **mypy**: Type checking
- **pydocstyle**: Docstring checking
- **pre-commit**: Automated checks on commit

All checks run automatically via pre-commit hooks and CI/CD.

## Questions?

If you have questions about style or need clarification:

1. Check existing code in the same module
2. Search for similar patterns in the codebase
3. Ask in code review comments
4. Update this guide if the question reveals a gap

---

**Remember**: The best code is the code that doesn't need to be written. Keep it simple, keep it clear, keep it tested.