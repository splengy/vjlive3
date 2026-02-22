"""
P2-D5 Audio-reactive DMX
Bridges the Audio Engine with the DMX FX Engine.
"""
from typing import Callable, Dict, List, Optional
import logging

_logger = logging.getLogger("vjlive3.core.dmx.audio_dmx")

class AudioDmxLink:
    """
    Bridges the Audio Engine with the DMX FX Engine.
    Reacts to frequency bands, envelope followers, and beat triggers 
    to modulate specific DMX parameters.
    """
    def __init__(self) -> None:
        # Maps a frequency band tuple (low_hz, high_hz) to a parameter string names
        self._band_mappings: List[dict] = []
        # Maps beat triggers to callback functions
        self._beat_mappings: List[Callable] = []
        # Store last known target parameter values for decay tracking
        self.target_values: Dict[str, float] = {}

    def map_frequency_band(self, low_hz: float, high_hz: float, target_fx_param: str) -> None:
        """Map amplitude in a specific frequency band to a DMX effect parameter."""
        mapping = {
            "low_hz": low_hz,
            "high_hz": high_hz,
            "target": target_fx_param
        }
        self._band_mappings.append(mapping)
        self.target_values[target_fx_param] = 0.0
        _logger.info("Mapped audio band %.1f-%.1f Hz to %s", low_hz, high_hz, target_fx_param)

    def map_beat(self, target_fx_action: Callable) -> None:
        """Map a beat trigger to a specific action callback."""
        self._beat_mappings.append(target_fx_action)
        _logger.info("Mapped beat trigger to action: %s", target_fx_action.__name__)

    def update(self, audio_data: dict, delta_time: float) -> None:
        """
        Update the mapped DMX parameters and trigger actions based on audio state.
        
        Args:
            audio_data: Contains 'bands', 'is_beat', 'rms', etc.
            delta_time: Time elapsed since last update (for decay logic)
        """
        # Handle beat triggers
        is_beat = audio_data.get("is_beat", False)
        if is_beat:
            for action in self._beat_mappings:
                try:
                    action()
                except Exception as e:
                    _logger.error("Error in mapped beat action %s: %s", action.__name__, e)
        
        # Determine if we have valid audio to update bands
        bands = audio_data.get("bands", [])
        
        if not bands:
            # Missing audio data: gracefully decay all modeled target values toward 0.0
            decay_rate = 1.0  # units per second, tune as needed
            decay_amount = decay_rate * delta_time
            for target in self.target_values:
                val = self.target_values[target]
                if val > 0:
                    self.target_values[target] = max(0.0, val - decay_amount)
                elif val < 0:
                    self.target_values[target] = min(0.0, val + decay_amount)
            return

        # Update frequency bands mapped to parameters
        # (Assuming the simplified structure where bands logic calculates the exact amplitude 
        # based on frequencies, or assuming bands is a dict/list of amplitudes matching our mapping).
        # For this spec implementation, we'll assume `audio_data['bands']` contains 
        # a structure we can query, like mapping (low_hz, high_hz) directly if it's a dict,
        # or we mock it as taking the max amplitude across a matching range from an array.
        # Since the spec doesn't strictly define the `bands` format, we'll treat it as a dictionary
        # of amplitudes keyed by a string "low-high", or a general float.
        # Let's say `audio_data['bands']` is a list of dicts: `[{"low": 20, "high": 80, "amp": 0.8}, ...]`
        
        for mapping in self._band_mappings:
            low = mapping["low_hz"]
            high = mapping["high_hz"]
            target = mapping["target"]
            
            # Find the corresponding band amplitude
            amplitude = 0.0
            
            if isinstance(bands, list):
                for b in bands:
                    if isinstance(b, dict) and b.get("low", 0) <= low and b.get("high", 20000) >= high:
                        amplitude = max(amplitude, b.get("amp", 0.0))
            elif isinstance(bands, dict):
                # Fallback simplistic mock if someone passed a dict
                key = f"{int(low)}-{int(high)}"
                amplitude = bands.get(key, 0.0)

            # Assign directly (no smoothing applied here besides the decay on audio loss)
            self.target_values[target] = amplitude

    def clear_mappings(self) -> None:
        """Clear all active audio-DMX mappings."""
        self._band_mappings.clear()
        self._beat_mappings.clear()
        self.target_values.clear()
        _logger.info("Cleared all audio-DMX mappings")
