"""
app/schemas/alert_schema.py

Pydantic request/response schemas for the Alerts API.

An "alert" is a session flagged as anomalous by the Isolation Forest
(anomaly_prediction == -1) in the ML pipeline output CSV.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


# ---------------------------------------------------------------------------
# Per-alert record
# ---------------------------------------------------------------------------

class AlertItem(BaseModel):
    """Schema representing a single anomaly alert derived from the ML pipeline."""

    id: str = Field(description="Deterministic row-based identifier (e.g. 'alert-00042').")
    risk_score: int = Field(
        description="Analyst-friendly risk score [0, 100]. 100 = most critical."
    )
    severity: AlertSeverity = Field(description="Severity bucket derived from risk score.")
    attack_type: str = Field(description="Predicted attack category.")
    status: AlertStatus = Field(
        default=AlertStatus.OPEN,
        description="Current triage status of the alert.",
    )
    timestamp: datetime = Field(description="Timestamp of the original access session.")

    # Optional enrichment fields
    entity_id: Optional[str] = Field(default=None, description="Entity/User associated with the session.")
    device_fingerprint: Optional[str] = Field(default=None, description="Device footprint of the session.")
    source_ip: Optional[str] = Field(default=None, description="Source IP address.")
    anomaly_score: float = Field(
        description="Raw Isolation Forest decision_function score (more negative = more anomalous)."
    )


# ---------------------------------------------------------------------------
# Paginated list response
# ---------------------------------------------------------------------------

class PaginatedAlertResponse(BaseModel):
    """Paginated response for GET /alerts."""

    total: int = Field(description="Total number of alerts matching the applied filters.")
    page: int = Field(description="Current page number (1-indexed).")
    page_size: int = Field(description="Number of alerts per page.")
    total_pages: int = Field(description="Total number of pages.")
    alerts: List[AlertItem] = Field(description="Alerts for the current page, sorted by risk descending.")


# ---------------------------------------------------------------------------
# Legacy schema kept for backward compatibility with other parts of the app
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Sub-models for AlertDetail
# ---------------------------------------------------------------------------

class ShapFeature(BaseModel):
    """A single SHAP feature contribution."""

    feature: str = Field(description="Feature name (e.g. 'login_hour').")
    shap_value: float = Field(description="SHAP contribution value (negative = pushes toward anomaly).")
    description: str = Field(description="Human-readable explanation of what the feature means.")


class ShapExplanation(BaseModel):
    """Structured SHAP explanation for an anomalous session."""

    top_features: List[ShapFeature] = Field(
        default_factory=list,
        description="Top contributing features, ordered by magnitude of SHAP value.",
    )
    summary: str = Field(
        default="",
        description="Natural-language summary produced by the explainability pipeline.",
    )


class DeviceInfo(BaseModel):
    """Device context associated with a session."""

    device_id: str
    device_type: Optional[str] = None
    os: Optional[str] = None
    browser: Optional[str] = None


class GeoLocation(BaseModel):
    """Geographical context of the session."""

    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


# ---------------------------------------------------------------------------
# Full alert detail (returned by GET /alerts/{id})
# ---------------------------------------------------------------------------

class AlertDetail(BaseModel):
    """Complete alert record returned by GET /alerts/{id}."""

    id: str
    timestamp: datetime
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    source_ip: Optional[str] = None
    geo_location: Optional[str] = None
    device_fingerprint: Optional[str] = None
    resource_accessed: Optional[str] = None
    auth_method: Optional[str] = None
    session_duration: Optional[float] = None
    command_sequence: Optional[str] = None
    login_success: Optional[bool] = None
    label: Optional[str] = None
    risk_score: int
    anomaly_score: float
    prediction: int = -1
    attack_type: str
    shap_explanation: ShapExplanation
    recommended_action: Optional[str] = None


# ---------------------------------------------------------------------------
# Legacy schemas — kept for backward compatibility with other parts of the app
# ---------------------------------------------------------------------------

class Alert(BaseModel):
    """Legacy schema — kept to avoid breaking existing imports."""

    id: Optional[str] = Field(default=None)
    user_id: str = ""
    title: str = ""
    description: Optional[str] = None
    severity: AlertSeverity = AlertSeverity.LOW
    status: AlertStatus = AlertStatus.OPEN
    risk_score: Optional[float] = None
    attack_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AlertListResponse(BaseModel):
    """Legacy response schema — kept for backward compatibility."""

    total: int
    alerts: List[Alert]
