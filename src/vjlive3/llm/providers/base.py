from abc import ABC, abstractmethod
from typing import Dict, Any, List

class LLMProvider(ABC):
    """Abstract Base Class for LLM API Providers."""
    
    def __init__(self, api_key: str, model_name: str, max_tokens: int, temperature: float):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return identifier string for this provider."""
        pass
        
    @abstractmethod
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate response from the provider asynchronously.
        Expected messages format: [{"role": "system", "content": "..."}]
        """
        pass
        
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Check if provider API is reachable and key is valid."""
        pass
