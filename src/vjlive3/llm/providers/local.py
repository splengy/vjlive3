import httpx
import logging
from typing import Dict, List

from vjlive3.llm.providers.base import LLMProvider

logger = logging.getLogger(__name__)

class LocalProvider(LLMProvider):
    """Local Provider bridging to Ollama over HTTP."""
    
    def __init__(self, api_key: str, model_name: str, max_tokens: int, temperature: float, base_url: str = "http://localhost:11434"):
        super().__init__(api_key, model_name, max_tokens, temperature)
        self.base_url = base_url
    
    @property
    def provider_name(self) -> str:
        return "local"
        
    async def generate(self, messages: List[Dict[str, str]]) -> str:
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            },
            "stream": False
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, timeout=60.0)
                response.raise_for_status()
                data = response.json()
                return data["message"]["content"]
            except httpx.ConnectError:
                logger.error(f"Local AI Provider unreachable at {self.base_url}.")
                raise
            except Exception as e:
                logger.error(f"Local Provider generation failed: {e}")
                raise
                
    async def validate_connection(self) -> bool:
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient() as client:
                res = await client.get(url, timeout=2.0)
                return res.status_code == 200
        except Exception:
            return False
