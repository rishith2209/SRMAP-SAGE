from fastapi import APIRouter
from src.api.v1.endpoints.chat import router as chat_router
from src.api.v1.endpoints.faculty import router as faculty_router
from src.api.v1.endpoints.campus import router as campus_router
from src.api.v1.endpoints.feedback import router as feedback_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(chat_router)
api_v1_router.include_router(faculty_router)
api_v1_router.include_router(campus_router)
api_v1_router.include_router(feedback_router)
