import pytest
import asyncio
from unittest.mock import Mock

from vjlive3.llm.suggestions import AISuggestionEngine
from vjlive3.llm.providers.base import LLMProvider

def test_suggestions_success():
    async def run_test():
        class MockProvider(LLMProvider):
            @property
            def provider_name(self): return "mock"
            async def generate(self, messages):
                return '{"effects": ["strobe", "color_shift"], "transition": "fade", "description": "Going hard"}'
            async def validate_connection(self): return True
            
        service = Mock()
        service.get_provider.return_value = MockProvider(api_key="", model_name="", max_tokens=100, temperature=0.7)
        
        engine = AISuggestionEngine(service)
        
        crowd_state = {"mood": "hype", "energy": 0.9}
        current_fx = ["tunnel"]
        
        result = await engine.generate_suggestions(crowd_state, current_fx)
        
        assert len(result["effects"]) == 2
        assert result["transition"] == "fade"
        assert result["description"] == "Going hard"
        
    asyncio.run(run_test())

def test_suggestions_no_provider():
    async def run_test():
        service = Mock()
        service.get_provider.return_value = None
        
        engine = AISuggestionEngine(service)
        result = await engine.generate_suggestions({}, [])
        
        assert result["effects"] == ["default"]
        assert result["transition"] == "cut"
        
    asyncio.run(run_test())

def test_suggestions_json_parse_error():
    async def run_test():
        class MockProviderError(LLMProvider):
            @property
            def provider_name(self): return "mock"
            async def generate(self, messages):
                return 'invalid json {'
            async def validate_connection(self): return True
            
        service = Mock()
        service.get_provider.return_value = MockProviderError(api_key="", model_name="", max_tokens=100, temperature=0.7)
        
        engine = AISuggestionEngine(service)
        result = await engine.generate_suggestions({}, [])
        assert result["description"] == "Parse failure fallback"
        
    asyncio.run(run_test())

