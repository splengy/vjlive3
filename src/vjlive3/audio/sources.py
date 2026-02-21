"""Audio input source abstractions for VJLive3.

Provides a common interface for different audio inputs so the rest of the
engine never cares where audio actually comes from.

Sources:
    NullAudioSource   — always returns silence. CI/headless safe.
    FileAudioSource   — reads from a WAV file (loops).
    SystemAudioSource — live mic/line-in via sounddevice (optional dep).
"""
from __future__ import annotations

import wave
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)


class AudioSource(ABC):
    """Abstract base class for audio input sources.

    Subclasses must implement ``read()``.
    """

    @abstractmethod
    def read(self, num_samples: int) -> np.ndarray:
        """Read ``num_samples`` PCM samples.

        Args:
            num_samples: How many frames to return.

        Returns:
            1-D float32 array of length ``num_samples``, values in [-1, 1].
        """

    def close(self) -> None:  # noqa: B027 — intentionally non-abstract
        """Release any held resources. Safe to call multiple times."""


class NullAudioSource(AudioSource):
    """Always returns silence. Zero deps. Use in headless/CI environments."""

    def read(self, num_samples: int) -> np.ndarray:
        return np.zeros(num_samples, dtype=np.float32)


class FileAudioSource(AudioSource):
    """Reads PCM audio from a WAV file, looping when EOF is reached.

    Args:
        path: Path to a WAV file.

    Raises:
        FileNotFoundError: If the WAV file does not exist.
        ValueError: If the file is not a valid WAV.
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        if not self._path.exists():
            raise FileNotFoundError(f"WAV file not found: {self._path}")
        self._wav = wave.open(str(self._path), "rb")
        self._channels = self._wav.getnchannels()
        self._sampwidth = self._wav.getsampwidth()
        self._framerate = self._wav.getframerate()
        self._dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(
            self._sampwidth, np.int16
        )
        self._scale = float(2 ** (self._sampwidth * 8 - 1))
        logger.info(
            "FileAudioSource: %s (sr=%d, ch=%d, depth=%d-bit)",
            self._path.name, self._framerate, self._channels, self._sampwidth * 8,
        )

    @property
    def sample_rate(self) -> int:
        return self._framerate

    def read(self, num_samples: int) -> np.ndarray:
        """Read samples from the WAV file, looping at EOF."""
        raw = self._wav.readframes(num_samples)
        if len(raw) < num_samples * self._sampwidth * self._channels:
            # Looped — rewind and read remainder
            self._wav.rewind()
            remaining = num_samples - len(raw) // (self._sampwidth * self._channels)
            raw += self._wav.readframes(remaining)

        samples = np.frombuffer(raw, dtype=self._dtype).astype(np.float32)
        samples /= self._scale

        # Downmix to mono if multichannel
        if self._channels > 1:
            samples = samples.reshape(-1, self._channels).mean(axis=1)

        # Pad with silence if still short (edge case: very short file)
        if len(samples) < num_samples:
            samples = np.pad(samples, (0, num_samples - len(samples)))

        return samples[:num_samples]

    def close(self) -> None:
        self._wav.close()


class SystemAudioSource(AudioSource):
    """Live audio input via sounddevice (optional dependency).

    Falls back to NullAudioSource if sounddevice is not installed.

    Args:
        device:      sounddevice device index or name (None = default)
        sample_rate: Sample rate in Hz (default 44100)
        chunk_size:  Frames per read (default 1024)
    """

    def __init__(
        self,
        device=None,
        sample_rate: int = 44100,
        chunk_size: int = 1024,
    ) -> None:
        try:
            import sounddevice as sd  # noqa: WPS433
            self._sd = sd
            self._stream = sd.InputStream(
                device=device,
                samplerate=sample_rate,
                channels=1,
                dtype="float32",
                blocksize=chunk_size,
            )
            self._stream.start()
            self._null = None
            logger.info("SystemAudioSource: live input started (device=%s)", device)
        except Exception as exc:
            logger.warning(
                "sounddevice unavailable (%s) — falling back to NullAudioSource", exc
            )
            self._sd = None
            self._stream = None
            self._null = NullAudioSource()

    def read(self, num_samples: int) -> np.ndarray:
        if self._null is not None:
            return self._null.read(num_samples)
        data, _ = self._stream.read(num_samples)
        return data.ravel()

    def close(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
