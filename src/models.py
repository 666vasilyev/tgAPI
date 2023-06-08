from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel

from db.models import ProxyType, ResultStatus
from utils import as_form


class DataModel(BaseModel):
    url: str
    source_id: str


class CollectReqModel(BaseModel):
    task_id: None | int
    data: list[DataModel]
    limit: int = 100
    asc: bool


class CollectResModel(BaseModel):
    task_id: str


class TaskModel(BaseModel):
    id: str
    celery_id: Optional[str]
    status: str

    class Config:
        orm_mode = True


class GetTasksModel(BaseModel):
    tasks: list[TaskModel]


class ResultModel(BaseModel):
    url: str
    source_type: str
    date_parsed: datetime
    reactions: Any
    result: Any
    status: ResultStatus

    class Config:
        orm_mode = True


class GetTaskResModel(BaseModel):
    task_status: Optional[str]
    results: list[ResultModel]


class PostProxyModel(BaseModel):
    addr: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: ProxyType

    class Config:
        orm_mode = True

    def get_url(self):
        return {
            self.proxy_type: f"{self.proxy_type}://{self.username}:{self.password}@{self.addr}:{self.port}"
            if self.username is not None and self.password is not None
            else f"{self.proxy_type}://{self.addr}:{self.port}"
        }


class PostProxyResModel(BaseModel):
    proxy_id: int


@as_form
class PutProxyModel(BaseModel):
    addr: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: Optional[ProxyType] = None


class PutProxyResModel(PostProxyResModel):
    pass


class SampleAccountModel(BaseModel):
    account_id: int
    proxy_id: int