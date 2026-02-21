#!/usr/bin/env python3
"""VJLive3 - Main Application Entry Point.

This module provides the command-line interface and main application loop
for the VJLive3 visual performance system.

Usage:
    python -m vjlive3 [OPTIONS]

Options:
    --config PATH    Path to configuration file
    --debug         Enable debug logging
    --version       Show version and exit
    --help          Show this help message

Example:
    python -m vjlive3 --config config/default.yaml
"""

import sys
import argparse
from pathlib import Path

# Add src directory to Python path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from vjlive3.core.pipeline import VideoPipeline
from vjlive3.sources.generator import TestPatternGenerator
from vjlive3.effects import BlurEffect, ColorCorrectionEffect
from vjlive3.utils.logging import setup_logging


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="VJLive3 - Next Generation Visual Performance System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config/my_setup.yaml
  %(prog)s --debug
  %(prog)s --version
        """
    )

    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (YAML/JSON)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"VJLive3 {__import__('vjlive3').__version__}",
    )

    return parser.parse_args()


def main() -> int:
    """Main application entry point.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    args = parse_args()

    # Setup logging
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(level=log_level)

    try:
        # Create a simple demo pipeline
        print("=" * 60)
        print("VJLive3 (The Reckoning) - Demo Mode")
        print("=" * 60)

        # Create video source (test pattern generator)
        source = TestPatternGenerator(
            pattern="color_bars",
            width=1280,
            height=720,
            fps=30.0,
        )

        # Create effects chain
        effects = [
            ColorCorrectionEffect(
                brightness=1.0,
                contrast=1.0,
                saturation=1.0,
            ),
            BlurEffect(kernel_size=5),
        ]

        # Create pipeline
        pipeline = VideoPipeline(
            source=source,
            effects=effects,
        )

        # Process a few frames as demo
        print("\nProcessing demo frames...")
        frame_count = 0
        max_frames = 10

        for frame in source.stream():
            processed = pipeline.process(frame)
            frame_count += 1
            print(f"  Processed frame {frame_count}/{max_frames} "
                  f"(shape: {processed.shape})")

            if frame_count >= max_frames:
                break

        print(f"\n✅ Successfully processed {frame_count} frames")
        print("=" * 60)
        print("VJLive3 is ready for development!")
        print("\nNext steps:")
        print("  1. Read README.md for project overview")
        print("  2. Read CONTRIBUTING.md for contribution guidelines")
        print("  3. Run 'make test' to verify installation")
        print("  4. Explore the codebase and start contributing!")
        print("=" * 60)

        return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())