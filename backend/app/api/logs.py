"""
app/api/logs.py

Router for log ingestion endpoints.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_log_service
from app.schemas.log_schema import LogUploadRequest, LogUploadResponse
from app.services.log_service import LogService

router = APIRouter(prefix="/logs", tags=["Logs"])


@router.post("", response_model=LogUploadResponse, summary="Upload behavioral logs")
async def upload_logs(
    request: LogUploadRequest,
    log_service: LogService = Depends(get_log_service),
) -> LogUploadResponse:
    """
    Ingests a batch of behavioral log entries.

    PLACEHOLDER: delegates to LogService.ingest_logs, which does not
    yet persist to Firestore or trigger the (not-yet-built) anomaly
    detection pipeline.
    """
    return await log_service.ingest_logs(request.logs)
