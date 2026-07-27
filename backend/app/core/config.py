"""
app/core/config.py

Centralized application configuration.

Loads environment variables (via pydantic-settings) and exposes a single
`settings` object that is imported throughout the application instead of
reading os.environ directly. This keeps configuration in one place and
makes it easy to mock/override during tests.
"""

from functools import lru_cache
from typing import List
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application-wide settings.

    Values are populated from environment variables / a `.env` file.
    See `.env.example` for the full list of required variables.
    """
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- General ---
    APP_NAME: str = "Behavioral Anomaly Detection Platform"
    ENVIRONMENT: str = "development"  # development | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    CORS_ORIGINS: List[str] = ["*"]

    # --- Firebase ---
    FIREBASE_SERVICE_ACCOUNT_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "secrets", "firebase-service-account.json")
    FIREBASE_PROJECT_ID: str = ""
    FIRESTORE_LOGS_COLLECTION: str = "logs"
    FIRESTORE_ALERTS_COLLECTION: str = "alerts"
    FIRESTORE_PREDICTIONS_COLLECTION: str = "predictions"

    # --- Auth (placeholder) ---
    FIREBASE_AUTH_ENABLED: bool = False

    # --- ML ---
    ML_MODEL_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "app", "ml", "models")   # directory containing .pkl model files
    GEMINI_API_KEY: str = ""
    DEEPSEEK_API_KEY: str = ""

    # --- Data ---
    PROCESSED_DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "processed")
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "uploads")
    PIPELINE_CONTAMINATION: float = 0.02         # IsolationForest anomaly fraction

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    Using lru_cache ensures the .env file / environment is parsed only
    once per process, and allows Settings to be used as a FastAPI
    dependency (Depends(get_settings)) elsewhere in the app.
    """
    return Settings()


settings = get_settings()
