"""
Main API router that aggregates all endpoint routers.
"""
from fastapi import APIRouter

from app.api import chat, library, processing, news, databank, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["Chat"]
)

api_router.include_router(
    library.router,
    prefix="/reports",
    tags=["Library"]
)

api_router.include_router(
    processing.router,
    prefix="/admin",
    tags=["Processing"]
)

api_router.include_router(
    news.router,
    prefix="/news",
    tags=["News"]
)

api_router.include_router(
    databank.router,
    prefix="/databank",
    tags=["Data Bank"]
)

api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"]
)
