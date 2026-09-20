import logging
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from src.core.config import settings
from src.core.database import async_session_factory
from src.api.v1.router import api_v1_router
from src.engines.orchestrator import sanitize_trace_data

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("srmap_sage")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing SRMAP SAGE backend...")
    logger.info(f"Active Model Provider: {settings.LLM_PROVIDER}")
    yield
    logger.info("Shutting down SRMAP SAGE backend.")


app = FastAPI(
    title="SRMAP SAGE API",
    description="Student Assistance & Guidance Engine for SRM University-AP",
    version="1.0.0",
    lifespan=lifespan
)

# Request Telemetry & Sanitized Observability Middleware
@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Process request
    response: Response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    # Attach diagnostic headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-MS"] = str(duration_ms)

    # Log sanitized telemetry (No secrets, tokens, PII)
    clean_path = sanitize_trace_data(str(request.url.path))
    logger.info(
        f"[REQ-{request_id}] {request.method} {clean_path} "
        f"-> Status: {response.status_code} ({duration_ms}ms)"
    )
    return response


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API v1 routes
app.include_router(api_v1_router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Liveness probe: verifies API process is alive and responsive."""
    return {
        "status": "healthy",
        "service": "srmap-sage-api",
        "version": "1.0.0",
        "provider": settings.LLM_PROVIDER
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe: verifies critical dependencies including database."""
    db_ok = True
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.warning(f"Readiness check database probe warning: {e}")
        db_ok = False

    if not db_ok:
        # Development fallback / graceful warning
        return {
            "status": "degraded",
            "service": "srmap-sage-api",
            "database": "disconnected_or_initializing",
            "ready": False
        }

    return {
        "status": "ready",
        "service": "srmap-sage-api",
        "database": "connected",
        "ready": True
    }

