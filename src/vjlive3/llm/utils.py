import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

class LLMUtils:
    """Helper utilities for LLM Service."""
    
    @staticmethod
    def build_prompt(system: str, user: str, context: dict = None) -> list[dict]:
        """Construct a standardized messages array for chat completion endpoints."""
        messages = [{"role": "system", "content": system}]
        
        if context:
            context_str = "\n".join(f"{k}: {v}" for k, v in context.items())
            user_msg = f"{user}\n\n[Context]\n{context_str}"
        else:
            user_msg = user
            
        messages.append({"role": "user", "content": user_msg})
        return messages
        
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate token count via a fast approximation (e.g., words * 1.3).
        Avoids the heavy tiktoken dependency on the main loop.
        """
        if not text:
            return 0
        return int(len(text.split()) * 1.3)

def safe_async_call(fallback_return: Any = None):
    """Decorator to catch LLM API errors and gracefully return fallbacks without crashing."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in LLM call {func.__name__}: {e}", exc_info=True)
                return fallback_return
        return wrapper
    return decorator
