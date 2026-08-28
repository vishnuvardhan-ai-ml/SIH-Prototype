# Frontend-Backend API Contract Specification

> **Base URL**: `http://localhost:8000/api`  
> **Interactive Swagger Documentation**: `http://localhost:8000/docs`  
> **ReDoc**: `http://localhost:8000/redoc`  
> **Data Format**: `application/json`

---

## Overview
This document specifies the complete API contract between the **SIH-Prototype Backend** and any frontend client. The frontend developer can implement user interfaces, forms, charts, and dashboards against these exact endpoints and response schemas.

---

## 1. System Health Check

### Endpoint: `GET /api/health`
- **Purpose**: Verify backend service availability and status.
- **Headers**: None required.
- **Request Body**: None.

#### Response: `200 OK`
```json
{
  "status": "ok",
  "service": "SIH Backend"
}
```

---

## 2. Land Acquisition Risk Prediction & Decision Support

### Endpoint: `POST /api/predict-risk`
- **Purpose**: Submit project land acquisition parameters to compute delay probability, risk score, classification, explainable AI (SHAP) feature attributions, and actionable mitigation recommendations. Also persists the assessment to the SQLite database.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Schema (`ProjectData`)
| Field Name | Type | Required | Range / Enum | Description |
|---|---|---|---|---|
| `project_type` | `string` | **Yes** | `"Highway"`, `"Railway"`, `"Urban Infrastructure"`, `"Energy & Power"`, `"Industrial Corridor"` | Sector vertical of the infrastructure project. |
| `land_area` | `integer` | **Yes** | $\ge 1$ (acres) | Total land parcel acreage required. |
| `affected_families` | `integer` | **Yes** | $\ge 0$ | Number of families/landowners impacted. |
| `legal_disputes` | `integer` | **Yes** | $\ge 0$ | Number of active litigations or court cases. |
| `pending_approvals` | `integer` | **Yes** | $\ge 0$ | Number of pending statutory / environmental clearances. |
| `compensation_percent` | `integer` | **Yes** | $0 \dots 100$ | Progress percentage of compensation disbursed. |
| `rr_progress_percent` | `integer` | **Yes** | $0 \dots 100$ | Rehabilitation & Resettlement (R&R) completion percentage. |
| `possession_percent` | `integer` | **Yes** | $0 \dots 100$ | Physical land possession percentage acquired. |

#### Example Request
```json
{
  "project_type": "Highway",
  "land_area": 180,
  "affected_families": 350,
  "legal_disputes": 6,
  "pending_approvals": 3,
  "compensation_percent": 45,
  "rr_progress_percent": 30,
  "possession_percent": 25
}
```

#### Response: `200 OK` (`PredictionResponse`)
```json
{
  "project_id": "PRJ-202608-0042",
  "delay_probability": 0.88,
  "risk_score": 84,
  "risk_category": "CRITICAL",
  "predicted_delay_days": 135,
  "risk_factors": [
    {
      "factor": "Legal disputes count",
      "impact": 32,
      "direction": "increases_risk"
    },
    {
      "factor": "Pending statutory clearances",
      "impact": 28,
      "direction": "increases_risk"
    },
    {
      "factor": "Low physical land possession",
      "impact": 22,
      "direction": "increases_risk"
    },
    {
      "factor": "Compensation disbursal lag",
      "impact": 18,
      "direction": "increases_risk"
    }
  ],
  "recommendations": [
    {
      "priority": "HIGH",
      "action": "Convene Special Land Acquisition Tribunal fast-track benches for 6 unresolved disputes."
    },
    {
      "priority": "HIGH",
      "action": "Escalate 3 pending clearances to State Single Window Clearance Committee."
    },
    {
      "priority": "MEDIUM",
      "action": "Accelerate direct DBT compensation disbursements to boost landowner consensus above 70%."
    }
  ]
}
```

#### Error Response: `422 Unprocessable Content` (Validation Failure)
```json
{
  "error": {
    "type": "ValidationError",
    "message": "Input validation failed",
    "details": [
      {
        "field": "body -> compensation_percent",
        "message": "Input should be less than or equal to 100"
      }
    ]
  }
}
```

---

## 3. Historical Project Assessments List

### Endpoint: `GET /api/projects`
- **Purpose**: Fetch list of previous project assessments with full breakdown and audit history.
- **Query Parameters**:
  - `limit` (*optional*, integer, default: 50, max: 100)

#### Response: `200 OK`
```json
[
  {
    "id": 1,
    "project_code": "PRJ-202608-0042",
    "project_type": "Highway",
    "land_area": 180.0,
    "affected_families": 350,
    "legal_disputes": 6,
    "pending_approvals": 3,
    "compensation_percent": 45.0,
    "rr_progress_percent": 30.0,
    "possession_percent": 25.0,
    "delay_probability": 0.88,
    "risk_score": 84,
    "risk_category": "CRITICAL",
    "predicted_delay_days": 135,
    "created_at": "2026-08-28 23:45:00",
    "factors": [
      {
        "id": 1,
        "assessment_id": 1,
        "factor_name": "Legal disputes count",
        "impact_score": 32,
        "direction": "increases_risk"
      }
    ],
    "recommendations": [
      {
        "id": 1,
        "assessment_id": 1,
        "priority": "HIGH",
        "action_text": "Convene Special Land Acquisition Tribunal fast-track benches for 6 unresolved disputes."
      }
    ]
  }
]
```

---

## 4. Portfolio Analytics Summary

### Endpoint: `GET /api/analytics/summary`
- **Purpose**: Retrieve aggregate metrics, risk distribution breakdown, and average timeline delays for executive dashboards and monitoring charts.

#### Response: `200 OK`
```json
{
  "total_assessments": 142,
  "avg_risk_score": 58.4,
  "avg_delay_days": 82.3,
  "avg_delay_probability": 0.62,
  "risk_distribution": {
    "LOW": 28,
    "MEDIUM": 45,
    "HIGH": 41,
    "CRITICAL": 28
  }
}
```

---

## 5. Standard Error Handling Formats

| Status Code | Description | JSON Structure |
|---|---|---|
| `400 Bad Request` | Client sent malformed business request | `{"error": {"type": "AppException", "message": "...", "details": {}}}` |
| `422 Unprocessable Content` | Schema / Field validation failed | `{"error": {"type": "ValidationError", "message": "...", "details": [{"field": "...", "message": "..."}]}}` |
| `500 Internal Server Error` | Unexpected backend failure | `{"error": {"type": "InternalServerError", "message": "..."}}` |
| `503 Service Unavailable` | ML model artifact is loading or missing | `{"error": {"type": "ModelNotLoadedException", "message": "..."}}` |
