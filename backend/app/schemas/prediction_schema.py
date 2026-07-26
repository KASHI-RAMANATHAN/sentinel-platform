"""
app/schemas/prediction_schema.py

Pydantic request/response schemas for POST /predict.

The request accepts one raw log record. The service layer derives
all model features from it and returns a structured prediction.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request — one raw log record
# ---------------------------------------------------------------------------

class LogRecordRequest(BaseModel):
    """
    A single access-log record to score.

    All fields mirror the columns in access_logs_processed.csv.
    Fields used directly by the models are marked (model feature).
    Fields marked optional are used for enrichment / context only.
    """

    # ── Time context (model features derived from these) ──────────────
    timestamp: Optional[datetime] = Field(
        default=None,
        description="ISO-8601 timestamp of the session. Used to derive login_hour and day_of_week.",
        example="2026-05-25T02:30:00",
    )

    # ── Direct model features (can be supplied instead of raw fields) ──
    login_hour: Optional[int] = Field(
        default=None, ge=0, le=23,
        description="(model feature) Hour of login (0-23). Derived from timestamp if not supplied.",
    )
    day_of_week: Optional[int] = Field(
        default=None, ge=0, le=6,
        description="(model feature) Day of week (0=Mon … 6=Sun). Derived from timestamp if not supplied.",
    )
    session_duration: float = Field(
        default=0.0, ge=0,
        description="(model feature) Session duration in minutes.",
        example=180.0,
    )
    command_length: int = Field(
        default=0, ge=0,
        description="(model feature) Number of commands executed in the session.",
        example=5,
    )
    unique_resources: int = Field(
        default=1, ge=0,
        description="(model feature) Number of distinct resources accessed.",
        example=8,
    )
    failed_login_count: int = Field(
        default=0, ge=0,
        description="(model feature) Number of failed login attempts in this session.",
        example=3,
    )
    is_known_device: int = Field(
        default=1, ge=0, le=1,
        description="(model feature) 1 if device was previously seen for this user, else 0.",
        example=0,
    )
    is_known_location: int = Field(
        default=1, ge=0, le=1,
        description="(model feature) 1 if location was previously seen for this user, else 0.",
        example=0,
    )
    auth_method_encoded: int = Field(
        default=0, ge=0,
        description="(model feature) Encoded authentication method.",
        example=1,
    )
    entity_type_encoded: int = Field(
        default=0, ge=0,
        description="(model feature) Encoded entity/role type.",
        example=2,
    )

    # ── Contextual fields (enrichment only, not used by model) ────────
    user_id: Optional[str] = Field(default=None, example="U00673")
    username: Optional[str] = Field(default=None, example="srocha")
    source_ip: Optional[str] = Field(default=None, example="114.162.72.184")
    device_id: Optional[str] = Field(default=None, example="DEV02151")
    resource: Optional[str] = Field(default=None, example="Email")
    login_method: Optional[str] = Field(default=None, example="Password")
    login_success: Optional[bool] = Field(default=None, example=True)

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-05-25T02:30:00",
                "session_duration": 180.0,
                "command_length": 5,
                "unique_resources": 8,
                "failed_login_count": 3,
                "is_known_device": 0,
                "is_known_location": 0,
                "user_id": "U00673",
                "username": "srocha",
                "source_ip": "114.162.72.184",
                "device_id": "DEV02151",
                "resource": "Email",
                "login_method": "Password",
                "login_success": True,
            }
        }


# ---------------------------------------------------------------------------
# SHAP explanation sub-model
# ---------------------------------------------------------------------------

class ShapFeatureContribution(BaseModel):
    """A single SHAP feature attribution."""

    feature: str
    shap_value: float = Field(description="Negative = pushes toward anomaly.")
    description: str = Field(description="Human-readable explanation of the feature's contribution.")


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class PredictionResponse(BaseModel):
    """Response body for POST /predict."""

    model_config = {"protected_namespaces": ()}

    # Core prediction outputs
    is_anomaly: bool = Field(description="True if the session was flagged as anomalous.")
    risk_score: float = Field(description="Normalised risk score [0–100]. 100 = highest risk.")
    predicted_attack: str = Field(
        description="Predicted attack category, or 'Normal' / 'Behavioral Anomaly'."
    )
    confidence: float = Field(
        description="Attack classifier's confidence in the predicted class [0–1]."
    )

    # SHAP explanation
    explanation: List[ShapFeatureContribution] = Field(
        default_factory=list,
        description="Top SHAP feature contributions driving the anomaly score.",
    )
    explanation_summary: str = Field(
        default="",
        description="Natural-language summary of why the session was flagged.",
    )

    # Context echoed back
    user_id: Optional[str] = None
    source_ip: Optional[str] = None
    device_id: Optional[str] = None

    # Metadata
    anomaly_score_raw: float = Field(
        description="Raw IsolationForest decision_function score (more negative = more anomalous)."
    )
    model_version: str = Field(default="isolation_forest_v1+random_forest_v1")
    generated_at: datetime = Field(default_factory=datetime.utcnow)
