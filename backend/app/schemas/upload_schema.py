"""
app/schemas/upload_schema.py

Pydantic response schemas for POST /upload.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StepSummary(BaseModel):
    """Result of a single pipeline step."""

    name: str = Field(description="Step identifier (e.g. 'feature_engineering').")
    success: bool
    rows_in: int = Field(default=0, description="Rows entering this step.")
    rows_out: int = Field(default=0, description="Rows produced / modified by this step.")
    duration_s: float = Field(default=0.0, description="Wall-clock time in seconds.")
    detail: str = Field(default="", description="Human-readable summary of what happened.")
    error: Optional[str] = Field(default=None, description="Error message if step failed.")


class UploadResponse(BaseModel):
    """
    Response body for POST /upload.
    Matches the exact JSON schema required by the frontend.
    """
    success: bool = Field(description="True only if all critical pipeline steps succeeded.")
    processed_records: int = Field(description="Total rows in the uploaded CSV.")
    anomalies_detected: int = Field(description="Number of sessions flagged as anomalous by IsolationForest.")
    alerts_created: int = Field(description="Number of alerts generated (matches anomalies_detected).")
    message: str = Field(description="Success or error message.")
