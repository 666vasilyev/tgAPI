from pydantic import BaseModel

class SampleAccountModel(BaseModel):
    account_id: int
    proxy_id: int