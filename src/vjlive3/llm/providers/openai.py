import httpx
import logging
from typing import Dict, List

from vjlive3.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)

class OpenAIProvider(LLMProvider):
    """OpenAI API Provider."""
    
    @property
    def provider_name(self) -> str:
        return "openai"
        
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key missing.")
            
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            
            if response.status_code != 200:
                logger.error(f"OpenAI API Error {response.status_code}: {response.text}")
                response.raise_for_status()
                
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
    async def validate_connection(self) -> bool:
        if not self.api_key:
            return False
            
        try:
            # Send minimal token request to models endpoint to verify auth
            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient() as client:
                res = await client.get(url, headers=headers, timeout=5.0)
                return res.status_code == 200
        except Exception as e:
            logger.error(f"Failed to validate OpenAI connection: {e}")
            return False
