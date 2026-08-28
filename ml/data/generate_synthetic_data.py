"""
Synthetic Dataset Generator for SIH Infrastructure & Land Acquisition Risk Prediction.

IMPORTANT NOTICE:
This module generates purely SYNTHETIC / DEMO data for initial prototyping,
model training baseline, and testing. It does NOT contain or represent actual
government or private land acquisition records. Model performance metrics
derived from this dataset do NOT represent real-world predictive validity.
"""

import os
import argparse
import numpy as np
import pandas as pd


def generate_synthetic_land_acquisition_data(
    num_samples: int = 2500,
    random_seed: int = 42
) -> pd.DataFrame:
    """
    Generates a structured synthetic dataset representing infrastructure projects
    and land acquisition milestones with realistic domain correlations.
    """
    np.random.seed(random_seed)

    project_types = [
        "Highway",
        "Railway",
        "Urban Infrastructure",
        "Energy & Power",
        "Industrial Corridor"
    ]
    type_probabilities = [0.35, 0.25, 0.20, 0.10, 0.10]
    
    project_types_col = np.random.choice(project_types, size=num_samples, p=type_probabilities)

    # Land area (acres) conditioned roughly on project type
    land_area = []
    for p_type in project_types_col:
        if p_type == "Highway":
            area = np.random.gamma(shape=5.0, scale=40.0) # ~200 acres
        elif p_type == "Railway":
            area = np.random.gamma(shape=6.0, scale=50.0) # ~300 acres
        elif p_type == "Urban Infrastructure":
            area = np.random.gamma(shape=3.0, scale=25.0) # ~75 acres
        elif p_type == "Industrial Corridor":
            area = np.random.gamma(shape=8.0, scale=100.0) # ~800 acres
        else: # Energy & Power
            area = np.random.gamma(shape=4.0, scale=60.0) # ~240 acres
        land_area.append(max(10, int(area)))

    land_area = np.array(land_area)

    # Affected families (scaled with land area and urban density)
    affected_families = []
    for i, p_type in enumerate(project_types_col):
        area = land_area[i]
        density_factor = 2.5 if p_type == "Urban Infrastructure" else (1.2 if p_type in ["Highway", "Railway"] else 0.6)
        families = int(np.random.poisson(lam=max(5, area * 0.4 * density_factor)) + np.random.randint(0, 20))
        affected_families.append(families)

    affected_families = np.array(affected_families)

    # Legal disputes (0 to 30+)
    dispute_intensity = (affected_families / (land_area + 1)) * 3.0
    legal_disputes = np.random.poisson(lam=np.clip(dispute_intensity * 2.5, 0.5, 15.0))

    # Pending approvals (0 to 12)
    pending_approvals = np.random.poisson(lam=np.random.uniform(0.5, 4.0, size=num_samples))

    # Milestones progress percentages (0 - 100%)
    compensation_percent = np.clip(
        np.random.normal(loc=65, scale=25, size=num_samples) - (legal_disputes * 1.5),
        0, 100
    ).astype(int)

    rr_progress_percent = np.clip(
        compensation_percent * np.random.uniform(0.6, 1.0, size=num_samples) - (affected_families * 0.01),
        0, 100
    ).astype(int)

    possession_percent = np.clip(
        (compensation_percent * 0.5 + rr_progress_percent * 0.5) * np.random.uniform(0.7, 1.0, size=num_samples) - (legal_disputes * 2.0),
        0, 100
    ).astype(int)

    # Environmental clearance status
    env_statuses = ["APPROVED", "IN_REVIEW", "PENDING", "REJECTED"]
    env_probabilities = [0.60, 0.25, 0.12, 0.03]
    env_status = np.random.choice(env_statuses, size=num_samples, p=env_probabilities)

    # Target calculation logic (Realistic domain risk score)
    # Base risk score: 0 to 100
    env_penalty = np.array([0 if s == "APPROVED" else (15 if s == "IN_REVIEW" else (30 if s == "PENDING" else 50)) for s in env_status])
    
    raw_risk = (
        (legal_disputes * 3.8) +
        (pending_approvals * 4.2) +
        (env_penalty * 0.4) +
        ((100 - compensation_percent) * 0.25) +
        ((100 - rr_progress_percent) * 0.22) +
        ((100 - possession_percent) * 0.28) +
        (np.log1p(affected_families) * 2.2) +
        np.random.normal(0, 4.5, size=num_samples)
    )

    # Normalize to 0 - 100
    risk_score = np.clip(raw_risk, 5, 99).astype(int)

    # Delay Probability via sigmoid curve
    delay_prob = 1 / (1 + np.exp(-(risk_score - 48) / 12.0))
    delay_prob = np.round(np.clip(delay_prob, 0.02, 0.98), 3)

    # Delay Days (0 if no delay, otherwise proportional to risk)
    is_delayed = (delay_prob > 0.45).astype(int)
    delay_days = np.where(
        is_delayed == 1,
        np.clip((risk_score * 3.5 + np.random.normal(0, 15, size=num_samples)), 20, 600).astype(int),
        0
    )

    # Risk Category
    risk_category = []
    for score in risk_score:
        if score < 35:
            risk_category.append("LOW")
        elif score < 60:
            risk_category.append("MEDIUM")
        elif score < 80:
            risk_category.append("HIGH")
        else:
            risk_category.append("CRITICAL")

    # Assemble DataFrame
    project_ids = [f"PRJ-SYNTH-{i+1001:05d}" for i in range(num_samples)]

    df = pd.DataFrame({
        "project_id": project_ids,
        "project_type": project_types_col,
        "land_area": land_area,
        "affected_families": affected_families,
        "legal_disputes": legal_disputes,
        "pending_approvals": pending_approvals,
        "compensation_percent": compensation_percent,
        "rr_progress_percent": rr_progress_percent,
        "possession_percent": possession_percent,
        "environmental_clearance": env_status,
        "delay_probability": delay_prob,
        "risk_score": risk_score,
        "risk_category": risk_category,
        "predicted_delay_days": delay_days,
        "is_delayed": is_delayed,
        "is_synthetic": True,
    })

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic land acquisition dataset")
    parser.add_argument("--samples", type=int, default=2500, help="Number of records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="sample-data/synthetic_dataset.csv", help="Output path")
    args = parser.parse_args()

    print(f"Generating {args.samples} synthetic records (seed={args.seed})...")
    dataset = generate_synthetic_land_acquisition_data(num_samples=args.samples, random_seed=args.seed)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    dataset.to_csv(args.output, index=False)
    print(f"Synthetic dataset saved successfully to {args.output}")
    print(f"Dataset summary:\n{dataset[['land_area', 'legal_disputes', 'risk_score', 'delay_probability', 'predicted_delay_days']].describe()}")
