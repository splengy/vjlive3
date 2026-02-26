# P3-EXT211_ascii_effect

## Description
The ASCII Effect is a visual shader that converts 3D models into ASCII art using dynamic contrast mapping. It creates a retro-futuristic aesthetic by breaking down textures into monochrome characters based on pixel intensity. This effect leverages GPU compute shaders to process vertex data in real-time, ensuring smooth performance even with complex models.

## What This Module Does / Does NOT Do
- **Does**:
  - Generate ASCII patterns from 3D models in real-time
  - Adjust character density based on lighting conditions
  - Support customizable character sets (e.g., symbols, emojis)
  - Integrate with lighting and rendering pipelines
- **Does NOT**:
  - Work with non-texture-based models (e.g., procedural geometry)
  - Support 4K+ resolution outputs without performance degradation
  - Handle non-monochrome character sets without shader modifications

## Integration
- **Connected Modules**:
  - **Lighting System**: Provides intensity data for character mapping
  - **Model Renderer**: Supplies base 3D geometry
  - **UI Layer**: Displays ASCII output in text-based interfaces
  - **Performance Monitor**: Tracks FPS and VRAM usage
- **Performance Targets**:
  - Maintain 60 FPS on mid-range GPUs (RTX 2060 equivalent)
  - Use <5MB VRAM per frame
  - Optimize for mobile devices with <1GB RAM

## Error Cases
- **Input Errors**:
  - Fails with models lacking diffuse maps (returns error code 404)
  - Crashes if character set exceeds GPU memory (triggers fallback to default set)
- **Runtime Issues**:
  - Artifacts in low-light conditions (mitigated by adaptive contrast mapping)
  - Lag when switching character sets (resolved via shader caching)

## Configuration Schema
```json
{
  "characterSet": {
    "type": "array",
    "items": {
      "type": "string",
      "enum": ["@", ".", "#", "$", "%"]
    }
  },
  "density": {
    "type": "number",
    "minimum": 1,
    "maximum": 20
  },
  "shaderCache": {
    "type": "boolean",
    "default": true
  }
}
```

## State Management
- **Per-Frame**:
  - Updates character positions based on camera movement
  - Recalculates intensity values per frame
- **Persistent**:
  - Saved character set preferences
  - Shader cache state
- **Init-Once**:
  - Initializes shader program
  - Loads default character set