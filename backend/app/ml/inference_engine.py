"""
app/ml/inference_engine.py

Singleton inference engine for real-time, single-record prediction.

Wraps the three existing ML modules without duplicating any logic:
  - app/ml/anomaly_detector.py   — IsolationForest (anomaly detection)
  - app/ml/attack_classifier.py  — RandomForestClassifier (attack typing)
  - app/ml/explainability.py     — SHAP TreeExplainer (feature attribution)
  - app/ml/feature_engineering.py — feature derivation helpers

Models are loaded from disk once at startup (lazy singleton pattern) and
reused across all requests.

Score normalisation
-------------------
The IsolationForest decision_function returns a raw float in roughly
[-0.6, 0.15].  We min-max normalise against the global threat-score
bounds that were observed when the pipeline ran over the full dataset
(stored in classified_predictions.csv) so the per-request risk score
is directly comparable to the scores shown in GET /alerts.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Feature list — must exactly match the order used during training
# ---------------------------------------------------------------------------
INFERENCE_FEATURES: List[str] = [
    "login_hour",
    "day_of_week",
    "session_duration",
    "command_length",
    "unique_resources",
    "failed_login_count",
    "is_known_device",
    "is_known_location",
    "auth_method_encoded",
    "entity_type_encoded",
]

# Human-readable descriptions (mirrors explainability.py feature_mapping)
_FEATURE_DESCRIPTIONS: Dict[str, str] = {
    "login_hour":          "Login occurred outside the user's normal hours",
    "day_of_week":         "Login occurred on an unusual day of the week",
    "session_duration":    "Session duration was highly irregular",
    "command_length":      "Unusual command activity was detected",
    "unique_resources":    "An unusual number of resources was accessed",
    "failed_login_count":  "Multiple failed login attempts were recorded",
    "is_known_device":     "An unknown or unfamiliar device was used",
    "is_known_location":   "Login originated from an unfamiliar location",
    "auth_method_encoded": "An unusual authentication method was used",
    "entity_type_encoded": "Activity deviates from normal behavior for this role",
}

# Isolation Forest score bounds observed over the full dataset threat slice.
# Used for normalisation so this endpoint's risk scores match GET /alerts.
# These are the actual min/max from classified_predictions.csv.
_THREAT_SCORE_MIN: float = -0.0557478383741799  # most anomalous
_THREAT_SCORE_MAX: float = -1.9384305316449968e-05  # least anomalous (still threat)


@dataclass
class InferenceResult:
    """Structured output from a single inference run."""

    is_anomaly: bool
    risk_score: float                          # normalised [0, 100]
    anomaly_score_raw: float                   # raw IsolationForest score
    predicted_attack: str
    confidence: float                          # classifier max class probability
    shap_features: List[Dict]                  # [{feature, shap_value, description}]
    explanation_summary: str
    model_version: str = "isolation_forest_v1+random_forest_v1"


class InferenceEngine:
    """
    Loads IsolationForest + RandomForest models once and exposes
    a single predict() method for real-time single-record inference.
    """

    _instance: Optional[InferenceEngine] = None
    _lock: Lock = Lock()

    def __init__(self, model_dir: str) -> None:
        self._model_dir = model_dir
        self._iso_model = None       # IsolationForest
        self._clf_model = None       # RandomForestClassifier
        self._shap_explainer = None  # shap.TreeExplainer
        self._loaded = False

    # ------------------------------------------------------------------
    # Singleton factory
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls, model_dir: str) -> "InferenceEngine":
        """Return the shared InferenceEngine, loading models on first call."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    engine = cls(model_dir=model_dir)
                    engine._load_models()
                    cls._instance = engine
        return cls._instance

    # ------------------------------------------------------------------
    # Model loading (called once)
    # ------------------------------------------------------------------

    def _load_models(self) -> None:
        iso_path = os.path.join(self._model_dir, "isolation_forest.pkl")
        clf_path = os.path.join(self._model_dir, "attack_classifier.pkl")

        if not os.path.exists(iso_path):
            raise FileNotFoundError(f"IsolationForest model not found: {iso_path}")
        if not os.path.exists(clf_path):
            raise FileNotFoundError(f"Attack classifier model not found: {clf_path}")

        logger.info("Loading IsolationForest from %s", iso_path)
        self._iso_model = joblib.load(iso_path)

        logger.info("Loading AttackClassifier from %s", clf_path)
        self._clf_model = joblib.load(clf_path)

        logger.info("Building SHAP TreeExplainer for IsolationForest...")
        self._shap_explainer = shap.TreeExplainer(self._iso_model)

        self._loaded = True
        logger.info("InferenceEngine ready.")

    # ------------------------------------------------------------------
    # Public inference API
    # ------------------------------------------------------------------

    def predict(self, feature_vector: Dict[str, float]) -> InferenceResult:
        """
        Run the full inference pipeline on a single pre-engineered feature dict.

        Args:
            feature_vector: Dict mapping each feature name in INFERENCE_FEATURES
                            to its numeric value.  Missing keys default to 0.

        Returns:
            InferenceResult with all output fields populated.
        """
        if not self._loaded:
            raise RuntimeError("InferenceEngine models are not loaded.")

        # ── Build feature DataFrame (preserves column order) ──────────
        row = {f: float(feature_vector.get(f, 0.0)) for f in INFERENCE_FEATURES}
        X = pd.DataFrame([row], columns=INFERENCE_FEATURES)

        # ── Step 1: Anomaly detection (reuses anomaly_detector logic) ──
        iso_pred: int = int(self._iso_model.predict(X)[0])        # -1 or 1
        iso_score: float = float(self._iso_model.decision_function(X)[0])
        is_anomaly = iso_pred == -1

        # ── Step 2: Risk score normalisation ──────────────────────────
        risk_score = self._normalise_score(iso_score)

        # ── Step 3: Attack classification (reuses attack_classifier) ───
        clf_pred: str = str(self._clf_model.predict(X)[0])
        clf_proba: np.ndarray = self._clf_model.predict_proba(X)[0]
        confidence: float = float(np.max(clf_proba))

        # If anomaly but classifier says "Normal", label as Behavioral Anomaly
        if is_anomaly and clf_pred == "Normal":
            predicted_attack = "Behavioral Anomaly"
        elif not is_anomaly:
            predicted_attack = "Normal"
        else:
            predicted_attack = clf_pred

        # ── Step 4: SHAP explanation (reuses explainability logic) ─────
        shap_values: np.ndarray = self._shap_explainer.shap_values(X)[0]
        shap_features, explanation_summary = self._build_explanation(
            shap_values, is_anomaly
        )

        return InferenceResult(
            is_anomaly=is_anomaly,
            risk_score=round(risk_score, 4),
            anomaly_score_raw=round(iso_score, 6),
            predicted_attack=predicted_attack,
            confidence=round(confidence, 4),
            shap_features=shap_features,
            explanation_summary=explanation_summary,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalise_score(score: float) -> float:
        """
        Normalise a raw IsolationForest decision_function score to [0, 100].

        Scores outside the observed training range are clamped.
        More negative raw score → higher risk → closer to 100.
        """
        s_min, s_max = _THREAT_SCORE_MIN, _THREAT_SCORE_MAX
        if s_max == s_min:
            return 100.0 if score <= s_min else 0.0

        negated = -score
        n_min, n_max = -s_max, -s_min  # flip direction
        raw = (negated - n_min) / (n_max - n_min) * 100.0
        return float(max(0.0, min(100.0, raw)))

    @staticmethod
    def _build_explanation(
        shap_values: np.ndarray,
        is_anomaly: bool,
    ) -> Tuple[List[Dict], str]:
        """
        Convert raw SHAP values into structured feature dicts and a
        natural-language summary.  Mirrors explainability.py logic.

        For IsolationForest: *negative* SHAP values push the sample
        toward anomaly territory.  We report only anomaly-contributing
        features (shap < 0) when the row is flagged as a threat.
        """
        if not is_anomaly:
            return [], "Activity aligns with normal baseline behaviour."

        # Sort by most negative first (biggest anomaly contribution)
        indexed = sorted(
            enumerate(shap_values), key=lambda x: x[1]
        )
        top = [(INFERENCE_FEATURES[i], v) for i, v in indexed if v < 0][:3]

        feature_dicts = [
            {
                "feature": feat,
                "shap_value": round(float(val), 4),
                "description": _FEATURE_DESCRIPTIONS.get(
                    feat, f"Unusual behaviour in {feat}"
                ),
            }
            for feat, val in top
        ]

        if not top:
            return [], "Flagged as anomaly; no dominant contributing feature identified."

        reasons = [_FEATURE_DESCRIPTIONS.get(f, f) for f, _ in top]
        if len(reasons) == 1:
            summary = f"High risk because {reasons[0].lower()}."
        elif len(reasons) == 2:
            summary = f"High risk because {reasons[0].lower()} and {reasons[1].lower()}."
        else:
            summary = (
                f"High risk because {reasons[0].lower()}, "
                f"{reasons[1].lower()}, and {reasons[2].lower()}."
            )

        return feature_dicts, summary
