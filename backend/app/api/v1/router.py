from fastapi import APIRouter
from .endpoints import health, analyze

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])
