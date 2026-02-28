# P4-COR013: AISanitizer (ai_sanitizer)

## Description

The `AISanitizer` (from `VJlive-2/core/ai_sanitizer.py`) acts as the ultimate gatekeeper for parsing string and dictionary inputs crossing trust boundaries (like the OSC Server or WebSocket API). It leverages regex matching for standard threats (SQL Injection, XSS) and an `AIAnomalyDetector` (Shannon entropy / Jensen-Shannon divergence) to quarantine highly unusual data streams.

## Public Interface Requirements

```python
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass

class ValidationLevel(Enum):
    PERMISSIVE = "permissive"
    STANDARD = "standard"
    STRICT = "strict"
    LOCKDOWN = "lockdown"

@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_value: Any = None
    error_message: Optional[str] = None

class AISanitizer:
    """
    AI-driven input validation engine for OSC and REST borders.
    """
    METADATA = {
        "id": "AISanitizer",
        "type": "security",
        "version": "1.0.0",
        "legacy_ref": "ai_sanitizer (AISanitizer)"
    }

    def __init__(self, level: ValidationLevel = ValidationLevel.STANDARD):
        self.level = level
        
    def validate_string(self, value: str, context: str) -> ValidationResult:
        """Sanitizes text targeting XSS and heuristic anomalies."""
        pass
        
    def validate_dict(self, data: dict, schema: dict, context: str) -> ValidationResult:
        """Performs deep schema validation and regex filtering against nested datasets."""
        pass
```

## Implementation Notes

- **Middleware Usage:** `AISanitizer` must be injected as middleware directly into the VJLive3 `ApiServer` and `OscServer` routers.
- **Porting the Anomaly Detector:** The Jensen-Shannon divergence calculation is computationally heavy. Since `vjlive3` enforces a 60FPS lock, this algorithm must be explicitly optimized using `numpy` if the input string exceeds 1,000 characters, or chunked asynchronously.

## Test Plan

- **Pytest:** Pass `<script>alert("hack")</script>` into `validate_string()`. Assert `ValidationResult.is_valid == False`.
- Pass a string with abnormally high entropy (`input = ''.join(random.choices(string.ascii_letters, k=800))`). At `ValidationLevel.STRICT`, assert that `is_valid == False` due to `high_entropy` anomalies.
- Coverage must exceed 80%.
