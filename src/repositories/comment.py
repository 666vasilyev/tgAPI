import logging
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert

from src.db.models import Comment

logger = logging.getLogger(__name__)


class CommentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_comment(
        self,
        comment_id: int,
        message_id: int,
        text: str,
        user_id: int,
        date: datetime
    ) -> None:
        """
        Создает комментарий.
        """
        stmt = insert(Comment).values(
            id=comment_id,
            post_id=message_id,
            text=text,
            user_id=user_id,
            time=date
        ).on_conflict_do_nothing()

        try:
            self.db.execute(stmt)
            self.db.commit()
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error("Ошибка при создании комментария: %s", e)

    def get_comments(self) -> list[Comment]:
        """
        Возвращает все комментарии.
        """
        return self.db.query(Comment).all()

    def get_comments_by_post_id(self, post_id: int) -> list[Comment]:
        """
        Возвращает комментарии для заданного поста.
        """
        return self.db.query(Comment).filter_by(post_id=post_id).all()