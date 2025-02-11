# celery -A src.celery_tasks worker --loglevel=INFO --purge
import asyncio
import logging

from celery import Celery
from redis import Redis

from src.core.config import Config
from src.db.sync_crud import create_channels_table
from src.core.worker import get_comments
from src.schemas.task import CollectReqModel

celery = Celery("celery_task", broker=Config().broker(), backend=Config().backend())
redis = Redis(host=Config().REDIS_HOST, port=Config().REDIS_PORT, db=1)

logger = logging.getLogger(__name__)


@celery.task
def celery_get_comments(request: dict):
    asyncio.run(
        get_comments(CollectReqModel.parse_obj(request)),
    )


@celery.task
def celery_create_channels_table():
    asyncio.run(
        create_channels_table()
    )