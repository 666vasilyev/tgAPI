# celery -A celery_tasks worker --loglevel=INFO --purge -P eventlet
import asyncio
import dataclasses
import logging
from telethon.errors.rpcerrorlist import MsgIdInvalidError
from celery import Celery
from config import Config
from db.models import TaskStatus, Task, ParsingResult, SourceType
from db.queries import get_session
from models import CollectReqModel
from utils import explode_link
from worker import get_comments_stack

celery = Celery("celery_task", broker=Config().broker(), backend=Config().backend())
logger = logging.getLogger(__name__)


@dataclasses.dataclass(kw_only=True)
class TaskModel:
    task_id: int
    url: str
    source_id: str
    limit: int
    sort: str
    channel_name: str
    message_id: str


def get_sources(request: CollectReqModel):
    sort = "asc" if request.asc else "desc"

    return [
        {
            "task_id": request.task_id,
            "url": item.url,
            "source_id": item.source_id,
            "limit": request.limit,
            "sort": sort,
            **explode_link(item.url),
        }
        for item in request.data
    ]


# TODO: Сделать протухание задач
@celery.task
def celery_get_comments(request: dict):
    asyncio.run(
        _celery_get_comments(CollectReqModel.parse_obj(request)),
    )


async def _celery_get_comments(request: CollectReqModel):
    try:
        logging.basicConfig(level=logging.DEBUG)
        sources = get_sources(request)

        # results = await asyncio.gather(
        #     *[
        #         # TODO: Подумать, что сделать с accounts.
        #         #  Не должны они собираться в основной функции и тут же после использоваться
        #         #   как полноценные объекты
        #         get_comments_stack(
        #             accounts[n],
        #             Config().API_ID,
        #             Config().API_HASH,
        #             stack,
        #             list(accounts),
        #             request.task_id,
        #         )
        #         for n, stack in enumerate(stacks)
        #     ],
        #     return_exceptions=False,
        # )
        results = await asyncio.gather(
            *[
                get_comments_stack(
                    Config().API_ID,
                    Config().API_HASH,
                    source,
                    request.task_id,
                )
                for source in sources
            ],
            return_exceptions=False,
        )

        async with get_session() as session:
            logger.info("\n".join([r.reactions for r in results]))
            session.add_all(results)
            task = await session.get(Task, request.task_id)
            task.status = TaskStatus.DONE
            await session.commit()
    except Exception as e:
        logger.error(e)
        async with get_session() as session:
            task = await session.get(Task, request.task_id)
            task.status = TaskStatus.ERROR
            session.add(
                ParsingResult(
                    task_id=task.id,
                    url="None",
                    result=str(e),
                    reactions="None",
                    source_type=SourceType.RESTRICTED
                    if isinstance(e, MsgIdInvalidError)
                    else SourceType.CHANNEL,
                )
            )
            await session.commit()
