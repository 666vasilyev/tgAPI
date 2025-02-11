import logging
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from src.db.models import Channel
from src.db.channels_table import channels_table

logger = logging.getLogger(__name__)


class ChannelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_channels_table(self, data: list = channels_table) -> None:
        """
        Заполняет таблицу каналов данными.
        """
        try:
            for url, channel_type in data:
                channel = Channel(channel_id=url, type=channel_type)
                self.db.execute(
                    insert(Channel).values(
                        channel_id=channel.channel_id,
                        type=channel.type
                    )
                )
            self.db.commit()
        except IntegrityError:
            logger.info('Table "Channels" already exists')

    def get_channel_type_by_id(self, channel_id: str) -> str | None:
        """
        Возвращает тип канала по его ID.
        """
        channel = self.db.query(Channel).filter_by(channel_id=channel_id).first()
        return channel.type.value if channel and channel.type else None
