import time
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RateLimiter:
    """Manages rate limits, cost tracking, and response caching for LLM Providers."""
    
    def __init__(self, cache_ttl: int = 300):
        self.cache_ttl = cache_ttl
        self._request_history: Dict[str, list[float]] = {}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._costs: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        
    async def acquire(self, provider: str, limit_rpm: int) -> bool:
        """Enforce rate limits asynchronously."""
        async with self._lock:
            now = time.time()
            if provider not in self._request_history:
                self._request_history[provider] = []
                
            # Filter history to keep only timestamps from the last minute
            self._request_history[provider] = [t for t in self._request_history[provider] if now - t < 60.0]
            
            if len(self._request_history[provider]) >= limit_rpm:
                logger.warning(f"Rate limit exceeded for provider {provider} ({limit_rpm} RPM).")
                return False
                
            self._request_history[provider].append(now)
            return True
            
    async def get_cached(self, cache_key: str) -> Optional[Any]:
        async with self._lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if time.time() - entry["timestamp"] < self.cache_ttl:
                    return entry["response"]
                else:
                    del self._cache[cache_key]
            return None
            
    async def set_cached(self, cache_key: str, response: Any) -> None:
        async with self._lock:
            self._cache[cache_key] = {
                "timestamp": time.time(),
                "response": response
            }
            
    async def track_cost(self, provider: str, tokens_used: int, cost_per_1k: float) -> None:
        async with self._lock:
            if provider not in self._costs:
                self._costs[provider] = 0.0
            self._costs[provider] += (tokens_used / 1000.0) * cost_per_1k
