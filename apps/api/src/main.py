import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import settings
from src.api.v1.router import api_v1_router

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
    return {
        "status": "healthy",
        "service": "srmap-sage-api",
        "version": "1.0.0",
        "provider": settings.LLM_PROVIDER
    }
