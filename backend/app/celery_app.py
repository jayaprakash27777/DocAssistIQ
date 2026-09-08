"""DocAssistIQ Backend — Celery Application.

Initializes the Celery task queue connected to the Redis broker.
Shared by both the FastAPI backend (for task dispatch) and the
Celery worker service (which consumes and executes tasks).

Tasks will be registered in later phases when background processing
features are implemented (e.g. document ingestion, AI inference pipelines).
"""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "docassistiq",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.ingestion"],  # Phase 13 Ingestion Framework
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)
