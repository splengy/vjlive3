# INBOX: Implementation Engineer Assignment

## Mission
Implement the AdvancedParticle3DSystem plugin for VJLive3. This is a TouchDesigner-level 3D particle system with full physics simulation, GPU instancing, and audio reactivity.

## Specification
**Reference**: `docs/specs/P3-EXT003_advanced_particle_3d_system.md`

### Key Requirements
- **GPU Instancing**: VAO/VBO architecture for 50,000 particles
- **Physics Simulation**: Velocity Verlet integration with force accumulation
- **Audio Reactivity**: Real-time parameter modulation via AudioAnalyzer/AudioReactor
- **3D Camera System**: Full 3D navigation with distance, FOV, and rotation controls
- **Force System**: Multiple force types (gravity, wind, attractor, repeller, magnetic, noise)
- **Flocking Behaviors**: Separation, alignment, and cohesion algorithms
- **Performance**: Target 60 FPS with 50,000 particles

### Code Files
```
src/vjlive3/plugins/particles_3d.py
```

### Test Files
```
tests/plugins/test_particles_3d.py
```

### Shader Files (embedded)
- Vertex shader: `_get_vertex_shader()` method
- Fragment shader: `_get_fragment_shader()` method

### Verification
- [ ] Unit tests: ≥80% coverage across all methods
- [ ] Rendering tests: Basic rendering, performance with 50,000 particles
- [ ] Integration tests: Audio reactivity, camera controls, force systems
- [ ] Performance benchmarks: 60 FPS target with 50,000 particles
- [ ] Memory management: Proper OpenGL resource cleanup

## Workflow Protocol

### Phase 1: Foundation (Days 1-2)
1. **Setup**: Create project structure, add to `pyproject.toml`
2. **Configuration**: Define particle system parameters (0.0-10.0 range)
3. **Base Classes**: Implement particle state management, emitters, and forces
4. **Testing Infrastructure**: Set up pytest, coverage, mock OpenGL context

### Phase 2: Core Engine (Days 3-5)
1. **Particle System Class**: Implement `AdvancedParticle3DSystem` with VAO/VBO
2. **Physics Engine**: Velocity Verlet integration, force accumulation
3. **Audio Integration**: AudioAnalyzer and AudioReactor parameter modulation
4. **Camera System**: 3D camera with distance, FOV, and rotation controls

### Phase 3: Advanced Features (Days 6-7)
1. **Force System**: Implement all force types (gravity, wind, attractor, etc.)
2. **Flocking Behaviors**: Separation, alignment, and cohesion algorithms
3. **Shader Implementation**: Vertex and fragment shaders for particle rendering
4. **Performance Optimization**: Batch updates, minimize state changes

### Phase 4: Testing & Validation (Days 8-9)
1. **Unit Tests**: ≥80% coverage, include edge cases and error conditions
2. **Rendering Tests**: Performance with 50,000 particles, camera controls
3. **Integration Tests**: Audio reactivity, force systems, flocking behaviors
4. **Manual QA**: Real hardware testing, performance profiling

## Safety Rails Reminder

### RAIL 1: 60 FPS SACRED
- GPU instancing with VAO/VBO for minimal CPU overhead
- Batch particle updates using NumPy arrays
- Profile to ensure 60 FPS with 50,000 particles

### RAIL 2: OFFLINE-FIRST ARCHITECTURE
- Particle system works without network connectivity
- Audio integration is optional, not core dependency

### RAIL 3: PLUGIN SYSTEM INTEGRITY
- Clean integration with existing Effect base class
- Use event bus for communication, not direct coupling

### RAIL 4: CODE SIZE DISCIPLINE
- Keep implementation under 750 lines
- Use composition over inheritance where appropriate

### RAIL 5: TEST COVERAGE GATE
- ≥80% code coverage mandatory
- Include performance and integration tests

### RAIL 6: HARDWARE INTEGRATION SAFETY
- Graceful handling of OpenGL context loss
- Proper cleanup of VAO/VBO resources
- No crashes during context recreation

### RAIL 7: NO SILENT FAILURES
- All OpenGL errors logged with context
- Shader compilation failures reported clearly
- Resource management with proper cleanup

### RAIL 8: RESOURCE LEAK PREVENTION
- Proper cleanup of VAO/VBO resources
- Use context managers for OpenGL resources
- Monitor GPU memory usage during stress tests

## Resources

### Legacy References
- `VJLive-2/plugins/vparticles/particles_3d.py` — AdvancedParticle3DSystem (canonical source)
- `VJLive-2/plugins/core/vparticles/particles_3d.py` — Alternative implementation
- `VJLive-2/plugins/core/silver_visions.py` — Flocking behavior reference

### Existing VJLive3 Code
- `src/vjlive3/render/effect.py` — Effect base class
- `src/vjlive3/render/engine.py` — Render loop integration
- `src/vjlive3/audio/analyzer.py` — AudioAnalyzer for audio reactivity
- `src/vjlive3/audio/engine.py` — AudioReactor for parameter modulation

### External Documentation
- OpenGL 3.3+ Core Profile: https://www.khronos.org/registry/OpenGL/specs/gl/
- NumPy for vector operations: https://numpy.org/
- Particle system physics: Velocity Verlet integration
- Flocking algorithms: Boids by Craig Reynolds

### Tools
- **PyOpenGL**: OpenGL bindings for Python
- **NumPy**: Vector operations and physics calculations
- **pytest**: Unit testing framework
- **coverage.py**: Test coverage measurement
- **cProfile**: Performance profiling

## Success Criteria

### Functional Completeness
- [ ] Particle system renders correctly with default parameters
- [ ] All force types work correctly (gravity, wind, attractor, etc.)
- [ ] Audio reactivity modulates particle parameters in real-time
- [ ] 3D camera controls work smoothly (distance, FOV, rotation)
- [ ] Flocking behaviors produce natural-looking motion

### Performance
- [ ] 60 FPS with 50,000 particles on target hardware
- [ ] GPU memory usage < 200MB for particle buffers
- [ ] CPU usage < 30% for full simulation
- [ ] No frame drops during 1-hour stress test

### Reliability
- [ ] System recovers gracefully from OpenGL context loss
- [ ] No crashes during 24-hour continuous operation
- [ ] All exceptions logged with context, no silent failures
- [ ] Unit test coverage ≥ 80%

### Integration
- [ ] Clean integration with existing Effect base class
- [ ] Audio-reactive plugins can subscribe to particle events
- [ ] Works in headless mode for server deployments
- [ ] Compatible with existing render chain

## Next Steps

1. **Read the specification**: `docs/specs/P3-EXT003_advanced_particle_3d_system.md`
2. **Set up development environment**: Create project structure, add dependencies
3. **Start with configuration**: Define particle system parameters
4. **Implement base classes**: Particle state, emitters, and forces
5. **Build core engine**: VAO/VBO implementation with physics
6. **Add audio integration**: AudioAnalyzer and AudioReactor
7. **Implement camera system**: 3D navigation controls
8. **Write tests**: Unit tests alongside implementation (TDD style)
9. **Profile and optimize**: Ensure performance targets are met
10. **Document**: Complete API docs and usage examples

**Remember**: This is a **high-performance visual effect**. It must be robust, well-tested, and maintain 60 FPS with 50,000 particles. Follow the workflow: SPEC → CODE → TEST → VERIFY → COMMIT → UPDATE BOARD.