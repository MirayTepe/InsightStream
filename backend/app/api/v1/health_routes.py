"""Health check and observability endpoints."""

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health", summary="Health check")
def health_check() -> dict[str, str]:
    """Basic liveness probe."""
    return {"status": "ok", "service": settings.project_name}


@router.get("/health/ready", summary="Readiness probe")
def readiness_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Readiness probe: checks DB connectivity.
    Used by orchestrators (K8s, Docker) to determine if the app can receive traffic.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "database": db_status,
    }


@router.get("/health/metrics", summary="Prometheus metrics")
def prometheus_metrics() -> str:
    """
    Prometheus metrics endpoint.
    In production, use prometheus_client to expose app metrics.
    """
    if not settings.prometheus_enabled:
        return "# Prometheus disabled\n"

    # Placeholder: actual metrics will be added when prometheus_client is used
    return "# HELP insightstream_info Application info\n# TYPE insightstream_info gauge\ninsightstream_info{env=\"" + settings.environment + "\"} 1\n"
