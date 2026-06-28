from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings

celery_app = Celery(
    "interviewloop_v2",
    broker=str(settings.redis_url),
    backend=str(settings.redis_url),
    include=[
        "app.workers.tasks.analytics_tasks",
        "app.workers.tasks.cleanup_tasks",
        "app.workers.tasks.email_tasks",
        "app.workers.tasks.report_tasks",
    ],
)

default_exchange = Exchange("interviewloop", type="direct")

celery_app.conf.update(
    accept_content=["json"],
    beat_schedule={
        "cleanup-soft-deleted-records-daily": {
            "task": "cleanup.soft_deleted_records",
            "schedule": 60 * 60 * 24,
        },
        "refresh-analytics-hourly": {
            "task": "analytics.refresh_all_users",
            "schedule": 60 * 60,
        },
    },
    broker_connection_retry_on_startup=True,
    result_serializer="json",
    task_acks_late=True,
    task_default_exchange="interviewloop",
    task_default_queue="default",
    task_default_routing_key="default",
    task_reject_on_worker_lost=True,
    task_routes={
        "analytics.*": {"queue": "analytics", "routing_key": "analytics"},
        "cleanup.*": {"queue": "maintenance", "routing_key": "maintenance"},
        "email.*": {"queue": "email", "routing_key": "email"},
        "reports.*": {"queue": "reports", "routing_key": "reports"},
    },
    task_queues=(
        Queue("default", default_exchange, routing_key="default"),
        Queue("analytics", default_exchange, routing_key="analytics"),
        Queue("email", default_exchange, routing_key="email"),
        Queue("maintenance", default_exchange, routing_key="maintenance"),
        Queue("reports", default_exchange, routing_key="reports"),
    ),
    task_serializer="json",
    timezone="UTC",
    worker_prefetch_multiplier=1,
)
