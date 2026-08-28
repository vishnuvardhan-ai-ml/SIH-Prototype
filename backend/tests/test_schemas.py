"""
Tests for Request Validation and Error Handling.
"""
import pytest
from httpx import ASGITransport, AsyncClient
from backend.app.main import app


@pytest.mark.asyncio
async def test_predict_risk_valid_payload():
    """
    Verify /api/predict-risk returns 200 with valid input.
    """
    transport = ASGITransport(app=app)
    valid_payload = {
        "project_type": "Highway",
        "land_area": 120,
        "affected_families": 250,
        "legal_disputes": 3,
        "pending_approvals": 2,
        "compensation_percent": 75,
        "rr_progress_percent": 60,
        "possession_percent": 70
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/predict-risk", json=valid_payload)

    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data
    assert "delay_probability" in data
    assert "risk_score" in data
    assert "risk_category" in data
    assert "predicted_delay_days" in data
    assert isinstance(data["risk_factors"], list)
    assert isinstance(data["recommendations"], list)


@pytest.mark.asyncio
async def test_predict_risk_invalid_percentage():
    """
    Verify /api/predict-risk returns 422 for out-of-range percentage.
    """
    transport = ASGITransport(app=app)
    invalid_payload = {
        "project_type": "Highway",
        "land_area": 120,
        "affected_families": 250,
        "legal_disputes": 3,
        "pending_approvals": 2,
        "compensation_percent": 150,  # Invalid: > 100
        "rr_progress_percent": 60,
        "possession_percent": 70
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/predict-risk", json=invalid_payload)

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["type"] == "ValidationError"


@pytest.mark.asyncio
async def test_not_found_endpoint():
    """
    Verify 404 handler returns structured error json.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/non-existent-endpoint")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data
