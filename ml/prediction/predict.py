"""
Standalone Offline Prediction Interface.
Can be invoked directly via CLI or imported into external batch evaluation scripts.
"""

import sys
import argparse
from backend.app.schemas.prediction import ProjectData
from backend.app.services.prediction_service import PredictionService


def run_standalone_prediction(
    project_type: str,
    land_area: int,
    affected_families: int,
    legal_disputes: int,
    pending_approvals: int,
    compensation_percent: int,
    rr_progress_percent: int,
    possession_percent: int,
):
    data = ProjectData(
        project_type=project_type,
        land_area=land_area,
        affected_families=affected_families,
        legal_disputes=legal_disputes,
        pending_approvals=pending_approvals,
        compensation_percent=compensation_percent,
        rr_progress_percent=rr_progress_percent,
        possession_percent=possession_percent,
    )

    result = PredictionService.evaluate_project_risk(data)
    print("\n" + "=" * 50)
    print(f"PREDICTION RESULT FOR: {result.project_id}")
    print("=" * 50)
    print(f"Delay Probability:      {result.delay_probability * 100:.1f}%")
    print(f"Risk Score:             {result.risk_score} / 100")
    print(f"Risk Classification:    {result.risk_category}")
    print(f"Estimated Delay:        {result.predicted_delay_days} days")
    print("\nTop Contributing Factors (SHAP XAI):")
    for f in result.risk_factors:
        print(f"  - {f.factor}: impact={f.impact}% ({f.direction})")
    print("\nActionable Recommendations:")
    for r in result.recommendations:
        print(f"  [{r.priority}] {r.action}")
    print("=" * 50)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run standalone risk prediction")
    parser.add_argument("--type", type=str, default="Highway", help="Project type")
    parser.add_argument("--area", type=int, default=150, help="Land area in acres")
    parser.add_argument("--families", type=int, default=300, help="Affected families")
    parser.add_argument("--disputes", type=int, default=4, help="Legal disputes")
    parser.add_argument("--approvals", type=int, default=2, help="Pending approvals")
    parser.add_argument("--compensation", type=int, default=60, help="Compensation %")
    parser.add_argument("--rr", type=int, default=45, help="R&R progress %")
    parser.add_argument("--possession", type=int, default=50, help="Possession %")
    args = parser.parse_args()

    run_standalone_prediction(
        project_type=args.type,
        land_area=args.area,
        affected_families=args.families,
        legal_disputes=args.disputes,
        pending_approvals=args.approvals,
        compensation_percent=args.compensation,
        rr_progress_percent=args.rr,
        possession_percent=args.possession,
    )
