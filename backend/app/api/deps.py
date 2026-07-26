"""
app/api/deps.py

Shared FastAPI dependency providers.

Routers depend on these functions (via Depends(...)) rather than
instantiating services directly, which keeps routers thin and makes
services easy to swap/mock in tests.
"""

from fastapi import Depends
from google.cloud.firestore_v1 import Client as FirestoreClient

from app.core.config import settings
from app.firebase.firestore_client import get_firestore_client
from app.services.alert_service import AlertService
from app.services.dashboard_service import DashboardService
from app.services.log_service import LogService
from app.services.prediction_service import PredictionService
from app.services.upload_service import UploadService


def get_log_service(db: FirestoreClient = Depends(get_firestore_client)) -> LogService:
    return LogService(db=db)


def get_alert_service(db: FirestoreClient = Depends(get_firestore_client)) -> AlertService:
    """
    Provides an AlertService that reads from the ML-generated CSV
    and syncs state with Firestore.
    """
    return AlertService(data_dir=settings.PROCESSED_DATA_DIR, db=db)


def get_prediction_service() -> PredictionService:
    """
    Provides a PredictionService backed by the trained ML models on disk.
    Does not require a Firestore connection.
    """
    return PredictionService(model_dir=settings.ML_MODEL_PATH)


def get_dashboard_service(db: FirestoreClient = Depends(get_firestore_client)) -> DashboardService:
    """
    Provides a DashboardService that reads from the ML-generated CSV
    and filters out resolved alerts using Firestore state.
    """
    return DashboardService(data_dir=settings.PROCESSED_DATA_DIR, db=db)


def get_upload_service() -> UploadService:
    """
    Provides an UploadService that runs the full ML pipeline on uploaded CSVs.
    """
    return UploadService(
        upload_dir=settings.UPLOAD_DIR,
        processed_dir=settings.PROCESSED_DATA_DIR,
        model_dir=settings.ML_MODEL_PATH,
        contamination=settings.PIPELINE_CONTAMINATION,
    )
