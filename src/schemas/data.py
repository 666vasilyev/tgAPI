from pydantic import BaseModel


class DataModel(BaseModel):
    url: str
    source_id: str


