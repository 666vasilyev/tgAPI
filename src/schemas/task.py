from pydantic import BaseModel
from typing import Optional, List
from src.schemas.data import DataModel


class TaskGetReqModel(BaseModel):
    task_id: str
    task_status: str
    task_result: Optional[str]


class AllTasksGetReqModel(BaseModel):
    tasks: List[TaskGetReqModel]

class TaskModel(BaseModel):
    id: str
    celery_id: Optional[str]
    status: str

    class Config:
        from_attributes = True


class GetTasksModel(BaseModel):
    tasks: List[TaskModel]



class CollectReqModel(BaseModel):
    data: List[DataModel]
    limit: int = 100
    asc: bool


class CollectResModel(BaseModel):
    task_id: str
