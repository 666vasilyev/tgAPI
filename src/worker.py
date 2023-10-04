import logging
from telethon import TelegramClient
from telethon.tl.types import User

from .utils import process_reactions
from .config import Config
from .db.sync_crud import (
    create_post,
    create_comment, 
    get_account, 
    get_proxy_by_id,
    increment_account_requests, 
    set_banned
    )
from .models import CollectReqModel
from .db.connection import Connection
from sqlalchemy.orm import Session


logger = logging.getLogger(__name__)

# TODO: тестить
async def get_client(session: Session) -> TelegramClient | None:

    # Получить аккаунт по ID
    account = get_account(session)
    increment_account_requests(session, account)
    
    # Получить прокси по ID
    proxy = get_proxy_by_id(session, account.proxy_id)
    logging.info(proxy)
    # Настройки API
    api_id = Config().API_ID
    api_hash = Config().API_HASH
    session_file = f'{Config().SESSIONS_DIR}/{account.login}.session'

    # Создать TelegramClient
    # client = TelegramClient(session_file, api_id, api_hash, proxy=proxy.as_dict())
    client = TelegramClient(session_file, api_id, api_hash)
    logging.info('client is created')
    try:
        # Попробовать установить соединение
        logging.info('before connect')
        await client.connect()
        logging.info('after connect')

        # Проверить, заблокирован ли аккаунт
        me = await client.get_me()
        if isinstance(me, User):
            return client  # Вернуть клиента, если он работоспособен
        else:
            set_banned(session, account)
            return None
    except Exception as e:
        logging.error(f'An error occurred while connecting to Telegram: {e}')
        return None
        

async def get_post_info(session: Session, client: TelegramClient, channel_name: str, message_id: int):
    
    message = await client.get_messages(await client.get_entity(channel_name), 
                                ids=message_id)
    
    # забирание реакций с поста через API + преобразование в JSON формат для бд
    data = []
    if message and message.reactions:
        data = message.reactions.results 
    reactions = [(item.reaction.emoticon, item.count) for item in data]
    reactions_pairs = process_reactions(reactions=reactions)
    # сбор медиа с поста
    logging.info('Media started downoloading')
    # await message.download_media(f'{Config().MEDIA_DIR}/{message_id}')
    logging.info('Media finished downoloading')
    # запись в базу данных
    create_post(
        session,
        message_id,
        int(message.peer_id.channel_id),
        f't.me/{channel_name}/{message_id}',
        message.text,
        f'{Config().MEDIA_DIR}{message_id}',
        reactions_pairs,
        message.date
    )


async def get_comments_info(session: Session, 
                            client: TelegramClient,
                            message_id: str, 
                            channel_name: str,
                            limit: int,
                            reverse: bool
                            ):
    
    async for comment in client.iter_messages(
                            entity=await client.get_entity(channel_name),
                            reply_to=int(message_id),
                            limit=limit,
                            reverse=reverse,
                            wait_time=1,
        ):
        try:
            create_comment(
                session,
                comment.id, 
                message_id, 
                comment.text, 
                comment.from_id.user_id, 
                comment.date
            )
        except AttributeError:
            create_comment(
                session,
                comment.id, 
                message_id, 
                comment.text, 
                f'channel_id:{comment.peer_id.channel_id}', 
                comment.date
            )

# TODO: в случае неимения аккаунта обработать эту ошибку по человечески
async def get_comments(tasks: CollectReqModel):
    limit = tasks.limit
    reverse = tasks.asc
    for task in tasks.data:
        channel_name, message_id = task.url.split('/')[-2:]
        logging.info(task.url)
        logging.info(task.url.split('/')[-2:])
        logging.info(task.url.split('/')[-1:])

        # открываем соединение с клиентом, также работаем с аккаунтом
        async with Connection.getConnection() as session:

            # открываем сессию работы с базой данных
            logging.info('Session is opened')

            # проверим работоспособность клиента
            client = await get_client(session=session)
            if client is not None:
                try:
                    await client.connect()
                    logging.info('Client is opened')
                except Exception as e:
                    logging.error(str(e))
                    logging.info('account status changed to banned')
                try:
                    # собираем информацию с поста
                    await get_post_info(
                        session=session,
                        client=client,
                        channel_name=channel_name, 
                        message_id=int(message_id)
                        )
                    
                    # собираем информацию о комментариях
                    await get_comments_info(
                        session=session,
                        client=client,
                        message_id=message_id,
                        channel_name=channel_name,
                        limit=limit,
                        reverse=reverse
                    )
                    await client.disconnect()
                    logging.info('Client is closed')
                except Exception as e:
                    logging.error(str(e))
                    await client.disconnect()
            else:
                logging.info('client is None')


# res = await client.get_messages(url, limit=1) очень медленно
async def get_last_post_id(session: Session, url: str) -> int | None:
    try:
        client = await get_client(session=session)
        if client is not None:
            await client.connect()
            res = await client.get_messages(url, limit=1)
            await client.disconnect()
            if res:
                return int(res[0].id)
            else:
                return None
        else:
            logging.info('client is None')
    except Exception as e:
        logging.error(str(e))