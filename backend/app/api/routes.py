"""
Main API Router aggregating all modular endpoint routers.
"""
from fastapi import APIRouter
from backend.app.api import health
from backend.app.schemas.prediction import ProjectData, PredictionResponse

api_router = APIRouter()

# Include health router under /api
api_router.include_router(health.router)


@api_router.post(
    "/predict-risk",
    response_model=PredictionResponse,
    tags=["Prediction"],
    summary="Predict Land Acquisition Delay & Risk"
)
async def predict_risk(data: ProjectData):
    """
    Placeholder prediction route until ML Service pipeline is integrated in Phase 12.
    """
    return {
        "project_id": "LA-MOCK-001",
        "delay_probability": 0.87,
        "risk_score": 87,
        "risk_category": "CRITICAL",
        "predicted_delay_days": 74,
        "risk_factors": [
            {"factor": "Legal disputes", "impact": 24, "direction": "increases_risk"},
            {"factor": "Pending approvals", "impact": 19, "direction": "increases_risk"}
        ],
        "recommendations": [
            {"priority": "HIGH", "action": "Prioritize unresolved legal cases via fast-track settlement tribunals"}
        ]
    }
