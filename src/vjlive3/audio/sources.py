"""
P1-A4 — Audio Sources
Spec: docs/specs/_02_fleshed_out/P1-A4_audio_sources.md
Tier: 🖥️ Pro-Tier Native

Classes:
  AudioSource        — single audio input source with level + connections
  AudioSourceManager — registry: add/remove/connect/level control
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AudioSource
# ---------------------------------------------------------------------------

class AudioSource:
    """
    Represents a single audio input source (physical or virtual).
    Manages its own level control, connection list, and error state.
    """

    def __init__(
        self,
        source_id: str,
        device_name: str,
        device_type: str = "physical",
        sample_rate: int = 44100,
        channels: int = 1,
    ) -> None:
        self.source_id = source_id
        self.device_name = device_name
        self.device_type = device_type
        self.sample_rate = sample_rate
        self.channels = channels

        self._level: float = 1.0
        self._connections: List[str] = []
        self.error_state: bool = False
        self.last_error: Optional[str] = None
        self._recovery_attempts: int = 0
        self._audio_level: float = 0.0
        self._status: str = "connected"

    # ---- Level / connection control ----------------------------------------

    def set_level(self, level: float) -> bool:
        """Set source volume level (0.0–1.0). Returns False if out-of-range."""
        if not (0.0 <= level <= 1.0):
            return False
        self._level = level
        return True

    def get_level(self) -> float:
        return self._level

    def add_connection(self, target: str) -> None:
        if target not in self._connections:
            self._connections.append(target)

    def remove_connection(self, target: str) -> None:
        if target in self._connections:
            self._connections.remove(target)

    def get_connected_targets(self) -> List[str]:
        return list(self._connections)

    def disconnect(self) -> bool:
        """Disconnect all targets and mark as idle."""
        self._connections.clear()
        self._status = "idle"
        return True

    # ---- Status / info ------------------------------------------------------

    def get_status(self) -> str:
        return self._status

    def get_device_info(self) -> dict:
        return {
            "source_id": self.source_id,
            "device_name": self.device_name,
            "device_type": self.device_type,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
        }

    def get_stats(self) -> dict:
        return {
            "source_id": self.source_id,
            "level": self._level,
            "audio_level": self._audio_level,
            "connections": list(self._connections),
            "error_state": self.error_state,
            "last_error": self.last_error,
            "status": self._status,
        }

    # ---- Error recovery -----------------------------------------------------

    def recover_from_error(self) -> bool:
        """Attempt to clear error state. Returns True on success."""
        if not self.error_state:
            return True
        try:
            # Reset error state (in production would re-open device)
            self.error_state = False
            self.last_error = None
            self._recovery_attempts = 0
            self._status = "connected"
            return True
        except Exception as exc:
            logger.error("AudioSource.recover_from_error: %s", exc)
            return False


# ---------------------------------------------------------------------------
# AudioSourceManager
# ---------------------------------------------------------------------------

class AudioSourceManager:
    """
    Central registry for audio sources.
    Supports add/remove, level control, connection routing, and hot-plug
    change notifications via subscriber callbacks.
    """

    METADATA: dict = {"spec": "P1-A4", "tier": "Pro-Tier Native"}

    def __init__(self) -> None:
        self._sources: Dict[str, AudioSource] = {}
        self._device_cache: List[dict] = []
        self._last_update: float = 0.0
        self._update_interval: float = 5.0
        self._subscribers: List[Callable] = []
        self._lock = threading.RLock()
        self.error_state: bool = False
        self.last_error: Optional[str] = None

    # ---- Source lifecycle ---------------------------------------------------

    def add_source(
        self,
        device_name: str,
        device_type: str = "physical",
        sample_rate: int = 44100,
        channels: int = 1,
    ) -> AudioSource:
        """Create and register a new audio source."""
        source_id = self._generate_id(device_name)
        source = AudioSource(
            source_id=source_id,
            device_name=device_name,
            device_type=device_type,
            sample_rate=sample_rate,
            channels=channels,
        )
        with self._lock:
            self._sources[source_id] = source
            self._refresh_device_cache()
        self._notify()
        logger.info("AudioSourceManager: added source '%s' (%s)", device_name, source_id)
        return source

    def remove_source(self, source_id: str) -> bool:
        """Remove a source by ID. Returns False if unknown."""
        with self._lock:
            if source_id not in self._sources:
                return False
            self._sources[source_id].disconnect()
            del self._sources[source_id]
            self._refresh_device_cache()
        self._notify()
        return True

    # ---- Signal routing ----------------------------------------------------

    def connect_source(self, source_id: str, target: str) -> bool:
        with self._lock:
            src = self._sources.get(source_id)
            if src is None:
                return False
            src.add_connection(target)
        return True

    def disconnect_source(self, source_id: str, target: str) -> bool:
        with self._lock:
            src = self._sources.get(source_id)
            if src is None:
                return False
            src.remove_connection(target)
        return True

    def get_connected_targets(self, source_id: str) -> List[str]:
        with self._lock:
            src = self._sources.get(source_id)
            return src.get_connected_targets() if src else []

    # ---- Level control -----------------------------------------------------

    def set_level(self, source_id: str, level: float) -> bool:
        with self._lock:
            src = self._sources.get(source_id)
            if src is None:
                return False
        return src.set_level(level)

    def get_level(self, source_id: str) -> float:
        with self._lock:
            src = self._sources.get(source_id)
            return src.get_level() if src else 0.0

    # ---- Info / stats -------------------------------------------------------

    def get_source_info(self, source_id: str) -> dict:
        with self._lock:
            src = self._sources.get(source_id)
            if src is None:
                return {}
            return {
                "source_id": source_id,
                "device_name": src.device_name,
                "device_type": src.device_type,
                "sample_rate": src.sample_rate,
                "channels": src.channels,
                "level": src.get_level(),
                "status": src.get_status(),
            }

    def get_active_sources(self) -> List[dict]:
        with self._lock:
            ids = list(self._sources.keys())
        return [self.get_source_info(sid) for sid in ids]

    def get_device_list(self) -> List[dict]:
        with self._lock:
            return list(self._device_cache)

    def get_device_status(self, device_id: str) -> dict:
        info = self.get_source_info(device_id)
        return info if info else {}

    def get_stats(self) -> dict:
        with self._lock:
            return {
                "source_count": len(self._sources),
                "device_count": len(self._device_cache),
                "error_state": self.error_state,
                "last_error": self.last_error,
            }

    def get_audio_level(self, source_id: str) -> float:
        with self._lock:
            src = self._sources.get(source_id)
            return src._audio_level if src else 0.0

    def get_sample_rate(self, source_id: str) -> int:
        with self._lock:
            src = self._sources.get(source_id)
            return src.sample_rate if src else 0

    def get_channels(self, source_id: str) -> int:
        with self._lock:
            src = self._sources.get(source_id)
            return src.channels if src else 0

    # ---- Subscriber pattern ------------------------------------------------

    def subscribe(self, callback: Callable) -> None:
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    # ---- Internal ----------------------------------------------------------

    def _generate_id(self, device_name: str) -> str:
        slug = device_name.lower().replace(" ", "_").replace("-", "_")
        # Ensure uniqueness if same name added twice
        base = slug
        counter = 0
        with self._lock:
            while slug in self._sources:
                counter += 1
                slug = f"{base}_{counter}"
        return slug

    def _refresh_device_cache(self) -> None:
        self._device_cache = [
            {"source_id": sid, "device_name": src.device_name, "device_type": src.device_type}
            for sid, src in self._sources.items()
        ]
        self._last_update = time.time()

    def _notify(self) -> None:
        for cb in list(self._subscribers):
            try:
                cb()
            except Exception as exc:
                logger.debug("AudioSourceManager subscriber: %s", exc)
