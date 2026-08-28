"""
Tests for Machine Learning Service, SHAP Explainability, and Recommendation Engine.
"""
import pytest
import numpy as np
from backend.app.schemas.prediction import ProjectData
from backend.app.services.prediction_service import PredictionService
from backend.app.services.recommendation_service import RecommendationEngine
from backend.app.ml.loader import model_manager


def test_model_manager_loading():
    """Verify that model artifacts load into memory properly."""
    preprocessor, classifier, regressor, explainer = model_manager.get_models()
    assert preprocessor is not None
    assert classifier is not None
    assert regressor is not None
    assert explainer is not None


def test_prediction_service_end_to_end():
    """Verify full prediction pipeline computation."""
    data = ProjectData(
        project_type="Highway",
        land_area=200,
        affected_families=350,
        legal_disputes=6,
        pending_approvals=3,
        compensation_percent=40,
        rr_progress_percent=35,
        possession_percent=30,
    )
    result = PredictionService.evaluate_project_risk(data)

    assert result.project_id.startswith("PRJ-LA-")
    assert 0.0 <= result.delay_probability <= 1.0
    assert 0 <= result.risk_score <= 100
    assert result.risk_category in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert result.predicted_delay_days >= 0
    assert len(result.risk_factors) >= 1
    assert len(result.recommendations) >= 1

    # Check factor structure
    for factor in result.risk_factors:
        assert isinstance(factor.factor, str)
        assert factor.impact > 0
        assert factor.direction in ["increases_risk", "decreases_risk"]


def test_recommendation_engine_rule_branching():
    """Verify domain rules produce expected recommendations under severe conditions."""
    high_risk_data = ProjectData(
        project_type="Urban Infrastructure",
        land_area=80,
        affected_families=600,
        legal_disputes=8,
        pending_approvals=4,
        compensation_percent=30,
        rr_progress_percent=20,
        possession_percent=15,
    )
    recs = RecommendationEngine.generate_recommendations(
        data=high_risk_data,
        risk_score=90,
        risk_category="CRITICAL",
        risk_factors=[],
    )

    priorities = [r.priority for r in recs]
    assert "HIGH" in priorities
    assert any("tribunal" in r.action.lower() or "larra" in r.action.lower() for r in recs)
    assert any("pmg" in r.action.lower() or "statutory" in r.action.lower() for r in recs)
