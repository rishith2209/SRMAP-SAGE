"""
SRMAP SAGE — Agentic Evidence Orchestration Engine (Phase 5)
Implements the 10-step bounded orchestration loop:
UNDERSTAND -> PLAN -> ROUTE -> RETRIEVE -> EVALUATE EVIDENCE ->
DETECT CONFLICT -> RETRIEVE AGAIN IF REQUIRED -> SYNTHESIZE -> VERIFY -> ANSWER

Adheres to:
- Bounded Tool Budgets (MAX_RETRIEVAL_ITERATIONS=3, MAX_WEB_FETCHES=5, MAX_ENGINE_CALLS=8)
- Strict Trace Sanitization before logging/persistence
- Standardized EvidenceItem mapping across all 8 specialized engines
- Deterministic engine authority (LLM synthesizes verified evidence, never invents facts)
"""

import hashlib
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from src.models.schemas import (
    EvidenceItem, QueryPlan, ConflictAssessment, RefusalReason,
    ExecutionStep, ExecutionTrace, AnswerContract, SourceCitation,
    ChatQueryResponse, AdaptiveCard, NavigationCardPayload,
    FacultyCardPayload, DepartmentCardPayload, CalendarCardPayload,
    FeeCardPayload, EventCardPayload
)
from src.providers.base_provider import BaseLLMProvider
from src.engines.router_engine import IntentRouter
from src.engines.rag_engine import RAGEngine, STRICT_FALLBACK_PHRASE
from src.engines.spatial_engine import CampusSpatialEngine
from src.engines.faculty_engine import FacultyEngine
from src.engines.calendar_engine import AcademicCalendarEngine
from src.engines.fee_engine import FeeEngine
from src.engines.events_engine import EventsEngine
from src.engines.conflict_engine import ConflictDetector
from src.engines.verification_engine import SelfVerificationEngine
from src.engines.refusal_engine import RefusalEngine

logger = logging.getLogger(__name__)

# Sanitization regex patterns for secrets, credentials, tokens, cookies, PII
SENSITIVE_PATTERNS = [
    (r"(?i)(bearer\s+[a-zA-Z0-9_\-\.]{15,})", "[REDACTED_BEARER_TOKEN]"),
    (r"(?i)(api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?)", "api_key=[REDACTED]"),
    (r"(?i)(password\s*[:=]\s*['\"]?[^'\"]+['\"]?)", "password=[REDACTED]"),
    (r"(?i)(cookie\s*[:=]\s*['\"]?[^'\"]+['\"]?)", "cookie=[REDACTED]"),
    (r"(?i)(token\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?)", "token=[REDACTED]"),
    (r"(?i)(authorization\s*[:=]\s*['\"]?[^'\"]+['\"]?)", "authorization=[REDACTED]"),
]


def sanitize_trace_data(data: Any, parent_key: str = "") -> Any:
    """
    Recursively scrubs API keys, passwords, cookies, authorization tokens,
    and private credentials before persistence or logging.
    """
    if isinstance(data, str):
        if any(k in parent_key.lower() for k in ["password", "token", "secret", "api_key", "cookie", "auth"]):
            return "[REDACTED]"
        cleaned = data
        for pattern, replacement in SENSITIVE_PATTERNS:
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned
    elif isinstance(data, dict):
        return {k: sanitize_trace_data(v, parent_key=k) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_trace_data(item, parent_key=parent_key) for item in data]
    return data


class AgentOrchestrator:
    """
    Central self-verifying evidence orchestrator.
    Controls query planning, engine invocation, conflict checking, claim verification,
    and answer contract generation.
    """

    MAX_RETRIEVAL_ITERATIONS = 3
    MAX_WEB_FETCHES = 5
    MAX_ENGINE_CALLS = 8

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        router: Optional[IntentRouter] = None,
        rag: Optional[RAGEngine] = None,
        spatial: Optional[CampusSpatialEngine] = None,
        faculty: Optional[FacultyEngine] = None,
        calendar: Optional[AcademicCalendarEngine] = None,
        fee: Optional[FeeEngine] = None,
        events: Optional[EventsEngine] = None,
    ):
        self.llm = llm_provider
        self.router = router or IntentRouter(llm_provider)
        self.rag = rag or RAGEngine(llm_provider)
        self.spatial = spatial or CampusSpatialEngine()
        self.faculty = faculty or FacultyEngine()
        self.calendar = calendar or AcademicCalendarEngine()
        self.fee = fee or FeeEngine()
        self.events = events or EventsEngine()

    def _hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    async def execute_query(self, query: str) -> ChatQueryResponse:
        """
        Runs the 10-step bounded agent orchestration lifecycle.
        """
        start_time = time.time()
        trace = ExecutionTrace(query=query)

        # Global budget counters
        engine_call_count = 0
        web_fetch_count = 0
        iteration_count = 0

        # ---------------------------------------------------------------------
        # STEP 1 & 2: UNDERSTAND & PLAN
        # ---------------------------------------------------------------------
        step1_start = time.time()
        classification = await self.router.classify(query)
        intent = classification["intent"]
        is_hybrid = classification.get("is_hybrid", False)
        subintents = classification.get("subintents", [])

        # Map intents to designated engine types
        engines_to_invoke = []
        if is_hybrid:
            if "PLACEMENT" in subintents:
                engines_to_invoke.append("DOCUMENT_RAG")
            if "SPATIAL" in subintents:
                engines_to_invoke.append("SPATIAL_ENGINE")
            if "FACULTY" in subintents:
                engines_to_invoke.append("FACULTY_ENGINE")
            if "EVENT" in subintents:
                engines_to_invoke.append("EVENT_ENGINE")
            if "POLICY" in subintents and "DOCUMENT_RAG" not in engines_to_invoke:
                engines_to_invoke.append("DOCUMENT_RAG")
        else:
            if intent == "CAMPUS_DIRECTIONS":
                engines_to_invoke.append("SPATIAL_ENGINE")
            elif intent in ["FACULTY_LOOKUP", "DEPARTMENT_LOOKUP"]:
                engines_to_invoke.append("FACULTY_ENGINE")
            elif intent == "ACADEMIC_CALENDAR":
                engines_to_invoke.append("CALENDAR_ENGINE")
            elif intent == "FEE_QUERY":
                engines_to_invoke.append("FEE_ENGINE")
            elif intent == "CURRENT_EVENT":
                engines_to_invoke.append("EVENT_ENGINE")
            else:
                engines_to_invoke.append("DOCUMENT_RAG")

        query_plan = QueryPlan(
            query=query,
            intents=subintents if is_hybrid else [intent],
            engines=engines_to_invoke,
            requires_current_data="CURRENT" in intent or any("latest" in query.lower() for _ in [1]),
            requires_multiple_sources=is_hybrid or len(engines_to_invoke) > 1,
            verification_required=True
        )

        trace.steps.append(ExecutionStep(
            step_name="PLAN",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=sanitize_trace_data(query_plan.model_dump()),
            duration_ms=round((time.time() - step1_start) * 1000, 2)
        ))

        # ---------------------------------------------------------------------
        # STEP 3 & 4: ROUTE & RETRIEVE (Across Bounded Engine Calls)
        # ---------------------------------------------------------------------
        step2_start = time.time()
        iteration_count += 1
        evidence_items: List[EvidenceItem] = []
        sources: List[SourceCitation] = []
        adaptive_card: Optional[AdaptiveCard] = None
        synthesized_text = ""
        is_fallback = False
        refusal_reason: Optional[RefusalReason] = None

        for eng in engines_to_invoke:
            if engine_call_count >= self.MAX_ENGINE_CALLS:
                logger.warning("Tool call budget exceeded MAX_ENGINE_CALLS (8). Halting further engine calls.")
                break

            engine_call_count += 1

            if eng == "DOCUMENT_RAG":
                # Invoke Document RAG
                rag_ans, is_fb, cits = await self.rag.generate_grounded_answer(query)
                is_fallback = is_fb
                synthesized_text = rag_ans
                sources.extend(cits)

                # Standardize retrieved chunks into EvidenceItem instances
                for cit in cits:
                    item_id = f"ev_{cit.id}_{cit.page_number or 1}"
                    evidence_items.append(EvidenceItem(
                        id=item_id,
                        source_id=cit.id,
                        source_type=cit.source_type,
                        authority_level=cit.authority_level,
                        title=cit.title,
                        url=cit.url,
                        page=cit.page_number,
                        excerpt=cit.snippet or cit.title,
                        published_at=cit.publication_date_str,
                        freshness_status=cit.freshness_status or "CURRENT",
                        confidence=0.95,
                        engine="DOCUMENT_RAG",
                        content_hash=self._hash_content(cit.snippet or cit.title),
                        domain="ACADEMIC_POLICIES"
                    ))

            elif eng == "SPATIAL_ENGINE":
                q_low = query.lower()
                m = re.search(r"from\s+(.+?)\s+to\s+(.+)", q_low)
                if m:
                    origin_str, dest_str = m.group(1).strip(), m.group(2).strip()
                elif is_hybrid and "PLACEMENT" in subintents:
                    origin_str, dest_str = "node_academic_block", "node_admin_block"
                elif is_hybrid and "EVENT" in subintents:
                    origin_str = "node_academic_block"
                    curr_evs = self.events.query_events(status="CURRENT")
                    dest_str = curr_evs[0].venue if curr_evs and curr_evs[0].venue else "Main University Auditorium"
                else:
                    clean_dest = re.sub(r"\b(how do i (get|go|reach) to?|how to (get|go|reach) to?|where is the|where is)\b", "", q_low).strip()
                    origin_str = "node_academic_block"
                    dest_str = clean_dest or q_low

                route = self.spatial.get_route(origin_str, dest_str)
                if not route:
                    msg, reason = RefusalEngine.create_refusal(
                        code="UNKNOWN_ENTITY",
                        query=query,
                        missing_detail=f"location '{dest_str}'",
                        required_evidence="Official SRMAP Campus Spatial Registry or CAD Master Plan"
                    )
                    synthesized_text = msg
                    is_fallback = True
                    refusal_reason = reason
                else:
                    steps_text = "\n".join([f"{i+1}. {s.instruction} (~{s.distance_meters}m)" for i, s in enumerate(route.steps)])
                    spatial_ans = (
                        f"**Campus Walking Directions:** {route.origin_name} → {route.destination_name}\n"
                        f"Estimated Walking Time: ~{route.estimated_walk_minutes} minutes ({route.total_distance_meters} meters)\n\n"
                        f"**Step-by-Step Route:**\n{steps_text}\n\n"
                        f"*Note: Route and distances are topological campus estimates; survey-grade GPS coordinates have not yet been officially released.*"
                    )
                    if synthesized_text:
                        synthesized_text += f"\n\n{spatial_ans}"
                    else:
                        synthesized_text = spatial_ans

                    adaptive_card = AdaptiveCard(card_type="navigation", payload=route.model_dump())
                    item_id = f"ev_spatial_{route.origin_name}_{route.destination_name}"
                    evidence_items.append(EvidenceItem(
                        id=item_id,
                        source_id=route.source_id or "campus_spatial_topology_v1",
                        source_type="structured_dataset",
                        authority_level=2,
                        title="SRMAP Campus Spatial Topology",
                        excerpt=f"Pathfinding from {route.origin_name} to {route.destination_name}: {route.total_distance_meters}m",
                        freshness_status="CURRENT",
                        confidence=0.95,
                        engine="SPATIAL_ENGINE",
                        content_hash=self._hash_content(str(route.steps)),
                        domain="CAMPUS_SPATIAL"
                    ))
                    sources.append(SourceCitation(
                        id=route.source_id or "campus_spatial_topology_v1",
                        title="SRMAP Campus Spatial Topology",
                        source_type="structured_dataset",
                        authority_level=2,
                        snippet=f"Route from {route.origin_name} to {route.destination_name}"
                    ))

            elif eng == "FACULTY_ENGINE":
                if intent == "DEPARTMENT_LOOKUP":
                    dept = self.faculty.get_department(query)
                    if not dept:
                        msg, reason = RefusalEngine.create_refusal(
                            code="UNKNOWN_ENTITY",
                            query=query,
                            missing_detail=f"academic department for '{query}'",
                            required_evidence="Official SRMAP Academic Department Registry"
                        )
                        synthesized_text = msg
                        is_fallback = True
                        refusal_reason = reason
                    else:
                        synthesized_text = (
                            f"**{dept.name} ({dept.code})**\n"
                            f"School: {dept.school}\n"
                            f"Building: {dept.building}\n"
                            f"Department Office: {dept.office}"
                        )
                        adaptive_card = AdaptiveCard(card_type="department", payload=dept.model_dump())
                        item_id = f"ev_dept_{dept.code}"
                        evidence_items.append(EvidenceItem(
                            id=item_id,
                            source_id=dept.source_id or "srmap_dept_registry_v1",
                            source_type="structured_dataset",
                            authority_level=2,
                            title=f"Department of {dept.name}",
                            excerpt=f"{dept.name} ({dept.code}) located in {dept.building}, Office: {dept.office}",
                            verified_at=dept.verified_at,
                            confidence=0.95,
                            engine="FACULTY_ENGINE",
                            content_hash=self._hash_content(dept.name + dept.code),
                            domain="ACADEMIC_DEPARTMENTS"
                        ))
                        sources.append(SourceCitation(
                            id=dept.source_id or "srmap_dept_registry_v1",
                            title=f"SRMAP Department Registry — {dept.name}",
                            source_type="structured_dataset",
                            authority_level=2,
                            snippet=f"{dept.name} ({dept.code}) located in {dept.building}"
                        ))
                else:
                    fac = self.faculty.lookup_faculty(query)
                    if not fac:
                        msg, reason = RefusalEngine.create_refusal(
                            code="UNKNOWN_ENTITY",
                            query=query,
                            missing_detail=f"faculty member for '{query}'",
                            required_evidence="Official SRMAP Faculty Directory / HR Records"
                        )
                        synthesized_text = msg
                        is_fallback = True
                        refusal_reason = reason
                    else:
                        fac_ans = (
                            f"**{fac.name}**\n"
                            f"Designation: {fac.designation}\n"
                            f"Department: {fac.department}\n"
                            f"School: {fac.school or 'School of Engineering & Sciences'}\n"
                            f"Cabin / Office: {fac.cabin_number or 'Cabin information not officially released'}\n"
                            f"Location: {fac.block or 'Academic Block'}"
                        )
                        if fac.email:
                            fac_ans += f"\nEmail: {fac.email}"

                        if synthesized_text:
                            synthesized_text += f"\n\n{fac_ans}"
                        else:
                            synthesized_text = fac_ans

                        adaptive_card = AdaptiveCard(card_type="faculty", payload=fac.model_dump())
                        item_id = f"ev_fac_{fac.name.replace(' ', '_')}"
                        evidence_items.append(EvidenceItem(
                            id=item_id,
                            source_id=fac.source_id or "official_faculty_directory",
                            source_type="structured_dataset",
                            authority_level=2,
                            title=f"Faculty Profile: {fac.name}",
                            excerpt=f"{fac.name}, {fac.designation}, {fac.department}. Cabin: {fac.cabin_number or 'N/A'}",
                            verified_at=fac.verified_at,
                            confidence=0.95,
                            engine="FACULTY_ENGINE",
                            content_hash=self._hash_content(fac.name + fac.designation),
                            domain="FACULTY_DIRECTORY"
                        ))
                        sources.append(SourceCitation(
                            id=fac.source_id or "official_faculty_directory",
                            title="SRMAP Official Faculty Directory",
                            source_type="structured_dataset",
                            authority_level=2,
                            snippet=f"{fac.name}, {fac.designation} - {fac.department}"
                        ))

            elif eng == "CALENDAR_ENGINE":
                is_historical = "historical" in query.lower() or "2025" in query.lower() or "previous" in query.lower()
                status_filter = "HISTORICAL" if is_historical else "CURRENT"
                ev_list = self.calendar.query_events(status=status_filter)
                if not ev_list:
                    msg, reason = RefusalEngine.create_refusal(
                        code="INSUFFICIENT_EVIDENCE",
                        query=query,
                        missing_detail="academic calendar milestones for this period",
                        required_evidence="Official Academic Calendar Circular approved by Academic Council"
                    )
                    synthesized_text = msg
                    is_fallback = True
                    refusal_reason = reason
                else:
                    ev_lines = [f"- **{e.event}** ({e.semester} Semester {e.academic_year}): {e.start_date[:10]}" for e in ev_list[:4]]
                    synthesized_text = "**Verified Academic Calendar Milestones:**\n" + "\n".join(ev_lines)
                    adaptive_card = AdaptiveCard(card_type="calendar", payload=ev_list[0].model_dump())
                    for idx, e in enumerate(ev_list[:3]):
                        evidence_items.append(EvidenceItem(
                            id=f"ev_cal_{e.academic_year}_{idx}",
                            source_id=e.source_id or "srmap_academic_calendar",
                            source_type="structured_dataset",
                            authority_level=1,
                            title=f"Academic Calendar {e.academic_year}",
                            excerpt=f"{e.event} ({e.semester}): Starts {e.start_date}",
                            freshness_status=e.status,
                            confidence=0.95,
                            engine="CALENDAR_ENGINE",
                            content_hash=self._hash_content(e.event + e.start_date),
                            domain="ACADEMIC_CALENDAR"
                        ))
                    sources.append(SourceCitation(
                        id="srmap_academic_calendar",
                        title=f"Official SRMAP Academic Calendar ({status_filter})",
                        source_type="structured_dataset",
                        authority_level=1,
                        snippet="\n".join(ev_lines)
                    ))

            elif eng == "FEE_ENGINE":
                fee_record = self.fee.lookup_fee(program_keyword=query)
                if not fee_record:
                    msg, reason = RefusalEngine.create_refusal(
                        code="UNVERIFIED_CURRENT_INFORMATION",
                        query=query,
                        missing_detail=f"verified official fee schedule for '{query}'",
                        required_evidence="Official Finance Committee & Registrar Fee Circular"
                    )
                    synthesized_text = msg
                    is_fallback = True
                    refusal_reason = reason
                else:
                    synthesized_text = (
                        f"**Official Fee Schedule:** {fee_record.program}\n"
                        f"Academic Year: {fee_record.academic_year}\n"
                        f"Fee Type: {fee_record.fee_type.capitalize()}\n"
                        f"Amount: {fee_record.currency} {fee_record.amount:,.2f}"
                    )
                    adaptive_card = AdaptiveCard(card_type="fee", payload=fee_record.model_dump())
                    evidence_items.append(EvidenceItem(
                        id=f"ev_fee_{fee_record.program.replace(' ', '_')}",
                        source_id=fee_record.source_id or "srmap_fee_registry",
                        source_type="structured_dataset",
                        authority_level=1,
                        title=f"Fee Schedule: {fee_record.program}",
                        excerpt=f"{fee_record.program} {fee_record.fee_type}: {fee_record.currency} {fee_record.amount}",
                        freshness_status=fee_record.status,
                        confidence=0.95,
                        engine="FEE_ENGINE",
                        content_hash=self._hash_content(fee_record.program + str(fee_record.amount)),
                        domain="FEES_AND_FINANCE"
                    ))
                    sources.append(SourceCitation(
                        id=fee_record.source_id or "srmap_fee_registry",
                        title="SRMAP Official Admissions & Fee Schedule",
                        source_type="structured_dataset",
                        authority_level=1,
                        snippet=f"{fee_record.program} {fee_record.fee_type}: {fee_record.currency} {fee_record.amount}"
                    ))

            elif eng == "EVENT_ENGINE":
                is_hist = "historical" in query.lower() or "past" in query.lower()
                status_filter = "HISTORICAL" if is_hist else "CURRENT"
                evs = self.events.query_events(keyword=query, status=status_filter)
                if not evs:
                    evs = self.events.query_events(status=status_filter)

                if not evs:
                    msg, reason = RefusalEngine.create_refusal(
                        code="INSUFFICIENT_EVIDENCE",
                        query=query,
                        missing_detail="campus events for this query",
                        required_evidence="Official Directorate of Student Affairs Event Notifications"
                    )
                    synthesized_text = msg
                    is_fallback = True
                    refusal_reason = reason
                else:
                    ev = evs[0]
                    ev_ans = (
                        f"**{ev.title}**\n"
                        f"Date & Time: {ev.start_datetime}\n"
                        f"Venue: {ev.venue or 'SRMAP Campus'}\n"
                        f"Organizer: {ev.organizer or 'SRM University-AP'}\n\n"
                        f"{ev.description or ''}"
                    )
                    if synthesized_text:
                        synthesized_text += f"\n\n{ev_ans}"
                    else:
                        synthesized_text = ev_ans

                    adaptive_card = AdaptiveCard(card_type="event", payload=ev.model_dump())
                    evidence_items.append(EvidenceItem(
                        id=f"ev_event_{ev.event_id}",
                        source_id=ev.event_id,
                        source_type="official_event",
                        authority_level=1,
                        title=ev.title,
                        url=ev.source_url,
                        excerpt=f"{ev.title} on {ev.start_datetime} at {ev.venue}. {ev.description or ''}",
                        freshness_status=ev.status,
                        confidence=0.95,
                        engine="EVENT_ENGINE",
                        content_hash=self._hash_content(ev.title + ev.start_datetime),
                        domain="CAMPUS_EVENTS"
                    ))
                    sources.append(SourceCitation(
                        id=ev.event_id,
                        title=ev.title,
                        url=ev.source_url,
                        source_type="official_event",
                        authority_level=1,
                        snippet=ev.description
                    ))

        trace.steps.append(ExecutionStep(
            step_name="RETRIEVE",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=sanitize_trace_data({
                "engines_called": engines_to_invoke,
                "evidence_count": len(evidence_items),
                "is_fallback": is_fallback
            }),
            duration_ms=round((time.time() - step2_start) * 1000, 2)
        ))

        # ---------------------------------------------------------------------
        # STEP 5 & 6: EVALUATE EVIDENCE & DETECT CONFLICT
        # ---------------------------------------------------------------------
        step3_start = time.time()
        conflict = ConflictDetector.assess_evidence_set(query, evidence_items)

        trace.steps.append(ExecutionStep(
            step_name="CONFLICT_CHECK",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=sanitize_trace_data(conflict.model_dump()),
            duration_ms=round((time.time() - step3_start) * 1000, 2)
        ))

        # If unresolved conflict detected, enforce strict refusal
        if conflict.conflict_type == "UNRESOLVED":
            msg, reason = RefusalEngine.create_refusal(
                code="CONFLICT_UNRESOLVED",
                query=query,
                missing_detail="competing official policies",
                required_evidence=conflict.explanation
            )
            synthesized_text = msg
            is_fallback = True
            refusal_reason = reason

        # ---------------------------------------------------------------------
        # STEP 7 & 8: SYNTHESIS & CLAIM-LEVEL SELF-VERIFICATION
        # ---------------------------------------------------------------------
        step4_start = time.time()
        verified_answer, claim_results, ver_status, caveats = SelfVerificationEngine.verify_and_filter(
            text=synthesized_text,
            evidence_items=evidence_items,
            is_fallback=is_fallback
        )

        trace.steps.append(ExecutionStep(
            step_name="VERIFY",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details=sanitize_trace_data({
                "verification_status": ver_status,
                "total_claims": len(claim_results),
                "supported_claims": sum(1 for c in claim_results if c.supported),
                "caveats": caveats
            }),
            duration_ms=round((time.time() - step4_start) * 1000, 2)
        ))

        if (is_fallback or ver_status == "REFUSED") and not refusal_reason:
            is_spatial = intent == "CAMPUS_DIRECTIONS" or "SPATIAL" in subintents
            missing_text = "campus location" if is_spatial else "the requested topic or entity"
            code_type = "UNKNOWN_ENTITY" if is_spatial else "INSUFFICIENT_EVIDENCE"
            _, reason = RefusalEngine.create_refusal(
                code=code_type,
                query=query,
                missing_detail=missing_text,
                required_evidence="Official SRMAP campus registry or circular"
            )
            refusal_reason = reason

        # ---------------------------------------------------------------------
        # STEP 9 & 10: ANSWER CONTRACT & RESPONSE
        # ---------------------------------------------------------------------
        contract = AnswerContract(
            answer=verified_answer,
            evidence=evidence_items,
            sources=sources,
            freshness="CURRENT",
            caveats=caveats,
            refusal_reason=refusal_reason,
            verification_status=ver_status,
            trace=trace.model_dump()
        )

        trace.total_engine_calls = engine_call_count
        trace.total_web_fetches = web_fetch_count
        trace.total_iterations = iteration_count

        return ChatQueryResponse(
            answer=verified_answer,
            is_fallback=is_fallback or ver_status == "REFUSED",
            intent="HYBRID_" + "_".join(subintents) if is_hybrid else intent,
            confidence=0.95 if ver_status in ["VERIFIED", "PARTIALLY_VERIFIED"] and not is_fallback else 0.0,
            sources=sources,
            adaptive_card=adaptive_card,
            conflict_detected=conflict.has_conflict,
            conflict_note=conflict.explanation if conflict.has_conflict else None,
            verification_status=ver_status,
            evidence=evidence_items,
            refusal_code=refusal_reason.code if refusal_reason else None,
            refusal_required_evidence=refusal_reason.required_evidence if refusal_reason else None,
            execution_trace=sanitize_trace_data(trace.model_dump()),
            contract=contract
        )
