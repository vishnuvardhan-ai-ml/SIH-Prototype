from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="SIH Risk Prediction API", version="1.0.0")

# --- Health Check Endpoint ---
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "SIH Backend"}

# --- API Contracts (Pydantic Models) ---
class ProjectData(BaseModel):
    project_type: str
    land_area: int
    affected_families: int
    legal_disputes: int
    pending_approvals: int
    compensation_percent: int
    rr_progress_percent: int
    possession_percent: int

class RiskFactor(BaseModel):
    factor: str
    impact: int

class Recommendation(BaseModel):
    priority: str
    action: str

class PredictionResponse(BaseModel):
    project_id: str
    delay_probability: float
    risk_score: int
    risk_category: str
    predicted_delay_days: int
    risk_factors: List[RiskFactor]
    recommendations: List[Recommendation]

# --- Mock Prediction Endpoint ---
@app.post("/api/predict-risk", response_model=PredictionResponse)
async def predict_risk(data: ProjectData):
    # MOCK DATA: To be replaced by your trained ML model later
    return {
        "project_id": "LA-MOCK-001",
        "delay_probability": 0.87,
        "risk_score": 87,
        "risk_category": "CRITICAL",
        "predicted_delay_days": 74,
        "risk_factors": [
            {"factor": "Legal disputes", "impact": 24},
            {"factor": "Pending approvals", "impact": 19}
        ],
        "recommendations": [
            {"priority": "HIGH", "action": "Prioritize unresolved legal cases"}
        ]
    }