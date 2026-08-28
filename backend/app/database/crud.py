"""
CRUD Operations and Database Repositories.
"""
from typing import Dict, List, Optional
from backend.app.database.models import (
    AssessmentFactorModel,
    AssessmentRecommendationModel,
    AssessmentRecord,
    ProjectModel,
)
from backend.app.database.session import get_db_connection
from backend.app.core.logging import logger


def create_or_get_project(project_code: str, project_name: str, project_type: str) -> ProjectModel:
    """Creates a project if it does not exist, or fetches existing one."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, project_code, project_name, project_type, created_at FROM projects WHERE project_code = ?", (project_code,))
        row = cursor.fetchone()
        if row:
            return ProjectModel(
                id=row["id"],
                project_code=row["project_code"],
                project_name=row["project_name"],
                project_type=row["project_type"],
                created_at=row["created_at"],
            )

        cursor.execute(
            "INSERT INTO projects (project_code, project_name, project_type) VALUES (?, ?, ?)",
            (project_code, project_name, project_type)
        )
        new_id = cursor.lastrowid
        cursor.execute("SELECT created_at FROM projects WHERE id = ?", (new_id,))
        created_at = cursor.fetchone()["created_at"]

        return ProjectModel(
            id=new_id,
            project_code=project_code,
            project_name=project_name,
            project_type=project_type,
            created_at=created_at,
        )


def save_assessment_record(assessment: AssessmentRecord) -> AssessmentRecord:
    """Persists a complete assessment along with risk factors and recommendations."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assessments (
                project_code, project_type, land_area, affected_families,
                legal_disputes, pending_approvals, compensation_percent,
                rr_progress_percent, possession_percent, delay_probability,
                risk_score, risk_category, predicted_delay_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            assessment.project_code,
            assessment.project_type,
            assessment.land_area,
            assessment.affected_families,
            assessment.legal_disputes,
            assessment.pending_approvals,
            assessment.compensation_percent,
            assessment.rr_progress_percent,
            assessment.possession_percent,
            assessment.delay_probability,
            assessment.risk_score,
            assessment.risk_category,
            assessment.predicted_delay_days,
        ))

        assessment_id = cursor.lastrowid
        assessment.id = assessment_id

        # Insert Factors
        for factor in assessment.factors:
            cursor.execute("""
                INSERT INTO assessment_factors (assessment_id, factor_name, impact_score, direction)
                VALUES (?, ?, ?, ?)
            """, (assessment_id, factor.factor_name, factor.impact_score, factor.direction))
            factor.assessment_id = assessment_id
            factor.id = cursor.lastrowid

        # Insert Recommendations
        for rec in assessment.recommendations:
            cursor.execute("""
                INSERT INTO assessment_recommendations (assessment_id, priority, action_text)
                VALUES (?, ?, ?)
            """, (assessment_id, rec.priority, rec.action_text))
            rec.assessment_id = assessment_id
            rec.id = cursor.lastrowid

        return assessment


def get_latest_assessments(limit: int = 50) -> List[AssessmentRecord]:
    """Fetches recently evaluated project assessments with their associated factors and recommendations."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM assessments ORDER BY id DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()

        results = []
        for row in rows:
            assessment_id = row["id"]
            
            # Fetch factors
            cursor.execute("SELECT * FROM assessment_factors WHERE assessment_id = ?", (assessment_id,))
            factor_rows = cursor.fetchall()
            factors = [
                AssessmentFactorModel(
                    id=f["id"],
                    assessment_id=f["assessment_id"],
                    factor_name=f["factor_name"],
                    impact_score=f["impact_score"],
                    direction=f["direction"],
                )
                for f in factor_rows
            ]

            # Fetch recommendations
            cursor.execute("SELECT * FROM assessment_recommendations WHERE assessment_id = ?", (assessment_id,))
            rec_rows = cursor.fetchall()
            recs = [
                AssessmentRecommendationModel(
                    id=r["id"],
                    assessment_id=r["assessment_id"],
                    priority=r["priority"],
                    action_text=r["action_text"],
                )
                for r in rec_rows
            ]

            rec_record = AssessmentRecord(
                id=row["id"],
                project_code=row["project_code"],
                project_type=row["project_type"],
                land_area=row["land_area"],
                affected_families=row["affected_families"],
                legal_disputes=row["legal_disputes"],
                pending_approvals=row["pending_approvals"],
                compensation_percent=row["compensation_percent"],
                rr_progress_percent=row["rr_progress_percent"],
                possession_percent=row["possession_percent"],
                delay_probability=row["delay_probability"],
                risk_score=row["risk_score"],
                risk_category=row["risk_category"],
                predicted_delay_days=row["predicted_delay_days"],
                created_at=str(row["created_at"]),
                factors=factors,
                recommendations=recs,
            )
            results.append(rec_record)

        return results


def get_analytics_summary() -> Dict:
    """Aggregates risk metrics, risk category counts, and high-level statistics."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_assessments,
                AVG(risk_score) as avg_risk_score,
                AVG(predicted_delay_days) as avg_delay_days,
                AVG(delay_probability) as avg_delay_prob
            FROM assessments
        """)
        summary = dict(cursor.fetchone())

        cursor.execute("""
            SELECT risk_category, COUNT(*) as count
            FROM assessments
            GROUP BY risk_category
        """)
        category_counts = {row["risk_category"]: row["count"] for row in cursor.fetchall()}

        return {
            "total_assessments": summary["total_assessments"] or 0,
            "avg_risk_score": round(summary["avg_risk_score"] or 0, 1),
            "avg_delay_days": round(summary["avg_delay_days"] or 0, 1),
            "avg_delay_probability": round(summary["avg_delay_prob"] or 0.0, 2),
            "risk_distribution": category_counts,
        }
