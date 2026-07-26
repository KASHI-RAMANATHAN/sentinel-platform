"""
app/api/upload.py

Router for CSV batch-upload and ML pipeline execution.

Endpoints
---------
POST /upload   — accept a CSV, run the full pipeline, return a summary.
"""

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_upload_service
from app.schemas.upload_schema import UploadResponse
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post(
    "",
    response_model=UploadResponse,
    summary="Upload a CSV and run the full ML pipeline",
    description=(
        "Accepts a CSV file of raw access logs and runs the complete ML pipeline:\n\n"
        "1. **Feature Engineering** — cleans, engineers, and encodes features "
        "(`feature_engineering.py`)\n"
        "2. **Baseline Profiling** — builds per-user behavioural baseline profiles "
        "(`baseline_model.py`)\n"
        "3. **Isolation Forest** — detects anomalous sessions; trains a fresh model "
        "and overwrites `isolation_forest.pkl` (`anomaly_detector.py`)\n"
        "4. **Attack Classification** — classifies each anomaly into an attack category; "
        "trains if ground-truth labels are present, otherwise uses the saved model "
        "(`attack_classifier.py`)\n"
        "5. **SHAP Explainability** — generates feature attributions for all anomalies "
        "(`explainability.py`)\n\n"
        "All outputs are stored under `data/processed/`. The response includes a "
        "per-step breakdown with row counts, timing, and KPI summary.\n\n"
        "**Required CSV columns**: `timestamp`, `session_duration`\n\n"
        "**File limit**: 50 MB"
    ),
)
async def upload_csv(
    file: UploadFile = File(
        description="Raw access-log CSV file. Must contain at minimum `timestamp` and `session_duration` columns."
    ),
    upload_service: UploadService = Depends(get_upload_service),
) -> UploadResponse:
    """
    Upload a CSV and run the full 5-step ML pipeline.
    Returns a structured processing summary with per-step breakdown.
    """
    return await upload_service.process_upload(file)
