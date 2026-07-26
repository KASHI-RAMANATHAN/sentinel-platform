"""
app/api/predict.py

Router for real-time risk prediction.

Endpoints
---------
POST /predict   — score a single access-log record through the ML pipeline.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_prediction_service
from app.schemas.prediction_schema import LogRecordRequest, PredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter(prefix="/predict", tags=["Prediction"])


@router.post(
    "",
    response_model=PredictionResponse,
    summary="Predict risk for a single log record",
    description=(
        "Runs a single access-log record through the full ML pipeline and returns:\n\n"
        "- **risk_score** — normalised risk [0–100]; comparable to scores in GET /alerts\n"
        "- **predicted_attack** — attack category or `'Normal'` / `'Behavioral Anomaly'`\n"
        "- **confidence** — attack classifier's class probability [0–1]\n"
        "- **explanation** — top SHAP feature contributions driving the anomaly score\n"
        "- **explanation_summary** — natural-language rationale\n\n"
        "**Pipeline** (existing modules, no duplication):\n"
        "1. Feature derivation (`feature_engineering.py`)\n"
        "2. Anomaly detection — IsolationForest (`anomaly_detector.py`)\n"
        "3. Attack classification — RandomForest (`attack_classifier.py`)\n"
        "4. SHAP explanation — TreeExplainer (`explainability.py`)\n"
        "5. Risk normalisation against training distribution\n\n"
        "The model weights (`isolation_forest.pkl`, `attack_classifier.pkl`) are loaded "
        "once at startup and reused across all requests."
    ),
)
async def predict(
    record: LogRecordRequest,
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PredictionResponse:
    """Score one log record through the ML pipeline."""
    return await prediction_service.predict(record)
