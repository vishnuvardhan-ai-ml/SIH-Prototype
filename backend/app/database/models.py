"""
Database Domain Models and DTOs.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class AssessmentFactorModel:
    factor_name: str
    impact_score: int
    direction: Optional[str] = "increases_risk"
    id: Optional[int] = None
    assessment_id: Optional[int] = None


@dataclass
class AssessmentRecommendationModel:
    priority: str
    action_text: str
    id: Optional[int] = None
    assessment_id: Optional[int] = None


@dataclass
class AssessmentRecord:
    project_code: str
    project_type: str
    land_area: float
    affected_families: int
    legal_disputes: int
    pending_approvals: int
    compensation_percent: float
    rr_progress_percent: float
    possession_percent: float
    delay_probability: float
    risk_score: int
    risk_category: str
    predicted_delay_days: int
    id: Optional[int] = None
    created_at: Optional[str] = None
    factors: List[AssessmentFactorModel] = field(default_factory=list)
    recommendations: List[AssessmentRecommendationModel] = field(default_factory=list)


@dataclass
class ProjectModel:
    project_code: str
    project_name: str
    project_type: str
    id: Optional[int] = None
    created_at: Optional[str] = None
