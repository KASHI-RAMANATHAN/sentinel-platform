"""
app/schemas/common.py

Shared/generic Pydantic response schemas used across multiple routers.
"""

from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthCheckResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str = Field(default="ok", description="Overall service status")
    app_name: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    firebase_connected: bool = Field(
        default=False, description="Placeholder — real Firebase ping not yet implemented"
    )


class GenericResponse(BaseModel, Generic[T]):
    """Generic success envelope for simple endpoints."""

    success: bool = True
    message: str = ""
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Standard error response schema."""

    success: bool = False
    error_code: str
    message: str
    details: Optional[Any] = None
