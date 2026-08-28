"""
ML Model Loader and Artifact Manager.
Loads preprocessors, models, and metadata into a thread-safe singleton cache.
"""

import os
import json
import joblib
from typing import Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.core.errors import ModelNotLoadedException
from backend.app.core.logging import logger
from ml.explainability.shap_explainer import ModelExplainer


class ModelManager:
    """
    Singleton class managing ML model artifacts, transformers, and SHAP explainers.
    """
    _instance: Optional["ModelManager"] = None

    def __init__(self):
        self.preprocessor = None
        self.classifier = None
        self.regressor = None
        self.metadata: Dict[str, Any] = {}
        self.explainer: Optional[ModelExplainer] = None
        self.is_loaded: bool = False
        self.load_models()

    @classmethod
    def get_instance(cls) -> "ModelManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _resolve_model_dir(self) -> str:
        """Finds the absolute path to the ml/models directory."""
        candidates = [
            settings.MODEL_DIR,
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "ml", "models"),
            os.path.abspath("ml/models"),
        ]
        for path in candidates:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "risk_classifier.joblib")):
                return path
        return candidates[0]

    def load_models(self):
        """Loads all serialized model artifacts from disk."""
        model_dir = self._resolve_model_dir()
        logger.info(f"Loading ML models from: {model_dir}")

        prep_path = os.path.join(model_dir, "preprocessor.joblib")
        cls_path = os.path.join(model_dir, "risk_classifier.joblib")
        reg_path = os.path.join(model_dir, "delay_regressor.joblib")
        meta_path = os.path.join(model_dir, "model_metadata.json")

        if not all(os.path.exists(p) for p in [prep_path, cls_path, reg_path]):
            logger.warning(f"One or more model files missing in {model_dir}. Models not loaded.")
            self.is_loaded = False
            return

        try:
            self.preprocessor = joblib.load(prep_path)
            self.classifier = joblib.load(cls_path)
            self.regressor = joblib.load(reg_path)

            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)

            feature_names = self.metadata.get("feature_names", [])
            self.explainer = ModelExplainer(model=self.classifier, feature_names=feature_names)
            self.is_loaded = True
            logger.info("ML Models and SHAP Explainer loaded successfully.")

        except Exception as e:
            logger.error(f"Error while loading ML models: {e}")
            self.is_loaded = False

    def get_models(self):
        """Returns loaded preprocessor, classifier, regressor, and explainer."""
        if not self.is_loaded or self.classifier is None:
            # Try reloading once in case models were just generated
            self.load_models()
            if not self.is_loaded or self.classifier is None:
                raise ModelNotLoadedException("ML models are currently not loaded or initialized.")
        return self.preprocessor, self.classifier, self.regressor, self.explainer


model_manager = ModelManager.get_instance()
