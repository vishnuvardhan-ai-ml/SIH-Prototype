"""
Prediction & Risk Assessment Schemas.
"""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    HIGHWAY = "Highway"
    RAILWAY = "Railway"
    URBAN_INFRA = "Urban Infrastructure"
    ENERGY_POWER = "Energy & Power"
    INDUSTRIAL_CORRIDOR = "Industrial Corridor"


class ProjectData(BaseModel):
    project_type: str = Field(..., description="Category of infrastructure project (e.g. Highway, Railway)", examples=["Highway"])
    land_area: int = Field(..., ge=1, description="Total land area in acres", examples=[150])
    affected_families: int = Field(..., ge=0, description="Total number of families affected by acquisition", examples=[320])
    legal_disputes: int = Field(..., ge=0, description="Count of active court cases or legal disputes", examples=[4])
    pending_approvals: int = Field(..., ge=0, description="Count of pending statutory / environmental clearances", examples=[2])
    compensation_percent: int = Field(..., ge=0, le=100, description="Percentage of compensation disbursed to land owners (0-100)", examples=[65])
    rr_progress_percent: int = Field(..., ge=0, le=100, description="Rehabilitation and Resettlement progress percentage (0-100)", examples=[50])
    possession_percent: int = Field(..., ge=0, le=100, description="Percentage of physical land possession acquired (0-100)", examples=[60])


class RiskFactor(BaseModel):
    factor: str = Field(..., examples=["Legal disputes"])
    impact: int = Field(..., examples=[24], description="Relative percentage or impact weight of this factor")
    direction: Optional[str] = Field(None, examples=["increases_risk"], description="Direction of contribution")


class Recommendation(BaseModel):
    priority: str = Field(..., examples=["HIGH"], description="Priority level: HIGH, MEDIUM, LOW")
    action: str = Field(..., examples=["Prioritize unresolved legal cases via fast-track settlement tribunals"])


class PredictionResponse(BaseModel):
    project_id: str = Field(..., examples=["LA-MOCK-001"])
    delay_probability: float = Field(..., ge=0.0, le=1.0, examples=[0.87], description="Estimated probability of project delay (0.0 - 1.0)")
    risk_score: int = Field(..., ge=0, le=100, examples=[87], description="Composite risk score from 0 to 100")
    risk_category: str = Field(..., examples=["CRITICAL"], description="Risk classification: LOW, MEDIUM, HIGH, CRITICAL")
    predicted_delay_days: int = Field(..., ge=0, examples=[74], description="Estimated timeline overrun in days")
    risk_factors: List[RiskFactor] = Field(default_factory=list, description="Top factors contributing to the risk assessment")
    recommendations: List[Recommendation] = Field(default_factory=list, description="Actionable mitigation strategies")
