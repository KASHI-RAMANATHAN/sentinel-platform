"""
app/api/health.py

Health check router.

Simple liveness endpoint. Does not (yet) perform a real Firestore
connectivity check — see TODO below.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthCheckResponse, summary="Health check")
async def health_check() -> HealthCheckResponse:
    """
    Returns basic service liveness info.

    TODO: Add a real Firestore ping (e.g. a lightweight read) and
    reflect the result in `firebase_connected` instead of the current
    hardcoded False placeholder.
    """
    return HealthCheckResponse(
        status="ok",
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        firebase_connected=False,
    )
