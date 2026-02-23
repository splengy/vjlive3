import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from vjlive3.llm.providers.openai import OpenAIProvider
from vjlive3.llm.providers.anthropic import AnthropicProvider
from vjlive3.llm.providers.local import LocalProvider

@pytest.fixture
def test_messages():
    return [{"role": "system", "content": "You are a VJ"}, {"role": "user", "content": "Make it red"}]

@patch("vjlive3.llm.providers.openai.httpx.AsyncClient")
def test_openai_provider(mock_client_class, test_messages):
    async def run_test():
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"choices": [{"message": {"content": "Success!"}}]})
        mock_client.post.return_value = mock_response
        
        provider = OpenAIProvider(api_key="test-key", model_name="gpt-4o", max_tokens=100, temperature=0.7)
        assert provider.provider_name == "openai"
        res = await provider.generate(test_messages)
        assert res == "Success!"
        
    asyncio.run(run_test())

@patch("vjlive3.llm.providers.anthropic.httpx.AsyncClient")
def test_anthropic_provider(mock_client_class, test_messages):
    async def run_test():
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"content": [{"text": "Anthropic Success!"}]})
        mock_client.post.return_value = mock_response
        
        provider = AnthropicProvider(api_key="test-key", model_name="claude", max_tokens=100, temperature=0.7)
        assert provider.provider_name == "anthropic"
        res = await provider.generate(test_messages)
        assert res == "Anthropic Success!"
        
    asyncio.run(run_test())

@patch("vjlive3.llm.providers.local.httpx.AsyncClient")
def test_local_provider(mock_client_class, test_messages):
    async def run_test():
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = MagicMock(return_value={"message": {"content": "Local Success!"}})
        mock_client.post.return_value = mock_response
        
        provider = LocalProvider(api_key="", model_name="mistral", max_tokens=100, temperature=0.7)
        assert provider.provider_name == "local"
        res = await provider.generate(test_messages)
        assert res == "Local Success!"
        
    asyncio.run(run_test())
