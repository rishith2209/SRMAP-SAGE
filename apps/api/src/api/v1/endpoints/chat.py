"""
SRMAP SAGE — Unified Multi-Engine Chat & Query Orchestrator
Routes queries dynamically across:
- Document RAG Engine (Policies, Regulations, Handbooks)
- Structured Faculty & Department Engine
- Campus Spatial & Navigation Graph Engine
- Structured Academic Calendar Engine
- Structured Fee Engine
- Structured Events Engine
- Hybrid Multi-Engine Aggregator
"""

import logging
import re
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_db
from src.models.schemas import (
    ChatQueryRequest, ChatQueryResponse, SourceCitation,
    AdaptiveCard, NavigationCardPayload, FacultyCardPayload,
    DepartmentCardPayload, CalendarCardPayload, FeeCardPayload,
    EventCardPayload, PolicyCardPayload
)
from src.providers.factory import get_llm_provider
from src.engines.router_engine import IntentRouter
from src.engines.rag_engine import RAGEngine, STRICT_FALLBACK_PHRASE
from src.engines.spatial_engine import CampusSpatialEngine
from src.engines.faculty_engine import FacultyEngine
from src.engines.calendar_engine import AcademicCalendarEngine
from src.engines.fee_engine import FeeEngine
from src.engines.events_engine import EventsEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Pre-instantiate router and engines
llm_provider = get_llm_provider()
intent_router = IntentRouter(llm_provider)
rag_engine = RAGEngine(llm_provider)
spatial_engine = CampusSpatialEngine()
faculty_engine = FacultyEngine()
calendar_engine = AcademicCalendarEngine()
fee_engine = FeeEngine()
events_engine = EventsEngine()


@router.post("/query", response_model=ChatQueryResponse)
async def handle_query(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    classification = await intent_router.classify(query)
    intent = classification["intent"]
    is_hybrid = classification.get("is_hybrid", False)
    subintents = classification.get("subintents", [])

    # =========================================================================
    # 1. HYBRID QUERY ORCHESTRATION
    # =========================================================================
    if is_hybrid:
        combined_answers = []
        combined_citations: List[SourceCitation] = []
        adaptive_card: Optional[AdaptiveCard] = None

        # A. Policy + Spatial / Location (e.g. Placement policy + placement office location)
        if "PLACEMENT" in subintents and "SPATIAL" in subintents:
            rag_ans, is_fb, cits = await rag_engine.generate_grounded_answer(query)
            route = spatial_engine.get_route("node_academic_block", "node_admin_block")
            combined_answers.append(rag_ans)
            combined_citations.extend(cits)
            if route:
                combined_answers.append(
                    f"\n\n**Office Location:** The Corporate Relations & Career Services (CRCS) office is located in the "
                    f"Administrative Block. (Walking distance: ~{route.total_distance_meters}m from Academic Block)."
                )
                adaptive_card = AdaptiveCard(card_type="navigation", payload=route.model_dump())
                combined_citations.append(
                    SourceCitation(
                        id="campus_spatial_topology_v1",
                        title="SRMAP Campus Spatial Topology",
                        source_type="structured_dataset",
                        authority_level=2,
                        snippet="CRCS Placement Office is in Administrative Block Ground Floor."
                    )
                )
            return ChatQueryResponse(
                answer="\n".join(combined_answers),
                is_fallback=is_fb,
                intent="HYBRID_PLACEMENT_SPATIAL",
                confidence=0.95,
                sources=combined_citations,
                adaptive_card=adaptive_card
            )

        # B. Policy + Faculty (e.g. UROP policy + faculty coordinator)
        if "POLICY" in subintents and "FACULTY" in subintents:
            rag_ans, is_fb, cits = await rag_engine.generate_grounded_answer(query)
            combined_answers.append(rag_ans)
            combined_citations.extend(cits)
            # Check if coordinator is designated in official document
            combined_answers.append(
                "\n\n**Faculty Supervision Note:** Under SRMAP UROP Policy, students must register under a faculty supervisor "
                "from their respective department. Individual faculty cabin details must be confirmed with the department office."
            )
            return ChatQueryResponse(
                answer="\n".join(combined_answers),
                is_fallback=is_fb,
                intent="HYBRID_POLICY_FACULTY",
                confidence=0.92,
                sources=combined_citations
            )

        # C. Event / Notice + Spatial (e.g. latest notice + venue location)
        if "EVENT" in subintents and "SPATIAL" in subintents:
            events = events_engine.query_events(status="CURRENT")
            if events:
                ev = events[0]
                venue_name = ev.venue or "Main Auditorium"
                dest_node = spatial_engine.find_node_by_keyword(venue_name) or "node_academic_block"
                route = spatial_engine.get_route("node_academic_block", dest_node)
                ans = f"**{ev.title}**\nDate: {ev.start_datetime}\nVenue: {ev.venue}\nOrganizer: {ev.organizer}"
                if route:
                    ans += f"\n\n**Route to Venue:** {route.steps[0].instruction if route.steps else 'Follow academic concourse.'}"
                return ChatQueryResponse(
                    answer=ans,
                    intent="HYBRID_EVENT_SPATIAL",
                    confidence=0.95,
                    sources=[
                        SourceCitation(
                            id=ev.event_id,
                            title=ev.title,
                            url=ev.source_url,
                            source_type="official_event",
                            authority_level=1,
                            snippet=ev.description
                        )
                    ],
                    adaptive_card=AdaptiveCard(card_type="event", payload=ev.model_dump())
                )

    # =========================================================================
    # 2. CAMPUS SPATIAL & NAVIGATION
    # =========================================================================
    if intent == "CAMPUS_DIRECTIONS":
        # Extract origin and destination
        q_low = query.lower()
        m = re.search(r"from\s+(.+?)\s+to\s+(.+)", q_low)
        if m:
            origin_str, dest_str = m.group(1).strip(), m.group(2).strip()
        else:
            origin_str = "node_academic_block"
            dest_str = q_low

        route = spatial_engine.get_route(origin_str, dest_str)
        if not route:
            return ChatQueryResponse(
                answer=f"{STRICT_FALLBACK_PHRASE} I couldn't verify this campus location in the official spatial database.",
                is_fallback=True,
                intent=intent,
                confidence=0.0,
                sources=[]
            )

        steps_text = "\n".join([f"{i+1}. {s.instruction} (~{s.distance_meters}m)" for i, s in enumerate(route.steps)])
        answer = (
            f"**Campus Walking Directions:** {route.origin_name} → {route.destination_name}\n"
            f"Estimated Walking Time: ~{route.estimated_walk_minutes} minutes ({route.total_distance_meters} meters)\n\n"
            f"**Step-by-Step Route:**\n{steps_text}\n\n"
            f"*Note: Route and distances are topological campus estimates; survey-grade GPS coordinates have not yet been officially released.*"
        )
        return ChatQueryResponse(
            answer=answer,
            intent=intent,
            confidence=0.95,
            sources=[
                SourceCitation(
                    id=route.source_id or "campus_spatial_topology_v1",
                    title="SRMAP Campus Spatial Topology Layout",
                    source_type="structured_dataset",
                    authority_level=2,
                    snippet=f"Pathfinding from {route.origin_name} to {route.destination_name}"
                )
            ],
            adaptive_card=AdaptiveCard(card_type="navigation", payload=route.model_dump())
        )

    # =========================================================================
    # 3. FACULTY & CABIN DIRECTORY
    # =========================================================================
    if intent == "FACULTY_LOOKUP":
        fac = faculty_engine.lookup_faculty(query)
        if not fac:
            return ChatQueryResponse(
                answer=f"{STRICT_FALLBACK_PHRASE} The requested faculty or cabin information is not documented in any verified university directory.",
                is_fallback=True,
                intent=intent,
                confidence=0.0,
                sources=[]
            )

        answer = (
            f"**{fac.name}**\n"
            f"Designation: {fac.designation}\n"
            f"Department: {fac.department}\n"
            f"School: {fac.school or 'School of Engineering & Sciences'}\n"
            f"Cabin / Office: {fac.cabin_number or 'Cabin information not officially released'}\n"
            f"Location: {fac.block or 'Academic Block'}"
        )
        if fac.email:
            answer += f"\nEmail: {fac.email}"

        return ChatQueryResponse(
            answer=answer,
            intent=intent,
            confidence=0.95,
            sources=[
                SourceCitation(
                    id=fac.source_id or "official_faculty_directory",
                    title="SRMAP Official Faculty Directory",
                    url=fac.profile_url,
                    source_type="structured_dataset",
                    authority_level=2,
                    snippet=f"{fac.name}, {fac.designation} - {fac.department}"
                )
            ],
            adaptive_card=AdaptiveCard(card_type="faculty", payload=fac.model_dump())
        )

    # =========================================================================
    # 4. DEPARTMENT DIRECTORY
    # =========================================================================
    if intent == "DEPARTMENT_LOOKUP":
        dept = faculty_engine.get_department(query)
        if not dept:
            return ChatQueryResponse(
                answer=f"{STRICT_FALLBACK_PHRASE} The requested academic department is not documented in the verified department registry.",
                is_fallback=True,
                intent=intent,
                confidence=0.0,
                sources=[]
            )

        answer = (
            f"**{dept.name} ({dept.code})**\n"
            f"School: {dept.school}\n"
            f"Building: {dept.building}\n"
            f"Department Office: {dept.office}"
        )
        return ChatQueryResponse(
            answer=answer,
            intent=intent,
            confidence=0.95,
            sources=[
                SourceCitation(
                    id=dept.source_id or "srmap_dept_registry_v1",
                    title="SRMAP Department Registry",
                    source_type="structured_dataset",
                    authority_level=2,
                    snippet=f"{dept.name} ({dept.code}) located in {dept.building}"
                )
            ],
            adaptive_card=AdaptiveCard(card_type="department", payload=dept.model_dump())
        )

    # =========================================================================
    # 5. ACADEMIC CALENDAR
    # =========================================================================
    if intent == "ACADEMIC_CALENDAR":
        events = calendar_engine.query_events()
        if not events:
            return ChatQueryResponse(
                answer=f"{STRICT_FALLBACK_PHRASE} No verified academic calendar events are currently on record for this query.",
                is_fallback=True,
                intent=intent,
                confidence=0.0,
                sources=[]
            )

        ev_lines = [f"- **{e.event}** ({e.semester} Semester {e.academic_year}): {e.start_date[:10]}" for e in events[:4]]
        answer = "**Verified Academic Calendar Milestones:**\n" + "\n".join(ev_lines)
        return ChatQueryResponse(
            answer=answer,
            intent=intent,
            confidence=0.95,
            sources=[
                SourceCitation(
                    id="srmap_academic_calendar",
                    title="Official SRMAP Academic Calendar 2026-27",
                    source_type="structured_dataset",
                    authority_level=1,
                    snippet="\n".join(ev_lines)
                )
            ],
            adaptive_card=AdaptiveCard(card_type="calendar", payload=events[0].model_dump())
        )

    # =========================================================================
    # 6. FEE INQUIRIES
    # =========================================================================
    if intent == "FEE_QUERY":
        fee = fee_engine.lookup_fee(program_keyword=query)
        if not fee:
            return ChatQueryResponse(
                answer=f"{STRICT_FALLBACK_PHRASE} I don't have a verified official fee schedule for this category.",
                is_fallback=True,
                intent=intent,
                confidence=0.0,
                sources=[]
            )

        answer = (
            f"**Official Fee Schedule:** {fee.program}\n"
            f"Academic Year: {fee.academic_year}\n"
            f"Fee Type: {fee.fee_type.capitalize()}\n"
            f"Amount: {fee.currency} {fee.amount:,.2f}"
        )
        return ChatQueryResponse(
            answer=answer,
            intent=intent,
            confidence=0.95,
            sources=[
                SourceCitation(
                    id=fee.source_id or "srmap_fee_registry",
                    title="SRMAP Official Admissions & Fee Schedule",
                    source_type="structured_dataset",
                    authority_level=1,
                    snippet=f"{fee.program} {fee.fee_type}: {fee.currency} {fee.amount}"
                )
            ],
            adaptive_card=AdaptiveCard(card_type="fee", payload=fee.model_dump())
        )

    # =========================================================================
    # 7. CAMPUS EVENTS
    # =========================================================================
    if intent == "CURRENT_EVENT":
        events = events_engine.query_events(keyword=query)
        if not events:
            events = events_engine.query_events(status="CURRENT")

        if events:
            ev = events[0]
            answer = (
                f"**{ev.title}**\n"
                f"Date & Time: {ev.start_datetime}\n"
                f"Venue: {ev.venue or 'SRMAP Campus'}\n"
                f"Organizer: {ev.organizer or 'SRM University-AP'}\n\n"
                f"{ev.description or ''}"
            )
            return ChatQueryResponse(
                answer=answer,
                intent=intent,
                confidence=0.95,
                sources=[
                    SourceCitation(
                        id=ev.event_id,
                        title=ev.title,
                        url=ev.source_url,
                        source_type="official_event",
                        authority_level=1,
                        snippet=ev.description
                    )
                ],
                adaptive_card=AdaptiveCard(card_type="event", payload=ev.model_dump())
            )

    # =========================================================================
    # 8. DEFAULT: GROUNDED DOCUMENT RAG ENGINE
    # =========================================================================
    answer, is_fallback, citations = await rag_engine.generate_grounded_answer(query)

    return ChatQueryResponse(
        answer=answer,
        is_fallback=is_fallback,
        intent=intent,
        confidence=0.95 if not is_fallback else 0.0,
        sources=citations
    )
