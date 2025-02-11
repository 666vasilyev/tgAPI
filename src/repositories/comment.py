import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
        try:
            new_comment = Comment(
                id=comment_id,
                post_id=message_id,
                text=text,
                user_id=user_id,
                time=date
            )
            self.db.add(new_comment)
            self.db.commit()
        except IntegrityError:
            logger.info('Comment already exists')

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
