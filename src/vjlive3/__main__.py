"""
VJLive3 — Milestone 1 entry point.

Wires: RenderContext → EffectChain → RenderEngine.
Runs until window is closed (ESC / Q / window X).

Usage:
    python3 -m vjlive3                      # full window
    VJ_HEADLESS=true python3 -m vjlive3     # headless CI test (renders 1 frame then exits)
    python3 -m vjlive3 --test-frame         # same as headless, exits 0 on success
"""

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger("vjlive3")


def main() -> int:
    """
    Entry point. Returns exit code.

    Milestone 1 gate: a window opens showing a solid colour passthrough.
    No effects — proves RenderContext/EffectChain/RenderEngine are wired correctly.
    """
    headless = (
        os.environ.get("VJ_HEADLESS", "").lower() == "true"
        or "--test-frame" in sys.argv
    )
    test_frame_only = "--test-frame" in sys.argv

    logger.info("VJLive3 starting — headless=%s", headless)

    try:
        from vjlive3.render.render_context import RenderContext
        from vjlive3.render.chain import EffectChain
        from vjlive3.render.engine import RenderEngine
    except ImportError as exc:
        logger.error("Import failed: %s", exc)
        logger.error(
            "Install dependencies: pip install -e '.[dev]'"
        )
        return 1

    width, height = 1280, 720

    try:
        with RenderContext(
            width=width,
            height=height,
            title="VJLive 3.0 :: The Reckoning — Milestone 1",
            headless=headless,
        ) as ctx:
            chain = EffectChain(width=width, height=height)

            # Add a colour-invert effect to prove the full GPU effect-chain pipeline.
            # InvertEffect.draw() receives the source texture view directly and
            # manages its own bind groups — no hardware dependency.
            try:
                from vjlive3.plugins.invert import InvertEffect
                chain.add_effect(InvertEffect())
                logger.info("InvertEffect added to chain")
            except Exception as exc:
                logger.warning("Could not add InvertEffect: %s", exc)

            engine = RenderEngine(ctx, chain, target_fps=60.0)

            if test_frame_only:
                # Render exactly one frame, prove the pipeline doesn't crash.
                logger.info("Test-frame mode: rendering 1 frame")
                ctx.poll_events()
                output_tex = chain.render(None, audio_reactor=None)
                chain.render_to_screen(output_tex, (0, 0, width, height))
                ctx.swap_buffers()
                logger.info("Test-frame: OK")
                return 0

            # Real window mode: run until user closes window.
            logger.info("Window open — press Q or close to exit")

            # Upload a static test frame so the chain has content to blit.
            # This exercises the SCREEN_BLIT_WGSL pipeline path (not the colour cycle).
            # Replace with a live webcam / video source for the actual VJ use-case.
            try:
                import numpy as np
                test_frame = np.zeros((height, width, 3), dtype=np.uint8)
                # Reddish-purple gradient: vivid enough to be unmistakeable
                test_frame[:, :, 0] = 180   # R
                test_frame[:, :, 1] = 40    # G
                test_frame[:, :, 2] = 120   # B
                # Horizontal gradient so we can verify aspect ratio is correct
                for x in range(width):
                    test_frame[:, x, 2] = int(40 + (200 - 40) * x / width)
                input_view = chain.upload_texture(test_frame)
                engine.set_input_texture_callback(lambda: input_view)
                logger.info("Test frame uploaded (%dx%d) — GPU blit path active", width, height)
            except Exception as exc:
                logger.warning("Could not upload test frame (GPU blit fallback to colour cycle): %s", exc)

            engine.run()


    except RuntimeError as exc:
        logger.error("Render pipeline failed: %s", exc)
        return 1
    except KeyboardInterrupt:
        logger.info("Interrupted")

    logger.info("VJLive3 exited cleanly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
