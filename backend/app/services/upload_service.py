"""
app/services/upload_service.py

Business logic for POST /upload.

Responsibilities
----------------
1. Validate the uploaded file (CSV, non-empty, expected columns).
2. Save the raw file to disk under UPLOAD_DIR.
3. Run the ML pipeline in a ThreadPoolExecutor so the async event-loop
   is never blocked by CPU-bound ML work.
4. Invalidate any in-process caches on AlertService / DashboardService
   so subsequent API calls see the new data immediately.
5. Return a structured UploadResponse.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
import uuid
from typing import Optional

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.ml.pipeline import PipelineResult, StepResult, run_pipeline
from app.schemas.upload_schema import StepSummary, UploadResponse

logger = logging.getLogger(__name__)

# Shared executor — avoids creating a new thread pool on every request
_EXECUTOR: Optional[ThreadPoolExecutor] = None

# Minimum expected columns for a valid raw-log CSV
_REQUIRED_COLUMNS = {"timestamp", "session_duration"}

# Maximum allowed file size (50 MB)
_MAX_FILE_BYTES = 50 * 1024 * 1024


def _get_executor() -> ThreadPoolExecutor:
    global _EXECUTOR
    if _EXECUTOR is None:
        _EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="ml-pipeline")
    return _EXECUTOR


class UploadService:
    """Handles CSV upload, validation, pipeline execution and response mapping."""

    def __init__(
        self,
        upload_dir: str,
        processed_dir: str,
        model_dir: str,
        contamination: float = 0.02,
    ) -> None:
        self._upload_dir = upload_dir
        self._processed_dir = processed_dir
        self._model_dir = model_dir
        self._contamination = contamination
        os.makedirs(upload_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process_upload(self, file: UploadFile) -> UploadResponse:
        """
        Validate, save, and pipeline-process an uploaded CSV file.

        Args:
            file: FastAPI UploadFile from the multipart/form-data request.

        Returns:
            UploadResponse with pipeline summary and per-step breakdown.

        Raises:
            HTTPException 400: invalid file type, empty file, missing columns.
            HTTPException 413: file exceeds 50 MB.
            HTTPException 422: CSV parsing failed.
            HTTPException 500: pipeline encountered an unrecoverable error.
        """
        original_name = file.filename or "upload.csv"
        logger.info("Received upload: %s", original_name)

        # ── 1. Read & validate ─────────────────────────────────────────
        raw_bytes = await file.read()
        self._validate_file(original_name, raw_bytes)

        df_raw = self._parse_csv(raw_bytes, original_name)

        # ── 2. Save raw file ───────────────────────────────────────────
        saved_path = self._save_raw(raw_bytes, original_name)
        logger.info("Saved raw upload → %s", saved_path)

        from app.services.audit_service import audit_service
        from app.schemas.audit_schema import AuditLogCreate, AuditActor, AuditCategory, AuditStatus
        await audit_service.log_event(
            AuditLogCreate(
                actor=AuditActor.BACKEND,
                action="CSV Uploaded",
                category=AuditCategory.SYSTEM,
                resource="upload",
                status=AuditStatus.SUCCESS,
                details=f"{len(df_raw)} records uploaded successfully from {original_name}."
            )
        )


        # ── 3. Run ML pipeline (in-process via thread to unblock event loop)
        try:
            from app.ml.pipeline import run_pipeline, PipelineResult
            pipeline_result: PipelineResult = await asyncio.to_thread(
                run_pipeline,
                df_raw,
                self._processed_dir,
                self._model_dir,
                self._contamination,
            )
        except Exception as exc:
            logger.exception("Pipeline failed critically")
            
            from app.services.audit_service import audit_service
            from app.schemas.audit_schema import AuditLogCreate, AuditActor, AuditCategory, AuditStatus
            await audit_service.log_event(
                AuditLogCreate(
                    actor=AuditActor.BACKEND,
                    action="Upload Failed",
                    category=AuditCategory.ERRORS,
                    resource="upload",
                    status=AuditStatus.FAILED,
                    details=f"Internal pipeline error: {exc}"
                )
            )

            raise HTTPException(
                status_code=500,
                detail=f"Internal pipeline error: {exc}"
            ) from exc

        # ── 4. Map result → response ───────────────────────────────────
        return self._build_response(len(df_raw), pipeline_result)

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_file(filename: str, raw_bytes: bytes) -> None:
        if not filename.lower().endswith(".csv"):
            raise HTTPException(
                status_code=400,
                detail=f"Only CSV files are accepted. Got: '{filename}'.",
            )
        if len(raw_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        if len(raw_bytes) > _MAX_FILE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({len(raw_bytes)//1024//1024} MB). Maximum is 50 MB.",
            )

    @staticmethod
    def _parse_csv(raw_bytes: bytes, filename: str) -> pd.DataFrame:
        try:
            import io
            df = pd.read_csv(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise HTTPException(
                status_code=422,
                detail=f"Failed to parse CSV '{filename}': {exc}",
            ) from exc

        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="The uploaded CSV contains no data rows.",
            )

        missing = _REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"CSV is missing required column(s): {sorted(missing)}. "
                    f"Found: {sorted(df.columns.tolist())}"
                ),
            )

        logger.info("Parsed CSV: %d rows × %d columns", len(df), len(df.columns))
        return df

    # ------------------------------------------------------------------
    # File persistence
    # ------------------------------------------------------------------

    def _save_raw(self, raw_bytes: bytes, original_name: str) -> str:
        """Save the raw bytes with a UUID prefix to avoid collisions."""
        safe_name = f"{uuid.uuid4().hex}_{original_name}"
        path = os.path.join(self._upload_dir, safe_name)
        with open(path, "wb") as fh:
            fh.write(raw_bytes)
        return path

    # ------------------------------------------------------------------
    # Response mapping
    # ------------------------------------------------------------------

    @staticmethod
    def _build_response(
        rows_uploaded: int,
        result: PipelineResult,
    ) -> UploadResponse:
        return UploadResponse(
            success=result.success,
            processed_records=rows_uploaded,
            anomalies_detected=result.anomalies_detected,
            alerts_created=result.anomalies_detected,
            message="Upload completed successfully." if result.success else "Upload completed with some step failures."
        )
