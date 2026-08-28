"""
Model Training and Evaluation Pipeline.
Trains Risk Classifier (Delay Likelihood / Risk Score) and Delay Regressor (Days Overrun).
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_absolute_error, root_mean_squared_error, r2_score
)

from ml.data.generate_synthetic_data import generate_synthetic_land_acquisition_data
from ml.preprocessing.pipeline import add_engineered_features, build_preprocessor, get_feature_names


def train_and_evaluate_models(
    data_path: str = "sample-data/synthetic_dataset.csv",
    models_dir: str = "ml/models",
    random_state: int = 42
):
    """
    Orchestrates full model training, evaluation, comparison, and serialization.
    """
    print("=" * 60)
    print("SIH ML PIPELINE: Training Risk Prediction Models")
    print("=" * 60)

    # 1. Load Data
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}. Generating fresh synthetic data...")
        df = generate_synthetic_land_acquisition_data(num_samples=2500, random_seed=random_state)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        df.to_csv(data_path, index=False)
    else:
        df = pd.read_csv(data_path)

    print(f"Dataset loaded: {df.shape[0]} records, {df.shape[1]} columns.")

    # 2. Prepare Features and Targets
    df_engineered = add_engineered_features(df)
    
    feature_cols = [
        "project_type", "land_area", "affected_families", "legal_disputes",
        "pending_approvals", "compensation_percent", "rr_progress_percent",
        "possession_percent", "families_per_acre", "milestone_completion_index",
        "litigation_approval_burden"
    ]

    X = df_engineered[feature_cols]
    y_class = df_engineered["is_delayed"]
    y_reg = df_engineered["predicted_delay_days"]

    # 3. Train-Test Split (80/20)
    X_train, X_test, y_train_cls, y_test_cls, y_train_reg, y_test_reg = train_test_split(
        X, y_class, y_reg, test_size=0.20, random_state=random_state, stratify=y_class
    )

    print(f"Training split: {X_train.shape[0]} samples | Test split: {X_test.shape[0]} samples")

    # 4. Preprocessing Fit & Transform
    preprocessor = build_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    feature_names = get_feature_names(preprocessor)

    # 5. Train & Evaluate Classification Models
    print("\n--- Training Delay Risk Classifier ---")
    cls_rf = RandomForestClassifier(n_estimators=120, max_depth=7, random_state=random_state, n_jobs=-1)
    cls_gb = GradientBoostingClassifier(n_estimators=100, max_depth=4, learning_rate=0.08, random_state=random_state)

    cls_rf.fit(X_train_transformed, y_train_cls)
    cls_gb.fit(X_train_transformed, y_train_cls)

    # Evaluate RF Classifier
    preds_rf = cls_rf.predict(X_test_transformed)
    probs_rf = cls_rf.predict_proba(X_test_transformed)[:, 1]
    auc_rf = roc_auc_score(y_test_cls, probs_rf)
    acc_rf = accuracy_score(y_test_cls, preds_rf)
    f1_rf = f1_score(y_test_cls, preds_rf)

    # Evaluate GB Classifier
    preds_gb = cls_gb.predict(X_test_transformed)
    probs_gb = cls_gb.predict_proba(X_test_transformed)[:, 1]
    auc_gb = roc_auc_score(y_test_cls, probs_gb)
    acc_gb = accuracy_score(y_test_cls, preds_gb)
    f1_gb = f1_score(y_test_cls, preds_gb)

    print(f"RandomForest Classifier  -> Accuracy: {acc_rf:.4f} | F1: {f1_rf:.4f} | ROC-AUC: {auc_rf:.4f}")
    print(f"GradientBoost Classifier -> Accuracy: {acc_gb:.4f} | F1: {f1_gb:.4f} | ROC-AUC: {auc_gb:.4f}")

    selected_classifier = cls_rf if f1_rf >= f1_gb else cls_gb
    chosen_cls_name = "RandomForestClassifier" if selected_classifier == cls_rf else "GradientBoostingClassifier"
    print(f"Selected Classifier: {chosen_cls_name}")

    # 6. Train & Evaluate Regression Models
    print("\n--- Training Delay Days Regressor ---")
    reg_rf = RandomForestRegressor(n_estimators=120, max_depth=7, random_state=random_state, n_jobs=-1)
    reg_gb = GradientBoostingRegressor(n_estimators=100, max_depth=4, learning_rate=0.08, random_state=random_state)

    reg_rf.fit(X_train_transformed, y_train_reg)
    reg_gb.fit(X_train_transformed, y_train_reg)

    # Evaluate Regressors
    preds_reg_rf = reg_rf.predict(X_test_transformed)
    mae_rf = mean_absolute_error(y_test_reg, preds_reg_rf)
    rmse_rf = root_mean_squared_error(y_test_reg, preds_reg_rf)
    r2_rf = r2_score(y_test_reg, preds_reg_rf)

    preds_reg_gb = reg_gb.predict(X_test_transformed)
    mae_gb = mean_absolute_error(y_test_reg, preds_reg_gb)
    rmse_gb = root_mean_squared_error(y_test_reg, preds_reg_gb)
    r2_gb = r2_score(y_test_reg, preds_reg_gb)

    print(f"RandomForest Regressor  -> MAE: {mae_rf:.2f} days | RMSE: {rmse_rf:.2f} days | R2: {r2_rf:.4f}")
    print(f"GradientBoost Regressor -> MAE: {mae_gb:.2f} days | RMSE: {rmse_gb:.2f} days | R2: {r2_gb:.4f}")

    selected_regressor = reg_rf if r2_rf >= r2_gb else reg_gb
    chosen_reg_name = "RandomForestRegressor" if selected_regressor == reg_rf else "GradientBoostingRegressor"
    print(f"Selected Regressor: {chosen_reg_name}")

    # 7. Model Persistence
    os.makedirs(models_dir, exist_ok=True)
    preprocessor_path = os.path.join(models_dir, "preprocessor.joblib")
    classifier_path = os.path.join(models_dir, "risk_classifier.joblib")
    regressor_path = os.path.join(models_dir, "delay_regressor.joblib")
    metadata_path = os.path.join(models_dir, "model_metadata.json")

    joblib.dump(preprocessor, preprocessor_path)
    joblib.dump(selected_classifier, classifier_path)
    joblib.dump(selected_regressor, regressor_path)

    from datetime import datetime, timezone
    metadata = {
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "dataset_samples": len(df),
        "feature_names": feature_names,
        "input_features": feature_cols,
        "selected_classifier": chosen_cls_name,
        "classifier_metrics": {
            "accuracy": float(acc_rf if selected_classifier == cls_rf else acc_gb),
            "f1_score": float(f1_rf if selected_classifier == cls_rf else f1_gb),
            "roc_auc": float(auc_rf if selected_classifier == cls_rf else auc_gb),
        },
        "selected_regressor": chosen_reg_name,
        "regressor_metrics": {
            "mae": float(mae_rf if selected_regressor == reg_rf else mae_gb),
            "rmse": float(rmse_rf if selected_regressor == reg_rf else rmse_gb),
            "r2_score": float(r2_rf if selected_regressor == reg_rf else r2_gb),
        }
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nArtifacts successfully persisted to {models_dir}/")
    print(f"- {preprocessor_path}")
    print(f"- {classifier_path}")
    print(f"- {regressor_path}")
    print(f"- {metadata_path}")


if __name__ == "__main__":
    train_and_evaluate_models()
