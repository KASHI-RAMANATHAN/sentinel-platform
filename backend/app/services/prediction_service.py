"""
app/services/prediction_service.py

Business logic for real-time single-record risk prediction.

Bridges the API layer and the ML inference engine without duplicating
any ML logic.  The InferenceEngine singleton (app/ml/inference_engine.py)
owns all model loading and inference; this service only:
  1. Derives model features from the raw LogRecordRequest
     (re-using feature_engineering.py helpers where possible).
  2. Calls InferenceEngine.predict().
  3. Maps the InferenceResult → PredictionResponse.
"""

import logging
from datetime import datetime
from typing import Optional

from app.ml.inference_engine import INFERENCE_FEATURES, InferenceEngine, InferenceResult
from app.schemas.prediction_schema import (
    LogRecordRequest,
    PredictionResponse,
    ShapFeatureContribution,
)

logger = logging.getLogger(__name__)


class PredictionService:
    """Orchestrates feature derivation and inference for a single log record."""

    def __init__(self, model_dir: str) -> None:
        """
        Args:
            model_dir: Directory containing the trained .pkl model files.
                       Passed to InferenceEngine.get_instance() which caches
                       the loaded models across all requests.
        """
        self._model_dir = model_dir

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def predict(self, record: LogRecordRequest) -> PredictionResponse:
        """
        Score a single log record through the full ML pipeline.

        Pipeline (all logic delegated to existing ML modules):
          1. Derive features  → feature_engineering helpers (inline)
          2. Anomaly score    → IsolationForest   (anomaly_detector.py)
          3. Attack type      → RandomForest      (attack_classifier.py)
          4. SHAP values      → TreeExplainer     (explainability.py)
          5. Risk normalise   → min-max against training distribution
        """
        # ── Step 1: Derive feature vector ─────────────────────────────
        feature_vector = self._derive_features(record)
        logger.info(
            "Running inference for user_id=%s | features=%s",
            record.user_id, feature_vector,
        )

        # ── Step 2: Run inference (all model logic in InferenceEngine) ─
        engine = InferenceEngine.get_instance(model_dir=self._model_dir)
        result: InferenceResult = engine.predict(feature_vector)

        logger.info(
            "Inference complete: is_anomaly=%s risk_score=%.2f predicted_attack=%s",
            result.is_anomaly, result.risk_score, result.predicted_attack,
        )

        # ── Step 3: Map to response schema ─────────────────────────────
        return self._build_response(record, result)

    # ------------------------------------------------------------------
    # Feature derivation
    # ------------------------------------------------------------------

    @staticmethod
    def _derive_features(record: LogRecordRequest) -> dict:
        """
        Convert a LogRecordRequest into the 8 numeric features expected
        by the IsolationForest and attack classifier.

        Priority for time features:
          1. Explicit login_hour / day_of_week fields (if provided)
          2. Derived from timestamp (if provided)
          3. Default to 0
        """
        # Time-based features (mirrors feature_engineering.engineer_features)
        if record.login_hour is not None:
            login_hour = int(record.login_hour)
        elif record.timestamp is not None:
            login_hour = record.timestamp.hour
        else:
            login_hour = 0

        if record.day_of_week is not None:
            day_of_week = int(record.day_of_week)
        elif record.timestamp is not None:
            day_of_week = record.timestamp.weekday()  # 0=Mon … 6=Sun
        else:
            day_of_week = 0

        return {
            "login_hour":          login_hour,
            "day_of_week":         day_of_week,
            "session_duration":    float(record.session_duration),
            "command_length":      int(record.command_length),
            "unique_resources":    int(record.unique_resources),
            "failed_login_count":  int(record.failed_login_count),
            "is_known_device":     int(record.is_known_device),
            "is_known_location":   int(record.is_known_location),
        }

    # ------------------------------------------------------------------
    # Response mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _build_response(
        record: LogRecordRequest, result: InferenceResult
    ) -> PredictionResponse:
        """Map InferenceResult + request context → PredictionResponse."""
        shap_contributions = [
            ShapFeatureContribution(
                feature=f["feature"],
                shap_value=f["shap_value"],
                description=f["description"],
            )
            for f in result.shap_features
        ]

        return PredictionResponse(
            is_anomaly=result.is_anomaly,
            risk_score=result.risk_score,
            predicted_attack=result.predicted_attack,
            confidence=result.confidence,
            explanation=shap_contributions,
            explanation_summary=result.explanation_summary,
            user_id=record.user_id,
            source_ip=record.source_ip,
            device_id=record.device_id,
            anomaly_score_raw=result.anomaly_score_raw,
            model_version=result.model_version,
        )
