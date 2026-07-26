"""
app/schemas/log_schema.py

Pydantic request/response schemas for behavioral log ingestion.

These define the wire format for the "Upload Logs" endpoint. Actual
validation rules / required fields will be refined once the dataset
schema (ml/) is finalized.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    """
    A single behavioral/security log event.

    Field set is intentionally generic (source, user, action, metadata)
    so it can represent auth logs, network logs, endpoint logs, etc.
    Tighten this once the real log schema for the hackathon dataset
    is decided.
    """

    user_id: str = Field(..., description="Identifier of the user/entity the log belongs to")
    source: str = Field(..., description="Log source system, e.g. 'auth', 'network', 'endpoint'")
    action: str = Field(..., description="Action or event type, e.g. 'login', 'file_access'")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Free-form event metadata")


class LogUploadRequest(BaseModel):
    """Request body for POST /logs — a batch of one or more log entries."""

    logs: List[LogEntry]


class LogUploadResponse(BaseModel):
    """Response body confirming log ingestion (placeholder)."""

    received: int
    accepted: int
    rejected: int
    batch_id: Optional[str] = None
