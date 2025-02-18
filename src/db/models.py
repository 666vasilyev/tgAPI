import datetime
import enum
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ChannelType(str, enum.Enum):
    ul = "ультра левый"
    l = "левый"
    n = "нейтральный"
    r = "правый"
    ur = "ультра правый"



class Post(Base):
    __tablename__ = "Posts"
    post_id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column()
    text: Mapped[str] = mapped_column()
    media: Mapped[str] = mapped_column()
    time: Mapped[datetime.datetime] = mapped_column()


class Account(Base):
    __tablename__ = "Accounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(nullable=False, unique=True)
    status: Mapped[str] = mapped_column(default="active")
    requests: Mapped[int] = mapped_column(default=0)
    proxy_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Proxies.id", ondelete="SET NULL"), nullable=True
    )
    proxy: Mapped[Optional["Proxy"]] = relationship()

    def __repr__(self):
        return f"<Account {self.login=} {self.status=}>"


class ProxyType(str, enum.Enum):
    HTTP = "http"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class Proxy(Base):
    __tablename__ = "Proxies"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    addr: Mapped[str] = mapped_column(nullable=False, unique=True)
    port: Mapped[int] = mapped_column()
    proxy_type: Mapped[ProxyType] = mapped_column()
    username: Mapped[Optional[str]] = mapped_column(nullable=True)
    password: Mapped[Optional[str]] = mapped_column(nullable=True)

    def as_dict(self) -> dict:
        return {
            "proxy_type": self.proxy_type,
            "addr": self.addr,
            "port": self.port,
            "username": self.username,
            "password": self.password,
        }
    
    def get_url(self) -> dict:
        return {
            self.proxy_type.value: f"{self.proxy_type}://{self.username}:{self.password}@{self.addr}:{self.port}"
            if self.username is not None and self.password is not None
            else f"{self.proxy_type}://{self.addr}:{self.port}"
        }
    
