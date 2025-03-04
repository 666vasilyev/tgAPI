from fastapi import Depends
from sqlalchemy.orm import Session
from contextlib import contextmanager

from src.repositories.account import AccountRepository
from src.repositories.proxy import ProxyRepository
from src.repositories.post import PostRepository
from src.repositories.comment import CommentRepository

from src.db.session import SessionLocal

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_account_repository(db: Session = Depends(get_db_dep)) -> AccountRepository:
    """
    Зависимость для получения экземпляра AccountRepository.
    """
    return AccountRepository(db)

def get_comment_repository(db: Session = Depends(get_db_dep)) -> CommentRepository:
    """
    Зависимость для получения экземпляра CommentRepository.
    """
    return CommentRepository(db)


def get_proxy_repository(db: Session = Depends(get_db_dep)) -> ProxyRepository:
    """
    Зависимость для получения экземпляра ProxyRepository.
    """
    return ProxyRepository(db)


def get_post_repository(db: Session = Depends(get_db_dep)) -> PostRepository:
    """
    Зависимость для получения экземпляра PostRepository.
    """
    return PostRepository(db)

