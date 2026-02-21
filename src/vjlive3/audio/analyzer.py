"""Real-time FFT audio analyzer.

Processes raw PCM samples and exposes:
- Full magnitude spectrum (FFT bins)
- Per-band energy (bass / mids / highs)
- RMS power

Designed to run every audio frame (~23ms @ 44100 Hz / 1024 hop).
No external dependencies beyond NumPy.
"""
from __future__ import annotations

import numpy as np

from vjlive3.utils.logging import get_logger

logger = get_logger(__name__)

# Default frequency band boundaries (Hz)
_BASS_HZ   = (20,   250)
_MIDS_HZ   = (250,  4000)
_HIGHS_HZ  = (4000, 20000)


class AudioAnalyzer:
    """Real-time FFT audio analysis pipeline.

    Args:
        sample_rate: Audio sample rate in Hz (default 44100)
        fft_size:    Number of FFT bins — must be power of 2 (default 2048)
        hop_size:    Samples between frames (default fft_size // 2)

    Example::

        analyzer = AudioAnalyzer(sample_rate=44100, fft_size=2048)
        analyzer.update(pcm_chunk)          # np.ndarray of float32, shape (N,)
        print(analyzer.rms)                 # 0.0 – 1.0
        print(analyzer.bass)                # band energy, 0.0 – 1.0
        print(analyzer.spectrum[:8])        # FFT magnitudes
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        fft_size: int = 2048,
        hop_size: int | None = None,
    ) -> None:
        if fft_size & (fft_size - 1):
            raise ValueError(f"fft_size must be a power of 2, got {fft_size}")

        self.sample_rate = sample_rate
        self.fft_size    = fft_size
        self.hop_size    = hop_size if hop_size is not None else fft_size // 2

        # Hann window — reduces spectral leakage
        self._window = np.hanning(fft_size).astype(np.float32)

        # Frequency axis for each bin
        self._freqs = np.fft.rfftfreq(fft_size, d=1.0 / sample_rate)

        # Ring buffer for incoming samples
        self._buffer = np.zeros(fft_size, dtype=np.float32)

        # Public output — updated on each call to update()
        self.spectrum: np.ndarray = np.zeros(fft_size // 2 + 1, dtype=np.float32)
        self.rms: float = 0.0
        self.bass: float = 0.0
        self.mids: float = 0.0
        self.highs: float = 0.0

        logger.debug(
            "AudioAnalyzer: sr=%d fft=%d hop=%d (%.1f ms/frame)",
            sample_rate, fft_size, self.hop_size,
            self.hop_size / sample_rate * 1000,
        )

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    def update(self, samples: np.ndarray) -> None:
        """Consume a chunk of PCM samples and recompute spectrum.

        Args:
            samples: 1-D float32 array, values in [-1, 1].
                     Any length — the internal ring buffer handles alignment.
        """
        samples = np.asarray(samples, dtype=np.float32).ravel()

        # Advance ring buffer
        n = len(samples)
        if n >= self.fft_size:
            # More samples than buffer — take the most recent window
            self._buffer[:] = samples[-self.fft_size:]
        else:
            self._buffer = np.roll(self._buffer, -n)
            self._buffer[-n:] = samples

        # Windowed FFT
        windowed = self._buffer * self._window
        fft_mag  = np.abs(np.fft.rfft(windowed))

        # Normalise to 0-1 range (half-spectrum, N//2+1 bins)
        peak = fft_mag.max()
        self.spectrum = fft_mag / (peak + 1e-9)

        # RMS energy
        self.rms = float(np.sqrt(np.mean(self._buffer ** 2)))

        # Band energies
        self.bass  = self._band_energy(_BASS_HZ)
        self.mids  = self._band_energy(_MIDS_HZ)
        self.highs = self._band_energy(_HIGHS_HZ)

    def frequency_band(self, low_hz: float, high_hz: float) -> float:
        """Return normalised energy in an arbitrary frequency band.

        Args:
            low_hz:  Lower frequency bound in Hz
            high_hz: Upper frequency bound in Hz

        Returns:
            Energy in [0, 1] range.
        """
        return self._band_energy((low_hz, high_hz))

    # ------------------------------------------------------------------ #
    #  Internal helpers                                                    #
    # ------------------------------------------------------------------ #

    def _band_energy(self, band: tuple[float, float]) -> float:
        low_hz, high_hz = band
        mask = (self._freqs >= low_hz) & (self._freqs < high_hz)
        band_bins = self.spectrum[mask]
        if len(band_bins) == 0:
            return 0.0
        return float(np.mean(band_bins))
