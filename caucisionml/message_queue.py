from .config import settings
from celery import Celery

from pydantic import BaseSettings
from kombu import Exchange, Queue


class CeleryConfig(BaseSettings):
    TASK_QUEUES = (
        Queue('data_imported', routing_key='data_imported'),
    )
    TASK_ROUTES = {
        'train_model': {'queue': 'data_imported', 'routing_key': 'data_imported'}
    }

    TASK_PROTOCOL = 1


def initialize_celery() -> Celery:
    config = CeleryConfig()

    celery_app = Celery('tasks', broker=settings.CELERY_BROKER_URL)
    celery_app.conf.task_queues = config.TASK_QUEUES
    celery_app.conf.task_routes = config.TASK_ROUTES
    celery_app.conf.task_protocol = config.TASK_PROTOCOL

    return celery_app
