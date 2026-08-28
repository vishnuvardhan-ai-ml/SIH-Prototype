"""
Health Check API Router.
"""
from fastapi import APIRouter
from backend.app.schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse, summary="System Health Check")
async def health_check():
    """
    Returns the operational status and service name of the backend.
    """
    return {"status": "ok", "service": "SIH Backend"}
