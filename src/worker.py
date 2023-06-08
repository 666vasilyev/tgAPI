import asyncio
import json
import logging
import os
from pathlib import Path

import telethon.tl.custom
from telethon import TelegramClient
from telethon.tl.types import User

from config import Config
from db.models import ParsingResult, ResultStatus, SourceType
from db.queries import (
    get_account_proxy,
    set_proxy,
    set_banned,
    get_session,
    get_free_proxies, get_active_accounts,
)

logger = logging.getLogger(__name__)


class Worker:
    __phone_number: str
    __api_id: int
    __api_hash: str
    __client: TelegramClient | None
    __sessions_dir: Path
    # TODO: Изменить на enum
    __status: str
    __error: str

    def __init__(
        self,
        phone_number="",
        api_id=0,
        api_hash="",
        sessions_dir: Path = "",
        status="error",
        error="",
    ):
        self.__phone_number = phone_number
        self.__api_id = api_id
        self.__api_hash = api_hash
        self.__client: TelegramClient | None = None
        self.__sessions_dir = Path(sessions_dir)
        self.__status = status
        self.__error = error

    @property
    def status(self):
        return self.__status

    @property
    def error(self):
        return self.__error

    async def connect(self):
        async with get_session() as session:
            # TODO: Починить получение прокси
            proxy = await get_account_proxy(session, self.__phone_number)
            if proxy is None:
                logger.info(f"No proxy for {self.__phone_number}")
                proxy = await get_free_proxies(session)
                if proxy is None:
                    logger.info("No free proxies")
                    self.__client = TelegramClient(
                        str((self.__sessions_dir / self.__phone_number).absolute()),
                        self.__api_id,
                        self.__api_hash,
                    )
                else:
                    logger.info(f"Setting free proxy {proxy} to {self.__phone_number}")
                    proxy = await set_proxy(session, self.__phone_number, proxy)
                    self.__client = TelegramClient(
                        str((self.__sessions_dir / self.__phone_number).absolute()),
                        self.__api_id,
                        self.__api_hash,
                        proxy=proxy.as_dict(),
                    )
            else:
                logger.info(f"Found proxy for account {self.__phone_number}")
                self.__client = TelegramClient(
                    str((self.__sessions_dir / self.__phone_number).absolute()),
                    self.__api_id,
                    self.__api_hash,
                    proxy=proxy.as_dict(),
                )
        logger.info(f"Created session: {self.__phone_number} {self.__client}")
        await self.__client.connect()
        if not await self.__client.is_user_authorized():
            await self.__client.send_code_request(self.__phone_number)
            await self.__client.sign_in(self.__phone_number, input("Enter the code: "))
        self.__status = "active"
        logger.info(f"Set up session: {self.__phone_number} {self.__client}")

    async def disconnect(self):
        if self.__client is not None:
            self.__client.disconnect()

    async def get_comments(
        self, channel_name, message_id, limit=50, sort="asc"
    ) -> tuple[list, list]:
        channel = await self.__client.get_entity(channel_name)
        reverse = sort != "asc"
        return list((
            await self.__client.get_messages(channel, ids=message_id)
        ).reactions.to_dict()["results"]), [
            self.comment_to_dict(comment)
            async for comment in self.__client.iter_messages(
                channel,
                reply_to=message_id,
                limit=limit,
                reverse=reverse,
                wait_time=1,
            )
        ]

    @staticmethod
    def comment_to_dict(comment: telethon.tl.custom.message.Message) -> dict:
        logger.info(comment)
        return {
            "type": "comment",
            "user": {
                "tg_id": comment.sender.id,
                "name": comment.sender.username,
                "first_name": comment.sender.first_name if isinstance(comment.sender, User) else comment.sender.title,
                "last_name": comment.sender.last_name if isinstance(comment.sender, User) else "",
                "phone": comment.sender.phone if isinstance(comment.sender, User) else "",
            },
            "date": comment.date.strftime("%Y-%m-%d %H:%M:%S"),
            "text": comment.message,
            "reactions": comment.reactions.to_json() if comment.reactions else "",
        }


async def check_and_connect(
    phone_number: str, api_id: int, api_hash: str, sessions_dir: Path
) -> Worker:
    try:
        worker = Worker(phone_number, api_id, api_hash, sessions_dir)
        await worker.connect()
        return worker
    except telethon.errors.rpcerrorlist.PhoneNumberBannedError:
        os.remove(sessions_dir / f"{phone_number}.session")
        return Worker(status="banned", error="Account is banned")
    except Exception as ex:
        logger.error(ex)
        return Worker(error=str(ex))


async def get_comments_stack(
    api_id: int,
    api_hash: str,
    source: dict,
    task_id: int,
) -> ParsingResult:
    # TODO: Убрать метод check_and_connect, сделать простую обработку исключений
    worker = Worker()
    async with get_session() as session:
        for account in (await get_active_accounts(session)):
            logger.info(f"Checking account: {account.login} - {account.requests}")
            worker = await check_and_connect(
                account.login, api_id, api_hash, Config().SESSIONS_DIR
            )
            match worker.status:
                case "error":
                    logger.error(f"Check error: {worker.error}")
                    account.status = "banned"
                    await session.commit()
                    continue
                case "banned":
                    logger.error(f"Account banned: {worker.error}")
                    os.remove(Config().SESSIONS_DIR / (account.login + ".session"))
                    account.status = "banned"
                    await session.commit()
                case "active":
                    account.requests += 1
                    await session.commit()
                    break
    logger.info(f"Got account: {account.login}")
    try:
        result = ParsingResult(task_id=task_id, url=source["url"])
        try:
            if "c/" in source["channel_name"]:
                result.status = ResultStatus.FAILURE
                result.source_type = SourceType.RESTRICTED
                result.result = json.dumps({"status": "channel is restricted"})
            else:
                reactions, comments = await worker.get_comments(
                    source["channel_name"],
                    int(source["message_id"]),
                    limit=source["limit"],
                    sort=source["sort"],
                )
                result.reactions = json.dumps(reactions, ensure_ascii=False)
                result.result = json.dumps(comments, ensure_ascii=False)
                result.status = ResultStatus.SUCCESS

        except Exception as ex:
            result.status = ResultStatus.FAILURE
            result.result = json.dumps({"status": f"Error occurred: {ex}"})
        finally:
            # TODO: Проверить время ожидания
            await asyncio.sleep(3)
            logger.info(f"Done task {result}")
        return result
    finally:
        await worker.disconnect()
