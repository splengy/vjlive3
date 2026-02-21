"""Image processing utilities.

This module provides common image processing operations used across effects
and sources.
"""

from typing import Tuple, Optional
import numpy as np
import cv2


def resize_frame(
    frame: np.ndarray,
    size: Tuple[int, int],
    interpolation: int = cv2.INTER_AREA,
) -> np.ndarray:
    """Resize a frame to the specified size.

    Args:
        frame: Input frame (HxWxC)
        size: Target size as (width, height)
        interpolation: OpenCV interpolation method

    Returns:
        Resized frame

    Example:
        >>> resized = resize_frame(frame, (1920, 1080))
    """
    if frame.ndim != 3:
        raise ValueError(f"Frame must be 3D, got {frame.ndim}D")

    return cv2.resize(frame, size, interpolation=interpolation)


def convert_color(
    frame: np.ndarray,
    code: int,
    keep_dim: bool = True
) -> np.ndarray:
    """Convert frame color space.

    Args:
        frame: Input frame
        code: OpenCV color conversion code (e.g., cv2.COLOR_RGB2HSV)
        keep_dim: If True, keep 3D shape even for single-channel

    Returns:
        Converted frame

    Example:
        >>> hsv = convert_color(frame, cv2.COLOR_RGB2HSV)
    """
    converted = cv2.cvtColor(frame, code)

    if keep_dim and len(converted.shape) == 2:
        # Add channel dimension for single-channel output
        converted = converted[:, :, np.newaxis]

    return converted


def validate_frame(
    frame: np.ndarray,
    require_rgb: bool = True,
    allow_float: bool = True,
) -> None:
    """Validate frame format and properties.

    Args:
        frame: Frame to validate
        require_rgb: If True, require 3 channels
        allow_float: If True, allow float32/float64, else require uint8

    Raises:
        ValueError: If frame is invalid

    Example:
        >>> validate_frame(frame)
    """
    if frame is None:
        raise ValueError("Frame is None")

    if frame.ndim != 3:
        raise ValueError(f"Frame must be 3D, got {frame.ndim}D")

    if require_rgb and frame.shape[2] != 3:
        raise ValueError(f"Frame must have 3 channels, got {frame.shape[2]}")

    if not allow_float and frame.dtype not in (np.uint8,):
        raise ValueError(f"Frame must be uint8, got {frame.dtype}")

    if frame.size == 0:
        raise ValueError("Frame is empty")


def normalize_frame(
    frame: np.ndarray,
    target_dtype: np.dtype = np.uint8,
    clip: bool = True,
) -> np.ndarray:
    """Normalize frame values to target dtype range.

    Args:
        frame: Input frame
        target_dtype: Target data type (np.uint8 or np.float32)
        clip: If True, clip values to valid range

    Returns:
        Normalized frame
    """
    if target_dtype == np.uint8:
        if clip:
            frame = np.clip(frame, 0, 255)
        return frame.astype(np.uint8)
    elif target_dtype == np.float32:
        if frame.dtype == np.uint8:
            frame = frame.astype(np.float32) / 255.0
        if clip:
            frame = np.clip(frame, 0.0, 1.0)
        return frame
    else:
        raise ValueError(f"Unsupported target dtype: {target_dtype}")


def blend_frames(
    frame1: np.ndarray,
    frame2: np.ndarray,
    alpha: float,
    blend_mode: str = "normal",
) -> np.ndarray:
    """Blend two frames with given alpha.

    Args:
        frame1: First frame
        frame2: Second frame
        alpha: Blend factor (0.0 = all frame1, 1.0 = all frame2)
        blend_mode: Blend mode ("normal", "multiply", "screen", etc.)

    Returns:
        Blended frame
    """
    if frame1.shape != frame2.shape:
        raise ValueError(f"Frames must have same shape: {frame1.shape} vs {frame2.shape}")

    if blend_mode == "normal":
        blended = (1 - alpha) * frame1 + alpha * frame2
    elif blend_mode == "multiply":
        blended = (frame1 * frame2) / 255.0
    elif blend_mode == "screen":
        blended = 255 - ((255 - frame1) * (255 - frame2)) / 255.0
    else:
        raise ValueError(f"Unknown blend mode: {blend_mode}")

    return np.clip(blended, 0, 255).astype(np.uint8)