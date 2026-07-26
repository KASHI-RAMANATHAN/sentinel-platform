"""
app/main.py

FastAPI application entrypoint.

Responsible for:
- Creating the FastAPI app instance.
- Configuring CORS.
- Registering startup/shutdown event handlers (Firebase init + data bootstrap).
- Mounting the aggregated API router.

Run locally with:
    uvicorn app.main:app --reload
"""

import asyncio
import logging
import os

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.firebase.firebase import init_firebase_app
from app.firebase.firestore_client import get_firestore_client

configure_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Behavioral Anomaly Detection Platform — backend API.",
    version="0.1.0",
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _processed_data_is_stale(source_csv: str, processed_dir: str) -> bool:
    """
    Return True if classified_predictions.csv is missing or older than the
    source CSV, meaning the pipeline needs to be re-run.
    """
    predictions_path = os.path.join(processed_dir, "classified_predictions.csv")
    if not os.path.exists(predictions_path):
        return True
    if not os.path.exists(source_csv):
        return False
    return os.path.getmtime(source_csv) > os.path.getmtime(predictions_path)


def _run_bootstrap_pipeline() -> None:
    """
    Synchronous function that runs the full ML pipeline on the built-in
    final_dataset.csv.  Called via asyncio.to_thread so it never blocks
    the event loop.
    """
    # Resolve paths relative to the backend root
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    source_csv   = os.path.join(backend_root, "data", "synthetic", "final_dataset.csv")

    if not os.path.exists(source_csv):
        logger.warning(
            "Bootstrap skipped — source dataset not found at: %s", source_csv
        )
        return

    if not _processed_data_is_stale(source_csv, settings.PROCESSED_DATA_DIR):
        logger.info(
            "Processed data is up-to-date. Skipping bootstrap pipeline run."
        )
        return

    logger.info(
        "Processed data missing or stale — running bootstrap pipeline on %s",
        source_csv,
    )

    try:
        import pandas as pd
        from app.ml.pipeline import run_pipeline

        df_raw = pd.read_csv(source_csv)
        result = run_pipeline(
            df_raw,
            processed_dir=settings.PROCESSED_DATA_DIR,
            model_dir=settings.ML_MODEL_PATH,
            contamination=settings.PIPELINE_CONTAMINATION,
        )

        if result.success:
            logger.info(
                "Bootstrap pipeline complete — %d rows, %d anomalies (%.1f%%).",
                result.total_rows,
                result.anomalies_detected,
                result.anomaly_rate_pct,
            )
        else:
            logger.warning("Bootstrap pipeline finished with errors: %s", result.error)

    except Exception as exc:
        logger.exception("Bootstrap pipeline failed: %s", exc)


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """
    1. Initialise Firebase.
    2. In the background, pre-process final_dataset.csv if the dashboard
       has no data yet (or the dataset has been updated since last run).
    """
    logger.info("Starting %s [%s]", settings.APP_NAME, settings.ENVIRONMENT)

    # --- Firebase ---
    try:
        init_firebase_app()
        get_firestore_client()  # Initialize gRPC in the main thread to prevent Windows crashes
    except Exception as exc:  # noqa: BLE001
        logger.warning("Firebase initialization skipped/failed: %s", exc)

    # --- Data bootstrap (non-blocking background task) ---
    asyncio.create_task(
        asyncio.to_thread(_run_bootstrap_pipeline),
    )


# --- Global Exception Handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error", "details": str(exc)},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail, "details": None},
    )

# --- Routers ---
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", tags=["Root"], summary="Root endpoint")
async def root() -> dict:
    """Basic root endpoint pointing to interactive docs."""
    return {
        "message": f"{settings.APP_NAME} API",
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }
