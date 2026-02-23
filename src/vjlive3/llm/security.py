import os
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles API key retrieval and basic input sanitization to prevent prompt injection."""
    
    @staticmethod
    def get_api_key(provider_name: str, config_key: Optional[str] = None) -> str:
        """
        Retrieve API key securely.
        Order of precedence:
        1. Passed in configuration (config_key)
        2. Environment variable (e.g., OPENAI_API_KEY)
        """
        if config_key and config_key.strip():
            return config_key
            
        env_var_name = f"{provider_name.upper()}_API_KEY"
        env_key = os.environ.get(env_var_name)
        if env_key:
            return env_key
            
        logger.warning(f"No API key found for provider {provider_name}.")
        return ""
        
    @staticmethod
    def sanitize_input(user_input: str) -> str:
        """
        Basic sanitization to neutralize obvious prompt injections.
        Replaces system instruction override attempts.
        """
        if not user_input:
            return ""
            
        # Simplified sanitization: strip excessive whitespace and block harmful imperatives
        sanitized = user_input.strip()
        
        # Danger list of words indicative of prompt injection attacks
        danger_patterns = [
            r"ignore previous instructions",
            r"ignore all prior instructions",
            r"system message override"
        ]
        
        for pattern in danger_patterns:
            sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
            
        return sanitized
        
    @staticmethod
    def filter_output(response: str) -> str:
        """Filter LLM output to prevent leaks or formatting breaks."""
        if not response:
            return ""
            
        # Strip potential markdown bleeding
        # A more sophisticated system might validate structured JSON here
        return response.strip()
