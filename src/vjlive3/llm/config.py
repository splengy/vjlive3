from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class LLMProviderConfig(BaseModel):
    """Configuration for a specific LLM Provider."""
    enabled: bool = True
    api_key: Optional[str] = None
    model_name: str = "default-model"
    max_tokens: int = Field(default=1024, description="Maximum tokens to generate per request.")
    temperature: float = Field(default=0.7, description="Control randomness of the output.")
    rate_limit_rpm: int = Field(default=60, description="Requests per minute rate limit")

class LLMConfig(BaseModel):
    """Central Configuration for LLM Service."""
    default_provider: str = Field(default="openai", description="Default provider to fall back to")
    providers: Dict[str, LLMProviderConfig] = Field(
        default_factory=lambda: {
            "openai": LLMProviderConfig(model_name="gpt-4o"),
            "anthropic": LLMProviderConfig(model_name="claude-3-opus-20240229"),
            "local": LLMProviderConfig(model_name="mistral", enabled=False)
        }
    )
    cache_ttl_seconds: int = Field(default=300, description="TTL for cached LLM responses")
    max_concurrent_requests: int = Field(default=10, description="Rate limit on total concurrent API requests")
