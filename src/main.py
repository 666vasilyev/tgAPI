# uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
import logging
import os
import aiofiles
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from pathlib import Path
from .convert_to_excel import converting

from .api import check_active_proxy
from .config import Config
from .db.channels_table import channels_table
from . import celery_tasks
from .db.sync_crud import (create_account_in_db, 
                           create_proxy_in_db, 
                           delete_account_from_db, 
                           delete_proxy_by_id, get_account_by_id, 
                           get_account_by_phone_number, 
                           get_accounts_by_status, 
                           get_all_proxies_from_db, 
                           get_proxy_by_id, 
                            )
from .models import AllTasksGetReqModel, CollectReqModel, CollectResModel, DataModel, PostProxyModel, PostProxyResModel, PutProxyModel, SampleAccountModel, TaskGetReqModel
from starlette import status
from .worker import get_last_post_id
from .db.connection import Connection
from sqlalchemy.exc import IntegrityError
app = FastAPI()

@app.on_event("startup")
async def startup():
    logging.basicConfig(level=logging.INFO)
    # celery_task = celery_create_channels_table.delay()


@app.get("/task/{task_id}")
async def get_task_by_id(task_id: str):
    task = celery_tasks.celery.AsyncResult(task_id)
    task_status = task.status
    task_result = celery_tasks.redis.get(task_id)
    return TaskGetReqModel(
        task_id=task_id, task_status=task_status, task_result=task_result
    )


@app.get("/task")
async def get_tasks():
    keys = celery_tasks.redis.keys("celery-task-meta-*")

    task_ids = [key.decode("utf-8").split("-", 3)[-1] for key in keys]

    tasks = []
    for task_id in task_ids:
        task = await get_task_by_id(task_id)
        tasks.append(task)

    return AllTasksGetReqModel(tasks=tasks)


@app.post("/task", response_model=CollectResModel)
async def create_task(collect_model: CollectReqModel):
    if len(collect_model.data) <= 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Empty data"
        )

    celery_task = celery_tasks.celery_get_comments.delay(collect_model.dict())

    return CollectResModel(task_id=celery_task.id)


# @app.post("/task_new")
# async def create_task_new():
#     async with Connection.getConnection() as session:

#         try:
#             # для каждого канала забирается его ссылка
#             for url, channel_type in channels_table:
#                 data_list = []
#                 channel_id, last_id = url.split('/')[-2:]
#                 last_id = int(last_id)
#                 logging.info(int(last_id))
#                 # формируется CollectReqModel для одного канала с 10 ссылками на последние 10 постов
#                 for i in range((last_id-20), (last_id)):
#                     parted_url = '/'.join(url.split('/')[:-1])
#                     data = DataModel(url=f'{parted_url}/{i}', source_id='')
#                     data_list.append(data)  
#                 collect_model = CollectReqModel(data=data_list, limit = 1000, asc=True)
#                 logging.info(collect_model)    

#                 # создается celery задача для каждого канала
#                 celery_task = celery_tasks.celery_get_comments.delay(collect_model.dict())
#         except Exception as e:
#                 logging.error(str(e))



@app.post("/account")
async def create_account(proxy_id: int, 
        session_file: UploadFile = File(...)
):

    try:
        logging.info('Start writting session file')
        async with aiofiles.open(
                Config().SESSIONS_DIR / session_file.filename, "wb"
        ) as internal_file:
            logging.info(f'{Config().SESSIONS_DIR}{session_file.filename}')
            await internal_file.write(await session_file.read())
            logging.info('Finished file writting')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex)
        )
    
    phone_number = session_file.filename.replace(".session", "")

    # получение активной сессии
    async with Connection.getConnection() as session:
        account = get_account_by_phone_number(
                                            session=session,
                                            phone_number=phone_number)
        logging.info(account)

        if account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
            )
        logging.info('Setting proxy in db')
        try:
            account = create_account_in_db(
                session=session,
                phone_number=phone_number,
                proxy=None,
                proxy_id=proxy_id)
            logging.info(f'Account created in db')
            return SampleAccountModel(
            account_id=account.id,
            proxy_id=account.proxy_id
        )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
            )
        


@app.post("/account_with_proxy")
async def create_account_with_proxy(
        proxy: PutProxyModel = Depends(PutProxyModel.as_form),
        session_file: UploadFile = File(...),
):

    try:
        logging.info('Start writting session file')
        async with aiofiles.open(
                Config().SESSIONS_DIR / session_file.filename, "wb"
        ) as internal_file:
            logging.info(f'{Config().SESSIONS_DIR}{session_file.filename}')
            await internal_file.write(await session_file.read())
            logging.info('Finished file writting')
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(ex)
        )
    
    phone_number = session_file.filename.replace(".session", "")

    # получение активной сессии
    async with Connection.getConnection() as session:
        logging.info('Set up db session')
        account = get_account_by_phone_number(session=session,
                                                    phone_number=phone_number)
        logging.info(account)

        if account is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
            )
        logging.info('Setting proxy in db')
        account = create_account_in_db(
            session=session,
            phone_number=phone_number, 
            proxy=proxy,
            proxy_id=None)
        logging.info(f'Account created in db')
        return SampleAccountModel(
            account_id=account.id,
            proxy_id=account.proxy_id
        )


@app.get("/account")
async def get_accounts(
        active: bool = Query(False)
):
    async with Connection.getConnection() as session:
        logging.info(session)
        return get_accounts_by_status(session, active)
    

@app.delete("/account/{account_id}", status_code=status.HTTP_200_OK)
async def delete_account(account_id: int):
    logging.info('getting account by id')
    async with Connection.getConnection() as session:
        account = get_account_by_id(session=session,
                                        account_id=account_id)
        logging.info(account)
        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
            )

        try:
            logging.info('start deleting acc file')
            os.remove(Config().SESSIONS_DIR / (account.login + ".session"))
            logging.info('finish deleting')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_304_NOT_MODIFIED,
                detail=f"Session file not found - {e}",
            )
        logging.info('start deleting account from db')
        delete_account_from_db(session=session, 
                                account=account)
        logging.info('finish deleting account from db')

@app.get("/proxy")
async def get_all_proxies():
    try:
        async with Connection.getConnection() as session:
            return get_all_proxies_from_db(session=session)
    except Exception as e:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

# {
#   "addr": "91.200.149.155",
#   "port": 8000,
#   "username": "UXct3g",
#   "password": "EAE5F9",
#   "proxy_type": "socks5"
# }
@app.post("/proxy", description="Proxy types: [https, socks4, socks5]")
async def create_proxy(proxy: PostProxyModel):
    # проверим прокси на работоспособность, в случае отрицательного ответа сразу выведем ошибку
    proxy_status, error = check_active_proxy(proxy)
    if proxy_status != status.HTTP_200_OK:
        raise HTTPException(status_code=proxy_status, detail=error)
    
    try:
        async with Connection.getConnection() as session:
            proxy_db = create_proxy_in_db(
                session=session,
                proxy=proxy
            )
            return PostProxyResModel(proxy_id=proxy_db.id)
    except IntegrityError:
        raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail='Proxy already exist'
            )
    except Exception as e:
        raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

@app.delete("/proxy/{proxy_id}", status_code=status.HTTP_200_OK)
async def delete_proxy(
    proxy_id: int
):
    async with Connection.getConnection() as session:
        if get_proxy_by_id(session=session, proxy_id=proxy_id) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail='Proxy not found'
            )
        try:
            delete_proxy_by_id(
                session=session,
                proxy_id=proxy_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )
    
@app.post("/report", status_code=status.HTTP_200_OK)
async def generate_excel():
    # Вызываем функцию converting()
    await converting()
    return 'Successfully created excel report'
    # После завершения функции, отправляем пользователю файл output.xlsx
    


@app.get("/report", status_code=status.HTTP_200_OK)
async def get_excel():
    # Укажите путь к файлу "output.xlsx"
    file_path = Path(__file__).resolve().parent / "output.xlsx"
    if file_path.exists():
        return FileResponse(file_path, filename="output.xlsx")
    else:
        return {"error": "Файл не найден"}