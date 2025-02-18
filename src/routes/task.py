from fastapi import APIRouter, HTTPException, status

from src.core.celery_tasks import celery, redis, celery_get_comments
from src.schemas.task import TaskGetReqModel, AllTasksGetReqModel, CollectReqModel, CollectResModel

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
async def create_task(collect_model: CollectReqModel):
    if len(collect_model.data) <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Empty data"
        )

    celery_task = celery_get_comments.delay(collect_model.model_dump())

    return CollectResModel(task_id=celery_task.id)
