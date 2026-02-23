import threading
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventBus:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
        self.subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._initialized = True
        
    def subscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        with self._lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            if callback not in self.subscribers[event_type]:
                self.subscribers[event_type].append(callback)
                
    def unsubscribe(self, event_type: str, callback: Callable[[Any], None]) -> None:
        with self._lock:
            if event_type in self.subscribers and callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                
    def publish(self, event_type: str, payload: Any = None) -> None:
        with self._lock:
            callbacks = list(self.subscribers.get(event_type, []))
            
        for callback in callbacks:
            try:
                callback(payload)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")
