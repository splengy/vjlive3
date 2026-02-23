import pytest
import asyncio
from unittest.mock import Mock, patch

from vjlive3.llm.service import LLMService
from vjlive3.llm.crowd_analysis import CrowdAnalysisAggregator
from vjlive3.llm.providers.base import LLMProvider

def test_crowd_analysis_success():
    async def run_test():
        # Setup mock provider
        class MockProvider(LLMProvider):
            @property
            def provider_name(self): return "mock"
            async def generate(self, messages):
                return '{"mood": "hype", "energy": 0.85}'
            async def validate_connection(self): return True
            
        service = Mock()
        service.get_provider.return_value = MockProvider(api_key="", model_name="", max_tokens=100, temperature=0.7)
        
        aggregator = CrowdAnalysisAggregator(service)
        features = {"rms": 0.5, "bands": {"bass": 0.8}}
        
        result = await aggregator.analyze_crowd_state(features)
        
        assert result["mood"] == "hype"
        assert result["energy"] == 0.85
        
    asyncio.run(run_test())

def test_crowd_analysis_fallback_on_parse_error():
    async def run_test():
        class MockProvider(LLMProvider):
            @property
            def provider_name(self): return "mock"
            async def generate(self, messages):
                return 'This is not JSON!'
            async def validate_connection(self): return True
            
        service = Mock()
        service.get_provider.return_value = MockProvider(api_key="", model_name="", max_tokens=100, temperature=0.7)
        
        aggregator = CrowdAnalysisAggregator(service)
        result = await aggregator.analyze_crowd_state({"rms": 0.1})
        
        assert result["mood"] == "neutral"
        assert result["energy"] == 0.5
        
    asyncio.run(run_test())

def test_crowd_analysis_no_provider():
    async def run_test():
        service = Mock()
        service.get_provider.return_value = None
        
        aggregator = CrowdAnalysisAggregator(service)
        result = await aggregator.analyze_crowd_state({"rms": 0.1})
        
        assert result["mood"] == "neutral"
        assert result["energy"] == 0.5
        
    asyncio.run(run_test())
