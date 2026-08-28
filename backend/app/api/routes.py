"""
Main API Router aggregating all endpoint routes.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Query, status
from backend.app.api import health
from backend.app.schemas.prediction import ProjectData, PredictionResponse
from backend.app.services.prediction_service import PredictionService
from backend.app.database.crud import get_latest_assessments, get_analytics_summary

api_router = APIRouter()

# Include health router
api_router.include_router(health.router)


@api_router.post(
    "/predict-risk",
    response_model=PredictionResponse,
    tags=["Prediction & Decision Support"],
    summary="Predict Land Acquisition Risk, Delay, SHAP Factors, and Mitigation Actions",
    status_code=status.HTTP_200_OK,
)
async def predict_risk(data: ProjectData):
    """
    Evaluates project parameters using the trained Machine Learning ensemble,
    computes local SHAP explainability feature attributions, generates prioritized
    mitigation strategies, and logs the assessment to the audit database.
    """
    return PredictionService.evaluate_project_risk(data)


@api_router.get(
    "/projects",
    tags=["Project History & Auditing"],
    summary="Retrieve Historical Project Assessments",
    status_code=status.HTTP_200_OK,
)
async def get_projects(limit: int = Query(50, ge=1, le=100, description="Max records to return")):
    """
    Fetches recent project evaluations including computed risk scores, SHAP factors, and recommendations.
    """
    return get_latest_assessments(limit=limit)


@api_router.get(
    "/analytics/summary",
    tags=["Analytics Dashboard"],
    summary="Aggregate Portfolio Risk Metrics and Category Distributions",
    status_code=status.HTTP_200_OK,
)
async def get_summary_analytics():
    """
    Returns aggregate summary statistics across all evaluated infrastructure projects.
    """
    return get_analytics_summary()
