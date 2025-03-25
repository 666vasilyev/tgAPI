from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.exc import IntegrityError

from src.utils.proxy_checker import check_active_proxy
from src.schemas.proxy import PostProxyModel, PostProxyResModel
from src.repositories.proxy import ProxyRepository
from src.dependencies import get_proxy_repository

router = APIRouter()


@router.get("/")
async def get_all_proxies(
    proxy_repo: ProxyRepository = Depends(get_proxy_repository)
):
    try:
        return proxy_repo.get_all_proxies_from_db()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/", description="Proxy types: [https, socks4, socks5]")
async def create_proxy(
    proxy: PostProxyModel,
    proxy_repo: ProxyRepository = Depends(get_proxy_repository)
):
    # Проверяем работоспособность прокси; если проверка не пройдена — возвращаем ошибку.
    proxy_status, error = check_active_proxy(proxy)
    if proxy_status != status.HTTP_200_OK:
        raise HTTPException(status_code=proxy_status, detail=error)
    
    try:
        proxy_db = proxy_repo.create_proxy_in_db(proxy)
        return PostProxyResModel(proxy_id=proxy_db.id)
    
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Proxy already exist'
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{proxy_id}", status_code=status.HTTP_200_OK)
async def delete_proxy(
    proxy_id: int,
    proxy_repo: ProxyRepository = Depends(get_proxy_repository)
):
    if proxy_repo.get_proxy_by_id(proxy_id=proxy_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Proxy not found'
        )
    try:
        proxy_repo.delete_proxy_by_id(proxy_id=proxy_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
