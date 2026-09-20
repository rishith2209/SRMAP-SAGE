"""
SRMAP SAGE — Unified Agentic Evidence Orchestrator Endpoint (Phase 5)
Orchestrates student inquiries across:
- Document RAG Engine (Policies, Regulations, Handbooks)
- Structured Faculty & Department Engine
- Campus Spatial & Navigation Graph Engine
- Structured Academic Calendar Engine
- Structured Fee Engine
- Structured Events Engine
- Semantic Conflict Detection & Claim-Level Self-Verification
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_db
from src.models.schemas import ChatQueryRequest, ChatQueryResponse
from src.providers.factory import get_llm_provider
from src.engines.router_engine import IntentRouter
from src.engines.rag_engine import RAGEngine
from src.engines.spatial_engine import CampusSpatialEngine
from src.engines.faculty_engine import FacultyEngine
from src.engines.calendar_engine import AcademicCalendarEngine
from src.engines.fee_engine import FeeEngine
from src.engines.events_engine import EventsEngine
from src.engines.orchestrator import AgentOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Pre-instantiate provider, specialized engines, and central agent orchestrator
llm_provider = get_llm_provider()
intent_router = IntentRouter(llm_provider)
rag_engine = RAGEngine(llm_provider)
spatial_engine = CampusSpatialEngine()
faculty_engine = FacultyEngine()
calendar_engine = AcademicCalendarEngine()
fee_engine = FeeEngine()
events_engine = EventsEngine()

orchestrator = AgentOrchestrator(
    llm_provider=llm_provider,
    router=intent_router,
    rag=rag_engine,
    spatial=spatial_engine,
    faculty=faculty_engine,
    calendar=calendar_engine,
    fee=fee_engine,
    events=events_engine
)


@router.post("/query", response_model=ChatQueryResponse)
async def handle_query(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    return await orchestrator.execute_query(query)
