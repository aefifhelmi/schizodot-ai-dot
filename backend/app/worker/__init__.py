# app/worker/__init__.py
"""
Celery worker configuration for SchizoDot AI
Handles background task processing for AI analysis
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "schizodot",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/1",
    include=["app.worker.tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=600,  # 10 minutes hard limit
    task_soft_time_limit=540,  # 9 minutes soft limit
    
    # Results
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },
    
    # Worker
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks
    
    # Retry policy
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
    
    # Logging
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s] [%(task_name)s(%(task_id)s)] %(message)s",
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    "app.worker.tasks.analyze_media": {"queue": "analysis"},
    "app.worker.tasks.process_emotion": {"queue": "ai"},
    "app.worker.tasks.process_object_detection": {"queue": "ai"},
}

__all__ = ["celery_app"]
