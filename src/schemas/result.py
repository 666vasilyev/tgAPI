from pydantic import BaseModel
from datetime import datetime
from typing import Any


class ResultModel(BaseModel):
    url: str
    source_type: str
    date_parsed: datetime
    reactions: Any
    result: Any
    # status: ResultStatus

    class Config:
        from_attributes = True