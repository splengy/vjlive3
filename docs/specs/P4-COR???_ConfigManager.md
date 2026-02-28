# Spec: P4-COR??? — ConfigManager

## Task: P4-COR??? — ConfigManager (Core Configuration System)

**Priority:** P0 (Critical Infrastructure)
**Source:** Legacy (`config_manager.py`)
**Status:** ◯ Todo → 🔄 In Progress (Specification)

---

## What This Module Does

ConfigManager is the **central configuration authority** for VJLive3. It manages loading, validation, persistence, and runtime updates of all application configuration with enhanced type safety using Pydantic models. It operates on the unified configuration's `vjlive` section and provides a single source of truth for all system settings.

**Key Responsibilities:**
- Load configuration from multiple sources (JSON files, environment variables, defaults)
- Validate configuration using Pydantic schemas with type safety
- Provide hierarchical configuration access (system, audio, video, plugins, etc.)
- Watch for configuration file changes and hot-reload
- Manage configuration persistence (save/load)
- Provide configuration change notifications via event bus
- Support multiple configuration environments (dev, staging, prod)
- Secure handling of sensitive data (API keys, secrets)

---

## What It Does NOT Do

- ❌ Does NOT implement business logic — purely configuration management
- ❌ Does NOT make decisions about configuration values — only validates and provides access
- ❌ Does NOT directly interact with hardware or plugins — they query ConfigManager
- ❌ Does NOT store runtime state — configuration is separate from application state
- ❌ Does NOT implement security encryption — relies on OS-level file permissions and secure vault for secrets

---

## Public Interface

### Core Classes

#### `ConfigManager`
Main configuration manager class (Singleton pattern).

```python
class ConfigManager:
    """Central configuration manager with type-safe access and validation."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize ConfigManager with optional config file path."""
        pass
    
    def load(self) -> VJLiveConfig:
        """Load configuration from all sources and validate."""
        pass
    
    def save(self) -> None:
        """Save current configuration to disk."""
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        pass
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value and validate."""
        pass
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get an entire configuration section as dict."""
        pass
    
    def reload(self) -> None:
        """Reload configuration from disk (hot-reload)."""
        pass
    
    def validate(self) -> List[str]:
        """Validate current configuration, return list of errors."""
        pass
    
    def get_environment(self) -> ConfigEnvironment:
        """Get current deployment environment."""
        pass
    
    def set_environment(self, env: ConfigEnvironment) -> None:
        """Set deployment environment."""
        pass
    
    def subscribe(self, callback: Callable[[str, Any], None]) -> None:
        """Subscribe to configuration changes."""
        pass
    
    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from configuration changes."""
        pass
    
    @property
    def vjlive(self) -> VJLiveConfig:
        """Get the main VJLive configuration section."""
        pass
```

#### `VJLiveConfig` (Pydantic Model)
Complete application configuration schema.

```python
class VJLiveConfig(BaseModel):
    """Complete VJLive configuration."""
    
    system: SystemConfig
    audio: AudioConfig
    video: VideoConfig
    plugins: PluginConfig
    midi: MIDIConfig
    osc: OSCConfig
    dmx: LightingConfig
    recording: RecordingConfig
    security: SecurityConfig
    logging: LoggingConfig
    paths: PathConfig
    defaults: DefaultsConfig
    mapping: MappingConfig
    media: MediaConfig
    output: List[OutputConfig]
    
    class Config:
        validate_assignment = True
        extra = "forbid"
```

#### `ConfigValidator`
Validates configuration files and environment variables.

```python
class ConfigValidator:
    """Validates VJLive configuration."""
    
    def validate_file(self, path: Path) -> ValidationResult:
        """Validate a configuration file."""
        pass
    
    def validate_env_vars(self) -> ValidationResult:
        """Validate environment variable overrides."""
        pass
    
    def schema(self) -> Dict[str, Any]:
        """Get JSON schema for configuration."""
        pass
```

#### `ConfigWatcher`
Watches for configuration file changes.

```python
class ConfigWatcher:
    """Watches config files for changes and triggers reload."""
    
    def __init__(self, config_manager: ConfigManager, paths: List[Path]):
        pass
    
    def start(self) -> None:
        """Start watching for changes."""
        pass
    
    def stop(self) -> None:
        """Stop watching."""
        pass
    
    def on_change(self, callback: Callable[[Path], None]) -> None:
        """Register change callback."""
        pass
```

---

## Inputs and Outputs

### Inputs
- **Configuration Files:** JSON/YAML files from standard locations:
  - `/etc/vjlive/config.json` (system-wide)
  - `~/.config/vjlive/config.json` (user)
  - `./config.json` (project-local)
  - Environment variables: `VJLIVE_*` overrides
- **Schema Definitions:** Pydantic models defining valid configuration structure
- **Default Values:** Hardcoded sensible defaults for all settings

### Outputs
- **Validated Configuration:** Type-safe `VJLiveConfig` object
- **Validation Errors:** Detailed error messages with line numbers
- **Change Events:** Notifications via EventBus when config changes
- **Saved Files:** Serialized configuration to disk

---

## Edge Cases and Error Handling

### Missing Configuration File
- **Behavior:** Load defaults + environment variables, log warning
- **Recovery:** Create default config file on first save

### Invalid Configuration
- **Behavior:** Raise `ConfigValidationError` with detailed field errors
- **Recovery:** Fall back to defaults, mark invalid sections as disabled

### Permission Errors
- **Behavior:** Log error, continue with read-only config if possible
- **Recovery:** Alert user, suggest running with proper permissions

### Circular References
- **Behavior:** Detect and reject with `ConfigCircularError`
- **Recovery:** User must fix config file structure

### Environment Variable Parsing
- **Behavior:** Strict type conversion, fail fast on invalid values
- **Recovery:** Log error, use default for that specific key

### Hot-Reload Race Conditions
- **Behavior:** Use file locking or atomic replace to prevent partial reads
- **Recovery:** Queue reload events, process sequentially

---

## Dependencies

### Direct Dependencies
- **Pydantic** (`pydantic.BaseModel`) — Type-safe configuration schemas
- **Pathlib** (`pathlib.Path`) — File path handling
- **JSON** / **YAML** — Configuration serialization
- **Watchdog** (optional) — File system watching for hot-reload
- **EventBus** — For configuration change notifications
- **Logging** — Structured logging for config operations

### Indirect Dependencies (consumers of ConfigManager)
- **All other core systems** — Every subsystem queries config
- **PluginRegistry** — Plugin configuration loading
- **AudioEngine** — Audio device and analysis settings
- **HardwareManager** — Hardware discovery and device settings
- **AgentManager** — Agent behavior configuration
- **NeuralEngine** — Model paths and inference settings

---

## Test Plan

### Unit Tests (≥80% coverage)

#### `test_config_manager_basic.py`
```python
def test_load_default_config():
    """Test loading with no config file uses defaults."""
    cm = ConfigManager()
    config = cm.load()
    assert config.system is not None
    assert config.audio is not None

def test_load_from_file():
    """Test loading from specific config file."""
    cm = ConfigManager(Path("test_config.json"))
    config = cm.load()
    # Verify custom values

def test_get_set():
    """Test getting and setting values."""
    cm = ConfigManager()
    cm.set("audio.sample_rate", 48000)
    assert cm.get("audio.sample_rate") == 48000

def test_get_section():
    """Test retrieving entire sections."""
    cm = ConfigManager()
    audio_config = cm.get_section("audio")
    assert "sample_rate" in audio_config

def test_validation_errors():
    """Test that invalid config raises errors."""
    cm = ConfigManager(Path("invalid_config.json"))
    with pytest.raises(ConfigValidationError):
        cm.load()

def test_environment_override():
    """Test environment variable overrides."""
    os.environ["VJLIVE_AUDIO_SAMPLE_RATE"] = "96000"
    cm = ConfigManager()
    config = cm.load()
    assert config.audio.sample_rate == 96000
```

#### `test_config_validator.py`
```python
def test_schema_generation():
    """Test JSON schema generation for external tools."""
    validator = ConfigValidator()
    schema = validator.schema()
    assert "properties" in schema

def test_validate_missing_required():
    """Test validation catches missing required fields."""
    validator = ConfigValidator()
    result = validator.validate_file(Path("missing_fields.json"))
    assert not result.is_valid
    assert "audio" in result.errors[0]
```

#### `test_config_watcher.py`
```python
def test_watcher_triggers_reload(tmp_path):
    """Test that file change triggers reload callback."""
    config_file = tmp_path / "config.json"
    config_file.write_text('{"audio": {"sample_rate": 44100}}')
    
    cm = ConfigManager(config_file)
    cm.load()
    
    watcher = ConfigWatcher(cm, [config_file])
    reloaded = False
    
    def on_reload(path):
        nonlocal reloaded
        reloaded = True
    
    watcher.on_change(on_reload)
    watcher.start()
    
    # Modify file
    config_file.write_text('{"audio": {"sample_rate": 48000}}')
    time.sleep(0.1)  # Allow watcher to detect
    
    assert reloaded
```

### Integration Tests
```python
def test_config_integration_with_audio_engine():
    """Test AudioEngine reads correct config."""
    cm = ConfigManager()
    cm.set("audio.sample_rate", 48000)
    engine = AudioEngine(cm)
    assert engine.sample_rate == 48000

def test_config_change_notification():
    """Test EventBus receives config change events."""
    cm = ConfigManager()
    events = []
    
    def on_config_change(key, value):
        events.append((key, value))
    
    EventBus.subscribe("config.changed", on_config_change)
    cm.set("audio.sample_rate", 96000)
    
    assert ("audio.sample_rate", 96000) in events
```

---

## Implementation Notes

### Configuration Hierarchy
1. **Defaults** (hardcoded in `VJLiveConfig` model)
2. **System Config** (`/etc/vjlive/config.json`)
3. **User Config** (`~/.config/vjlive/config.json`)
4. **Project Config** (`./config.json` in current working directory)
5. **Environment Variables** (`VJLIVE_*` — highest priority)

Later sources override earlier ones. Merge is deep (nested dicts combined, not replaced wholesale).

### File Format
- Primary: JSON (for machine readability)
- Optional: YAML support for human editing
- Schema: Defined by Pydantic models, exportable as JSON Schema

### Type Safety
- All configuration values typed via Pydantic
- Nested models for sections (AudioConfig, VideoConfig, etc.)
- Validators for custom constraints (sample_rate ∈ {44100, 48000, 96000})
- Enum types for restricted choices (e.g., `ConfigEnvironment`)

### Hot-Reload Strategy
- **Watchdog** observer monitors config files
- On change: validate new config → if valid, atomically swap → emit event
- Subsystems subscribe to `config.changed` events to update runtime settings
- Invalid changes: log error, keep current config, alert user

### Security Considerations
- **Secrets Management:** Do NOT store API keys in plain text config. Use:
  - Environment variables for LLM API keys
  - OS keyring for persistent secrets
  - ConfigManager only references secure vault
- **File Permissions:** Config files should be `0600` (user-only)
- **Input Sanitization:** Pydantic validation prevents injection attacks

### Performance
- **Lazy Loading:** Config loaded on first access, cached thereafter
- **Immutable Snapshots:** After load, provide read-only snapshot to consumers
- **Change Notifications:** EventBus pub/sub, O(1) dispatch
- **Memory:** Single config object in memory (~100 KB typical)

### Error Recovery
- **Corrupted Config:** Back up last-known-good, restore defaults, alert user
- **Permission Denied:** Read-only mode, log warning, continue with defaults
- **Schema Mismatch:** Detailed error messages with field paths

---

## Verification Checkpoints

### ✅ Phase 1: Foundation (Days 1-2)
- [ ] Pydantic models defined for all config sections
- [ ] Default values populated with sensible defaults
- [ ] Basic load/save working with JSON
- [ ] Unit tests for ConfigManager core (≥80% coverage)

### ✅ Phase 2: Core Engine (Days 3-5)
- [ ] Environment variable override support
- [ ] Config validation with detailed error messages
- [ ] Hierarchical merging (defaults + files + env)
- [ ] ConfigValidator with JSON Schema export
- [ ] Integration tests with 2-3 consumers (AudioEngine, PluginRegistry)

### ✅ Phase 3: Advanced Analysis (Days 6-8)
- [ ] ConfigWatcher with file system monitoring
- [ ] Hot-reload functionality with atomic swaps
- [ ] EventBus integration for change notifications
- [ ] YAML format support (optional but nice)
- [ ] Performance benchmarks: load <100ms, get <0.1ms

### ✅ Phase 4: Integration & Polish (Days 9-10)
- [ ] Security audit: no plaintext secrets, proper file perms
- [ ] Documentation: config file reference with all options
- [ ] Migration tools: convert legacy configs to new format
- [ ] Stress test: 1000 config loads/gets in <1s
- [ ] Final integration testing with full system

### ✅ Phase 5: Testing & Validation (Days 11-12)
- [ ] All tests passing (≥80% coverage)
- [ ] No safety rail violations (memory, FPS impact negligible)
- [ ] Performance benchmarks met
- [ ] Code review completed
- [ ] Ready for production deployment

---

## Resources

### Legacy References
- `vjlive/config_manager.py` — Original configuration manager
- `vjlive/config_types.py` — Configuration data types and schemas
- `vjlive/config_validation.py` — Validation logic
- `VJlive-2/core/config/` — Clean architecture config patterns

### Existing VJLive3 Code
- `src/vjlive3/audio/config.py` — Audio-specific config (already ported)
- `src/vjlive3/llm/config.py` — LLM service config (already ported)
- `src/vjlive3/core/event_bus.py` — Event bus for notifications

### External Documentation
- [Pydantic Documentation](https://docs.pydantic.dev/) — Data validation
- [JSON Schema](https://json-schema.org/) — Configuration schema standard
- [Watchdog](https://python-watchdog.readthedocs.io/) — File system monitoring

---

## Success Criteria

### Functional Completeness
- ✅ Loads configuration from all sources (defaults, files, env vars)
- ✅ Validates against Pydantic schemas with clear error messages
- ✅ Provides dot-notation access to nested values
- ✅ Supports hot-reload with file watching
- ✅ Emits change events via EventBus
- ✅ Saves configuration with proper serialization
- ✅ Manages multiple environments (dev/staging/prod)

### Performance
- ✅ Config load time <100ms (cold start)
- ✅ Config get/set <0.1ms (cached)
- ✅ Hot-reload latency <500ms from file change to notification
- ✅ Memory footprint <50 MB for config + schemas

### Reliability
- ✅ Graceful degradation on config errors (fallback to defaults)
- ✅ Atomic config swaps during hot-reload (no partial state)
- ✅ Backup of previous config on save
- ✅ Handles concurrent access safely (thread-safe reads, exclusive writes)

### Integration
- ✅ All core systems can query config without circular dependencies
- ✅ EventBus notifications allow runtime adaptation
- ✅ Configuration changes propagate correctly to AudioEngine, HardwareManager, etc.
- ✅ No hardcoded values — everything configurable

### Security
- ✅ No plaintext secrets in config files
- ✅ File permissions enforced (0600 for user config)
- ✅ Environment variable overrides validated
- ✅ Secure vault integration for sensitive data

---

## Next Steps After Approval

1. Create `src/vjlive3/core/config/` directory structure
2. Implement Pydantic models for all config sections
3. Build ConfigManager with load/save/merge logic
4. Add ConfigValidator with schema generation
5. Integrate EventBus for change notifications
6. Implement ConfigWatcher with watchdog
7. Write comprehensive unit and integration tests
8. Document all configuration options with examples
9. Performance tuning and safety rail validation
10. Update BOARD.md to mark P4-COR??? as in progress

---

**Specification Status:** ✅ Ready for Implementation (Auto-Approved)
**Estimated Effort:** 5-7 days (depending on integration complexity)
**Critical Path:** Blocking — Required by nearly all other core systems
**Assignment:** Implementation Engineer Alpha (next in alternating sequence)