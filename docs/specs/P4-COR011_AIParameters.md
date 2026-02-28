# P4-COR011: AIParameters (config_constants)

## Description

The `AIParameters` class (legacy `VJlive-2/core/config_constants.py`) is a static configuration container defining the hardcoded magic numbers the AI subsystems use for pacing and creativity scaling: suggestion intervals, cooldowns, and creativity boost thresholds.

## Public Interface Requirements

```python
from dataclasses import dataclass

@dataclass
class AIParameters:
    """
    Configuration dataclass for AI pacing and heuristics.
    """
    METADATA = {
        "id": "AIParameters",
        "type": "ai_config",
        "version": "1.0.0",
        "legacy_ref": "config_constants (AIParameters)"
    }

    suggestion_interval: float = 1.0     # seconds
    suggestion_cooldown: float = 2.0     # seconds
    creativity_boost: float = 0.1
    magic_moment_cooldown: float = 30.0  # seconds

    def update_from_env(self) -> None:
        """Hydrates values from equivalent VJLIVE_ OS environment variables."""
        pass
```

## Implementation Notes

- **Decoupling from Legacy Config:** VJLive3 relies on the `ConfigManager` built in Phase 1 (Hydra-backed JSON configs). This dataclass should implement a `@classmethod` factory that reads from the validated `ConfigManager` dictionaries rather than relying on direct `os.getenv` calls internally.

## Test Plan

- **Pytest:** Set os.environ['VJLIVE_CREATIVITY_BOOST'] = "0.5". Call `update_from_env()`. Assert `creativity_boost == 0.5`.
- Coverage must exceed 80%.
