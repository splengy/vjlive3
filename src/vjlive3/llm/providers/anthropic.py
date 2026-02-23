import httpx
import logging
from typing import Dict, List

from vjlive3.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(LLMProvider):
    """Anthropic API Provider (Claude)."""
    
    @property
    def provider_name(self) -> str:
        return "anthropic"
        
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise ValueError("Anthropic API key missing.")
            
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Anthropic extracts the system message from the array
        system_content = ""
        claude_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_content = msg["content"]
            else:
                claude_messages.append(msg)
                
        payload = {
            "model": self.model_name,
            "system": system_content,
            "messages": claude_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                logger.error(f"Anthropic API Error {response.status_code}: {response.text}")
                response.raise_for_status()
                
            data = response.json()
            return data["content"][0]["text"]
            
    async def validate_connection(self) -> bool:
        """Validate Anthropic connection by creating a minimal message."""
        if not self.api_key:
            return False
            
        try:
            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            # Sending a request engineered to fail cheaply if authenticated
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "ping"}]
            }
            async with httpx.AsyncClient() as client:
                res = await client.post(url, headers=headers, json=payload, timeout=5.0)
                # Authentic keys will get 200, or a specific API error (not 401 Unauthorized)
                return res.status_code != 401
        except Exception as e:
            logger.error(f"Failed to validate Anthropic connection: {e}")
            return False
