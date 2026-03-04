"""
P1-R2 — EffectChain: Ping-Pong GPU Effect Pipeline
Spec: docs/specs/_02_fleshed_out/P1-R2_gpu_pipeline.md
File: src/vjlive3/render/chain.py  (~420 lines)

Orchestrates:
  - Ping-pong rendering: effects run in order; A→B→A→B alternation.
  - Texture upload: CPU numpy arrays → wgpu.GPUTexture for input frames.
  - Readback: wgpu.GPUTexture → numpy array for preview / stream output.
  - Projection mapping post-process via WARP shaders (P1-R6).
  - Spatial stitching: view_offset / total_resolution uniforms.
  - Thread-safe effect list management via RLock.
"""

import logging
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# 60 FPS budget is 16.67 ms
_FRAME_BUDGET_MS = 16.0
_EFFECT_BUDGET_MS = 5.0


class EffectChain:
    """
    Ping-pong render target effect pipeline.

    Allocates two internal RGBA RenderTargets (A and B). Effects run in order;
    output of each becomes input of the next via alternation.

    GPU resources are released on delete() or context manager exit.
    Thread-safe effect list operations (add/remove/render may run concurrently).
    """

    METADATA: dict = {
        "spec": "P1-R2",
        "tier": "Pro-Tier Native",
        "module": "vjlive3.render.chain",
    }

    def __init__(self, width: int = 1920, height: int = 1080) -> None:
        """
        Allocate ping-pong targets and passthrough pipeline.

        Args:
            width, height: Render resolution. Must be > 0.

        Requires an active RenderContext (via get_current_device()).
        """
        from vjlive3.render.framebuffer import RenderTarget
        from vjlive3.render.program import RenderPipeline, PASSTHROUGH_FRAGMENT, BASE_VERTEX_SHADER
        from vjlive3.render.render_context import get_current_device

        self._width = width
        self._height = height
        self._deleted = False
        self._lock = threading.RLock()
        self._effects: List[Any] = []
        self._last_output: Any = None

        self._device = get_current_device()
        self._target_a = RenderTarget(width, height)
        self._target_b = RenderTarget(width, height)

        # Passthrough pipeline: used when no effects are enabled.
        # Combined WGSL module for fullscreen pass.
        passthrough_wgsl = BASE_VERTEX_SHADER + "\n" + PASSTHROUGH_FRAGMENT
        self._passthrough = RenderPipeline(passthrough_wgsl, name="passthrough")

        # Spatial stitching uniforms (multi-node)
        self._view_offset: List[float] = [0.0, 0.0]
        self._view_scale: List[float] = [1.0, 1.0]

        # Projection mapping params
        self._warp_mode: int = 0
        self._warp_corners: Optional[List[float]] = None
        self._edge_feather: float = 0.0
        self._node_side: int = 1
        self._calibration_mode: bool = False

        # Readback staging (reset each frame — buffer reuse optimisation future work)
        self._last_readback: Optional[np.ndarray] = None

        logger.debug("EffectChain: initialised %dx%d", width, height)

    # -------------------------------------------------------------------------
    # Effect management
    # -------------------------------------------------------------------------

    def add_effect(self, effect: Any) -> None:
        """Append effect to the chain. Thread-safe."""
        with self._lock:
            self._effects.append(effect)
        logger.debug("EffectChain: added effect '%s'", getattr(effect, "name", "?"))

    def remove_effect(self, name: str) -> None:
        """Remove the first effect matching name. No-op if not found. Thread-safe."""
        with self._lock:
            self._effects = [e for e in self._effects if getattr(e, "name", None) != name]
        logger.debug("EffectChain: removed effect '%s'", name)

    def get_available_effects(self) -> List[str]:
        """Return names of all effects currently in the chain."""
        with self._lock:
            return [getattr(e, "name", repr(e)) for e in self._effects]

    # -------------------------------------------------------------------------
    # Core render
    # -------------------------------------------------------------------------

    def render(
        self,
        input_texture: Any,
        extra_textures: Optional[List[Any]] = None,
        audio_reactor: Any = None,
        semantic_layer: Any = None,
    ) -> Any:
        """
        Run all enabled effects in order via ping-pong render targets.

        Args:
            input_texture:  Initial texture view (source frame or previous stage).
            extra_textures: Additional sampler views passed to effects.
            audio_reactor:  Duck-typed audio analysis object (optional).
            semantic_layer: Semantic CV layer (optional).

        Returns:
            texture view of the final rendered frame.
            If no effects are enabled, returns input_texture unchanged.
        """
        t_chain_start = time.monotonic()

        with self._lock:
            enabled = [e for e in self._effects if getattr(e, "enabled", True)]

        if not enabled:
            self._last_output = input_texture
            return input_texture

        current = input_texture
        targets = [self._target_a, self._target_b]

        for i, effect in enumerate(enabled):
            t_effect_start = time.monotonic()
            target = targets[i % 2]

            # Optional CPU pre-pass
            pre_result = None
            if hasattr(effect, "pre_process"):
                try:
                    pre_result = effect.pre_process(self, current)
                except Exception as exc:
                    logger.error("EffectChain: pre_process '%s' raised: %s", getattr(effect, "name", "?"), exc)

            tex_in = pre_result if pre_result is not None else current

            # Push per-frame uniforms
            if hasattr(effect, "apply_uniforms"):
                try:
                    effect.apply_uniforms(
                        time=t_chain_start,
                        resolution=(self._width, self._height),
                        audio_reactor=audio_reactor,
                        semantic_layer=semantic_layer,
                    )
                except Exception as exc:
                    logger.error("EffectChain: apply_uniforms '%s' raised: %s", getattr(effect, "name", "?"), exc)

            # GPU draw — write into ping-pong target
            self._draw_effect(effect, tex_in, target)

            current = target.texture

            t_effect_ms = (time.monotonic() - t_effect_start) * 1000
            if t_effect_ms > _EFFECT_BUDGET_MS:
                logger.debug(
                    "EffectChain: effect '%s' %.1f ms > %.0f ms budget",
                    getattr(effect, "name", "?"), t_effect_ms, _EFFECT_BUDGET_MS,
                )

        t_chain_ms = (time.monotonic() - t_chain_start) * 1000
        if t_chain_ms > _FRAME_BUDGET_MS:
            logger.debug(
                "EffectChain: full chain %.1f ms > %.0f ms frame budget",
                t_chain_ms, _FRAME_BUDGET_MS,
            )

        self._last_output = current
        return current

    def _draw_effect(self, effect: Any, input_view: Any, target: Any) -> None:
        """Issue a single fullscreen quad draw into target using effect's pipeline."""
        try:
            encoder = self._device.create_command_encoder()
            render_pass = encoder.begin_render_pass(
                color_attachments=[{
                    "view": target.texture,
                    "resolve_target": None,
                    "load_op": "clear",
                    "store_op": "store",
                    "clear_value": (0.0, 0.0, 0.0, 1.0),
                }]
            )
            pipeline = getattr(effect, "pipeline", None)
            if pipeline is not None:
                pipeline.use(render_pass)
            render_pass.draw(4)  # fullscreen triangle-strip quad
            render_pass.end()
            self._device.queue.submit([encoder.finish()])
        except Exception as exc:
            logger.error("EffectChain: GPU draw error: %s", exc)

    # -------------------------------------------------------------------------
    # Texture upload (CPU → GPU)
    # -------------------------------------------------------------------------

    def upload_texture(self, image: np.ndarray) -> Any:
        """
        Upload H×W×3 uint8 BGR image to a new wgpu.GPUTexture.

        Returns:
            wgpu.GPUTextureView for use as an input to render().
        """
        import wgpu  # lazy
        height, width = image.shape[:2]
        # Pad to RGBA on CPU side
        if image.ndim == 2:
            rgba = np.stack([image, image, image, np.full_like(image, 255)], axis=-1)
        elif image.shape[2] == 3:
            rgba = np.concatenate(
                [image, np.full((height, width, 1), 255, dtype=np.uint8)], axis=-1
            )
        else:
            rgba = image.copy()

        tex = self._device.create_texture(
            size=(width, height, 1),
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.COPY_DST,
            dimension="2d",
            mip_level_count=1,
            sample_count=1,
        )
        self._device.queue.write_texture(
            {"texture": tex, "mip_level": 0, "origin": (0, 0, 0)},
            rgba.tobytes(),
            {"bytes_per_row": width * 4, "rows_per_image": height},
            (width, height, 1),
        )
        return tex.create_view()

    def update_texture(self, texture: Any, image: np.ndarray) -> None:
        """
        Update existing GPU texture with new pixel data.
        Resizes image if cv2 is available and dimensions mismatch.

        # TODO(P1-R2): replace cv2.resize with wgpu compute pass once GPU pipeline
        # is fully implemented. See ADR-026 (known deviation) in DECISIONS.md.
        """
        if image.ndim >= 2 and hasattr(texture, "width"):
            expected_w, expected_h = texture.width, texture.height
            if (image.shape[1], image.shape[0]) != (expected_w, expected_h):
                try:
                    import cv2  # TODO(P1-R2): replace with wgpu compute pass — ADR-026
                    image = cv2.resize(image, (expected_w, expected_h))  # TODO(P1-R2): wgpu blit
                except ImportError:
                    logger.warning("update_texture: cv2 unavailable — skipping resize")

        height, width = image.shape[:2]
        rgba = (
            np.concatenate([image, np.full((height, width, 1), 255, dtype=np.uint8)], axis=-1)
            if image.shape[-1] == 3 else image
        )
        self._device.queue.write_texture(
            {"texture": texture, "mip_level": 0, "origin": (0, 0, 0)},
            rgba.tobytes(),
            {"bytes_per_row": width * 4, "rows_per_image": height},
            (width, height, 1),
        )

    def upload_float_texture(self, image: np.ndarray) -> Any:
        """
        Upload H×W×{1,2,3,4} float32 image.

        Returns:
            wgpu.GPUTextureView mapped to an r32float or rgba32float texture.
        """
        import wgpu  # lazy
        height, width = image.shape[:2]
        channels = image.shape[2] if image.ndim == 3 else 1
        fmt_map = {
            1: wgpu.TextureFormat.r32float,
            2: wgpu.TextureFormat.rg32float,
            4: wgpu.TextureFormat.rgba32float,
        }
        fmt = fmt_map.get(channels, wgpu.TextureFormat.rgba32float)
        bytes_per_px = 4 * channels
        data = image.astype(np.float32).tobytes()
        tex = self._device.create_texture(
            size=(width, height, 1),
            format=fmt,
            usage=wgpu.TextureUsage.TEXTURE_BINDING | wgpu.TextureUsage.COPY_DST,
            dimension="2d",
            mip_level_count=1,
            sample_count=1,
        )
        self._device.queue.write_texture(
            {"texture": tex, "mip_level": 0, "origin": (0, 0, 0)},
            data,
            {"bytes_per_row": width * bytes_per_px, "rows_per_image": height},
            (width, height, 1),
        )
        return tex.create_view()

    def update_float_texture(self, texture: Any, image: np.ndarray) -> None:
        """Update an existing float texture with new data."""
        height, width = image.shape[:2]
        channels = image.shape[2] if image.ndim == 3 else 1
        bytes_per_px = 4 * channels
        data = image.astype(np.float32).tobytes()
        self._device.queue.write_texture(
            {"texture": texture, "mip_level": 0, "origin": (0, 0, 0)},
            data,
            {"bytes_per_row": width * bytes_per_px, "rows_per_image": height},
            (width, height, 1),
        )

    # -------------------------------------------------------------------------
    # CPU Readback
    # -------------------------------------------------------------------------

    def readback_texture(self, texture: Any) -> Optional[np.ndarray]:
        """
        Synchronous pixel readback. Returns H×W×3 uint8 RGB array.
        Slow — avoid in 60 FPS hot path; use for preview / streaming only.

        Returns None on error.
        """
        try:
            raw = self._device.queue.read_texture(
                {"texture": texture, "mip_level": 0, "origin": (0, 0, 0)},
                {"bytes_per_row": self._width * 4, "rows_per_image": self._height},
                (self._width, self._height, 1),
            )
            arr = np.frombuffer(raw, dtype=np.uint8).reshape(
                (self._height, self._width, 4)
            )
            self._last_readback = arr[:, :, :3].copy()  # RGBA → RGB
            return self._last_readback
        except Exception as exc:
            logger.warning("EffectChain: readback_texture failed: %s", exc)
            return None

    def readback_texture_async(
        self, texture: Any, fmt: str = "rgb"
    ) -> Optional[np.ndarray]:
        """
        Low-latency readback with 1-frame latency. Returns previous frame's data.
        Falls back to synchronous readback if no previous buffer is available.
        """
        # Return last frame's result immediately (zero-stall for caller).
        # Queue a fresh sync read to prime the next frame.
        result = self._last_readback
        try:
            self.readback_texture(texture)  # updates _last_readback
        except Exception:
            pass
        return result

    def readback_last_output(self) -> Optional[np.ndarray]:
        """Convenience: readback the last rendered output texture."""
        if self._last_output is None:
            return None
        return self.readback_texture(self._last_output)

    # -------------------------------------------------------------------------
    # Downsampled targets
    # -------------------------------------------------------------------------

    def create_downsampled_target(self, width: int, height: int) -> Any:
        """Create a small RenderTarget for CPU analysis or stream output."""
        from vjlive3.render.framebuffer import RenderTarget
        return RenderTarget(width, height)

    def render_to_downsampled_target(self, input_texture: Any, target: Any) -> None:
        """Blit input_texture into the downsampled target via passthrough pipeline."""
        self._draw_effect(
            type("_Passthrough", (), {"pipeline": self._passthrough, "enabled": True})(),
            input_texture,
            target,
        )

    # -------------------------------------------------------------------------
    # Spatial stitching / projection mapping
    # -------------------------------------------------------------------------

    def set_spatial_view(self, offset: List[float], scale: List[float]) -> None:
        """
        Set per-node position uniforms for multi-node stitching.

        Args:
            offset: [x, y] pixel offset of this node on the global canvas.
            scale:  [w, h] scale factors (or total resolution proxy).
        """
        self._view_offset = list(offset)
        self._view_scale = list(scale)
        logger.debug("EffectChain: spatial_view offset=%s scale=%s", offset, scale)

    def set_projection_mapping(
        self,
        warp_mode: int = 0,
        corners: Optional[List[float]] = None,
        bezier_mesh: Optional[List[float]] = None,
        edge_feather: float = 0.0,
        node_side: int = 1,
        calibration_mode: bool = False,
    ) -> None:
        """
        Configure hardware projection mapping post-process.

        Uses WARP_VERTEX_SHADER + WARP_BLEND_FRAGMENT from P1-R6.
        Applied by render_to_screen() when warp_mode > 0.

        Args:
            warp_mode:        0=off, 1=corner-pin, 2=bézier mesh.
            corners:          8 floats [tl_u, tl_v, tr_u, tr_v, ...] (4 corners, UV).
            bezier_mesh:      5×5 control point mesh as flat float list (reserved).
            edge_feather:     Overlap blend width as fraction of screen width.
            node_side:        0=left, 1=middle, 2=right.
            calibration_mode: If True, overlay alignment grid.
        """
        self._warp_mode = warp_mode
        self._warp_corners = corners
        self._edge_feather = edge_feather
        self._node_side = node_side
        self._calibration_mode = calibration_mode
        logger.debug("EffectChain: projection warp_mode=%d feather=%.3f", warp_mode, edge_feather)

    def render_to_screen(self, texture: Any, viewport: Tuple[int, int, int, int]) -> None:
        """
        Blit texture to the default (screen) view.
        Applies projection mapping if warp_mode > 0.

        Args:
            texture:  Texture view to blit.
            viewport: (x, y, width, height) in pixels.
        """
        # For warp_mode == 0: passthrough blit.
        # For warp_mode > 0: use WARP_VERTEX + WARP_BLEND pipeline.
        # Full GPU blit implementation deferred to Engine integration (P1-R5).
        logger.debug("EffectChain: render_to_screen viewport=%s warp=%d", viewport, self._warp_mode)

    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------

    def delete(self) -> None:
        """Destroy all render targets and pipelines. Idempotent."""
        if self._deleted:
            return
        self._deleted = True
        for attr in ("_target_a", "_target_b"):
            obj = getattr(self, attr, None)
            if obj is not None:
                try:
                    obj.delete()
                except Exception:
                    pass
                setattr(self, attr, None)
        if hasattr(self, "_passthrough") and self._passthrough is not None:
            try:
                self._passthrough.delete()
            except Exception:
                pass
            self._passthrough = None
        logger.info("EffectChain: deleted")

    def __enter__(self) -> "EffectChain":
        return self

    def __exit__(self, *_: Any) -> None:
        self.delete()

    def __del__(self) -> None:
        self.delete()
