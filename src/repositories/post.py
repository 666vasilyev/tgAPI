import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from typing import List

from src.db.models import Post

logger = logging.getLogger(__name__)


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_post(
        self,
        post_id: int,
        url: str,
        text: str,
        media: str,
        date: datetime,
        channel_id: str,
        reactions: str
    ) -> None:
        """
        Создает пост.
        """
        stmt = insert(Post).values(
            post_id=post_id,
            url=url,
            text=text,
            media=media,
            time=date,
            channel_id=channel_id,
            reactions=reactions,
            channel_name=url.split('/')[3]
        ).on_conflict_do_nothing(
            index_elements=['post_id']
        )
        
        try:
            self.db.execute(stmt)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Ошибка при создании поста: %s", e)

    def get_posts(self) -> list[Post]:
        """
        Возвращает все посты.
        """
        return self.db.query(Post).all()

    def get_posts_by_channel_id(self, channel_id: str) -> List[Post]:
        """
        Возвращает все посты для заданного channel_id.
        """
        return self.db.query(Post).filter(Post.channel_id == channel_id).all()
    
    def get_posts_by_channel_name(self, channel_name: str) -> List[Post]:
        """
        Возвращает все посты для заданного channel_name.
        """
        return self.db.query(Post).filter(Post.channel_name == channel_name).all()