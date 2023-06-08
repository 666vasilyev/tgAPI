# uvicorn api:app --host 0.0.0.0 --port 8000  --reload
import logging
import os
from typing import Sequence

import aiofiles
import sqlalchemy.exc
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, lazyload
from starlette import status

from api import check_active_proxy
from celery_tasks import celery_get_comments
from config import Config
from db.models import Task, Account, Proxy
from db.queries import (
    get_session_dep,
    get_free_proxies, set_banned, get_active_accounts,
)
from models import (
    CollectReqModel,
    CollectResModel,
    GetTaskResModel,
    PostProxyModel,
    GetTasksModel,
    TaskModel,
    ResultModel,
    PostProxyResModel,
    PutProxyModel,
    PutProxyResModel,
    SampleAccountModel
)
from worker import check_and_connect

app = FastAPI()


@app.on_event("startup")
async def startup():
    logging.basicConfig(level=logging.INFO)


active_db_session = Depends(get_session_dep)
TaskIdType = int | str


@app.post("/task", response_model=CollectResModel)
async def create_task(
        collect_model: CollectReqModel, session: AsyncSession = active_db_session
):
    if len(collect_model.data) <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Empty data"
        )
    new_task = Task()
    session.add(new_task)
    await session.commit()
    await session.refresh(new_task)
    collect_model.task_id = new_task.id
    # TODO: Разделить модель на DTO и модель общения в celery
    celery_task = celery_get_comments.delay(collect_model.dict())
    new_task.celery_id = celery_task.id
    await session.commit()
    return CollectResModel(task_id=celery_task.id)


@app.get("/task", response_model=GetTasksModel)
async def get_tasks(session: AsyncSession = active_db_session):
    tasks: Sequence[Task] = (
        (await session.execute(select(Task).options(lazyload(Task.results))))
        .scalars()
        .fetchall()
    )

    return GetTasksModel(tasks=[TaskModel.from_orm(task) for task in tasks])


@app.get(
    "/task/{task_id}",
    response_model=GetTaskResModel,
    description="task_id may be celery task id (str) or db task id (int)",
)
async def get_task(task_id: TaskIdType, session: AsyncSession = active_db_session):
    task: Task | None = None
    if isinstance(task_id, int):
        task = await session.get(Task, task_id)
    if isinstance(task_id, str):
        task = (
            (
                await session.execute(
                    select(Task)
                    .options(joinedload(Task.results))
                    .where(Task.celery_id == task_id)
                )
            )
            .unique()
            .scalar_one_or_none()
        )
    match task:
        case None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
            )
        case Task(status=s, results=results):
            return GetTaskResModel(
                task_status=s,
                results=[ResultModel.from_orm(result) for result in results],
            )
        case _:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="task is incorrect",
            )


@app.delete("/task", status_code=status.HTTP_200_OK)
async def delete_tasks(session: AsyncSession = active_db_session):
    await session.execute(delete(Task))
    await session.commit()


@app.delete(
    "/task/{task_id}",
    description="task_id may be celery task id (str) or db task id (int)",
)
async def delete_task(task_id: TaskIdType, session: AsyncSession = active_db_session):
    task: Task | None = None
    if isinstance(task_id, int):
        task = await session.get(Task, task_id)
    if isinstance(task_id, str):
        task = await session.get(Task, {"celery_id": task_id})
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    await session.delete(task)
    await session.commit()


# TODO: Сделать response model
@app.post("/proxy", description="Proxy types: [https, socks5, socks4]")
async def create_proxy(
        proxy: PostProxyModel, session: AsyncSession = active_db_session
):
    try:
        proxy_status, error = await check_active_proxy(proxy)
        if proxy_status != status.HTTP_200_OK:
            raise HTTPException(status_code=proxy_status, detail=error)
        try:
            new_proxy = Proxy(**proxy.dict())
            session.add(new_proxy)
            await session.commit()
            await session.refresh(new_proxy)
        except sqlalchemy.exc.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Proxy already exists"
            )

        return PostProxyResModel(proxy_id=new_proxy.id)
    except Exception as e:
        await session.rollback()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@app.get("/proxy")
async def get_proxies(session: AsyncSession = active_db_session):
    return {"proxies": list(await get_free_proxies(session, None))}


async def valid_proxy(proxy_id: int, session: AsyncSession = active_db_session):
    proxy = await session.get(Proxy, proxy_id)
    if proxy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Proxy not found"
        )
    return proxy


@app.get("/proxy/{proxy_id}")
async def get_proxy(proxy: Proxy = Depends(valid_proxy)):
    return proxy


@app.put(
    "/proxy/{proxy_id}",
    response_model=PutProxyResModel,
    description="Proxy types: [https, socks5, socks4]",
)
async def update_proxy(
        proxy_id: int, proxy_model: PutProxyModel, session: AsyncSession = active_db_session
):
    proxy = await session.get(Proxy, proxy_id)
    if proxy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Proxy not found"
        )

    for key, value in proxy_model.dict().items():
        if value is not None:
            setattr(proxy, key, value)

    proxy_status, error = await check_active_proxy(PostProxyModel.from_orm(proxy))
    if proxy_status != status.HTTP_200_OK:
        await session.rollback()
        raise HTTPException(status_code=proxy_status, detail=error)

    await session.commit()
    await session.refresh(proxy)
    return PutProxyResModel(proxy_id=proxy.id)


@app.delete("/proxy")
async def delete_proxies(session: AsyncSession = active_db_session):
    await session.execute(delete(Proxy))
    await session.commit()


@app.delete("/proxy/{proxy_id}")
async def delete_proxy(proxy_id: int, session: AsyncSession = active_db_session):
    proxy = await session.get(Proxy, proxy_id)
    if proxy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    await session.delete(proxy)
    await session.commit()


# TODO: Посмотреть, можно ли выделить блоки кода в отдельные части. DRY
@app.get("/account")
async def get_accounts(
        active: bool = Query(False), session: AsyncSession = active_db_session
):
    return await get_active_accounts(session, active)


@app.post("/account_post_with_proxy")
async def create_account_with_proxy(
        proxy: PutProxyModel = Depends(PutProxyModel.as_form),
        session_file: UploadFile = File(...),
        session: AsyncSession = active_db_session,
):
    try:
        # TODO: Проверить
        # if Path(Config().SESSIONS_DIR / session_file.filename).exists():
        #     os.remove(Config().SESSIONS_DIR / session_file.filename)

        async with aiofiles.open(
                Config().SESSIONS_DIR / session_file.filename, "wb"
        ) as internal_file:
            await internal_file.write(await session_file.read())
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex)
        )
    phone_number = session_file.filename.replace(".session", "")
    account = (
        await session.execute(
            select(Account)
            .options(lazyload(Account.proxy))
            .where(Account.login == phone_number)
        )
    ).scalar_one_or_none()
    if account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )
    account = Account(login=phone_number)

    if proxy is not None:
        proxy_db = (await session.execute(
            select(Proxy).where(
                and_(
                    Proxy.username == proxy.username,
                    Proxy.password == proxy.password,
                    Proxy.addr == proxy.addr,
                    Proxy.port == proxy.port,
                )
            )
        )).scalar_one_or_none()
        if proxy_db is None:
            proxy_db = Proxy(**proxy.dict())
        account.proxy = proxy_db
    session.add(account)
    await session.commit()
    await session.refresh(account)

    worker = await check_and_connect(
        account.login, Config().API_ID, Config().API_HASH, Config().SESSIONS_DIR
    )
    await worker.disconnect()
    if worker.status == "active":
        return {"account_id": account.id}
    else:
        await set_banned(session, account.login)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=worker.error
        )


@app.post("/account")
async def create_account(session_file: UploadFile = File(...), proxy_id: int = 1,
                         session: AsyncSession = active_db_session):
    try:
        # TODO: Проверить
        # if Path(Config().SESSIONS_DIR / session_file.filename).exists():
        #     os.remove(Config().SESSIONS_DIR / session_file.filename)

        async with aiofiles.open(
                Config().SESSIONS_DIR / session_file.filename, "wb"
        ) as internal_file:
            await internal_file.write(await session_file.read())
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex)
        )

    phone_number = session_file.filename.replace(".session", "")
    worker = await check_and_connect(
        phone_number, Config().API_ID, Config().API_HASH, Config().SESSIONS_DIR
    )

    await worker.disconnect()
    if worker.status == "active":
        account = (
            await session.execute(
                select(Account)
                .options(lazyload(Account.proxy))
                .where(Account.login == phone_number)
            )
        ).scalar_one_or_none()
        if account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
            )
        account = Account(login=phone_number, proxy_id=proxy_id)
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return SampleAccountModel(
            account_id=account.id,
            proxy_id=account.proxy_id
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=worker.error
        )


# TODO: тестить - это объединенный запрос put и patch
@app.put("/account/{account_id}")
async def update_account(
        account_id: int,
        session_file: UploadFile = File(None),
        proxy_id: int = None,
        session: AsyncSession = active_db_session,
):
    account = await session.get(Account, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
        )

    if session_file is not None:
        try:
            os.remove(Config().SESSIONS_DIR / (account.login + ".session"))
        except OSError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=e)

        try:
            async with aiofiles.open(
                    Config().SESSIONS_DIR / session_file.filename, "wb"
            ) as internal_file:
                await internal_file.write(await session_file.read())
        except Exception as ex:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex)
            )

        phone_number = session_file.filename.replace(".session", "")
        worker = await check_and_connect(
            phone_number, Config().API_ID, Config().API_HASH, Config().SESSIONS_DIR
        )
        await worker.disconnect()
        if worker.status != "active":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=worker.error
            )

        account = (
            await session.execute(
                select(Account)
                .options(lazyload(Account.proxy))
                .where(Account.login == phone_number)
            )
        ).scalar_one_or_none()
        if account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
            )
        account = Account(login=phone_number)
        session.add(account)

    if proxy_id is not None:
        account.proxy_id = proxy_id

    await session.commit()
    await session.refresh(account)

    return {"account_id": account.id}


@app.delete("/account/{account_id}", status_code=status.HTTP_200_OK)
async def delete_account(account_id: int, session: AsyncSession = active_db_session):
    account = await session.get(Account, account_id)
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
        )

    try:
        os.remove(Config().SESSIONS_DIR / (account.login + ".session"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail=f"Session file not found - {e}",
        )

    await session.delete(account)
    await session.commit()
