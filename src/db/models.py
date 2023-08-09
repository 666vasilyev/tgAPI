import datetime
import enum
from typing import Optional, List

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ProxyType(str, enum.Enum):
    HTTPS = "https"
    SOCKS4 = "socks4"
    SOCKS5 = "socks5"


class Base(DeclarativeBase):
    pass


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    login: Mapped[str] = mapped_column(nullable=False, unique=True)
    # TODO: Вынести в отдельный enum статусов
    status: Mapped[str] = mapped_column(default="active")
    requests: Mapped[int] = mapped_column(default=0)
    proxy_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("proxies.id", ondelete="SET NULL"), nullable=True
    )
    proxy: Mapped[Optional["Proxy"]] = relationship()

    def __repr__(self):
        return f"<Account {self.login=} {self.status=}>"


class Proxy(Base):
    __tablename__ = "proxies"
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


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    DONE = "done"
    ERROR = "error"


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    celery_id: Mapped[Optional[str]] = mapped_column(nullable=True)
    results: Mapped[List["ParsingResult"]] = relationship(
        "ParsingResult", back_populates="task", cascade="all,delete"
    )
    status: Mapped[TaskStatus] = mapped_column(default=TaskStatus.PENDING)


class ResultStatus(str, enum.Enum):
    FAILURE = "failed"
    SUCCESS = "success"


class SourceType(str, enum.Enum):
    CHANNEL = "channel"
    RESTRICTED = "restricted"


class ParsingResult(Base):
    __tablename__ = "parsing_results"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    task: Mapped[Task] = relationship("Task")
    url: Mapped[str] = mapped_column()
    source_type: Mapped[str] = mapped_column(default=SourceType.CHANNEL)
    date_parsed: Mapped[datetime.datetime] = mapped_column(server_default=text("NOW()"))
    reactions: Mapped[str] = mapped_column()
    result: Mapped[str] = mapped_column()
    status: Mapped[ResultStatus] = mapped_column(default=ResultStatus.FAILURE)

    def __repr__(self):
        return f"<ParsingResult {self.status=} {self.result=}>"



class ChannelType(str, enum.Enum):
    ul = "ультра левый"
    l = "левый"
    n =  "нейтральняый"
    r = "правый"
    ur= "ультра правый"

class Channel(Base):
    channel_id: Mapped[str] = mapped_column()
    type: Mapped[ChannelType] = mapped_column()

class Post(Base):
    __tablename__ = "Posts"
    post_id: Mapped[int] = mapped_column(primary_key=True)
    channel_id: Mapped[str] = mapped_column()
    url: Mapped[str] = mapped_column()
    text: Mapped[str] = mapped_column()
    media: Mapped[bytes] = mapped_column()
    reactions: Mapped[str] = mapped_column()
    time: Mapped[datetime.datetime] = mapped_column()


class Comment(Base):
    __tablename__ = "Comments"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column()
    text: Mapped[str] = mapped_column()
    user_id: Mapped[str] = mapped_column()
    time: Mapped[datetime.datetime] = mapped_column()

