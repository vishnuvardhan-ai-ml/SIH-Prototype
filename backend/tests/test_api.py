"""
Full End-to-End API Route Tests.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app
from backend.app.database.session import init_db


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


@pytest.mark.asyncio
async def test_full_predict_risk_flow():
    """Verify POST /api/predict-risk executes ML and saves to database."""
    transport = ASGITransport(app=app)
    payload = {
        "project_type": "Railway",
        "land_area": 300,
        "affected_families": 450,
        "legal_disputes": 5,
        "pending_approvals": 2,
        "compensation_percent": 50,
        "rr_progress_percent": 40,
        "possession_percent": 45
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/predict-risk", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "project_id" in data
        assert "delay_probability" in data
        assert "risk_score" in data
        assert len(data["risk_factors"]) > 0
        assert len(data["recommendations"]) > 0

        # Verify record appears in /api/projects
        projects_resp = await client.get("/api/projects?limit=5")
        assert projects_resp.status_code == 200
        projects = projects_resp.json()
        assert len(projects) >= 1
        assert any(p["project_code"] == data["project_id"] for p in projects)

        # Verify analytics endpoint reflects evaluation
        analytics_resp = await client.get("/api/analytics/summary")
        assert analytics_resp.status_code == 200
        analytics = analytics_resp.json()
        assert analytics["total_assessments"] >= 1
        assert "risk_distribution" in analytics


@pytest.mark.asyncio
async def test_invalid_negative_land_area():
    """Verify validation error when land_area is 0 or negative."""
    transport = ASGITransport(app=app)
    payload = {
        "project_type": "Highway",
        "land_area": 0,  # Invalid: must be >= 1
        "affected_families": 10,
        "legal_disputes": 0,
        "pending_approvals": 0,
        "compensation_percent": 100,
        "rr_progress_percent": 100,
        "possession_percent": 100
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/predict-risk", json=payload)
        assert response.status_code == 422
        error_json = response.json()
        assert error_json["error"]["type"] == "ValidationError"
