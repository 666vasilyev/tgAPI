import logging
import os
import socks
import json
import glob

from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.tl.types import Message, Channel, ReactionCustomEmoji
from telethon.tl.functions.channels import JoinChannelRequest


from src.repositories.post import PostRepository
from src.repositories.comment import CommentRepository
from src.core.config import Config
from src.db.models import Account

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, post_repo: PostRepository, account: Account, comment_repo: CommentRepository):
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

        self.comment_repo = comment_repo
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

    async def process_message(self, message: Message, channel: Channel):
        """
        Преобразует сообщение Telethon в параметры для создания поста и вызывает метод create_post из PostRepository.
        """
        # Формирование URL поста, если у канала есть username
        if hasattr(channel, "username") and channel.username:
            url = f"https://t.me/{channel.username}/{message.id}"
        else:
            url = ""

        text = message.message or ""

        post_date = message.date if message.date else datetime.now(timezone.utc)

        # Сохраняем медиа, если оно есть
        media_file_path = ""
        if message.media:
            # Формируем шаблон для поиска старых файлов:
            # Например: "1234567_42*" – все файлы, начинающиеся c "{channel.id}_{message.id}"
            file_prefix_pattern = f"{channel.id}_{message.id}*"
            pattern_path = os.path.join(self.media_dir, file_prefix_pattern)

            # Удаляем все старые файлы, которые подходят под шаблон
            old_files = glob.glob(pattern_path)
            for old_file in old_files:
                try:
                    os.remove(old_file)
                    logger.info(f"Старый файл удалён: {old_file}")
                except Exception as ex:
                    logger.error(f"Ошибка при удалении файла {old_file}: {ex}")

            # Генерируем «основное» имя файла (без добавления .(1))
            file_name = f"{channel.id}_{message.id}"
            file_path = os.path.join(self.media_dir, file_name)

            try:
                # Скачиваем заново
                media_file_path = await self.client.download_media(message, file=file_path)
                logger.info(f"Медиа заново сохранено: {media_file_path}")
            except Exception as e:
                logger.error(f"Ошибка при скачивании медиа для сообщения {message.id}: {e}")
                media_file_path = ""

        data = message.reactions.results if message and message.reactions else []
        reactions = [(item.reaction.emoticon, item.count) for item in data if not isinstance(item.reaction, ReactionCustomEmoji)]
        # Сохранение поста через репозиторий
        self.post_repo.create_post(
            post_id=message.id,
            url=url,
            text=text,
            media=media_file_path,
            date=post_date,
            channel_id=channel.id,
            reactions=json.dumps(reactions)
        )
        await self.get_comments_info(message, channel, limit=100, reverse=False)
        logger.info(f"Обработан пост с id: {message.id}")


    async def publish_saved_posts(self, source_channel: str, target_channel: str):
        """
        Публикует все сохраненные в базе данных посты в указанный канал.
        
        :param target_channel: Идентификатор или ссылка на канал, в который будут опубликованы посты.
        """
        # Предполагается, что PostRepository имеет метод get_posts, возвращающий список постов
        posts = self.post_repo.get_posts_by_channel_name(
            channel_name=source_channel
        )

        logger.info(f"Найдено {len(posts)} постов для публикации в канал {target_channel}")

        await self.connect()  # Убедимся, что клиент подключен
        try:
            for post in posts:
                try:
                    if post.media:
                        # Если есть медиа файл, публикуем его с текстом в качестве подписи
                        await self.client.send_file(target_channel, post.media, caption=post.text)
                        logger.info(f"Опубликован пост с медиа: {post.post_id}")
                    else:
                        # Публикуем только текст
                        await self.client.send_message(target_channel, post.text)
                        logger.info(f"Опубликован текстовый пост: {post.post_id}")
                except Exception as e:
                    logger.error(f"Ошибка при публикации поста {post.post_id}: {e}")
        finally:
            await self.disconnect()

    async def get_comments_info(self, message: Message, channel: Channel, limit: int, reverse: bool):
        async for comment in self.client.iter_messages(
                entity=channel,
                reply_to=message.id,
                limit=limit,
                reverse=reverse,
                wait_time=1):
            try:
                self.comment_repo.create_comment(
                    comment.id, message.id, comment.text, comment.from_id.user_id, comment.date)
            except AttributeError:
                self.comment_repo.create_comment(
                    comment.id, message.id, comment.text, f'channel_id:{comment.peer_id.channel_id}', comment.date)
                
    async def subscribe(self, channel_username: str):
        await self.connect()
        try:
            await self.client(JoinChannelRequest(channel_username))
        finally:
            await self.disconnect()

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
