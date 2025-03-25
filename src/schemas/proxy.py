from typing import Optional
from pydantic import BaseModel

from src.utils.utils import as_form
from src.db.models import ProxyType


@as_form
class PutProxyModel(BaseModel):
    addr: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: Optional[ProxyType] = None



class PostProxyModel(BaseModel):
    addr: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: ProxyType

    class Config:
        from_attributes = True

    def get_url(self):
        return {
            self.proxy_type: f"{self.proxy_type}://{self.username}:{self.password}@{self.addr}:{self.port}"
            if self.username is not None and self.password is not None
            else f"{self.proxy_type}://{self.addr}:{self.port}"
        }



class PostProxyResModel(BaseModel):
    proxy_id: int


