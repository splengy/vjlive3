# INBOX: Implementation Engineer Assignment

## Mission
Implement the AgentAvatarEffect plugin for VJLive3. This effect renders a reactive geometric entity that visualizes agent state with optional IR camera integration for shadow mode and eye tracking.

## Specification
**Reference**: `docs/specs/P3-EXT004_agent_avatar_effect.md`

### Key Requirements
- **Geometric Avatar Rendering**: Spinning hexagon core with orbiting triangles and dots
- **Agent State Visualization**: Thinking (fast spin), Confident (bright glow), Overwhelmed (fragmentation)
- **Shadow Mode (Optional)**: IR camera-based body detection for conditional rendering
- **Eye Tracking (Optional)**: Face detection with gaze following using OpenCV
- **Performance**: 60 FPS with all features enabled
- **Fallback**: Works without IR camera (shadow/eye tracking disabled)

### Code Files
```
src/vjlive3/plugins/agent_avatar.py
```

### Test Files
```
tests/plugins/test_agent_avatar.py
```

### Shader (embedded)
- Fragment shader: `AVATAR_FRAGMENT_SHADER` constant (238 lines)

### Verification
- [ ] Unit tests: ≥80% coverage across all methods
- [ ] Rendering tests: Avatar renders correctly with all states
- [ ] Feature tests: Shadow mode, eye tracking (if IR available)
- [ ] Performance tests: 60 FPS with all effects enabled
- [ ] Edge case tests: No IR source, face not detected, invalid parameters

## Workflow Protocol

### Phase 1: Foundation (Days 1-2)
1. **Setup**: Create project structure, add to `pyproject.toml`
2. **Configuration**: Define avatar parameters (0.0-10.0 range)
3. **Base Classes**: Implement AgentAvatarEffect extending Effect
4. **Testing Infrastructure**: Set up pytest, coverage, mock OpenGL context

### Phase 2: Core Rendering (Days 3-4)
1. **Shader Implementation**: Implement AVATAR_FRAGMENT_SHADER with geometric SDFs
2. **Parameter System**: All 21 parameters with proper ranges
3. **Basic Rendering**: Avatar renders with default parameters
4. **State Visualization**: Implement spin, glow, fragmentation effects

### Phase 3: Advanced Features (Days 5-6)
1. **Shadow Mode**: IR-based shadow mask generation (optional)
2. **Eye Tracking**: Face detection and gaze following (optional)
3. **Combined Modes**: Shadow + eye tracking simultaneously
4. **Performance Optimization**: Ensure 60 FPS with all features

### Phase 4: Testing & Validation (Days 7-8)
1. **Unit Tests**: ≥80% coverage, include edge cases and error conditions
2. **Rendering Tests**: All presets, state changes, positioning
3. **Integration Tests**: IR integration, face detection (if available)
4. **Manual QA**: Real hardware testing with/without IR camera

## Safety Rails Reminder

### RAIL 1: 60 FPS SACRED
- Simple 2D fragment shader with minimal operations
- Face detection can run at reduced frequency if needed
- Profile to ensure 60 FPS with all features enabled

### RAIL 2: OFFLINE-FIRST ARCHITECTURE
- Effect works without IR camera (shadow/eye tracking disabled)
- No network dependencies for core functionality

### RAIL 3: PLUGIN SYSTEM INTEGRITY
- Clean integration with existing Effect base class
- Optional IR integration via set_ir_source method
- Agent bridge for state-driven updates

### RAIL 4: CODE SIZE DISCIPLINE
- Keep implementation under 750 lines
- Current: ~476 lines (including shader) - well under limit

### RAIL 5: TEST COVERAGE GATE
- ≥80% code coverage mandatory
- Include tests for all parameter ranges and rendering states

### RAIL 6: HARDWARE INTEGRATION SAFETY
- Graceful handling when IR camera unavailable
- OpenCV cascade loading failures handled gracefully
- No crashes during face detection

### RAIL 7: NO SILENT FAILURES
- All exceptions logged with context
- IR source errors reported clearly
- Face detection failures logged, no crashes

### RAIL 8: RESOURCE LEAK PREVENTION
- OpenCV cascade classifier reused, no leaks
- Shadow mask buffers properly managed
- IR frame references cleared when done

## Resources

### Legacy References
- `VJLive-2/core/effects/agent_avatar.py` — AgentAvatarEffect (canonical source)
- `VJLive-2/plugins/vagent/agent_avatar.py` — Plugin wrapper
- `VJLive-2/plugins/core/vagent/agent_avatar.py` — Alternative implementation

### Existing VJLive3 Code
- `src/vjlive3/render/effect.py` — Effect base class
- `src/vjlive3/render/engine.py` — Render loop integration
- `src/vjlive3/plugins/astra.py` — IR camera integration example

### External Documentation
- OpenGL 3.3+ Core Profile: https://www.khronos.org/registry/OpenGL/specs/gl/
- Signed Distance Functions (SDF): https://iquilezles.org/articles/distfunctions/
- OpenCV Haar Cascades: https://docs.opencv.org/master/d7/d00/tutorial_meanshift.html
- Surface IR Camera: Windows thermal imaging API

### Tools
- **PyOpenGL**: OpenGL bindings for Python
- **OpenCV**: Face detection and image processing
- **NumPy**: Array operations for IR mask processing
- **pytest**: Unit testing framework
- **coverage.py**: Test coverage measurement

## Success Criteria

### Functional Completeness
- [ ] Avatar renders correctly with all geometric elements (hexagon, triangles, dots)
- [ ] All agent states work: thinking (fast spin), confident (bright), overwhelmed (fragmented)
- [ ] All 21 parameters functional and within 0.0-10.0 range
- [ ] Shadow mode generates correct IR-based mask (when IR available)
- [ ] Eye tracking detects faces and follows gaze smoothly
- [ ] Effect works without IR camera (fallback mode)

### Performance
- [ ] 60 FPS with avatar rendering only
- [ ] 60 FPS with shadow mode enabled (if IR available)
- [ ] 60 FPS with eye tracking enabled (if IR available)
- [ ] Face detection processes IR frame in <16ms
- [ ] Memory usage <50MB for effect with shadow mask

### Reliability
- [ ] Effect works without IR camera (graceful degradation)
- [ ] No crashes when IR camera disconnects
- [ ] Face detection failures handled without crashes
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Integration
- [ ] Clean integration with existing Effect base class
- [ ] Agent bridge connection for state updates
- [ ] Works in headless mode for server deployments
- [ ] Compatible with existing render chain

## Next Steps

1. **Read the specification**: `docs/specs/P3-EXT004_agent_avatar_effect.md`
2. **Set up development environment**: Create project structure, add dependencies (OpenCV optional)
3. **Start with shader**: Implement AVATAR_FRAGMENT_SHADER and test basic rendering
4. **Implement parameter system**: All 21 parameters with proper ranges
5. **Add state visualization**: Spin, glow, fragmentation effects
6. **Optional IR integration**: Shadow mode and eye tracking (if SurfaceIRSource available)
7. **Write tests**: Unit tests alongside implementation (TDD style)
8. **Profile and optimize**: Ensure 60 FPS with all features
9. **Document**: Complete API docs and usage examples

**Remember**: This is a **visual effect with optional hardware integration**. It must be robust, work without IR camera, and maintain 60 FPS. Follow the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.