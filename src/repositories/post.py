import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.db.models import Post

logger = logging.getLogger(__name__)


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_post(
        self,
        post_id: int,
        channel_id: str,
        url: str,
        text: str,
        media: str,
        reactions: str,
        date: datetime
    ) -> None:
        """
        Создает пост.
        """
        try:
            new_post = Post(
                post_id=post_id,
                channel_id=channel_id,
                url=url,
                text=text,
                media=media,
                reactions=reactions,
                time=date
            )
            self.db.add(new_post)
            self.db.commit()
        except IntegrityError:
            logger.info('Post already exists')

    def get_posts(self) -> list[Post]:
        """
        Возвращает все посты.
        """
        return self.db.query(Post).all()
