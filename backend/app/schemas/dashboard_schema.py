"""
app/schemas/dashboard_schema.py

Pydantic response schemas for dashboard/summary statistics endpoints.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SeverityBreakdown(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0


class TrendResponse(BaseModel):
    labels: List[str]
    normal: List[int]
    anomaly: List[int]


class DistributionResponse(BaseModel):
    labels: List[str]
    values: List[int]


class NetworkTrafficResponse(BaseModel):
    labels: List[str]
    ingress: List[int]
    egress: List[int]


class ConnectionProtocol(BaseModel):
    name: str
    count: int


class ConnectionProtocolsResponse(BaseModel):
    protocols: List[ConnectionProtocol]


class DashboardStatsResponse(BaseModel):
    """Response schema for GET /dashboard."""

    total_sessions: int = Field(
        0, description="Total number of access sessions in the dataset."
    )
    active_threats: int = Field(
        0, description="Number of sessions flagged as anomalies (anomaly_prediction == -1)."
    )
    average_risk_score: float = Field(
        0.0, description="Mean anomaly score across all sessions (lower = more anomalous)."
    )
    devices_monitored: int = Field(
        0, description="Number of unique devices observed in the dataset."
    )

    # Extended fields for richer dashboard context
    total_logs_ingested: int = Field(
        0, description="Alias for total_sessions, for compatibility."
    )
    top_attack_types: Optional[List[Dict]] = Field(
        default=None, description="Top attack types from classified predictions."
    )
    severity_breakdown: SeverityBreakdown = Field(
        default_factory=SeverityBreakdown,
        description="Breakdown of threat severity."
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of when stats were computed."
    )
