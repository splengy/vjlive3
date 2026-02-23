import pytest
import asyncio
from unittest.mock import patch

from vjlive3.llm.config import LLMConfig
from vjlive3.llm.service import LLMService

@pytest.fixture(autouse=True)
def reset_service_singleton():
    LLMService._instance = None
    yield

def test_service_initialization():
    config = LLMConfig()
    config.providers["openai"].api_key = "dummy"
    config.providers["anthropic"].api_key = "dummy"
    service = LLMService(config)
    assert service.active_provider_name == "openai"
    assert "openai" in service.providers
    assert "anthropic" in service.providers

def test_service_switch_provider():
    config = LLMConfig()
    config.providers["openai"].api_key = "dummy"
    config.providers["anthropic"].api_key = "dummy"
    service = LLMService(config)
    
    assert service.switch_provider("anthropic") is True
    assert service.active_provider_name == "anthropic"
    
    assert service.switch_provider("invalid") is False
    assert service.active_provider_name == "anthropic"

@patch("vjlive3.llm.providers.openai.OpenAIProvider.generate")
def test_service_generate(mock_generate):
    async def run_test():
        config = LLMConfig()
        config.providers["openai"].api_key = "dummy"
        mock_generate.return_value = "Generated text"
        service = LLMService(config)
        
        # Test basic generation (uses cache if available)
        res1 = await service.generate([{"role": "user", "content": "hi"}], use_cache=False)
        assert res1 == "Generated text"
        
        # Test rate limit triggers
        service.config.providers["openai"].rate_limit_rpm = 1
        res2 = await service.generate([{"role": "user", "content": "hi2"}], use_cache=False)
        assert res2 == "Error: Rate limit exceeded."
        
        # Test cache hit
        # We need to manually set the cache for res1's cache_key
        service.config.providers["openai"].rate_limit_rpm = 200
        cache_key = f"{service.active_provider_name}:{hash(str([{'role': 'user', 'content': 'hi'}]))}"
        await service.rate_limiter.set_cached(cache_key, "Cached text")
        res3 = await service.generate([{"role": "user", "content": "hi"}], use_cache=True)
        assert res3 == "Cached text"
        
        # Test exception in generate
        mock_generate.side_effect = Exception("API failure")
        with pytest.raises(Exception):
            await service.generate([{"role": "user", "content": "fail"}], use_cache=False)
        
    asyncio.run(run_test())

def test_service_singleton_reinit():
    config = LLMConfig()
    service1 = LLMService(config)
    
    config2 = LLMConfig()
    service2 = LLMService(config2)  # Should return instance without re-initializing
    
    assert service1 is service2

def test_service_no_providers():
    config = LLMConfig()
    # Disable all so no providers are added
    for p in config.providers.values():
        p.enabled = False
        
    service = LLMService(config)
    assert not service.providers
    
    async def run_test():
        with pytest.raises(RuntimeError):
            await service.generate([{"role": "user", "content": "fail"}])
            
    asyncio.run(run_test())

def test_service_fallback_provider():
    config = LLMConfig()
    config.default_provider = "missing"
    config.providers["openai"].api_key = "dummy"
    config.providers["anthropic"].enabled = False
    
    service = LLMService(config)
    # the default is 'missing' which is not in the dict, it should fall back to openai
    assert service.active_provider_name == "openai"

