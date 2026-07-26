"""
app/api/routes.py

Central API router aggregator.

Combines all individual routers (health, logs, alerts, predict,
dashboard) into a single `api_router` that main.py mounts under the
configured API prefix. Add new routers here as the platform grows —
main.py should never need to import individual routers directly.
"""

from fastapi import APIRouter

from app.api import alerts, dashboard, health, logs, predict, upload

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(logs.router)
api_router.include_router(alerts.router)
api_router.include_router(predict.router)
api_router.include_router(dashboard.router)
api_router.include_router(upload.router)
