import logging
from typing import Dict, Optional, Any

from vjlive3.llm.config import LLMConfig
from vjlive3.llm.security import SecurityManager
from vjlive3.llm.rate_limiting import RateLimiter
from vjlive3.llm.providers.base import LLMProvider
from vjlive3.llm.providers.openai import OpenAIProvider
from vjlive3.llm.providers.anthropic import AnthropicProvider
from vjlive3.llm.providers.local import LocalProvider
from vjlive3.llm.crowd_analysis import CrowdAnalysisAggregator
from vjlive3.llm.suggestions import AISuggestionEngine

logger = logging.getLogger(__name__)

class LLMService:
    """Core LLM Service acting as a singleton orchestrator for AI capabilities."""
    
    _instance = None
    
    def __new__(cls, config: Optional[LLMConfig] = None):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self, config: Optional[LLMConfig] = None):
        if self._initialized:
            return
            
        self.config = config or LLMConfig()
        self.rate_limiter = RateLimiter(cache_ttl=self.config.cache_ttl_seconds)
        self.providers: Dict[str, LLMProvider] = {}
        
        self.crowd_analysis = CrowdAnalysisAggregator(self)
        self.suggestions = AISuggestionEngine(self)
        
        self.active_provider_name = self.config.default_provider
        
        # Load providers
        self._initialize_providers()
        self._initialized = True
        
    def _initialize_providers(self):
        for name, pconfig in self.config.providers.items():
            if not pconfig.enabled:
                continue
                
            api_key = SecurityManager.get_api_key(name, pconfig.api_key)
            if not api_key and name != "local":
                logger.warning(f"Skipping provider '{name}' initialization due to missing API key.")
                continue
                
            if name == "openai":
                self.providers[name] = OpenAIProvider(api_key, pconfig.model_name, pconfig.max_tokens, pconfig.temperature)
            elif name == "anthropic":
                self.providers[name] = AnthropicProvider(api_key, pconfig.model_name, pconfig.max_tokens, pconfig.temperature)
            elif name == "local":
                self.providers[name] = LocalProvider(api_key, pconfig.model_name, pconfig.max_tokens, pconfig.temperature)
                
        if self.active_provider_name not in self.providers and self.providers:
            self.active_provider_name = next(iter(self.providers.keys()))
            logger.warning(f"Default provider missing. Falling back to {self.active_provider_name}.")
            
    def get_provider(self) -> Optional[LLMProvider]:
        return self.providers.get(self.active_provider_name)
        
    def switch_provider(self, provider_name: str) -> bool:
        if provider_name in self.providers:
            self.active_provider_name = provider_name
            logger.info(f"Switched active LLM provider to {provider_name}")
            return True
        logger.error(f"Cannot switch to unavailable provider: {provider_name}")
        return False
        
    async def generate(self, messages: list[dict], use_cache: bool = True) -> str:
        """
        Directly invoke the active provider with rate limiting and caching.
        """
        provider = self.get_provider()
        if not provider:
            raise RuntimeError("No active LLM providers configured.")
            
        provider_config = self.config.providers[self.active_provider_name]
        
        # Rate limit check
        if not await self.rate_limiter.acquire(self.active_provider_name, provider_config.rate_limit_rpm):
            return "Error: Rate limit exceeded."
            
        # Caching logic
        # Simple cache key based on prompt and provider
        cache_key = f"{self.active_provider_name}:{hash(str(messages))}"
        if use_cache:
            cached = await self.rate_limiter.get_cached(cache_key)
            if cached:
                return cached
                
        try:
            # Generation
            response = await provider.generate(messages)
            filtered = SecurityManager.filter_output(response)
            
            if use_cache:
                await self.rate_limiter.set_cached(cache_key, filtered)
                
            return filtered
            
        except Exception as e:
            logger.error(f"LLM Generation failed: {e}")
            raise
