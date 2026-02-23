import json
import logging
from typing import Dict, Any

from vjlive3.llm.providers.base import LLMProvider
from vjlive3.llm.utils import LLMUtils, safe_async_call

logger = logging.getLogger(__name__)

class CrowdAnalysisAggregator:
    """Analyzes crowd audio features to determine crowd emotion and energy."""
    
    def __init__(self, service_ref):
        self.service = service_ref
        
    @safe_async_call(fallback_return={"mood": "neutral", "energy": 0.5})
    async def analyze_crowd_state(self, audio_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses LLM to interpret raw audio features into crowd mood and energy.
        Normally, a lightweight sentiment model is best here, or just basic heuristics,
        but the spec mandates LLM integration for intelligent crowd analysis.
        """
        system_prompt = (
            "You are an expert VJ crowd analyst. Given audio features (RMS volume, EQ bands, beat frequency), "
            "determine the crowd's current mood and energy level. "
            "Return ONLY valid JSON with 'mood' (string: e.g. hype, chill, building) and 'energy' (float 0.0-1.0)."
        )
        
        provider = self.service.get_provider()
        if not provider:
            logger.warning("No LLM provider available for crowd analysis.")
            return {"mood": "neutral", "energy": 0.5}
            
        messages = LLMUtils.build_prompt(system_prompt, str(audio_features))
        
        # In a real scenario, we might want a structured output format strictly enforced
        response_text = await provider.generate(messages)
        
        try:
            # Clean up potential markdown code block artifacts
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)
            return {"mood": result.get("mood", "neutral"), "energy": float(result.get("energy", 0.5))}
        except Exception as e:
            logger.error(f"Failed to parse crowd analysis response: {response_text}, Error: {e}")
            return {"mood": "neutral", "energy": 0.5}
