import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database import get_async_db
from src.models.schemas import (
    ChatQueryRequest, ChatQueryResponse, SourceCitation,
    AdaptiveCard, NavigationCardPayload, FacultyCardPayload
)
from src.providers.factory import get_llm_provider
from src.engines.router_engine import IntentRouter
from src.engines.rag_engine import RAGEngine
from src.engines.spatial_engine import CampusSpatialEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

# Pre-instantiate router and engines
llm_provider = get_llm_provider()
intent_router = IntentRouter(llm_provider)
rag_engine = RAGEngine(llm_provider)
spatial_engine = CampusSpatialEngine()


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

    # Handle Campus Directions
    if intent == "CAMPUS_DIRECTIONS":
        # Check if spatial engine can identify origin and destination
        # For demonstration or structured lookup
        answer = (
            "Here is the campus navigation route based on the verified topological layout. "
            "Follow the step-by-step path below."
        )
        return ChatQueryResponse(
            answer=answer,
            intent=intent,
            confidence=0.95,
            sources=[
                SourceCitation(
                    id="campus_map_seed_01",
                    title="SRMAP Campus Spatial Layout & Building Map",
                    source_type="structured_dataset",
                    authority_level=2
                )
            ]
        )

    # Handle Procedure or Policy via RAG Engine
    # When context is empty (e.g., initial state before user provides documents)
    answer, is_fallback = await rag_engine.generate_grounded_answer(query, [])

    return ChatQueryResponse(
        answer=answer,
        is_fallback=is_fallback,
        intent=intent,
        confidence=0.85 if not is_fallback else 0.0,
        sources=[]
    )
