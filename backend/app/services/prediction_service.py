"""
End-to-End Prediction Service Layer.
Orchestrates feature engineering, inference, SHAP explanations, recommendations, and DB persistence.
"""

import uuid
import datetime
import numpy as np
import pandas as pd
from typing import Tuple

from backend.app.schemas.prediction import (
    ProjectData,
    PredictionResponse,
    RiskFactor,
    Recommendation,
)
from backend.app.database.models import (
    AssessmentRecord,
    AssessmentFactorModel,
    AssessmentRecommendationModel,
)
from backend.app.database.crud import save_assessment_record, create_or_get_project
from backend.app.ml.loader import model_manager
from backend.app.services.recommendation_service import RecommendationEngine
from ml.preprocessing.pipeline import add_engineered_features
from backend.app.core.logging import logger


class PredictionService:
    """
    Coordinates machine learning inference, explainability, recommendations, and persistence.
    """

    @classmethod
    def evaluate_project_risk(cls, data: ProjectData) -> PredictionResponse:
        # 1. Retrieve model artifacts
        preprocessor, classifier, regressor, explainer = model_manager.get_models()

        # 2. Build input DataFrame
        raw_dict = {
            "project_type": [data.project_type],
            "land_area": [data.land_area],
            "affected_families": [data.affected_families],
            "legal_disputes": [data.legal_disputes],
            "pending_approvals": [data.pending_approvals],
            "compensation_percent": [data.compensation_percent],
            "rr_progress_percent": [data.rr_progress_percent],
            "possession_percent": [data.possession_percent],
        }
        df_input = pd.DataFrame(raw_dict)

        # 3. Apply Feature Engineering
        df_engineered = add_engineered_features(df_input)

        # 4. Preprocess / Scale / Encode
        feature_cols = [
            "project_type", "land_area", "affected_families", "legal_disputes",
            "pending_approvals", "compensation_percent", "rr_progress_percent",
            "possession_percent", "families_per_acre", "milestone_completion_index",
            "litigation_approval_burden"
        ]
        X_vec = df_engineered[feature_cols]
        X_transformed = preprocessor.transform(X_vec)

        # 5. Predict Delay Likelihood (Classification Probabilities)
        probs = classifier.predict_proba(X_transformed)[0]
        delay_prob = float(probs[1]) if len(probs) > 1 else float(probs[0])
        delay_prob = round(delay_prob, 2)

        # 6. Predict Delay Days (Regression)
        raw_delay_days = float(regressor.predict(X_transformed)[0])
        predicted_delay_days = max(0, int(round(raw_delay_days))) if delay_prob >= 0.35 else 0

        # 7. Compute Composite Risk Score (0 - 100) & Category
        risk_score = int(np.clip(round(delay_prob * 80 + (data.legal_disputes * 2.5) + (data.pending_approvals * 2.5)), 5, 99))
        
        if risk_score < 35:
            risk_category = "LOW"
        elif risk_score < 60:
            risk_category = "MEDIUM"
        elif risk_score < 80:
            risk_category = "HIGH"
        else:
            risk_category = "CRITICAL"

        # 8. Compute SHAP Feature Attributions
        raw_factors = explainer.explain_instance(X_transformed, top_k=4)
        risk_factors = [
            RiskFactor(
                factor=f["factor"],
                impact=int(f["impact"]),
                direction=f.get("direction", "increases_risk")
            )
            for f in raw_factors
        ]

        # 9. Generate Domain Recommendations
        recommendations = RecommendationEngine.generate_recommendations(
            data=data,
            risk_score=risk_score,
            risk_category=risk_category,
            risk_factors=raw_factors,
        )

        # 10. Generate Project Identifier
        unique_suffix = uuid.uuid4().hex[:6].upper()
        project_id = f"PRJ-LA-{datetime.date.today().strftime('%Y%m')}-{unique_suffix}"

        # 11. Persist to SQLite Database
        try:
            create_or_get_project(
                project_code=project_id,
                project_name=f"{data.project_type} Land Acquisition Parcel {unique_suffix}",
                project_type=data.project_type,
            )

            db_factors = [
                AssessmentFactorModel(
                    factor_name=f.factor,
                    impact_score=f.impact,
                    direction=f.direction or "increases_risk",
                )
                for f in risk_factors
            ]
            db_recs = [
                AssessmentRecommendationModel(
                    priority=r.priority,
                    action_text=r.action,
                )
                for r in recommendations
            ]

            assessment_record = AssessmentRecord(
                project_code=project_id,
                project_type=data.project_type,
                land_area=float(data.land_area),
                affected_families=data.affected_families,
                legal_disputes=data.legal_disputes,
                pending_approvals=data.pending_approvals,
                compensation_percent=float(data.compensation_percent),
                rr_progress_percent=float(data.rr_progress_percent),
                possession_percent=float(data.possession_percent),
                delay_probability=delay_prob,
                risk_score=risk_score,
                risk_category=risk_category,
                predicted_delay_days=predicted_delay_days,
                factors=db_factors,
                recommendations=db_recs,
            )
            save_assessment_record(assessment_record)
            logger.info(f"Assessment {project_id} stored in database successfully.")

        except Exception as e:
            logger.error(f"Failed to persist assessment to database: {e}")

        # 12. Return Final Schema
        return PredictionResponse(
            project_id=project_id,
            delay_probability=delay_prob,
            risk_score=risk_score,
            risk_category=risk_category,
            predicted_delay_days=predicted_delay_days,
            risk_factors=risk_factors,
            recommendations=recommendations,
        )
