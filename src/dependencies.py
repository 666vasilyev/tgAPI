from fastapi import Depends
from sqlalchemy.orm import Session

from src.repositories.account import AccountRepository
from src.repositories.proxy import ProxyRepository
from src.repositories.comment import CommentRepository
from src.repositories.post import PostRepository
from src.repositories.channel import ChannelRepository

from src.db.session import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_account_repository(db: Session = Depends(get_db)) -> AccountRepository:
    """
    Зависимость для получения экземпляра AccountRepository.
    """
    return AccountRepository(db)


def get_proxy_repository(db: Session = Depends(get_db)) -> ProxyRepository:
    """
    Зависимость для получения экземпляра ProxyRepository.
    """
    return ProxyRepository(db)


def get_comment_repository(db: Session = Depends(get_db)) -> CommentRepository:
    """
    Зависимость для получения экземпляра CommentRepository.
    """
    return CommentRepository(db)


def get_post_repository(db: Session = Depends(get_db)) -> PostRepository:
    """
    Зависимость для получения экземпляра PostRepository.
    """
    return PostRepository(db)


def get_channel_repository(db: Session = Depends(get_db)) -> ChannelRepository:
    """
    Зависимость для получения экземпляра ChannelRepository.
    """
    return ChannelRepository(db)
