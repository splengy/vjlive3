"""Tests for rate limiting functionality."""

import pytest
import time
from src.vjlive3.core.security.rate_limiter import (
    RateLimiter, RateLimitConfig, get_rate_limit_info, reset_rate_limiter
)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Reset rate limiter before each test."""
    reset_rate_limiter()
    yield
    reset_rate_limiter()


def test_unauthenticated_rate_limit():
    """Test that unauthenticated requests are limited to 10 per minute."""
    limiter = RateLimiter(RateLimitConfig(
        authenticated_limit=100,
        unauthenticated_limit=10,
        window_seconds=60
    ))
    
    # First 10 requests should pass
    for i in range(10):
        is_limited, headers = limiter.is_rate_limited(ip="127.0.0.1")
        assert not is_limited, f"Request {i+1} should not be rate limited"
        assert headers['X-RateLimit-Limit'] == '10'
        assert int(headers['X-RateLimit-Remaining']) == 9 - i
    
    # 11th request should be rate limited
    is_limited, headers = limiter.is_rate_limited(ip="127.0.0.1")
    assert is_limited, "11th request should be rate limited"
    assert headers['X-RateLimit-Remaining'] == '0'


def test_authenticated_rate_limit():
    """Test that authenticated requests are limited to 100 per minute."""
    reset_rate_limiter()
    limiter = RateLimiter(RateLimitConfig(
        authenticated_limit=100,
        unauthenticated_limit=10,
        window_seconds=60
    ))
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6IjEyMzQ1NiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # First 100 requests should pass
    for i in range(100):
        is_limited, headers = limiter.is_rate_limited(token=token)
        assert not is_limited, f"Request {i+1} should not be rate limited"
        assert headers['X-RateLimit-Limit'] == '100'
        assert int(headers['X-RateLimit-Remaining']) == 99 - i
    
    # 101st request should be rate limited
    is_limited, headers = limiter.is_rate_limited(token=token)
    assert is_limited, "101st request should be rate limited"
    assert headers['X-RateLimit-Remaining'] == '0'


def test_user_id_extraction():
    """Test JWT user ID extraction."""
    limiter = RateLimiter()
    
    # Valid JWT with user_id
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6IjEyMzQ1NiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    identifier = limiter._get_identifier(token=token)
    assert identifier == "user:123456"
    
    # Invalid token should fall back to IP
    identifier = limiter._get_identifier(token="invalid", ip="192.168.1.1")
    assert identifier == "ip:192.168.1.1"


def test_rate_limit_headers():
    """Test that rate limit headers are correctly set."""
    limiter = RateLimiter()
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6IjEyMzQ1NiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    is_limited, headers = limiter.is_rate_limited(token=token)
    assert not is_limited
    assert 'X-RateLimit-Limit' in headers
    assert 'X-RateLimit-Remaining' in headers
    assert 'X-RateLimit-Reset' in headers
    assert 'X-RateLimit-Identifier' in headers


def test_different_users_separate_limits():
    """Test that different users have separate rate limit counters."""
    reset_rate_limiter()
    limiter = RateLimiter(RateLimitConfig(authenticated_limit=5, window_seconds=60))
    
    token1 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcl9pZCI6IjEiLCJyb2xlIjoidXNlciIsImV4cCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    token2 = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwidXNlcl9pZCI6IjIiLCJyb2xlIjoidXNlciIsImV4cCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Use up token1's limit
    for _ in range(5):
        is_limited, _ = limiter.is_rate_limited(token=token1)
        assert not is_limited
    
    # Token1 should be rate limited
    is_limited, _ = limiter.is_rate_limited(token=token1)
    assert is_limited
    
    # Token2 should still have capacity
    is_limited, _ = limiter.is_rate_limited(token=token2)
    assert not is_limited


def test_ip_based_limits():
    """Test that different IPs have separate rate limit counters."""
    reset_rate_limiter()
    limiter = RateLimiter(RateLimitConfig(unauthenticated_limit=5, window_seconds=60))
    
    # Use up IP1's limit
    for _ in range(5):
        is_limited, _ = limiter.is_rate_limited(ip="192.168.1.1")
        assert not is_limited
    
    # IP1 should be rate limited
    is_limited, _ = limiter.is_rate_limited(ip="192.168.1.1")
    assert is_limited
    
    # IP2 should still have capacity
    is_limited, _ = limiter.is_rate_limited(ip="192.168.1.2")
    assert not is_limited


def test_rate_limit_reset_after_window():
    """Test that rate limits reset after the time window."""
    reset_rate_limiter()
    limiter = RateLimiter(RateLimitConfig(authenticated_limit=2, window_seconds=1))
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6IjEyMzQ1NiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Use up limit
    limiter.is_rate_limited(token=token)
    limiter.is_rate_limited(token=token)
    is_limited, _ = limiter.is_rate_limited(token=token)
    assert is_limited
    
    # Wait for window to expire
    time.sleep(1.1)
    
    # Should be able to make requests again
    is_limited, _ = limiter.is_rate_limited(token=token)
    assert not is_limited


def test_get_rate_limit_info():
    """Test the get_rate_limit_info helper function."""
    reset_rate_limiter()
    limiter = RateLimiter(RateLimitConfig(authenticated_limit=10, window_seconds=60))
    
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwidXNlcl9pZCI6IjEyMzQ1NiIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    
    # Make a request
    limiter.is_rate_limited(token=token)
    
    info = get_rate_limit_info(token=token)
    assert info['identifier'] == 'user:123456'
    assert info['count'] == 1
    assert info['limit'] == 10
    assert info['window_seconds'] == 60