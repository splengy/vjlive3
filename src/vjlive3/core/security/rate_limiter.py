"""User-based rate limiting with JWT token support.

This module implements a flexible rate limiting system that supports:
- User-based rate limiting using JWT token claims
- IP-based rate limiting for unauthenticated requests
- Configurable rate limits for different user roles
- TTL-based counter storage
- HTTP headers for rate limit information
"""

import time
import re
from typing import Optional, Dict, Tuple, List
from dataclasses import dataclass, field
from collections import defaultdict
from functools import wraps
import logging

from src.vjlive3.utils.security import validate_ip_address

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    authenticated_limit: int = 100  # requests per minute
    unauthenticated_limit: int = 10  # requests per minute
    window_seconds: int = 60  # time window in seconds


@dataclass
class RateLimitCounter:
    """Counter for tracking rate limit usage."""
    count: int = 0
    reset_time: float = field(default_factory=lambda: time.time() + 60)


class RateLimiter:
    """Rate limiting system with JWT and IP-based support."""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.counters: Dict[str, RateLimitCounter] = defaultdict(RateLimitCounter)
        self.ip_counters: Dict[str, RateLimitCounter] = defaultdict(RateLimitCounter)
        
    def _get_identifier(self, token: Optional[str] = None, ip: Optional[str] = None) -> str:
        """Get the rate limiting identifier."""
        if token:
            # Try to extract user ID from JWT token
            user_id = self._extract_user_id(token)
            if user_id:
                return f"user:{user_id}"
        
        # Fall back to IP-based limiting
        if ip and validate_ip_address(ip):
            return f"ip:{ip}"
        
        # Last resort: use request path or generic identifier
        return "generic"
    
    def _extract_user_id(self, token: str) -> Optional[str]:
        """Extract user ID from JWT token (simplified implementation)."""
        # In production, use a proper JWT library like PyJWT
        # This is a simplified version for demonstration
        try:
            # JWT format: header.payload.signature
            # We'll look for user_id in the payload
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (base64url)
            import base64
            import json
            
            payload = base64.urlsafe_b64decode(parts[1] + '==')
            claims = json.loads(payload)
            
            return claims.get('user_id') or claims.get('sub')
        except (ValueError, json.JSONDecodeError, base64.binascii.Error):
            return None
    
    def is_rate_limited(self, token: Optional[str] = None, ip: Optional[str] = None) -> Tuple[bool, Dict]:
        """Check if the request is rate limited.
        
        Returns:
            Tuple of (is_limited, headers_dict)
        """
        identifier = self._get_identifier(token, ip)
        
        # Get the appropriate counter and limit
        if identifier.startswith('user:'):
            counter = self.counters[identifier]
            limit = self.config.authenticated_limit
        else:
            counter = self.ip_counters[identifier]
            limit = self.config.unauthenticated_limit
        
        current_time = time.time()
        
        # Check if counter needs reset
        if current_time >= counter.reset_time:
            counter.count = 0
            counter.reset_time = current_time + self.config.window_seconds
        
        # Check rate limit
        if counter.count >= limit:
            headers = self._build_headers(identifier, counter, limit)
            return True, headers
        
        # Increment counter
        counter.count += 1
        
        headers = self._build_headers(identifier, counter, limit)
        return False, headers
    
    def _build_headers(self, identifier: str, counter: RateLimitCounter, limit: int) -> Dict:
        """Build rate limit headers."""
        remaining = max(0, limit - counter.count)
        reset_seconds = max(0, int(counter.reset_time - time.time()))
        
        return {
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset_seconds),
            'X-RateLimit-Identifier': identifier
        }
    
    def reset_all(self):
        """Reset all rate limit counters (for testing)."""
        self.counters.clear()
        self.ip_counters.clear()


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit_middleware(get_response):
    """WSGI middleware for rate limiting."""
    
    def middleware(request):
        # Extract token from Authorization header
        token = None
        ip = request.headers.get('X-Real-IP') or request.headers.get('X-Forwarded-For') or request.remote_addr
        
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        is_limited, headers = rate_limiter.is_rate_limited(token, ip)
        
        if is_limited:
            response = get_response(request)
            response.status_code = 429
            response.headers.update(headers)
            response.data = b'Rate limit exceeded'
            return response
        
        response = get_response(request)
        response.headers.update(headers)
        return response
    
    return middleware


def rate_limit(token: Optional[str] = None, ip: Optional[str] = None):
    """Decorator for rate limiting specific functions."""
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_limited, headers = rate_limiter.is_rate_limited(token, ip)
            
            if is_limited:
                raise RateLimitExceeded(headers)
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, headers: Dict = None):
        self.headers = headers or {}
        super().__init__('Rate limit exceeded')


# Convenience functions for testing

def get_rate_limit_info(token: Optional[str] = None, ip: Optional[str] = None) -> Dict:
    """Get rate limit information for testing."""
    identifier = rate_limiter._get_identifier(token, ip)
    
    if identifier.startswith('user:'):
        counter = rate_limiter.counters[identifier]
        limit = rate_limiter.config.authenticated_limit
    else:
        counter = rate_limiter.ip_counters[identifier]
        limit = rate_limiter.config.unauthenticated_limit
    
    return {
        'identifier': identifier,
        'count': counter.count,
        'limit': limit,
        'reset_time': counter.reset_time,
        'window_seconds': rate_limiter.config.window_seconds
    }


def reset_rate_limiter():
    """Reset the global rate limiter (for testing)."""
    rate_limiter.reset_all()