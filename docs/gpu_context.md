# GPU Context Manager for VJLive3

## Overview

The GPU context manager provides a comprehensive OpenGL/ModernGL framework for
VJLive3, enabling shader-based effects, texture management, and GPU-accelerated
image processing. It follows VJLive-2's shader_base.py patterns while adapting
to VJLive3's architecture.

## Architecture

### Core Components

#### OpenGLContextManager
- **Purpose**: Manages ModernGL context lifecycle and GPU resource caching
- **Features**: Lazy initialization, thread safety, headless mode support
- **Integration**: Works with VideoPipeline architecture

#### ShaderCompiler
- **Purpose**: Advanced shader compilation with preprocessing and caching
- **Features**: Include system, preprocessor defines, source validation
- **Integration**: Provides shader programs for effects pipeline

#### TextureManager
- **Purpose**: Efficient texture creation and lifecycle management
- **Features**: Multiple source formats, texture atlases, mipmap support
- **Integration**: Supplies textures for rendering operations

#### FramebufferManager
- **Purpose**: Framebuffer creation and multi-pass rendering
- **Features**: Ping-pong buffers, depth attachments, multisample support
- **Integration**: Enables complex effect chains and post-processing

## Usage

### Initialization

```python
from vjlive3.gpu import initialize_context, shutdown_context

# Initialize context (headless mode for testing)
initialize_context(headless=True)

try:
    # Use GPU functionality
    pass
finally:
    shutdown_context()
```

### Shader Compilation

```python
from vjlive3.gpu import ShaderCompiler, get_context_manager

# Get context manager
ctx_mgr = get_context_manager()

# Create shader compiler
compiler = ShaderCompiler(ctx_mgr)

# Compile shader with defines
vertex = """
    #version 330
    #ifdef USE_COLOR
    in vec3 in_color;
    out vec3 color;
    #endif
    void main() {
        gl_Position = vec4(0.0);
    }
"""

fragment = """
    #version 330
    #ifdef USE_COLOR
    in vec3 color;
    #endif
    out vec4 out_color;
    void main() {
        out_color = vec4(1.0);
    }
"""

shader = compiler.compile("my_shader", vertex, fragment, defines={'USE_COLOR': True})
```

### Texture Management

```python
from vjlive3.gpu import TextureManager
import numpy as np

# Create texture manager
tex_mgr = TextureManager()

# Create from numpy array
data = np.random.rand(256, 256, 3).astype(np.float32)
texture = tex_mgr.create_from_numpy("input_texture", data)

# Create empty render target
target = tex_mgr.create_empty("render_target", 512, 512)
```

### Framebuffer Operations

```python
from vjlive3.gpu import FramebufferManager

# Create framebuffer manager
fb_mgr = FramebufferManager()

# Create simple framebuffer
color_tex = tex_mgr.create_empty("color", 512, 512)
fb = fb_mgr.create_simple("main_fb", 512, 512)

# Create with depth
fb_depth = fb_mgr.create_with_depth("fb_depth", 512, 512)

# Create ping-pong pair
fb_a, fb_b = fb_mgr.create_pingpong("blur_pass", 512, 512)
```

### Integration with VideoPipeline

```python
from vjlive3.core.pipeline import VideoPipeline
from vjlive3.gpu import OpenGLContextManager

class GPUEffect:
    """Example GPU-based effect for VideoPipeline."""
    
    def __init__(self):
        self.context_manager = OpenGLContextManager()
        self.context_manager.initialize(headless=True)
        
        # Initialize shader compiler, texture manager, etc.
        self.compiler = ShaderCompiler(self.context_manager)
        self.texture_mgr = TextureManager()
        self.framebuffer_mgr = FramebufferManager()
        
        # Compile effect shader
        self.shader = self.compiler.compile("gpu_effect", vertex_source, fragment_source)
    
    def apply(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """Apply GPU effect to frame."""
        # Convert frame to texture
        input_texture = self.texture_mgr.create_from_numpy("input", frame)
        
        # Create output texture
        output_texture = self.texture_mgr.create_empty("output", frame.shape[1], frame.shape[0])
        
        # Render to texture
        self.context_manager.render_to_texture(
            output_texture,
            self.shader,
            input_texture,
            uniforms={'time': timestamp}
        )
        
        # Read back to numpy array
        result = output_texture.texture.read()
        result_array = np.frombuffer(result, dtype='f4').reshape(frame.shape[0], frame.shape[1], 4)
        
        return result_array
```

## Thread Safety

All GPU components use thread locks to ensure safe concurrent access:

```python
from vjlive3.gpu import get_context_manager

# Thread-safe operations
with get_context_manager()._lock:
    # GPU operations here
    pass
```

## Error Handling

Components provide comprehensive error handling with descriptive messages:

```python
from vjlive3.gpu import ShaderCompiler

try:
    shader = compiler.compile("invalid", "invalid_source", "invalid_source")
except ValueError as e:
    print(f"Shader compilation failed: {e}")
```

## Performance Considerations

### Caching
- Shader compilation results are cached by source hash
- Textures and framebuffers are cached by name
- Use `clear_*_cache()` methods to release resources

### Memory Management
- Monitor memory usage with `get_stats()` methods
- Use `clear_all()` methods to release all resources
- Consider texture atlases for batch rendering

### Headless Mode
- Initialize with `headless=True` for testing and server environments
- Reduces dependencies on display hardware
- Maintains full functionality for shader compilation and texture operations

## Integration Points

### With Existing Effects
- GPU effects can be added to VideoPipeline's effects list
- Follow the same interface as CPU-based effects
- Use `apply()` method signature for compatibility

### With Hardware Integration
- Works seamlessly with MIDI, OSC, and DMX controllers
- Shader parameters can be controlled via hardware
- Real-time parameter updates supported

### With Audio Reactivity
- GPU effects can respond to audio analysis
- Use audio data as shader uniforms
- Create audio-reactive visual effects

## Best Practices

1. **Initialize Early**: Initialize context at application startup
2. **Use Caching**: Reuse compiled shaders and textures
3. **Clean Up**: Always shutdown context when done
4. **Error Handling**: Wrap GPU operations in try/except blocks
5. **Memory Monitoring**: Regularly check resource usage
6. **Thread Safety**: Use provided locking mechanisms
7. **Headless Testing**: Use headless mode for automated tests

## Troubleshooting

### Common Issues

#### Context Not Initialized
```python
# Ensure context is initialized before use
if not is_context_initialized():
    initialize_context()
```

#### Shader Compilation Fails
- Check shader syntax
- Verify OpenGL version compatibility
- Use shader validation tools

#### Memory Issues
- Monitor texture and framebuffer usage
- Use texture atlases for efficiency
- Clear unused resources regularly

#### Performance Problems
- Profile shader execution
- Optimize texture formats
- Use appropriate filtering and wrapping

## Future Enhancements

- **Compute Shaders**: Add compute shader support
- **Geometry Shaders**: Support for geometry processing
- **Instancing**: Efficient rendering of multiple objects
- **Compute Pipelines**: Advanced GPU compute operations
- **Multi-GPU Support**: Support for multiple GPU devices

## API Reference

See the individual module documentation for detailed API specifications:
- `OpenGLContextManager`
- `ShaderCompiler`
- `TextureManager`
- `FramebufferManager`