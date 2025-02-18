import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

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
        date: datetime
    ) -> None:
        """
        Создает пост.
        """
        stmt = insert(Post).values(
            post_id=post_id,
            url=url,
            text=text,
            media=media,
            time=date
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
