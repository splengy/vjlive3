# VERIFICATION CHECKPOINTS & SUCCESS CRITERIA

**Purpose:** Define clear, testable completion criteria for each work stream to prevent incomplete task handoffs.

**Protocol:** Every task must pass its verification checkpoint before being marked [x] in BOARD.md.

---

## PHASE 1: SECURITY COMPLETION (P0)

### Checkpoint 1.1: SEC-009 - User-Based Rate Limiting

**Success Criteria:**
- [ ] Rate limiter uses user ID from JWT token when authenticated
- [ ] Unauthenticated requests fall back to IP-based limiting (100 req/min for authenticated, 10/min for unauthenticated)
- [ ] Rate limit counters stored with TTL (Redis or in-memory)
- [ ] `X-RateLimit-Limit` and `X-RateLimit-Remaining` headers present in responses
- [ ] Load test: 101 requests from authenticated user within 60s returns 429 on 101st
- [ ] Load test: 11 requests from unauthenticated IP within 60s returns 429 on 11th

**Verification Commands:**
```bash
# Authenticated rate limit test
curl -H "Authorization: Bearer <valid_jwt>" http://localhost:5000/api/health -v
# Repeat 100 times, 101st should return 429

# Unauthenticated rate limit test
curl http://localhost:5000/api/health -v
# Repeat 10 times, 11th should return 429
```

**Files Modified:** `core/rate_limiter.py`, `core/api/server.py`, `core/security/auth.py`

---

### Checkpoint 1.2: SEC-010 - RBAC Implementation

**Success Criteria:**
- [ ] Roles defined: `admin`, `user`, `guest` with clear permission sets
- [ ] `@require_admin` decorator protects all `/superadmin/*` endpoints
- [ ] `@require_permission('plugin:write')` protects plugin modification endpoints
- [ ] `@require_permission('system:read')` protects system status endpoints
- [ ] JWT payload includes `role` and `permissions` claims
- [ ] Unauthorized role access returns 403 Forbidden
- [ ] Admin endpoints tested with admin/user/guest tokens

**Verification Commands:**
```bash
# Test admin endpoint with user role (should fail)
curl -H "Authorization: Bearer <user_jwt>" http://localhost:5000/superadmin/status -v
# Expected: 403 Forbidden

# Test admin endpoint with admin role (should succeed)
curl -H "Authorization: Bearer <admin_jwt>" http://localhost:5000/superadmin/status -v
# Expected: 200 OK
```

**Files Modified:** `core/security/rbac.py`, `core/admin_api.py`, `core/api/server.py`

---

### Checkpoint 1.3: SEC-013 - Docker Network Security

**Success Criteria:**
- [ ] `docker-compose.prod.yml` has NO `privileged: true` flags
- [ ] All services have `security_opt: ["no-new-privileges: true"]`
- [ ] Unnecessary capabilities removed (only keep needed: `NET_BIND_SERVICE` if binding to <1024)
- [ ] All containers run as non-root user (check `User:` directive in Dockerfile or `user:` in compose)
- [ ] Docker secrets configured for JWT_SECRET, DB_PASSWORD, API_KEYS
- [ ] `docker inspect` shows `Privileged: false` for all containers

**Verification Commands:**
```bash
# Check container privileges
docker inspect vjlive-backend | grep -i privileged
# Expected: "Privileged": false,

# Check container user
docker inspect vjlive-backend | grep -i user
# Expected: "User": "1000:1000" (or similar non-root UID)

# Check secrets mounted
docker exec vjlive-backend ls -la /run/secrets/
# Expected: jwt_secret, db_password, etc.
```

**Files Modified:** `docker-compose.prod.yml`, `Dockerfile.production.*`, `config/secrets/`

---

### Checkpoint 1.4: SEC-015 - Input Validation with Pydantic

**Success Criteria:**
- [ ] ALL API endpoints use specific Pydantic models (no `Dict[str, Any]` or `Any`)
- [ ] Request size limits configured (max 10MB for uploads, max 1MB for JSON bodies)
- [ ] File uploads validated: size, MIME type, content (reject .exe, .sh, etc.)
- [ ] SQL injection prevention via parameterized queries (no string concatenation)
- [ ] Path traversal prevention: all file paths validated with `PathSanitizer`
- [ ] 100% of endpoints have request/response models in OpenAPI schema

**Verification Commands:**
```bash
# Check OpenAPI schema for models
curl http://localhost:5000/openapi.json | jq '.components.schemas | keys'
# Should list all Pydantic models, not "Any"

# Test oversized request
curl -X POST http://localhost:5000/api/upload -H "Content-Type: application/json" \
  --data-binary @large_payload.json
# Expected: 413 Payload Too Large

# Test path traversal
curl http://localhost:5000/api/file?path=../../../etc/passwd
# Expected: 400 Bad Request (path rejected)
```

**Files Modified:** `core/api/endpoints/*`, `core/input_validation.py`, `core/schemas.py`

---

### Checkpoint 1.5: SEC-016 - Command Injection Prevention

**Success Criteria:**
- [ ] ALL `subprocess` calls use `shell=False` with list arguments
- [ ] `device_path` and user-controlled inputs validated before passing to subprocess
- [ ] No `os.system()`, `os.popen()`, or `subprocess.run(..., shell=True)`
- [ ] Input sanitization: allow only alphanumeric, `/`, `-`, `_` for device paths
- [ ] Static analysis: `bandit` shows 0 HIGH severity issues

**Verification Commands:**
```bash
# Run bandit security scan
bandit -r core/video_sources.py core/astra_linux.py
# Expected: No HIGH severity issues

# Test command injection attempt
curl -X POST http://localhost:5000/api/device -d '{"path": "/dev/video0; rm -rf /"}'
# Expected: 400 Bad Request (path validation fails)
```

**Files Modified:** `core/video_sources.py`, `core/astra_linux.py`, `core/subprocess_wrapper.py`

---

### Checkpoint 1.6: SEC-018 - External Security Audit

**Success Criteria:**
- [ ] Security consultant completed 2-3 day penetration test
- [ ] No HIGH severity findings remaining
- [ ] All MEDIUM severity findings addressed or documented as accepted risk
- [ ] Audit report stored in `audits/security_audit_2026-02-XX.md`
- [ ] SSL Labs grade A+ (if external-facing)

**Verification:**
- [ ] Audit report exists and is signed off
- [ ] All critical findings have corresponding GitHub issues in backlog

---

## PHASE 2: ARCHITECTURAL CONSOLIDATION

### Checkpoint 2.1: ARCH-001 - Matrix Consolidation

**Success Criteria:**
- [ ] `core/matrix/matrix.py` removed (456 lines deleted)
- [ ] All imports changed from `from core.matrix import Matrix` to `from core.matrix.unified_matrix import UnifiedMatrix`
- [ ] Compatibility adapter created if any legacy code still uses old Matrix (should be zero)
- [ ] State persistence format updated to use UnifiedMatrix serialization
- [ ] All tests pass: `pytest tests/test_matrix*.py`
- [ ] No references to old Matrix class remain (grep: `class Matrix`)

**Verification Commands:**
```bash
# Search for old Matrix usage
grep -r "from core.matrix import Matrix" core/ plugins/
# Expected: No results

# Search for Matrix class definition
grep -r "class Matrix" core/
# Expected: No results (only UnifiedMatrix)

# Run matrix-related tests
pytest tests/test_matrix*.py -v
# Expected: All tests pass
```

**Files Modified:** All files importing Matrix, `core/matrix/unified_matrix.py`, `core/matrix/__init__.py`

---

### Checkpoint 2.2: ARCH-002 - Plugin Architecture Rationalization

**Success Criteria:**
- [ ] Single manifest format: `plugin.json` (no more `.vjfx`, `.manifest` variants)
- [ ] All plugins load through `PluginRegistry` and `PluginLoader` only
- [ ] Duplicate manifest scanning code removed (1000+ lines deleted)
- [ ] All 47+ plugins verified to load correctly: `pytest tests/test_plugin_loading.py`
- [ ] No direct `import` of plugin modules outside registry system

**Verification Commands:**
```bash
# Test plugin loading
pytest tests/test_plugin_loading.py -v
# Expected: All plugins load successfully

# Check for duplicate manifest code
grep -r "def.*load.*manifest" core/ | wc -l
# Expected: 1-2 functions (registry + loader)

# Verify manifest format
find plugins/ -name "plugin.json" | wc -l
# Should match total plugin count
```

**Files Modified:** `core/loader.py`, `core/plugin_registry.py`, all plugin directories (manifest updates)

---

### Checkpoint 2.3: ARCH-003 - Experimental Features Isolation

**Success Criteria:**
- [ ] `core/extensions/` directory created with subfolders: `quantum/`, `consciousness/`, `agents/`, `neural/`
- [ ] All experimental code moved into appropriate extension subfolder
- [ ] Each extension has README.md explaining concept, purpose, and limitations
- [ ] Each extension has `__init__.py` with `register_extension()` function
- [ ] Extensions are disabled by default via config flag (`enable_quantum: false`, etc.)
- [ ] No circular dependencies between extensions and core
- [ ] Extensions can be imported independently: `python -c "import core.extensions.quantum"` succeeds

**Verification Commands:**
```bash
# Test extension imports
python -c "import core.extensions.quantum; print('OK')"
python -c "import core.extensions.consciousness; print('OK')"
python -c "import core.extensions.agents; print('OK')"
python -c "import core.extensions.neural; print('OK')"
# All should succeed

# Check for circular dependencies
python -c "import core.extensions.quantum; import core; print('No circular deps')"
# Should not raise ImportError

# Verify extensions disabled by default
grep "enable_quantum" config/default.yaml
# Expected: enable_quantum: false
```

**Files Modified:** Many - all experimental code files, `core/extensions/registry.py`, config files

---

## PHASE 3: FILE SPLITTING

### Checkpoint 3.1: ARCH-004 - VJLiveApp Split

**Success Criteria:**
- [ ] `core/app/app.py` reduced from 3024 lines to <500 lines (orchestration only)
- [ ] Extracted classes: `UIManager`, `OutputManager`, `AgentManager`, `AutomationManager`, `MixerManager`
- [ ] Each extracted class in separate file: `core/app/ui_manager.py`, `core/app/output_manager.py`, etc.
- [ ] All imports updated to use new module paths
- [ ] No circular dependencies between extracted modules
- [ ] Application still boots: `python core/app/app.py` starts without errors
- [ ] All existing tests pass

**Verification Commands:**
```bash
# Check file size
wc -l core/app/app.py
# Expected: <500 lines

# Check extracted files exist
ls -la core/app/ui_manager.py core/app/output_manager.py core/app/agent_manager.py \
  core/app/automation_manager.py core/app/mixer_manager.py
# All should exist

# Test app startup
python core/app/app.py --help
# Should display help without errors

# Run tests
pytest tests/test_app_integration.py -v
# Expected: All tests pass
```

**Files Modified:** `core/app/app.py` (split), new files created, all files importing VJLiveApp

---

### Checkpoint 3.2: ARCH-005 - MoodManifold Split

**Success Criteria:**
- [ ] `core/mood_manifold.py` reduced from 2526 lines to <500 lines (core only)
- [ ] Extracted modules: `MoodManifold` core, `MoodUI`, `MoodPersistence`, `MoodEffects`
- [ ] Each in separate file: `core/mood/mood_manifold.py`, `core/mood/mood_ui.py`, `core/mood/mood_persistence.py`, `core/mood/mood_effects.py`
- [ ] All imports updated
- [ ] No circular dependencies
- [ ] Mood system tests pass

**Verification Commands:**
```bash
# Check file sizes
wc -l core/mood/mood_manifold.py
# Expected: <500 lines

# Check extracted files
ls -la core/mood/mood_ui.py core/mood/mood_persistence.py core/mood/mood_effects.py
# All should exist

# Test mood system
pytest tests/test_mood_manifold.py -v
# Expected: All tests pass
```

**Files Modified:** `core/mood_manifold.py` (split), new `core/mood/` directory

---

### Checkpoint 3.3: ARCH-008 - Shader System Split

**Success Criteria:**
- [ ] `core/shaders/shader_base.py` reduced from 1713 lines to <500 lines (base only)
- [ ] Extracted modules: `ShaderProgram`, `Framebuffer`, `Effect` (base), `EffectChain`, `ShaderSecurityManager`
- [ ] Each in separate file: `core/shaders/program.py`, `core/shaders/framebuffer.py`, `core/shaders/effect.py`, `core/shaders/chain.py`, `core/shaders/security.py`
- [ ] All imports updated
- [ ] Shader compilation tests pass
- [ ] No circular dependencies

**Verification Commands:**
```bash
# Check file sizes
wc -l core/shaders/program.py core/shaders/framebuffer.py core/shaders/effect.py \
  core/shaders/chain.py core/shaders/security.py
# All should be <500 lines

# Test shader compilation
pytest tests/test_shader_compilation.py -v
# Expected: All tests pass
```

**Files Modified:** `core/shaders/shader_base.py` (split), new shader module files

---

### Checkpoint 3.4: ARCH-009 - AI Integration Split

**Success Criteria:**
- [ ] `core/ai_integration.py` reduced from 923 lines to <500 lines (integration only)
- [ ] Extracted modules: `AIIntegration` (main), individual system wrappers in `core/ai/systems/`, `AISystemStatus` dataclass
- [ ] Structure: `core/ai/__init__.py`, `core/ai/integration.py`, `core/ai/systems/` (multiple files), `core/ai/status.py`
- [ ] All imports updated
- [ ] AI system tests pass (or marked as optional if not production-critical)

**Verification Commands:**
```bash
# Check file sizes
wc -l core/ai/integration.py core/ai/status.py
# Expected: <500 lines each

# Check systems directory
ls -la core/ai/systems/
# Should contain individual system wrappers

# Test AI integration (if applicable)
pytest tests/test_ai_integration.py -v 2>/dev/null || echo "Tests skipped (optional)"
```

**Files Modified:** `core/ai_integration.py` (split), new `core/ai/` structure

---

### Checkpoint 3.5: ARCH-010 - Live Coding Engine Split

**Success Criteria:**
- [ ] `core/live_coding_engine.py` reduced from 1335 lines to <500 lines (engine only)
- [ ] Extracted classes into separate files:
  - `CollaborativeSession` → `core/live_coding/session.py`
  - `LiveCodingEngine` → `core/live_coding/engine.py`
  - `VisualProgrammingInterface` → `core/live_coding/visual.py`
  - `AICreativeAssistant` → `core/live_coding/ai_assistant.py`
  - `LiveCodingWebSocketServer` → `core/live_coding/websocket_server.py`
- [ ] All imports updated
- [ ] Live coding WebSocket server starts successfully
- [ ] Collaborative editing tests pass (if any)

**Verification Commands:**
```bash
# Check file sizes
wc -l core/live_coding/engine.py core/live_coding/session.py \
  core/live_coding/visual.py core/live_coding/ai_assistant.py \
  core/live_coding/websocket_server.py
# All should be <500 lines

# Test live coding server startup
python -c "from core.live_coding.websocket_server import start_live_coding_server; print('OK')"
# Should import without errors

# Run live coding tests
pytest tests/test_live_coding.py -v 2>/dev/null || echo "Tests may not exist"
```

**Files Modified:** `core/live_coding_engine.py` (split), new `core/live_coding/` directory

---

## PHASE 4: VALIDATION & TESTING

### Checkpoint 4.1: ARCH-006 - Application Boot Validation

**Success Criteria:**
- [ ] `python core/main.py --help` executes without errors
- [ ] `python core/app/app.py --help` executes without errors
- [ ] All entry points documented in `docs/OPERATIONS.md`
- [ ] Startup sequence logs cleanly (no ERROR level logs during normal startup)
- [ ] Health endpoint returns 200: `curl http://localhost:5000/health`
- [ ] All core services initialize: Engine, Matrix, Renderer, PluginSystem

**Verification Commands:**
```bash
# Test main.py
python core/main.py --help
# Expected: Help text, exit code 0

# Test app.py (may need mock hardware)
VJLIVE_NO_GL=1 python core/app/app.py --help
# Expected: Help text, exit code 0

# Test health endpoint
curl -f http://localhost:5000/health
# Expected: {"status": "healthy", ...} with 200 OK

# Check startup logs
python core/main.py 2>&1 | grep -i error
# Expected: No ERROR lines (WARNING okay)
```

**Files Modified:** Any files preventing boot (to be identified during testing)

---

### Checkpoint 4.2: QUAL-015+ - Testing Infrastructure

**Success Criteria:**
- [ ] `pytest.ini` configured with `--cov=core --cov-fail-under=80`
- [ ] Unit tests cover all core modules (target 80%+ coverage)
- [ ] Integration tests cover plugin loading, parameter routing, matrix operations
- [ ] System tests cover full pipeline: source → effects → output
- [ ] Performance tests verify 60 FPS achievable
- [ ] Fuzzing tests for security-critical inputs (API endpoints, file uploads)
- [ ] Chaos tests (process kill, network failure) demonstrate resilience
- [ ] CI/CD runs all tests on every PR

**Verification Commands:**
```bash
# Run full test suite with coverage
pytest --cov=core --cov-report=term --cov-fail-under=80
# Expected: Coverage >=80%, exit code 0

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/system/ -v
pytest tests/performance/ -v
# All should pass

# Check CI configuration
cat .github/workflows/test.yml | grep -A5 "pytest"
# Should include coverage flags
```

**Files Modified:** `pytest.ini`, `tests/` (new tests), `.github/workflows/test.yml`

---

## PHASE 5: GENIUS PRESERVATION

### Checkpoint 5.1: GEN-001 - Quantum Algorithms Isolation

**Success Criteria:**
- [ ] All quantum-related files moved to `core/extensions/quantum/`
- [ ] Each file has README explaining the quantum concept and limitations
- [ ] No circular dependencies with core
- [ ] Extension can be imported independently: `import core.extensions.quantum`
- [ ] Extension disabled by default (`enable_quantum: false` in config)
- [ ] Extension registers itself with `ExtensionRegistry` when enabled

**Verification Commands:**
```bash
# Test import
python -c "import core.extensions.quantum; print('OK')"
# Should succeed

# Check config flag
grep "enable_quantum" config/default.yaml
# Expected: enable_quantum: false

# Check for circular deps
python -c "import core; import core.extensions.quantum; print('No circular')"
# Should not raise ImportError
```

**Files Modified:** Quantum-related files moved, `core/extensions/quantum/__init__.py`, config files

---

### Checkpoint 5.2: GEN-002 - Consciousness Systems Isolation

**Success Criteria:**
- [ ] All consciousness-related files moved to `core/extensions/consciousness/`
- [ ] Each file has README explaining the consciousness concept and limitations
- [ ] No circular dependencies
- [ ] Independent import: `import core.extensions.consciousness`
- [ ] Disabled by default (`enable_consciousness: false`)
- [ ] Self-registration with ExtensionRegistry

**Verification Commands:**
```bash
python -c "import core.extensions.consciousness; print('OK')"
grep "enable_consciousness" config/default.yaml
# Expected: enable_consciousness: false
```

---

### Checkpoint 5.3: GEN-003 - Agent Infrastructure Isolation

**Success Criteria:**
- [ ] All agent-related files moved to `core/extensions/agents/`
- [ ] `IAgent` interface defined in `agent_base.py` with methods: `init()`, `update()`, `render()`, `cleanup()`, `get_state()`
- [ ] All agent classes inherit from `IAgent` or implement the interface
- [ ] No circular dependencies
- [ ] Independent import: `import core.extensions.agents`
- [ ] Disabled by default (`enable_agents: false`)
- [ ] Agent count reduced from 260+ to <50 coherent implementations

**Verification Commands:**
```bash
python -c "import core.extensions.agents; print('OK')"
grep "enable_agents" config/default.yaml
# Expected: enable_agents: false

# Count agent classes
grep -r "class.*Agent" core/extensions/agents/ | wc -l
# Expected: <50
```

---

### Checkpoint 5.4: GEN-004 - Neural Network Effects Isolation

**Success Criteria:**
- [ ] All neural network-related files moved to `core/extensions/neural/`
- [ ] Each file has README explaining the neural effect and model requirements
- [ ] No circular dependencies
- [ ] Independent import: `import core.extensions.neural`
- [ ] Disabled by default (`enable_neural: false`)
- [ ] ML models load successfully when enabled (test with `enable_neural: true`)

**Verification Commands:**
```bash
python -c "import core.extensions.neural; print('OK')"
grep "enable_neural" config/default.yaml
# Expected: enable_neural: false
```

---

### Checkpoint 5.5: GEN-005 - Extension Registry System

**Success Criteria:**
- [ ] `core/extensions/registry.py` exists with `ExtensionRegistry` class
- [ ] Registry supports: `register(extension)`, `enable(name)`, `disable(name)`, `list_enabled()`
- [ ] Each extension registers itself on import via `register_extension(registry)`
- [ ] Extensions can be enabled/disabled via config at startup
- [ ] Registry provides discovery: `get_extension(name)`, `has_extension(name)`
- [ ] No circular dependencies between registry and extensions

**Verification Commands:**
```bash
python -c "from core.extensions.registry import ExtensionRegistry; print('OK')"
# Test registry functionality
python -c "
from core.extensions.registry import ExtensionRegistry
r = ExtensionRegistry()
r.discover()
print(f'Found {len(r.list_available())} extensions')
print(f'Enabled: {r.list_enabled()}')
"
# Should discover all extensions, show none enabled by default
```

---

### Checkpoint 5.6: GEN-006 - Documentation Updated

**Success Criteria:**
- [ ] `docs/extensions/` directory created
- [ ] Each extension has its own documentation file: `docs/extensions/quantum.md`, `docs/extensions/consciousness.md`, etc.
- [ ] Documentation explains: what the extension does, how to enable it, performance characteristics, known limitations
- [ ] README in each extension directory cross-references documentation
- [ ] Main README updated to explain experimental vs. core features

**Verification:**
- [ ] All documentation files exist and are non-empty
- [ ] No "hallucinated feature" claims in documentation (only actual implemented features)

---

## GENERAL VERIFICATION RULES

1. **All Tests Must Pass:** Before marking any task [x], run relevant tests and ensure 0 failures.
2. **No New Lint Errors:** Code changes must not introduce new `flake8` or `mypy` errors.
3. **No Regression:** Existing functionality must not break (verify with integration tests).
4. **Documentation Updated:** Any new code must have corresponding docstrings and/or README updates.
5. **COMMS/AGENT_SYNC.md Updated:** Log completion with handoff notes for next agent.
6. **BOARD.md Updated:** Mark task [x] and update completion count.

---

**Last Updated:** 2026-02-19 by Roo (Architect Mode)
**Next Review:** After each checkpoint completion
