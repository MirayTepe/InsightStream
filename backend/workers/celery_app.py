"""Celery application configuration."""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "insightstream",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
    include=["workers.tasks.pdf_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min max per task
    task_soft_time_limit=540,  # Soft limit 9 min
    worker_prefetch_multiplier=1,  # One task at a time for fairness
    task_acks_late=True,  # Ack after completion
    task_reject_on_worker_lost=True,
    result_expires=86400,  # 24h
)

celery_app.conf.task_routes = {
    "workers.tasks.pdf_tasks.process_pdf_task": {"queue": "pdf"},
}
