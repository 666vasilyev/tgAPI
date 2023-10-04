import datetime
import enum
import json
from typing import Optional

from sqlalchemy import ForeignKey, Text

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChannelType(str, enum.Enum):
    ul = "ультра левый"
    l = "левый"
    n = "нейтральный"
    r = "правый"
    ur = "ультра правый"


class Channel(Base):
    __tablename__ = "Channels"
    channel_id: Mapped[str] = mapped_column(primary_key=True)
    type: Mapped[ChannelType] = mapped_column()


class Post(Base):
    __tablename__ = "Posts"
    post_id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[str] = mapped_column(ForeignKey("Channels.channel_id"))
    url: Mapped[str] = mapped_column()
    text: Mapped[str] = mapped_column()
    media: Mapped[str] = mapped_column()
    reactions: Mapped[str] = mapped_column()    
    time: Mapped[datetime.datetime] = mapped_column()

class Comment(Base):
    __tablename__ = "Comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("Posts.post_id"))
    text: Mapped[str] = mapped_column()
    user_id: Mapped[str] = mapped_column()
    time: Mapped[datetime.datetime] = mapped_column()


class Account(Base):
    __tablename__ = "Accounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(nullable=False, unique=True)
    # TODO: Вынести в отдельный enum статусов
    status: Mapped[str] = mapped_column(default="active")
    requests: Mapped[int] = mapped_column(default=0)
    proxy_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("Proxies.id", ondelete="SET NULL"), nullable=True
    )
    # proxy: Mapped[Optional["Proxy"]] = relationship()

    def __repr__(self):
        return f"<Account {self.login=} {self.status=}>"


class ProxyType(str, enum.Enum):
    HTTPS = "https"
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
    

# class Task(Base):
#     __tablename__ = "Tasks"
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     task_id: Mapped[str] = mapped_column(nullable=True)
#     task_status: Mapped[str] = mapped_column(default="pending")
#     detail: Mapped[str] = mapped_column(nullable=True)

