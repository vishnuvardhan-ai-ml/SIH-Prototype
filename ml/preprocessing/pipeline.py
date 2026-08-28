"""
Machine Learning Preprocessing Pipeline.
Encapsulates feature transformations, scalers, and encoders without data leakage.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer


NUMERICAL_FEATURES: List[str] = [
    "land_area",
    "affected_families",
    "legal_disputes",
    "pending_approvals",
    "compensation_percent",
    "rr_progress_percent",
    "possession_percent",
]

CATEGORICAL_FEATURES: List[str] = [
    "project_type",
]


def add_engineered_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes domain-specific engineered features from raw project inputs.
    """
    data = df.copy()
    
    # Population density per acre of acquired land
    data["families_per_acre"] = data["affected_families"] / (data["land_area"] + 1.0)
    
    # Progress weighted completion index (0 - 100)
    data["milestone_completion_index"] = (
        data["compensation_percent"] * 0.35 +
        data["rr_progress_percent"] * 0.35 +
        data["possession_percent"] * 0.30
    )

    # Bottleneck severity ratio
    data["litigation_approval_burden"] = data["legal_disputes"] * 1.5 + data["pending_approvals"] * 2.0

    return data


def build_preprocessor() -> ColumnTransformer:
    """
    Constructs a ColumnTransformer for numerical scaling and categorical encoding.
    """
    engineered_numerical = NUMERICAL_FEATURES + [
        "families_per_acre",
        "milestone_completion_index",
        "litigation_approval_burden",
    ]

    num_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    cat_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Highway")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, engineered_numerical),
            ("cat", cat_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop"
    )

    return preprocessor


def get_feature_names(preprocessor: ColumnTransformer) -> List[str]:
    """Extracts output feature column names after fitting the preprocessor."""
    feature_names = []
    
    # Numerical names
    num_cols = preprocessor.transformers_[0][2]
    feature_names.extend(num_cols)

    # OneHot encoded names
    cat_encoder = preprocessor.transformers_[1][1].named_steps["onehot"]
    cat_cols = preprocessor.transformers_[1][2]
    cat_names = cat_encoder.get_feature_names_out(cat_cols)
    feature_names.extend(list(cat_names))

    return feature_names
