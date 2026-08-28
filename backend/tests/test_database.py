"""
Tests for SQLite Database Layer and CRUD operations.
"""
import pytest
from backend.app.database.session import init_db, get_db_connection
from backend.app.database.models import (
    AssessmentRecord,
    AssessmentFactorModel,
    AssessmentRecommendationModel,
)
from backend.app.database.crud import (
    create_or_get_project,
    save_assessment_record,
    get_latest_assessments,
    get_analytics_summary,
)


@pytest.fixture(autouse=True)
def setup_test_database():
    """Ensure clean database schema before tests."""
    init_db()


def test_create_and_get_project():
    """Verify creating a new project or retrieving an existing one."""
    project = create_or_get_project(
        project_code="PRJ-TEST-001",
        project_name="Mumbai-Ahmedabad Corridor Subsegment",
        project_type="Highway",
    )
    assert project.id is not None
    assert project.project_code == "PRJ-TEST-001"
    assert project.project_type == "Highway"

    # Duplicate fetch should return existing
    duplicate = create_or_get_project(
        project_code="PRJ-TEST-001",
        project_name="Different Name",
        project_type="Highway",
    )
    assert duplicate.id == project.id
    assert duplicate.project_name == "Mumbai-Ahmedabad Corridor Subsegment"


def test_save_and_retrieve_assessment_record():
    """Verify storing and querying assessments with child factors and recommendations."""
    assessment = AssessmentRecord(
        project_code="PRJ-TEST-002",
        project_type="Railway",
        land_area=250.0,
        affected_families=400,
        legal_disputes=5,
        pending_approvals=3,
        compensation_percent=55.0,
        rr_progress_percent=45.0,
        possession_percent=40.0,
        delay_probability=0.85,
        risk_score=82,
        risk_category="CRITICAL",
        predicted_delay_days=120,
        factors=[
            AssessmentFactorModel(factor_name="Legal disputes", impact_score=35, direction="increases_risk"),
            AssessmentFactorModel(factor_name="Compensation lag", impact_score=25, direction="increases_risk"),
        ],
        recommendations=[
            AssessmentRecommendationModel(priority="HIGH", action_text="Expedite legal hearings via tribunal"),
        ],
    )

    saved = save_assessment_record(assessment)
    assert saved.id is not None
    assert len(saved.factors) == 2
    assert len(saved.recommendations) == 1

    latest = get_latest_assessments(limit=10)
    assert len(latest) >= 1
    found = next((item for item in latest if item.project_code == "PRJ-TEST-002"), None)
    assert found is not None
    assert found.risk_category == "CRITICAL"
    assert len(found.factors) == 2
    assert len(found.recommendations) == 1


def test_analytics_summary():
    """Verify aggregated statistics computation."""
    summary = get_analytics_summary()
    assert "total_assessments" in summary
    assert "avg_risk_score" in summary
    assert "risk_distribution" in summary
    assert isinstance(summary["risk_distribution"], dict)
