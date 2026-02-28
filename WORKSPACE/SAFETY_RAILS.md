# SAFETY RAILS: HARD LIMITS & NON-NEGOTIABLE CONSTRAINTS

**Purpose:** Define absolute boundaries that MUST NEVER be violated, regardless of task pressure or creative ambition.

**Enforcement:** These are automated checks and manual review gates. Violations trigger immediate workflow halt and BOARD.md flagging.

---

## 🚨 RAIL 1: 60 FPS SACRED (NON-NEGOTIABLE)

**Constraint:** At every phase completion, framerate MUST be tested and verified stable at 60 FPS in window mode before marking any task [x] or proceeding to next phase.

**Verification Protocol:**
```bash
# Run FPS validation
python profile_engine.py --duration 30 --resolution 1920x1080
# OR use test_fps_impact.py
pytest test_fps_impact.py -v
```

**Acceptance Criteria:**
- ✅ Average FPS ≥ 58 (2-frame buffer for GC spikes)
- ✅ Frame time variance < 5ms (consistent timing)
- ✅ No dropped frames in 60-second sample
- ✅ Memory usage stable (no monotonic increase indicating leaks)

**Violation Consequences:**
- Task marked [ ] with RED FLAG ⚠️
- Performance profiling required before continuation
- Root cause analysis in COMMS/PERFORMANCE_DEBUG.md

---

## 🚨 RAIL 2: OFFLINE-FIRST ARCHITECTURE

**Constraint:** NO dependencies on paid, cloud-based, or external APIs for core functionality.

**Allowed:**
- ✅ Local LLMs (Ollama, llama.cpp)
- ✅ Procedural generation
- ✅ Internal agentic systems
- ✅ Open-source libraries (MIT, Apache, GPL)

**Forbidden:**
- ❌ OpenAI API, Claude API, or any paid AI service
- ❌ Cloud databases (Firebase, Supabase) for core data
- ❌ External CDNs for critical assets
- ❌ SaaS services for essential features

**Verification:**
```bash
# Scan for API keys and external endpoints
grep -r "api_key\|OPENAI\|ANTHROPIC\|cloud:" core/ plugins/ config/
# Check requirements.txt for cloud SDKs
cat requirements.txt | grep -i "aws\|azure\|gcp\|openai"
```

**Violation:** Immediate revert + BOARD.md security flag

---

## 🚨 RAIL 3: PLUGIN SYSTEM INTEGRITY

**Constraint:** Every plugin MUST have a complete, creative manifest.json that acts as self-documentation.

**Required Manifest Fields:**
```json
{
  "name": "Creative, descriptive name (not 'plugin1')",
  "description": "2-3 sentences of evocative, data-driven description",
  "author": "Plugin author or 'VJLive Community'",
  "version": "1.0.0",
  "api_version": "2.0",
  "parameters": [
    {
      "name": "param_name",
      "type": "float|int|bool|color|vec2|vec3|vec4|enum",
      "min": 0.0,
      "max": 1.0,
      "default": 0.5,
      "description": "Evocative, specific description of effect"
    }
  ],
  "metadata": {
    "tags": ["glitch", "datamosh", "audio_reactive"],
    "category": "core|custom|experimental",
    "complexity": "low|medium|high",
    "performance_impact": "low|medium|high"
  }
}
```

**Verification:**
```bash
# Validate all manifests
python plugins/_verify.py
# Check for METADATA constant in plugin code
grep -r "METADATA" plugins/ | wc -l
```

**Violation:** Plugin excluded from build until manifest complete

---

## 🚨 RAIL 4: CODE SIZE DISCIPLINE

**Constraint:** No file shall exceed 750 lines of code (excluding comments and blank lines).

**Enforcement:**
- Automated check in CI/CD pipeline
- Pre-commit hook validation
- BOARD.md flag for violations

**Refactoring Required When:**
- File > 700 lines: Plan refactoring
- File > 750 lines: Block merge, immediate split

**Split Strategy:**
1. Extract classes into separate modules
2. Move helper functions to utils/
3. Create sub-packages for complex features
4. Preserve public API via __init__.py re-exports

**Violation:** PR blocked until refactoring complete

---

## 🚨 RAIL 5: TEST COVERAGE GATE

**Constraint:** All new code MUST have corresponding tests with ≥80% coverage.

**Test Requirements:**
- Unit tests for all public functions/classes
- Integration tests for plugin loading and execution
- Performance tests for effects (FPS impact)
- Hardware integration tests (MIDI, OSC, NDI)

**Verification:**
```bash
pytest --cov=core --cov=plugins --cov-report=html
# Coverage threshold enforced in pytest.ini
```

**Violation:** Code review blocked, tests required before merge

---

## 🚨 RAIL 6: HARDWARE INTEGRATION SAFETY

**Constraint:** Hardware drivers (Astra, MIDI, OSC, NDI) MUST fail gracefully with clear error messages.

**Required:**
- ✅ Try-except blocks with user-friendly error messages
- ✅ Fallback modes (software simulation if hardware unavailable)
- ✅ Resource cleanup on exit (device release)
- ✅ No crashes on device disconnect/reconnect

**Example Pattern:**
```python
try:
    self.astra = AstraCamera()
except AstraNotFoundError:
    logger.warning("Astra camera not found - running in simulation mode")
    self.astra = SimulatedDepthCamera()
```

**Violation:** Critical bug, immediate fix required

---

## 🚨 RAIL 7: NO SILENT FAILURES

**Constraint:** All errors MUST be logged with context and, where appropriate, user notification.

**Logging Requirements:**
- ERROR level: Failures that affect functionality
- WARNING level: Recoverable issues, degraded mode
- INFO level: Normal operations, state changes
- DEBUG level: Detailed diagnostic info (disabled in production)

**Anti-patterns (Forbidden):**
```python
# ❌ SILENT FAILURE
try:
    load_plugin()
except:
    pass  # BAD: No logging, no user feedback

# ✅ PROPER ERROR HANDLING
try:
    load_plugin()
except PluginLoadError as e:
    logger.error(f"Failed to load plugin {plugin_name}: {e}")
    self.ui.show_error(f"Plugin {plugin_name} failed to load: {e}")
    raise
```

**Violation:** Code review rejection

---

## 🚨 RAIL 8: RESOURCE LEAK PREVENTION

**Constraint:** All resources (GPU memory, file handles, network sockets, camera devices) MUST be properly released.

**Critical Resources:**
- OpenGL textures and framebuffers
- Video capture devices (cameras, NDI sources)
- Audio streams and MIDI ports
- WebSocket connections
- Thread pools and worker processes

**Verification:**
```bash
# Check for GL leaks
python fix_gl_leaks.py --check
# Monitor resource usage during stress test
python run_stress_test.sh --monitor-resources
```

**Violation:** Memory leak bug, P1 priority fix

---

## 🚨 RAIL 9: BACKWARD COMPATIBILITY

**Constraint:** All plugin APIs MUST maintain backward compatibility with VJLive-2 plugin interface.

**Compatibility Requirements:**
- Plugin manifest format matches VJLive-2 spec
- Effect class signature: `__init__(self, params)` and `process(self, frame, audio_data)`
- Parameter types match original (float, int, bool, color)
- Audio reactivity: `audio_data` contains FFT and waveform

**Breaking Changes:**
- Only allowed with deprecation warnings and 2-version grace period
- Must be documented in MIGRATION_GUIDE.md
- Old plugin support via compatibility layer

**Violation:** Revert, compatibility restored first

---

## 🚨 RAIL 10: SECURITY NON-NEGOTIABLES

**Constraint:** All security fixes from SECURITY_AUDIT_REPORT.md and PRODUCTION_READINESS_AUDIT.md MUST be implemented.

**Mandatory Security Features:**
- ✅ Rate limiting (authenticated: 100/min, unauthenticated: 10/min)
- ✅ RBAC with role-based permissions
- ✅ Pydantic validation on ALL API endpoints
- ✅ Command injection prevention
- ✅ Path traversal protection
- ✅ JWT secret rotation capability
- ✅ Docker security: non-root users, no privileged mode

**Verification:**
```bash
# Run security test suite
pytest tests/security/ -v
# Audit Docker config
docker-compose -f docker-compose.prod.yml config | grep -i privileged
```

**Violation:** Production deployment blocked

---

## 🚨 RAIL 11: ANTI-HALLUCINATION & ANTI-STUB PROTOCOL (ZERO TOLERANCE)

**Constraint:** You are strictly forbidden from "slashing and burning" working logic or replacing robust, detailed documents/code with tiny, incomplete stubs. 

**The Rule of Conservation:**
- You MUST research the original legacy code (via Qdrant on Julie) *before* attempting to port a feature.
- You MUST explicitly read a file's contents before modifying or replacing it.
- **NEVER** replace a 110k file with a 5-line stub because you didn't bother to read it.
- If you do not understand a component, you halt and ask the Manager. You do not hallucinate a simplified version.

**Verification:**
- Every Git commit replacing a file must have a line count differential that makes sense. If `-2800 lines, +5 lines`, the commit is rejected as a Hallucinated Stub.

**Violation Consequences:** Immediate termination of the agent session. This is the exact behavior that destroyed previous configurations.

---

## 📊 COMPLIANCE TRACKING

**Daily Safety Standup:**
- Manager reviews SAFETY_RAILS.md at start of each work session
- Any violations logged in BOARD.md with [SAFETY_RAIL_X] tag
- Weekly compliance report generated from test results

**Automated Gates:**
- CI/CD pipeline runs safety checks on every commit
- Pre-merge: All rails must pass
- Pre-deployment: Full safety audit required

**Escalation:**
- Safety Rail violation → Immediate halt
- Manager notified via BOARD.md update
- Root cause analysis required before resumption
- Repeated violations → Team retrospective

---

**Final Authority:** These rails supersede all other instructions. When in doubt, prioritize safety over speed, quality over features, and stability over innovation.
