"""
SRMAP SAGE — Intent & Query Router Engine
Multi-engine routing across Document RAG, Structured SQL, Spatial Graph, Live Web, Calendar, and Fee engines.
Supports fine-grained intent classification and hybrid query decomposition.
"""

import re
from typing import Dict, List, Any, Optional
from src.providers.base_provider import BaseLLMProvider


class IntentRouter:
    """
    Classifies student inquiries into specific knowledge domains and routes
    them to the appropriate engine (Document RAG, Structured SQL, Spatial, Live Web, Fee, Calendar).
    """

    PATTERNS = {
        # Navigation & Spatial
        "CAMPUS_DIRECTIONS": [
            r"\b(how do i go|how to go|how to reach|directions to|route to|where is block|where is hostel|way to)\b",
            r"\b(from .+ to .+|nearest (medical|canteen|library|washroom|clinic))\b",
            r"\b(where is the library|how to get to library|how do i reach)\b"
        ],
        # Faculty & Department
        "FACULTY_LOOKUP": [
            r"\b(where is prof|where is professor|where is dr|cabin of|office of|contact prof|faculty|hod of)\b",
            r"\b(who is teaching|who teaches|faculty member|professor [a-z]+)\b"
        ],
        "DEPARTMENT_LOOKUP": [
            r"\b(where is the [a-z]+ department|head of [a-z]+ department|dept of [a-z]+|department of [a-z]+)\b"
        ],
        # Academic & Procedures
        "PROCEDURE_FORM": [
            r"\b(how do i apply|how to apply|procedure for|steps? to apply|application process|form for|download form)\b",
            r"\b(medical leave|od leave|on duty|hostel leave|scholarship application)\b"
        ],
        "ATTENDANCE_POLICY": [
            r"\b(attendance requirement|minimum attendance|attendance percentage|condonation|shortage of attendance)\b"
        ],
        "PLACEMENT_QUERY": [
            r"\b(placement|placed|highest package|average package|ctc|recruited|recruiting companies|tcs|amazon|google)\b",
            r"\b(placement statistics|placement policy|eligibility for placements)\b"
        ],
        "RESEARCH_POLICY": [
            r"\b(urop|undergraduate research|seed funding|sponsored research|consultancy rules)\b"
        ],
        "INTERNSHIP_POLICY": [
            r"\b(internship policy|student internship|professional internship|summer internship)\b"
        ],
        # Calendar & Milestones
        "ACADEMIC_CALENDAR": [
            r"\b(academic calendar|semester start|classes begin|mid[- ]semester exam|end semester exam dates|holiday list|exam dates)\b",
            r"\b(when do classes start|when are exams|calendar 2026)\b"
        ],
        # Fees & Charges
        "FEE_QUERY": [
            r"\b(fee structure|tuition fee|hostel fee|exam fee|registration fee|annual fee|cost of b\.?tech|fee for)\b"
        ],
        # Events & Activities
        "CURRENT_EVENT": [
            r"\b(happening this week|upcoming events|cultural fest|hackathon|seminar today|notices today|robotics workshop|event)\b"
        ],
        # Hostel & Facilities
        "HOSTEL_FACILITIES": [
            r"\b(hostel room|ac sharing|hostel accommodation|curfew timing|hostel warden)\b"
        ],
        "GENERAL_POLICY": [
            r"\b(code of conduct|anti[- ]ragging|disciplinary rules|recruitment policy)\b"
        ]
    }

    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider

    def classify_fast(self, query: str) -> str:
        """Rule-based fast classification for minimal latency."""
        q = query.lower()

        # Check hybrid patterns first
        is_nav = any(re.search(p, q) for p in self.PATTERNS["CAMPUS_DIRECTIONS"])
        is_fac = any(re.search(p, q) for p in self.PATTERNS["FACULTY_LOOKUP"])
        is_proc = any(re.search(p, q) for p in self.PATTERNS["PROCEDURE_FORM"])
        is_place = any(re.search(p, q) for p in self.PATTERNS["PLACEMENT_QUERY"])
        is_event = any(re.search(p, q) for p in self.PATTERNS["CURRENT_EVENT"])
        is_cal = any(re.search(p, q) for p in self.PATTERNS["ACADEMIC_CALENDAR"])
        is_fee = any(re.search(p, q) for p in self.PATTERNS["FEE_QUERY"])

        # Preserve legacy aliases for existing tests
        if is_proc:
            return "PROCEDURE_FORM"
        if is_fac:
            return "FACULTY_LOOKUP"
        if is_nav:
            return "CAMPUS_DIRECTIONS"
        if is_place:
            return "PLACEMENT_QUERY"
        if is_event:
            return "CURRENT_EVENT"
        if is_cal:
            return "ACADEMIC_CALENDAR"
        if is_fee:
            return "FEE_QUERY"

        for intent, patterns in self.PATTERNS.items():
            for p in patterns:
                if re.search(p, q):
                    if intent == "ATTENDANCE_POLICY" or intent == "GENERAL_POLICY" or intent == "RESEARCH_POLICY":
                        return "ACADEMIC_POLICY"
                    return intent

        return "ACADEMIC_POLICY"

    def detect_hybrid_subintents(self, query: str) -> List[str]:
        """Detects whether query spans multiple knowledge engines."""
        q = query.lower()
        subintents = []

        if any(k in q for k in ["policy", "rule", "attendance", "urop", "internship", "regulations"]):
            subintents.append("POLICY")
        if any(k in q for k in ["faculty", "prof", "professor", "dr ", "dr.", "cabin"]):
            subintents.append("FACULTY")
        if any(k in q for k in ["placement", "company", "package", "crcs"]):
            subintents.append("PLACEMENT")
        if any(k in q for k in ["where is", "how do i go", "how to reach", "directions", "location", "office located"]):
            subintents.append("SPATIAL")
        if any(k in q for k in ["notice", "announcement", "event", "workshop"]):
            subintents.append("EVENT")
        if any(k in q for k in ["fee", "cost", "tuition"]):
            subintents.append("FEES")
        if any(k in q for k in ["calendar", "exam date", "semester start"]):
            subintents.append("CALENDAR")

        return subintents if len(subintents) > 1 else []

    async def classify(self, query: str) -> Dict[str, Any]:
        """Full intent classification with hybrid query support."""
        fast_intent = self.classify_fast(query)
        hybrid_subintents = self.detect_hybrid_subintents(query)

        is_hybrid = len(hybrid_subintents) > 1

        return {
            "intent": fast_intent,
            "is_hybrid": is_hybrid,
            "subintents": hybrid_subintents,
            "requires_fresh_web": fast_intent in ["CURRENT_EVENT", "PLACEMENT_QUERY"],
            "engines": self._map_intent_to_engines(fast_intent, hybrid_subintents)
        }

    def _map_intent_to_engines(self, intent: str, hybrid_subintents: List[str] = None) -> List[str]:
        if hybrid_subintents:
            engines = set()
            for s in hybrid_subintents:
                if s == "POLICY":
                    engines.add("document_rag")
                elif s == "FACULTY":
                    engines.add("faculty_engine")
                elif s == "SPATIAL":
                    engines.add("spatial_engine")
                elif s == "PLACEMENT":
                    engines.add("document_rag")
                    engines.add("live_web")
                elif s == "EVENT":
                    engines.add("events_engine")
                    engines.add("live_web")
                elif s == "FEES":
                    engines.add("fee_engine")
                elif s == "CALENDAR":
                    engines.add("calendar_engine")
            return list(engines)

        mapping = {
            "PROCEDURE_FORM": ["document_rag", "sources_catalog"],
            "FACULTY_LOOKUP": ["faculty_engine"],
            "DEPARTMENT_LOOKUP": ["faculty_engine", "spatial_engine"],
            "CAMPUS_DIRECTIONS": ["spatial_engine"],
            "PLACEMENT_QUERY": ["document_rag", "live_web"],
            "CURRENT_EVENT": ["events_engine", "live_web"],
            "ACADEMIC_CALENDAR": ["calendar_engine", "document_rag"],
            "FEE_QUERY": ["fee_engine"],
            "ACADEMIC_POLICY": ["document_rag"]
        }
        return mapping.get(intent, ["document_rag"])
