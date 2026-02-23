import json
import logging
from typing import Dict, Any, List

from vjlive3.llm.utils import LLMUtils, safe_async_call

logger = logging.getLogger(__name__)

class AISuggestionEngine:
    """Generates visual suggestions based on crowd state and current visuals."""
    
    def __init__(self, service_ref):
        self.service = service_ref
        
    @safe_async_call(fallback_return={"effects": ["rgb_shift"], "transition": "fade", "description": "Safe default."})
    async def generate_suggestions(self, crowd_state: Dict[str, Any], current_effects: List[str]) -> Dict[str, Any]:
        """
        Suggests new effects and transitions based on the crowd.
        """
        system_prompt = (
            "You are an expert generative VJ assistant. Analyze the crowd state and suggest "
            "visual effects to play next, a transition style, and a short description of the intent. "
            "Return ONLY valid JSON with keys: 'effects' (list of strings), 'transition' (string), "
            "and 'description' (string)."
        )
        
        user_context = {
            "Crowd State": crowd_state,
            "Currently Playing Effects": current_effects
        }
        
        provider = self.service.get_provider()
        if not provider:
            logger.warning("No LLM provider available for suggestion engine.")
            return {"effects": ["default"], "transition": "cut", "description": "Fallback state"}
            
        messages = LLMUtils.build_prompt(system_prompt, "Generate next visual suggestions.", context=user_context)
        
        response_text = await provider.generate(messages)
        
        try:
            cleaned = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned)
            return {
                "effects": result.get("effects", []),
                "transition": result.get("transition", "cut"),
                "description": result.get("description", "")
            }
        except Exception as e:
            logger.error(f"Failed to parse suggestions response: {response_text}, Error: {e}")
            return {"effects": [], "transition": "cut", "description": "Parse failure fallback"}
