"""Task status service for Celery job tracking."""

from typing import Any, Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class TaskService:
    """Retrieve Celery task status from Redis result backend."""

    def __init__(self) -> None:
        self._backend = None
        self._connect()

    def _connect(self) -> None:
        """Connect to Celery result backend."""
        try:
            from celery.result import AsyncResult
            from workers.celery_app import celery_app
            self._celery_app = celery_app
        except Exception as e:
            logger.warning("Celery not available for task status: %s", e)
            self._celery_app = None

    def get_status(self, task_id: str) -> dict[str, Any]:
        """
        Get task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY.
        Returns dict with status, result, error, etc.
        """
        if not self._celery_app:
            return {"status": "UNKNOWN", "error": "Celery not configured"}

        try:
            from celery.result import AsyncResult
            result = AsyncResult(task_id, app=self._celery_app)
            resp: dict[str, Any] = {"status": result.status}

            if result.ready():
                if result.successful():
                    resp["result"] = result.result
                else:
                    resp["error"] = str(result.result) if result.result else "Task failed"
            elif result.status == "STARTED":
                resp["info"] = getattr(result, "info", {}) or {}

            return resp
        except Exception as e:
            logger.warning("Failed to get task status: %s", e)
            return {"status": "UNKNOWN", "error": str(e)}
