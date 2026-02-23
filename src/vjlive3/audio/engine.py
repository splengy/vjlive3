"""
Core AudioEngine managing capture threads, analysis, and device orchestration.
"""

import time
import logging
import threading
from typing import Dict, Optional, List, Callable, Any

from .config import AudioConfig, AudioDeviceConfig, AudioSourceType
from .source import AudioSource, MicrophoneSource, DummySource, AudioFeatures
from .analyzer import AudioAnalyzer

try:
    from ..core.event_bus import EventBus
    EVENT_BUS_AVAILABLE = True
except ImportError:
    EVENT_BUS_AVAILABLE = False


logger = logging.getLogger(__name__)

class AudioEngine:
    """
    Singleton orchestrator for audio acquisition and analysis.
    Spawns background threads to poll AudioSources and dispatch events.
    """
    
    _instance: Optional['AudioEngine'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    def __init__(self, config: Optional[AudioConfig] = None, event_bus: Optional[Any] = None):
        if getattr(self, "_initialized", False) and config is None:
            return
            
        self.config = config or AudioConfig()
        self.event_bus = event_bus if event_bus else (EventBus() if EVENT_BUS_AVAILABLE else None)
        
        self.sources: Dict[str, AudioSource] = {}
        self.analyzer = AudioAnalyzer(self.config)
        
        # Latest features per source ID
        self._latest_features: Dict[str, AudioFeatures] = {}
        
        # Threading state
        self._is_running = False
        self._analysis_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()
        
        # Optional PyAudio instance pool
        self._pa = None
        if globals().get('PYAUDIO_AVAILABLE'):
            import pyaudio
            self._pa = pyaudio.PyAudio()
            
        self._initialized = True
        
    def initialize(self) -> None:
        """Start pre-configured default audio sources."""
        with self._lock:
            for dev_cfg in self.config.devices:
                if dev_cfg.enabled:
                    source_id = f"src_{dev_cfg.device_name or dev_cfg.device_id or 'default'}"
                    self.add_source(source_id, dev_cfg)
                    
            if not self.sources:
                logger.info("No audio sources configured natively, spinning up a default Microphone.")
                default_cfg = AudioDeviceConfig(source_type=AudioSourceType.MICROPHONE)
                self.add_source("default_mic", default_cfg)

    def start(self) -> None:
        if self._is_running:
            return
            
        self._stop_event.clear()
        
        # Start all active sources
        with self._lock:
            for source in self.sources.values():
                source.start()
                
        # Start central analysis thread
        self._analysis_thread = threading.Thread(
            target=self._analysis_loop,
            name="AudioEngineAnalysis",
            daemon=True
        )
        self._analysis_thread.start()
        self._is_running = True
        logger.info("AudioEngine started.")
        
    def stop(self) -> None:
        if not self._is_running:
            return
            
        logger.info("Stopping AudioEngine...")
        self._stop_event.set()
        
        with self._lock:
            for source in self.sources.values():
                source.stop()
                
        if self._analysis_thread and self._analysis_thread.is_alive():
            self._analysis_thread.join(timeout=1.0)
            
        self._is_running = False
        
    def cleanup(self) -> None:
        """Release audio hardware and memory entirely."""
        self.stop()
        with self._lock:
            self.sources.clear()
            self._latest_features.clear()
            
        if self._pa:
            self._pa.terminate()
            self._pa = None

    def add_source(self, source_id: str, config: AudioDeviceConfig) -> Optional[AudioSource]:
        """Dynamically add and start a new audio source."""
        with self._lock:
            if source_id in self.sources:
                logger.warning(f"Audio source {source_id} already exists.")
                return self.sources[source_id]
                
            if len(self.sources) >= self.config.max_sources:
                logger.error(f"Cannot add source {source_id}: Maximum ({self.config.max_sources}) reached.")
                return None
                
            # Create instance based on type
            source = None
            if config.source_type == AudioSourceType.MICROPHONE:
                source = MicrophoneSource(source_id, config, self.config, self._pa)
            elif config.source_type == AudioSourceType.DUMMY:
                source = DummySource(source_id, config, self.config)
            else:
                # Fallback implementation
                logger.warning(f"Source type {config.source_type} not natively implemented yet. Using Dummy.")
                source = DummySource(source_id, config, self.config)
                
            if source:
                self.sources[source_id] = source
                self._latest_features[source_id] = AudioFeatures()
                
                # If engine is already running, jumpstart the source
                if self._is_running and config.enabled:
                    source.start()
                    
                if self.event_bus:
                    self.event_bus.publish("AudioSourceAdded", {"source_id": source_id, "config": config})
                    
                return source
        return None
        
    def remove_source(self, source_id: str) -> None:
        with self._lock:
            if source_id in self.sources:
                source = self.sources.pop(source_id)
                source.stop()
                if source_id in self._latest_features:
                    del self._latest_features[source_id]
                    
                if self.event_bus:
                    self.event_bus.publish("AudioSourceRemoved", {"source_id": source_id})

    def get_source(self, source_id: str) -> Optional[AudioSource]:
        with self._lock:
            return self.sources.get(source_id)
            
    def get_features(self, source_id: str) -> Optional[AudioFeatures]:
        with self._lock:
            return self._latest_features.get(source_id)

    def set_master_volume(self, volume: float) -> None:
        self.config.master_volume = max(0.0, min(volume, 2.0))

    def _analysis_loop(self) -> None:
        """
        Main background loop. Plucks audio chunks from all sources,
        analyzes them, and broadcasts results 60 times a second.
        """
        # Target 60 FPS for feature updates
        target_delay = 1.0 / 60.0 
        
        while not self._stop_event.is_set():
            start_t = time.perf_counter()
            
            with self._lock:
                sources_snapshot = list(self.sources.items())
                
            for src_id, source in sources_snapshot:
                if not source.is_active:
                    continue
                    
                # Dequeue audio chunks
                chunk = source.read_chunk()
                if chunk is not None:
                    # Apply master volume mapping
                    if self.config.master_volume != 1.0:
                        chunk = chunk * self.config.master_volume
                        
                    # Process signals
                    features = self.analyzer.analyze(chunk)
                    
                    with self._lock:
                        self._latest_features[src_id] = features
                        
                    # Broadcast events
                    if self.event_bus:
                        # 1. Feature updates
                        self.event_bus.publish("AudioFeaturesUpdated", {
                            "source_id": src_id,
                            "features": features
                        })
                        
                        # 2. Transients / Beats
                        if features.is_beat:
                            self.event_bus.publish("BeatDetected", {
                                "source_id": src_id,
                                "timestamp": time.time(),
                                "bpm": self.analyzer._beat_history[-1] if hasattr(self.analyzer, '_beat_history') else 120.0
                            })
                            
            elapsed = time.perf_counter() - start_t
            sleep_time = target_delay - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
