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
        
    asyncio.run(run_test())
