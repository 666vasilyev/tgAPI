import contextlib
from typing import Sequence

import sqlalchemy.pool
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config import Config
from db.models import Account, Proxy

engine = create_async_engine(
    Config().db_url("postgresql+asyncpg"), poolclass=sqlalchemy.pool.NullPool
)
async_session = async_sessionmaker(engine, expire_on_commit=False, autoflush=True)


async def get_session_dep() -> AsyncSession:
    async with async_session() as session:
        yield session


@contextlib.asynccontextmanager
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def get_free_proxies(
    session: AsyncSession, limit: int | None = 1
) -> Sequence[Proxy] | Proxy | None:
    statement = (
        select(Proxy)
        .join(Account, isouter=True)
        .group_by(Proxy.id)
        .order_by(func.count(Account.id))
        .limit(limit)
    )

    if limit is None:
        return (await session.execute(statement)).scalars().fetchall()
    elif limit > 0:
        return (await session.execute(statement)).scalar_one_or_none()


async def set_banned(session: AsyncSession, login: str) -> None:
    account: Account = (
        await session.execute(select(Account).where(Account.login == login))
    ).scalar_one_or_none()
    account.status = "banned"
    await session.commit()


async def set_proxy(session: AsyncSession, login: str, proxy: Proxy) -> Proxy:
    account: Account | None = (
        await session.execute(select(Account).where(Account.login == login))
    ).scalar_one_or_none()
    if account is not None:
        account.proxy = proxy
    await session.commit()

    return proxy


async def get_account_proxy(session: AsyncSession, login: str) -> Proxy | None:
    return (
        await session.execute(select(Proxy).join(Account).where(Account.login == login))
    ).scalar_one_or_none()


async def get_account(session: AsyncSession, login: str) -> Account | None:
    return (
        await session.execute(select(Account).where(Account.login == login))
    ).scalar_one_or_none()


async def get_active_accounts(session: AsyncSession, active: bool = True) -> Sequence[Account]:
    return (
        (
            await session.execute(
                select(Account)
                .where(or_(not active, Account.status == "active"))
                .order_by(Account.requests)
            )
        )
        .scalars()
        .fetchall()
    )
