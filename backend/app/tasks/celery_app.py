from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "platform_tasks",
    broker=f"{settings.REDIS_URL}/0",
    backend=f"{settings.REDIS_URL}/0"
)
