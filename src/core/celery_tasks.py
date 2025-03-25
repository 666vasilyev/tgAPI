# celery -A src.celery_tasks worker --loglevel=INFO --purge
import asyncio
import logging

from celery import Celery
from redis import Redis

from src.core.config import Config
from src.core.worker import Worker
from src.dependencies import get_db
from src.repositories.post import PostRepository
from src.repositories.account import AccountRepository
from src.repositories.comment import CommentRepository


celery = Celery("celery_task", broker=Config().broker, backend=Config().backend)
redis = Redis(host=Config().REDIS_HOST, port=Config().REDIS_PORT, db=1)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@celery.task
def celery_get_posts(params: dict): 

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())


    channel_link = params.get("channel_link")
    limit = params.get("limit")

    with get_db() as session:
        
        account_repo = AccountRepository(session)
        post_repo = PostRepository(session)
        comment_repo = CommentRepository(session)

        account = account_repo.get_account()

        worker = Worker(post_repo, account, comment_repo)

        asyncio.run(worker.run(channel_link=channel_link, limit=limit))

