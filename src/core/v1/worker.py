import logging
from telethon import TelegramClient
from telethon.tl.types import User
from sqlalchemy.orm import Session

from src.utils.utils import process_reactions
from src.core.config import Config
from src.repositories.channel import ChannelRepository
from src.repositories.post import PostRepository
from src.repositories.comment import CommentRepository
from src.repositories.account import AccountRepository
from src.repositories.proxy import ProxyRepository
from src.schemas.task import CollectReqModel
from src.dependencies import get_db

logger = logging.getLogger(__name__)


class Worker:
    def __init__(self, session: Session):
        self.session = session
        self.account_repo = AccountRepository(session)
        self.proxy_repo = ProxyRepository(session)
        self.post_repo = PostRepository(session)
        self.comment_repo = CommentRepository(session)
        self.api_id = Config().API_ID
        self.api_hash = Config().API_HASH

    async def get_client(self) -> TelegramClient | None:
        account = self.account_repo.get_account()

        if account is None:
            return None
        
        self.account_repo.increment_account_requests(account)
        # proxy = self.proxy_repo.get_proxy_by_id(account.proxy_id)
        
        session_file = f'{Config().SESSIONS_DIR}/{account.login}.session'

        logger.info(session_file)
        
        client = TelegramClient(session_file, self.api_id, self.api_hash)

        logger.info(client)

        try:

            logger.info('Start client connecting')
            await client.connect()

            logger.info(f'Client connected {client}')

            me = await client.get_me()

            logger.info(me)

            if isinstance(me, User):
                return client
            else:
                self.account_repo.set_banned(account)
                return None
        except Exception as e:
            logger.error(f'Error connecting to Telegram: {e}')
            return None

    async def get_post_info(self, client: TelegramClient, channel_name: str, message_id: int):
        message = await client.get_messages(await client.get_entity(channel_name), ids=message_id)
        data = message.reactions.results if message and message.reactions else []
        reactions = [(item.reaction.emoticon, item.count) for item in data]
        reactions_pairs = process_reactions(reactions)
        
        self.post_repo.create_post(
            message_id,
            int(message.peer_id.channel_id),
            f't.me/{channel_name}/{message_id}',
            message.text,
            f'{Config().MEDIA_DIR}{message_id}',
            reactions_pairs,
            message.date
        )

    async def get_comments_info(self, client: TelegramClient, message_id: str, channel_name: str, limit: int, reverse: bool):
        async for comment in client.iter_messages(
                entity=await client.get_entity(channel_name),
                reply_to=int(message_id),
                limit=limit,
                reverse=reverse,
                wait_time=1):
            try:
                self.comment_repo.create_comment(
                    comment.id, message_id, comment.text, comment.from_id.user_id, comment.date)
            except AttributeError:
                self.comment_repo.create_comment(
                    comment.id, message_id, comment.text, f'channel_id:{comment.peer_id.channel_id}', comment.date)

    async def get_comments(self, tasks: CollectReqModel):
        limit = tasks.limit
        reverse = tasks.asc
        
        for task in tasks.data:
            channel_name, message_id = task.url.split('/')[-2:]
            client = await self.get_client()
            
            if client:
                try:
                    await client.connect()
                    await self.get_post_info(client, channel_name, int(message_id))
                    await self.get_comments_info(client, message_id, channel_name, limit, reverse)
                except Exception as e:
                    logger.error(str(e))
                
                finally:
                    await client.disconnect()
            else:
                logger.info('Client is None')

    async def get_last_post_id(self, url: str) -> int | None:
        client = await self.get_client()
        
        if client:
            try:
                await client.connect()
                res = await client.get_messages(url, limit=1)
                await client.disconnect()
                return int(res[0].id) if res else None
            except Exception as e:
                logger.error(str(e))
                return None
        else:
            logger.info('Client is None')
            return None
