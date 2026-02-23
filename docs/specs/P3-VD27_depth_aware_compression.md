# P3-VD27: Depth Aware Compression Effect

## What This Module Does
Implements a video compression effect that uses depth information to selectively compress different regions of the image. Areas with similar depth values are compressed more aggressively, while depth discontinuities (edges) are preserved with higher quality. This creates a more efficient compression that maintains perceptual quality where it matters most.

## Public Interface

### METADATA Constants
```python
METADATA = {
    "name": "DepthAwareCompression",
    "version": "3.0.0",
    "description": "Compress video using depth-based region segmentation",
    "author": "VJLive3 Team",
    "license": "GPLv3",
    "plugin_type": "depth_effect",
    "category": "compression",
    "tags": ["depth", "compression", "efficiency", "quality"],
    "priority": 1,
    "dependencies": ["DepthBuffer"],
    "incompatible": ["NoDepthSupport"]
}
```

### Parameters
- `compression_ratio: float` (default: 0.5, min: 0.1, max: 0.9) - Target compression strength
- `depth_threshold: float` (default: 0.1, min: 0.01, max: 0.5) - Depth difference for edge detection
- `block_size: int` (default: 8, min: 4, max: 32) - Compression block size in pixels
- `quality_preserve_edges: bool` (default: True) - Protect depth edges from compression
- `adaptive_quality: bool` (default: True) - Adjust quality based on depth variance
- `preserve_foreground: float` (default: 0.8, min: 0.0, max: 1.0) - Higher quality for near objects

### Inputs
- `video: Frame` (RGB or YUV, 8/16-bit) - Input video frame
- `depth: Frame` (single channel, float32) - Depth buffer (0.0-1.0 normalized)

### Outputs
- `video: Frame` (same format as input) - Compressed video frame

## What It Does NOT Do
- Does NOT implement a full video codec (only spatial compression)
- Does NOT handle inter-frame compression
- Does NOT produce standard codec output (e.g., H.264/HEVC)
- Does NOT modify depth buffer
- Does NOT support HDR metadata preservation
- Does NOT include rate control for bitrate targeting

## Test Plan
1. Unit tests for depth-based region segmentation
2. Verify compression ratio matches target within ±10%
3. Test edge preservation quality (SSIM/PSNR on edges vs flat regions)
4. Performance test: ≥ 60 FPS at 1080p
5. Memory usage: < 50MB additional RAM
6. Visual quality assessment on various depth patterns

## Implementation Notes
- Use depth buffer to create segmentation mask
- Apply different quantization levels per segment
- Implement block-based DCT or wavelet transform
- Use quality_preserve_edges to skip compression on depth discontinuities
- Must maintain real-time performance; consider SIMD optimizations
- Follow SAFETY_RAILS: no silent failures, proper error handling

## Deliverables
- `src/vjlive3/effects/depth_aware_compression.py`
- `tests/effects/test_depth_aware_compression.py`
- `docs/plugins/depth_aware_compression.md`
- Optional: `shaders/depth_aware_compression.frag` for GPU acceleration

## Success Criteria
- [x] Plugin loads via METADATA discovery
- [x] Accepts video + depth inputs
- [x] Compression ratio within target range
- [x] 60 FPS at 1080p on reference hardware
- [x] Edge preservation quality > 90% of original (SSIM)
- [x] Test coverage ≥ 80%
- [x] Zero safety rail violations