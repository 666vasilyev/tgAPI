import logging
import os
import aiofiles

from fastapi import APIRouter, HTTPException, status, UploadFile, File, Depends, Query
from typing import Optional

from src.core.config import Config
from src.schemas.account import SampleAccountModel
from src.schemas.proxy import PutProxyModel
from src.dependencies import get_account_repository
from src.repositories.account import AccountRepository

router = APIRouter()

@router.post("/")
async def create_account(
    proxy_id: Optional[int] = None,
    session_file: UploadFile = File(...),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    try:
        logging.info("Start writing session file")
        async with aiofiles.open(
            Config().SESSIONS_DIR / session_file.filename, "wb"
        ) as internal_file:
            logging.info(f"Writing file to {Config().SESSIONS_DIR / session_file.filename}")
            await internal_file.write(await session_file.read())
            logging.info("Finished writing session file")
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ex)
        )

    phone_number = session_file.filename.replace(".session", "")

    # Получение аккаунта по номеру телефона
    account = account_repo.get_account_by_phone_number(phone_number=phone_number)
    logging.info(f"Account lookup result: {account}")

    if account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )

    logging.info("Creating account with provided proxy_id")
    try:
        account = account_repo.create_account_in_db(
            phone_number=phone_number,
            proxy=None,
            proxy_id=proxy_id
        )
        logging.info("Account successfully created in DB")
        return SampleAccountModel(
            account_id=account.id,
            proxy_id=account.proxy_id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(e)
        )


@router.post("/with_proxy")
async def create_account_with_proxy(
    proxy: PutProxyModel = Depends(PutProxyModel.as_form),
    session_file: UploadFile = File(...),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    try:
        logging.info("Start writing session file")
        async with aiofiles.open(
            Config().SESSIONS_DIR / session_file.filename, "wb"
        ) as internal_file:
            logging.info(f"Writing file to {Config().SESSIONS_DIR / session_file.filename}")
            await internal_file.write(await session_file.read())
            logging.info("Finished writing session file")
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(ex)
        )

    phone_number = session_file.filename.replace(".session", "")

    logging.info("Looking up account by phone number")
    account = account_repo.get_account_by_phone_number(phone_number=phone_number)
    logging.info(f"Account lookup result: {account}")

    if account is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Account already exists"
        )

    logging.info("Creating account with proxy data")
    account = account_repo.create_account_in_db(
        phone_number=phone_number,
        proxy=proxy,
        proxy_id=None
    )
    logging.info("Account successfully created in DB")
    return SampleAccountModel(
        account_id=account.id,
        proxy_id=account.proxy_id
    )


@router.get("/")
async def get_accounts(
    active: bool = Query(False),
    account_repo: AccountRepository = Depends(get_account_repository)
):
    return account_repo.get_accounts_by_status(active=active)


@router.delete("/{account_id}", status_code=status.HTTP_200_OK)
async def delete_account(
    account_id: int,
    account_repo: AccountRepository = Depends(get_account_repository)
):
    logging.info("Getting account by id")
    account = account_repo.get_account_by_id(account_id=account_id)
    logging.info(f"Found account: {account}")
    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Account does not exist"
        )

    try:
        logging.info("Start deleting account session file")
        os.remove(Config().SESSIONS_DIR / (account.login + ".session"))
        logging.info("Session file successfully deleted")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail=f"Session file not found - {e}"
        )

    logging.info("Deleting account from DB")
    account_repo.delete_account_from_db(account=account)
    logging.info("Account successfully deleted from DB")
