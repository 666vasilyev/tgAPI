import logging
import os
import socks

from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.tl.types import Message

from src.repositories.post import PostRepository
from src.core.config import Config
from src.db.models import Account

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, post_repo: PostRepository, account: Account):
        """
        Инициализация Worker.
        
        :param db: Сессия SQLAlchemy для работы с базой данных.
        :param api_id: Ваш api_id из my.telegram.org.
        :param api_hash: Ваш api_hash.
        :param session_name: Имя файла сессии Telethon.
        """
        self.config = Config()

        self.session_name = f'{self.config.SESSIONS_DIR}/{account.login}.session'

        self.proxy = (
            socks.HTTP, 
            account.proxy.addr, 
            account.proxy.port, 
            True,
            account.proxy.username, 
            account.proxy.password
            )
        
        self.post_repo = post_repo  # Инициализация репозитория постов

        self.api_id = self.config.API_ID
        self.api_hash = self.config.API_HASH
        self.media_dir = self.config.MEDIA_DIR

        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash, proxy=self.proxy)

    async def connect(self):
        """Подключение к Telegram через Telethon."""
        await self.client.start()
        logger.info("Подключение к Telegram успешно.")

    async def disconnect(self):
        """Отключение от Telegram."""
        await self.client.disconnect()
        logger.info("Отключение от Telegram выполнено.")

    async def fetch_channel_posts(self, channel_link: str, limit: int):
        """
        Получает сообщения из канала по ссылке и сохраняет их в базу данных через PostRepository.
        
        :param channel_link: Ссылка на Telegram-канал (например, "https://t.me/some_channel").
        """
        try:
            channel = await self.client.get_entity(channel_link)
        except Exception as e:
            logger.error(f"Ошибка получения канала {channel_link}: {e}")
            return

        logger.info(f"Начало сбора постов из канала: {getattr(channel, 'title', channel.id)}")

        # Итерация по сообщениям канала
        async for message in self.client.iter_messages(channel, limit=limit):
            if not message:
                continue

            await self.process_message(message, channel)

    async def process_message(self, message: Message, channel):
        """
        Преобразует сообщение Telethon в параметры для создания поста и вызывает метод create_post из PostRepository.
        """
        # Формирование URL поста, если у канала есть username
        if hasattr(channel, "username") and channel.username:
            url = f"https://t.me/{channel.username}/{message.id}"
        else:
            url = ""

        text = message.message or ""
        media = str(message.media) if message.media else ""

        post_date = message.date if message.date else datetime.now(timezone.utc)


        # Сохраняем медиа, если оно есть
        media_file_path = ""
        if message.media:
            # Генерируем имя файла на основе channel.id и message.id
            file_name = f"{channel.id}_{message.id}"
            file_path = os.path.join(self.media_dir, file_name)
            try:
                media_file_path = await self.client.download_media(message, file=file_path)
                logger.info(f"Медиа сохранено: {media_file_path}")
            except Exception as e:
                logger.error(f"Ошибка при скачивании медиа для сообщения {message.id}: {e}")
                media_file_path = ""

        # Сохранение поста через репозиторий
        self.post_repo.create_post(
            post_id=message.id,
            url=url,
            text=text,
            media=media,
            date=post_date
        )
        logger.info(f"Обработан пост с id: {message.id}")

    async def run(self, channel_link: str, limit: int):
        """
        Основной метод для запуска сборщика постов.
        
        :param channel_link: Ссылка на Telegram-канал.
        """
        await self.connect()
        try:
            await self.fetch_channel_posts(channel_link, limit)
        finally:
            await self.disconnect()
