# celery -A src.celery_tasks worker --loglevel=INFO --purge
import asyncio
import logging

from celery import Celery
from redis import Redis

from src.core.config import Config
from src.core.worker import Worker
from src.dependencies import get_db
from src.schemas.task import CollectReqModel

celery = Celery("celery_task", broker=Config().broker, backend=Config().backend)
redis = Redis(host=Config().REDIS_HOST, port=Config().REDIS_PORT, db=1)

logger = logging.getLogger(__name__)


@celery.task
def celery_get_comments(request: dict):

    with get_db() as session:
        worker = Worker(session)

    asyncio.run(
        worker.get_comments(CollectReqModel.model_validate(request)),
    )

