from fastapi import APIRouter
from .endpoints import health, analyze, jobs, results

api_router = APIRouter()

# Health check
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Analysis job creation
api_router.include_router(analyze.router, prefix="/analyze", tags=["analyze"])

# Job status and management
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])

# Analysis results
api_router.include_router(results.router, prefix="/results", tags=["results"])
