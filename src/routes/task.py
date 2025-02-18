from fastapi import APIRouter

from src.core.celery_tasks import celery, redis, celery_get_posts
from src.schemas.task import TaskGetReqModel, AllTasksGetReqModel, CollectResModel

router = APIRouter()

@router.get("/{task_id}")
async def get_task_by_id(task_id: str):
    task = celery.AsyncResult(task_id)
    task_status = task.status
    task_result = redis.get(task_id)
    return TaskGetReqModel(
        task_id=task_id, task_status=task_status, task_result=task_result
    )


@router.get("/")
async def get_tasks():
    keys = redis.keys("celery-task-meta-*")

    task_ids = [key.decode("utf-8").split("-", 3)[-1] for key in keys]

    tasks = []
    for task_id in task_ids:
        task = await get_task_by_id(task_id)
        tasks.append(task)

    return AllTasksGetReqModel(tasks=tasks)


@router.post("/", response_model=CollectResModel)
async def create_task(
    channel_link: str,
    limit: int,
):

    celery_task = celery_get_posts.delay({
        "channel_link": channel_link,
        "limit": limit,
    })

    return CollectResModel(task_id=celery_task.id)
