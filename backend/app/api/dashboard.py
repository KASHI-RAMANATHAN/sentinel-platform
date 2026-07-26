"""
app/api/dashboard.py

Router for dashboard/summary statistics endpoints.

Endpoints
---------
GET /dashboard        — primary endpoint (returns DashboardStatsResponse)
GET /dashboard/stats  — alias kept for backward compatibility
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_dashboard_service
from app.schemas.dashboard_schema import DashboardStatsResponse, TrendResponse, DistributionResponse, NetworkTrafficResponse, ConnectionProtocolsResponse
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


async def _fetch_stats(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStatsResponse:
    """Shared handler — delegates to DashboardService.get_stats()."""
    return await dashboard_service.get_stats()


@router.get(
    "",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics",
    description=(
        "Returns aggregate statistics computed from the ML pipeline output:\n\n"
        "- **total_sessions** – total number of access sessions in the dataset\n"
        "- **active_threats** – sessions flagged as anomalies (`anomaly_prediction == -1`)\n"
        "- **average_risk_score** – negated mean Isolation Forest score (higher = riskier)\n"
        "- **devices_monitored** – unique device IDs observed\n"
        "- **top_attack_types** – top-5 predicted attack categories (threats only)\n"
        "- **severity_breakdown** – threats bucketed into Low/Medium/High/Critical\n"
    ),
)
async def get_dashboard(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStatsResponse:
    """Primary dashboard endpoint — reads classified_predictions.csv."""
    return await dashboard_service.get_stats()


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Get dashboard statistics (alias)",
    include_in_schema=True,
)
async def get_dashboard_stats(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DashboardStatsResponse:
    """/dashboard/stats — backward-compatible alias for GET /dashboard."""
    return await dashboard_service.get_stats()


@router.get(
    "/trends",
    response_model=TrendResponse,
    summary="Get anomaly trends over time",
)
async def get_dashboard_trends(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> TrendResponse:
    """Returns anomaly trends for the line chart."""
    return await dashboard_service.get_trends()


@router.get(
    "/distribution",
    response_model=DistributionResponse,
    summary="Get attack distribution",
)
async def get_dashboard_distribution(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> DistributionResponse:
    """Returns the distribution of attack types for the pie chart."""
    return await dashboard_service.get_distribution()


@router.get(
    "/network",
    response_model=NetworkTrafficResponse,
    summary="Get network traffic (ingress vs egress)",
)
async def get_dashboard_network(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> NetworkTrafficResponse:
    """Returns network traffic based on session lengths and commands."""
    return await dashboard_service.get_network_traffic()


@router.get(
    "/protocols",
    response_model=ConnectionProtocolsResponse,
    summary="Get top connection protocols",
)
async def get_dashboard_protocols(
    dashboard_service: DashboardService = Depends(get_dashboard_service),
) -> ConnectionProtocolsResponse:
    """Returns the top connection protocols used in sessions."""
    return await dashboard_service.get_connection_protocols()
