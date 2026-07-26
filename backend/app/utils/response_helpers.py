"""
app/utils/response_helpers.py

Small shared helpers for building consistent API responses.
"""

from typing import Any, Optional

from app.schemas.common import GenericResponse


def success_response(data: Optional[Any] = None, message: str = "") -> GenericResponse:
    """Wraps data in the standard GenericResponse success envelope."""
    return GenericResponse(success=True, message=message, data=data)
