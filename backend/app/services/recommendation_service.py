"""
Domain-Driven Recommendation Engine for Land Acquisition Risk Mitigation.
Generates prioritized, actionable intervention strategies based on project bottlenecks and SHAP factors.
"""

from typing import List, Dict, Any
from backend.app.schemas.prediction import ProjectData, Recommendation


class RecommendationEngine:
    """
    Evaluates project status, predicted risk, and key bottlenecks to generate
    context-aware mitigation recommendations.
    """

    @staticmethod
    def generate_recommendations(
        data: ProjectData,
        risk_score: int,
        risk_category: str,
        risk_factors: List[Dict[str, Any]],
    ) -> List[Recommendation]:
        recommendations: List[Recommendation] = []

        # 1. Legal Dispute Interventions
        if data.legal_disputes >= 5:
            recommendations.append(
                Recommendation(
                    priority="HIGH",
                    action=f"Convene Special LARRA fast-track tribunal benches to resolve {data.legal_disputes} high-impact litigation disputes."
                )
            )
        elif data.legal_disputes > 0:
            recommendations.append(
                Recommendation(
                    priority="MEDIUM",
                    action=f"Initiate Lok Adalat & administrative mediation for {data.legal_disputes} titleholder dispute cases."
                )
            )

        # 2. Statutory / Regulatory Approvals
        if data.pending_approvals >= 3:
            recommendations.append(
                Recommendation(
                    priority="HIGH",
                    action=f"Escalate {data.pending_approvals} statutory clearances to State Project Monitoring Group (PMG) for inter-departmental resolution."
                )
            )
        elif data.pending_approvals > 0:
            recommendations.append(
                Recommendation(
                    priority="MEDIUM",
                    action=f"Liaise with nodal environmental/forest authorities for {data.pending_approvals} pending stage clearances."
                )
            )

        # 3. Compensation Disbursal Lags
        if data.compensation_percent < 50:
            recommendations.append(
                Recommendation(
                    priority="HIGH",
                    action=f"Launch decentralized DBT compensation camps to accelerate payout beyond current {data.compensation_percent}%."
                )
            )
        elif data.compensation_percent < 75:
            recommendations.append(
                Recommendation(
                    priority="MEDIUM",
                    action=f"Expedite supplementary award disbursals to achieve target 80%+ compensation coverage."
                )
            )

        # 4. Rehabilitation & Resettlement (R&R)
        if data.rr_progress_percent < 50 and data.affected_families > 100:
            recommendations.append(
                Recommendation(
                    priority="HIGH",
                    action=f"Accelerate transit housing and R&R colony infrastructure for {data.affected_families} affected families (currently {data.rr_progress_percent}%)."
                )
            )
        elif data.rr_progress_percent < 70:
            recommendations.append(
                Recommendation(
                    priority="MEDIUM",
                    action=f"Complete pending livelihood grant disbursements to progress R&R past {data.rr_progress_percent}%."
                )
            )

        # 5. Possession Conversion Gap
        if data.possession_percent < 50 and data.compensation_percent >= 60:
            recommendations.append(
                Recommendation(
                    priority="HIGH",
                    action=f"Conduct joint revenue & survey demarcation to take physical possession of compensated parcels (currently at {data.possession_percent}%)."
                )
            )

        # 6. Default fallback for low risk / on-track projects
        if not recommendations:
            recommendations.append(
                Recommendation(
                    priority="LOW",
                    action="Maintain standard bi-weekly milestone audits; land acquisition milestones are proceeding within scheduled tolerances."
                )
            )

        # Sort recommendations: HIGH -> MEDIUM -> LOW
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        recommendations.sort(key=lambda r: priority_order.get(r.priority, 3))

        return recommendations
