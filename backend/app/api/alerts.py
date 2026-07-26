"""
app/api/alerts.py

Router for anomaly alert endpoints.

Endpoints
---------
GET /alerts   — paginated list of anomaly alerts, sorted by highest risk first.

Query parameters
----------------
page        : int  (default 1)       — 1-indexed page number
page_size   : int  (default 50, max 200) — records per page
severity    : AlertSeverity (optional) — filter by severity band
status      : AlertStatus   (optional) — filter by triage status
"""

from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_alert_service
from app.schemas.alert_schema import AlertDetail, AlertSeverity, AlertStatus, PaginatedAlertResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=PaginatedAlertResponse,
    summary="List anomaly alerts",
    description=(
        "Returns a **paginated, risk-sorted** list of alerts derived from the ML pipeline.\n\n"
        "Each alert includes:\n"
        "- **id** — deterministic identifier (`alert-NNNNNN`)\n"
        "- **risk** — normalised score in [0, 100]; 100 = highest risk\n"
        "- **severity** — `low | medium | high | critical` (derived from risk)\n"
        "- **attack_type** — predicted category or `'Behavioral Anomaly'`\n"
        "- **status** — triage status (`open` by default)\n"
        "- **timestamp** — time of the original access session\n\n"
        "Results are sorted by **risk descending** (highest threat first)."
    ),
)
async def get_alerts(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)."),
    page_size: int = Query(
        default=50, ge=1, le=200, alias="page_size",
        description="Number of alerts per page (max 200).",
    ),
    severity: Optional[AlertSeverity] = Query(
        default=None, description="Filter by severity level."
    ),
    status: Optional[AlertStatus] = Query(
        default=None, description="Filter by triage status."
    ),
    alert_service: AlertService = Depends(get_alert_service),
) -> PaginatedAlertResponse:
    """
    Lists anomaly alerts read from classified_predictions.csv.
    Only sessions flagged by the Isolation Forest (anomaly_prediction == -1)
    are returned. Results are sorted by risk score descending.
    """
    return await alert_service.list_alerts(
        severity=severity,
        status_filter=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertDetail,
    summary="Get alert detail",
    description=(
        "Returns the **complete detail** for a single anomaly alert.\n\n"
        "Fields returned:\n"
        "- **attack** (`attack_type`) — predicted attack category\n"
        "- **risk** — normalised risk score [0–100]\n"
        "- **source_ip** — originating IP address\n"
        "- **geo_location** — city, country, latitude, longitude\n"
        "- **device** — device ID, type, OS, browser\n"
        "- **recommended_action** — contextual SOC remediation guidance\n"
        "- **shap_explanation** — top contributing features with SHAP values and human-readable descriptions\n\n"
        "Raises **404** if the ID does not correspond to a flagged threat row."
    ),
)
async def get_alert_by_id(
    alert_id: str = Path(
        description="Alert ID in the format `alert-NNNNNN` (e.g. `alert-076649`).",
        example="alert-076649",
    ),
    alert_service: AlertService = Depends(get_alert_service),
) -> AlertDetail:
    """
    Fetch full details for a single alert by its ID.
    Reads from explanations.csv (preferred) or classified_predictions.csv.
    """
    return await alert_service.get_alert_by_id(alert_id)
