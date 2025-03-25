from fastapi import APIRouter, Depends, HTTPException

from src.core.celery_tasks import celery, redis, celery_get_posts
from src.schemas.task import TaskGetReqModel, AllTasksGetReqModel, CollectResModel
from src.dependencies import get_account_repository, get_post_repository, get_comment_repository

from src.repositories.post import PostRepository
from src.repositories.account import AccountRepository
from src.repositories.comment import CommentRepository

from src.core.worker import Worker

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


@router.post("/publish-posts", response_model=dict)
async def publish_saved_posts_endpoint(
    source_channel: str,
    target_channel: str,
    post_repo: PostRepository = Depends(get_post_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository)
):
    """
    Публикует сохранённые в базе данных посты в указанный канал.

    - **target_channel**: идентификатор или ссылка на канал, куда будут опубликованы посты.
    """
    worker = Worker(post_repo=post_repo, account=account_repo.get_account(), comment_repo=comment_repo)
    try:
        await worker.publish_saved_posts(
            source_channel=source_channel,
            target_channel=target_channel
            )
        return {"message": "Posts published successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.post("/subscribe", response_model=dict)
async def subscribe_to_channel(
    channel_username: str,
    post_repo: PostRepository = Depends(get_post_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    comment_repo: CommentRepository = Depends(get_comment_repository)
):
    worker = Worker(post_repo=post_repo, account=account_repo.get_account(), comment_repo=comment_repo)
    try:
        await worker.subscribe(
            channel_username=channel_username,
            )
        return {"message": f"Subscribed to {channel_username} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    