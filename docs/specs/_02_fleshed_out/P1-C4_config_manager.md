# P1-C4: ConfigManager — Type-Safe Configuration Management

**Version:** 1.0 | **Date:** 2026-02-22 | **Manager:** ROO CODE (Manager-Gemini-3.1)

---

## Problem Statement

VJLive3 requires a robust configuration system that:
- Manages application configuration with type safety and validation
- Supports multiple configuration sources (files, environment, defaults)
- Provides hot-reloading of configuration changes
- Handles configuration schemas with Pydantic validation
- Supports different environments (development, production, testing)
- Manages sensitive data (API keys, secrets) securely
- Integrates with ApplicationStateManager for config changes
- Provides configuration migration when schemas change

The legacy codebases have configuration scattered and lack type safety.

---

## Proposed Solution

Implement `ConfigManager` as a type-safe, layered configuration system with:

1. **Pydantic Models** — all config schemas validated at load time
2. **Layered Sources** — defaults → files → environment → runtime overrides
3. **Hot Reload** — watch config files for changes and update live
4. **Secure Secrets** — encrypted storage for sensitive values
5. **Schema Migration** — automatic migration of old config formats
6. **Environment Support** — dev/staging/production configurations
7. **State Integration** — broadcast config changes via ApplicationStateManager

---

## API/Interface Definition

```python
from typing import Dict, Any, Optional, List, Type, TypeVar
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json
import os
from pydantic import BaseModel, ValidationError, Field

T = TypeVar('T', bound=BaseModel)

class ConfigLayer(Enum):
    """Configuration layer precedence."""
    DEFAULTS = 0
    FILE = 1
    ENVIRONMENT = 2
    RUNTIME = 3  # Highest precedence

@dataclass
class ConfigSchema:
    """Schema definition for a configuration section."""
    name: str
    model_class: Type[BaseModel]
    description: str
    version: str = "1.0"
    migration_required: bool = False

class ConfigManager:
    """
    Type-safe configuration management with layered sources.

    Usage:
        config_mgr = ConfigManager(
            config_path="/path/to/config",
            environment="development"
        )

        # Register schema
        config_mgr.register_schema(ConfigSchema(
            name="audio",
            model_class=AudioConfig,
            description="Audio subsystem configuration"
        ))

        # Get config (validated)
        audio_cfg = config_mgr.get("audio", AudioConfig)

        # Set config (runtime override)
        config_mgr.set("audio", AudioConfig(sample_rate=48000))

        # Save to file
        config_mgr.save()
    """

    def __init__(
        self,
        config_path: Union[str, Path],
        environment: str = "development",
        default_config: Optional[Dict[str, Any]] = None,
        state_mgr: Optional['ApplicationStateManager'] = None
    ):
        """
        Initialize configuration manager.

        Args:
            config_path: Directory for config files
            environment: Environment name (dev/staging/prod)
            default_config: Optional default configuration dict
            state_mgr: Optional ApplicationStateManager for broadcasting
        """
        self.config_path = Path(config_path)
        self.environment = environment
        self.state_mgr = state_mgr
        self.default_config = default_config or {}

        self._schemas: Dict[str, ConfigSchema] = {}
        self._config: Dict[str, BaseModel] = {}
        self._layers: Dict[ConfigLayer, Dict[str, Dict]] = {
            ConfigLayer.DEFAULTS: {},
            ConfigLayer.FILE: {},
            ConfigLayer.ENVIRONMENT: {},
            ConfigLayer.RUNTIME: {}
        }
        self._file_watcher = None
        self._initialize()

    def _initialize(self) -> None:
        """Initialize configuration system."""
        self.config_path.mkdir(parents=True, exist_ok=True)
        self._load_all_layers()
        self._validate_and_merge()
        self._start_file_watcher()

    def register_schema(self, schema: ConfigSchema) -> None:
        """
        Register a configuration schema.

        Args:
            schema: ConfigSchema definition
        """
        self._schemas[schema.name] = schema

        # Initialize with defaults if not present
        if schema.name not in self._config:
            # Create default instance
            default_instance = schema.model_class()
            self._layers[ConfigLayer.DEFAULTS][schema.name] = default_instance.dict()

    def get(self, section: str, model_class: Type[T] = None) -> T:
        """
        Get configuration section.

        Args:
            section: Configuration section name
            model_class: Optional Pydantic model class for validation

        Returns:
            Configuration data as Pydantic model or dict

        Raises:
            KeyError: If section not found
            ValidationError: If validation fails
        """
        if section not in self._config:
            raise KeyError(f"Configuration section '{section}' not found")

        data = self._config[section]
        if model_class:
            return model_class(**data)
        return data

    def set(
        self,
        section: str,
        value: Union[BaseModel, Dict[str, Any]],
        layer: ConfigLayer = ConfigLayer.RUNTIME
    ) -> None:
        """
        Set configuration value at specified layer.

        Args:
            section: Configuration section name
            value: Configuration value (Pydantic model or dict)
            layer: Configuration layer to set
        """
        if isinstance(value, BaseModel):
            value_dict = value.dict()
        else:
            value_dict = value

        # Validate against schema if registered
        if section in self._schemas:
            schema = self._schemas[section]
            validated = schema.model_class(**value_dict)
            value_dict = validated.dict()

        # Set in layer
        self._layers[layer][section] = value_dict

        # Re-merge and validate
        self._validate_and_merge()

        # Broadcast change if state manager available
        if self.state_mgr:
            self.state_mgr.set(
                category=StateCategory.SYSTEM,
                key=f"config.{section}",
                value=self._config[section].dict() if hasattr(self._config[section], 'dict') else self._config[section]
            )

    def save(self, section: Optional[str] = None) -> None:
        """
        Save configuration to file.

        Args:
            section: Optional specific section to save; if None, saves all
        """
        config_file = self.config_path / f"{self.environment}.json"

        # Prepare data to save (from FILE layer or higher)
        save_data = {}
        for sec_name, data in self._layers[ConfigLayer.FILE].items():
            if section is None or sec_name == section:
                save_data[sec_name] = data

        # Include runtime overrides that should be persisted
        for sec_name, data in self._layers[ConfigLayer.RUNTIME].items():
            if section is None or sec_name == section:
                save_data[sec_name] = data

        # Write to file
        with open(config_file, 'w') as f:
            json.dump(save_data, f, indent=2)

    def reload(self) -> None:
        """Reload configuration from file (hot reload)."""
        self._load_layer(ConfigLayer.FILE)
        self._validate_and_merge()

    def _load_all_layers(self) -> None:
        """Load all configuration layers."""
        # Load defaults (already in _layers[DEFAULTS] from registration)
        pass

        # Load file layer
        self._load_layer(ConfigLayer.FILE)

        # Load environment layer (from env vars)
        self._load_layer(ConfigLayer.ENVIRONMENT)

    def _load_layer(self, layer: ConfigLayer) -> None:
        """Load a specific configuration layer."""
        if layer == ConfigLayer.FILE:
            config_file = self.config_path / f"{self.environment}.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self._layers[ConfigLayer.FILE] = data

        elif layer == ConfigLayer.ENVIRONMENT:
            # Load from environment variables (VJLIVE_ prefix)
            env_config = {}
            for key, value in os.environ.items():
                if key.startswith("VJLIVE_"):
                    # Convert VJLIVE_SECTION_KEY → section.key
                    parts = key[7:].lower().split('_')
                    if len(parts) >= 2:
                        section = parts[0]
                        config_key = '_'.join(parts[1:])
                        if section not in env_config:
                            env_config[section] = {}
                        env_config[section][config_key] = value
            self._layers[ConfigLayer.ENVIRONMENT] = env_config

    def _validate_and_merge(self) -> None:
        """Validate and merge all configuration layers."""
        merged = {}

        # Merge in precedence order
        for layer in [ConfigLayer.DEFAULTS, ConfigLayer.FILE, ConfigLayer.ENVIRONMENT, ConfigLayer.RUNTIME]:
            for section, data in self._layers[layer].items():
                if section not in merged:
                    merged[section] = {}
                merged[section].update(data)

        # Validate each section against schema
        for section, data in merged.items():
            if section in self._schemas:
                schema = self._schemas[section]
                try:
                    validated = schema.model_class(**data)
                    self._config[section] = validated
                except ValidationError as e:
                    print(f"Config validation error for section '{section}': {e}")
                    # Keep existing config if validation fails
                    if section not in self._config:
                        # Use defaults if no valid config
                        self._config[section] = schema.model_class()
            else:
                # No schema, store as dict
                self._config[section] = data

    def _start_file_watcher(self) -> None:
        """Start watching config files for changes (hot reload)."""
        # Would use watchdog or similar to monitor file changes
        pass

    def get_schema(self, section: str) -> Optional[ConfigSchema]:
        """Get schema for a configuration section."""
        return self._schemas.get(section)

    def list_sections(self) -> List[str]:
        """List all available configuration sections."""
        return list(self._config.keys())

    def validate_all(self) -> Dict[str, List[str]]:
        """
        Validate all configuration sections.

        Returns:
            Dict mapping section names to list of validation errors
        """
        errors = {}
        for section, schema in self._schemas.items():
            if section in self._config:
                try:
                    data = self._config[section]
                    if hasattr(data, 'dict'):
                        data = data.dict()
                    schema.model_class(**data)
                except ValidationError as e:
                    errors[section] = [str(err) for err in e.errors()]
        return errors
```

---

## Example Pydantic Config Models

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class AudioConfig(BaseModel):
    """Audio subsystem configuration."""
    sample_rate: int = Field(44100, ge=8000, le=192000, description="Audio sample rate in Hz")
    buffer_size: int = Field(512, ge=64, le=4096, description="Audio buffer size")
    channels: int = Field(2, ge=1, le=8, description="Number of audio channels")
    input_device: Optional[str] = Field(None, description="Audio input device name")
    output_device: Optional[str] = Field(None, description="Audio output device name")
    latency_ms: int = Field(50, ge=10, le=500, description="Target audio latency in ms")

    @validator('buffer_size')
    def buffer_power_of_two(cls, v):
        assert v & (v - 1) == 0, 'buffer_size must be power of 2'
        return v

class VideoConfig(BaseModel):
    """Video processing configuration."""
    width: int = Field(1920, ge=640, le=7680, description="Output width")
    height: int = Field(1080, ge=480, le=4320, description="Output height")
    fps: int = Field(60, ge=30, le=240, description="Target frame rate")
    vsync: bool = Field(True, description="Enable vertical sync")
    fullscreen: bool = Field(False, description="Start in fullscreen mode")

class DMXConfig(BaseModel):
    """DMX subsystem configuration."""
    universe_count: int = Field(1, ge=1, le=64, description="Number of DMX universes")
    refresh_rate: int = Field(44, ge=1, le=100, description="DMX refresh rate Hz")
    artnet_enabled: bool = Field(True, description="Enable Art-Net output")
    sacn_enabled: bool = Field(False, description="Enable sACN output")
    default_fade_time: float = Field(0.5, ge=0.0, le=10.0, description="Default fade time in seconds")
```

---

## Implementation Plan

### Day 1: Core Structure
- Create `src/vjlive3/config/config_manager.py`
- Implement `ConfigManager` class with basic get/set
- Define `ConfigSchema`, `ConfigLayer` enums
- Add Pydantic model validation
- Write unit tests for validation and layer merging

### Day 2: Layered Configuration
- Implement configuration layers (defaults, file, environment, runtime)
- Add file I/O for config persistence
- Implement environment variable loading (VJLIVE_ prefix)
- Add hot reload file watching
- Write integration tests for layers

### Day 3: State Integration & Schemas
- Integrate with ApplicationStateManager for change broadcasting
- Create initial config schemas (audio, video, dmx, etc.)
- Add configuration validation with detailed error reporting
- Implement config migration framework
- Write tests for state integration

### Day 4: Advanced Features
- Add secure secrets management (encryption for API keys)
- Implement configuration templates for different environments
- Add configuration UI integration hooks
- Implement configuration backup and restore
- Write tests for security and migration

### Day 5: Testing & Polish
- Comprehensive test suite (≥80% coverage)
- Performance profiling
- Error scenario testing (corrupted config, invalid types)
- Documentation and usage examples
- Migration utilities for legacy config formats

---

## Test Strategy

**Unit Tests:**
- Layer merging and precedence
- Pydantic validation (valid and invalid data)
- Schema registration and retrieval
- Get/set operations with type safety
- Environment variable parsing
- File I/O and serialization

**Integration Tests:**
- Full config lifecycle (create → modify → save → reload)
- ApplicationStateManager integration
- Hot reload functionality
- Migration scenarios (old → new schema)
- Multi-environment support

**Performance Tests:**
- Config load/save latency
- Memory usage with large configs
- Hot reload overhead

---

## Performance Requirements

- **Load Time:** <100ms for typical config (100KB)
- **Save Time:** <50ms for typical config
- **Hot Reload:** <10ms detection to application
- **Memory:** Config data <10MB typical

---

## Safety Rail Compliance

- **Rail 7 (No Silent Failures):** Validation errors raised with detailed messages
- **Rail 8 (Resource Leak Prevention):** File handles closed; no resource leaks
- **Rail 10 (Security):** Secrets encrypted at rest; no plaintext API keys

---

## Dependencies

- **P1-C1:** ApplicationStateManager — for change broadcasting
- **P1-C2:** StatePersistenceManager — optional for backup/restore
- **Blocking:** None beyond P1-C1
- **Blocked By:** P1-C1

---

## Open Questions

1. Should we use a database (SQLite) for config instead of JSON? (JSON fine for now)
2. How to handle binary config data? (Base64 encode or separate files)
3. Do we need remote config sync? (Future phase)
4. Should config changes require restart? (No, hot reload preferred)

---

## References

- `WORKSPACE/PRIME_DIRECTIVE.md`
- `WORKSPACE/SAFETY_RAILS.md`
- Legacy: `vjlive/config_manager.py`, `VJlive-2/config_types.py`

---

**"The best code is code that knows what it is and does it well."**
*— WORKSPACE/PRIME_DIRECTIVE.md*