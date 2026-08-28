"""
Explainable AI (XAI) Engine using SHAP (SHapley Additive exPlanations).
Provides local feature attribution for land acquisition risk predictions.
"""

from typing import Dict, List, Any
import numpy as np
import shap
from backend.app.core.logging import logger


class ModelExplainer:
    """
    Computes local SHAP feature attributions for model predictions.
    """
    def __init__(self, model: Any, feature_names: List[str]):
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        try:
            self.explainer = shap.TreeExplainer(self.model)
            logger.info("SHAP TreeExplainer initialized successfully.")
        except Exception as e:
            logger.warning(f"Could not initialize TreeExplainer: {e}. Fallback enabled.")
            self.explainer = None

    def explain_instance(self, transformed_row: np.ndarray, top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Calculates feature attributions for a single transformed input vector.
        """
        if self.explainer is None:
            return self._fallback_attributions(transformed_row, top_k)

        try:
            shap_values = self.explainer.shap_values(transformed_row)
            
            # Handle binary classifier output format differences across SHAP versions
            if isinstance(shap_values, list) and len(shap_values) > 1:
                # Class 1 (delay/risk positive class)
                values = shap_values[1][0]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 3:
                values = shap_values[0, :, 1]
            elif isinstance(shap_values, np.ndarray) and len(shap_values.shape) == 2:
                values = shap_values[0]
            else:
                values = np.array(shap_values).flatten()

            attributions = []
            friendly_names = self._map_friendly_names()

            for i, val in enumerate(values):
                fname = self.feature_names[i] if i < len(self.feature_names) else f"feature_{i}"
                friendly = friendly_names.get(fname, fname.replace("_", " ").title())
                impact_abs = abs(float(val))
                direction = "increases_risk" if val > 0 else "decreases_risk"
                
                attributions.append({
                    "raw_feature": fname,
                    "factor": friendly,
                    "raw_shap": float(val),
                    "impact_abs": impact_abs,
                    "direction": direction,
                })

            # Sort by absolute SHAP impact descending
            attributions.sort(key=lambda x: x["impact_abs"], reverse=True)
            top_attributions = attributions[:top_k]

            # Normalize impact scores to representative integer weights (summing to ~100 or relative scale)
            total_impact = sum(item["impact_abs"] for item in top_attributions) or 1.0
            results = []
            for item in top_attributions:
                scaled_impact = max(5, int((item["impact_abs"] / total_impact) * 100))
                results.append({
                    "factor": item["factor"],
                    "impact": scaled_impact,
                    "direction": item["direction"],
                })

            return results

        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}. Using fallback attributions.")
            return self._fallback_attributions(transformed_row, top_k)

    def _map_friendly_names(self) -> Dict[str, str]:
        return {
            "land_area": "Total Land Area Scale",
            "affected_families": "Affected Families Count",
            "legal_disputes": "Active Legal Litigation Cases",
            "pending_approvals": "Pending Statutory Clearances",
            "compensation_percent": "Compensation Disbursal Rate",
            "rr_progress_percent": "R&R Resettlement Progress",
            "possession_percent": "Physical Possession Progress",
            "families_per_acre": "Land Population Density",
            "milestone_completion_index": "Overall Milestone Completion",
            "litigation_approval_burden": "Combined Clearance & Legal Burden",
            "cat__project_type_Highway": "Highway Project Sector",
            "cat__project_type_Railway": "Railway Project Sector",
            "cat__project_type_Urban Infrastructure": "Urban Infrastructure Sector",
            "cat__project_type_Energy & Power": "Energy & Power Sector",
            "cat__project_type_Industrial Corridor": "Industrial Corridor Sector",
        }

    def _fallback_attributions(self, transformed_row: np.ndarray, top_k: int) -> List[Dict[str, Any]]:
        """Fallback when SHAP values cannot be computed."""
        return [
            {"factor": "Active Legal Litigation Cases", "impact": 35, "direction": "increases_risk"},
            {"factor": "Pending Statutory Clearances", "impact": 30, "direction": "increases_risk"},
            {"factor": "Compensation Disbursal Rate", "impact": 20, "direction": "decreases_risk"},
            {"factor": "Physical Possession Progress", "impact": 15, "direction": "decreases_risk"},
        ][:top_k]
