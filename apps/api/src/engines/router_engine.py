import re
from typing import Dict, Any
from src.providers.base_provider import BaseLLMProvider


class IntentRouter:
    """
    Classifies student inquiries into specific knowledge domains and routes
    them to the appropriate engine (Document RAG, Structured SQL, Spatial, Live Web).
    """

    PATTERNS = {
        "CAMPUS_DIRECTIONS": [
            r"\b(how do i go|how to go|how to reach|directions to|route to|where is block|where is hostel|way to)\b",
            r"\b(from .+ to .+|nearest (medical|canteen|library|washroom|clinic))\b"
        ],
        "FACULTY_LOOKUP": [
            r"\b(where is prof|where is professor|where is dr|cabin of|office of|contact prof|faculty|hod of)\b",
            r"\b(who is teaching|who teaches|faculty member)\b"
        ],
        "PROCEDURE_FORM": [
            r"\b(how do i apply|how to apply|procedure for|steps? to apply|application process|form for|download form)\b",
            r"\b(medical leave|od leave|on duty|hostel leave|scholarship application)\b"
        ],
        "PLACEMENT_QUERY": [
            r"\b(placement|placed|highest package|average package|ctc|recruited|recruiting companies|tcs|amazon|google)\b",
            r"\b(placement statistics|placement policy|eligibility for placements)\b"
        ],
        "CURRENT_EVENT": [
            r"\b(happening this week|upcoming events|cultural fest|hackathon|seminar today|notices today)\b"
        ]
    }

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def classify_fast(self, query: str) -> str:
        """Rule-based fast classification for minimal latency."""
        q = query.lower()
        for intent, patterns in self.PATTERNS.items():
            for p in patterns:
                if re.search(p, q):
                    return intent
        return "ACADEMIC_POLICY"

    async def classify(self, query: str) -> Dict[str, Any]:
        """Full intent classification with reasoning and target extraction."""
        fast_intent = self.classify_fast(query)
        
        return {
            "intent": fast_intent,
            "requires_fresh_web": fast_intent == "CURRENT_EVENT",
            "engines": self._map_intent_to_engines(fast_intent)
        }

    def _map_intent_to_engines(self, intent: str) -> list[str]:
        mapping = {
            "PROCEDURE_FORM": ["document_rag", "sources_catalog"],
            "FACULTY_LOOKUP": ["structured_sql", "spatial_graph"],
            "CAMPUS_DIRECTIONS": ["spatial_graph"],
            "PLACEMENT_QUERY": ["structured_sql", "document_rag"],
            "CURRENT_EVENT": ["live_web", "document_rag"],
            "ACADEMIC_POLICY": ["document_rag"]
        }
        return mapping.get(intent, ["document_rag"])
