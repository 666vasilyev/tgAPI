from typing import Sequence
from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from src.db.models import Proxy


class ProxyRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_proxy_by_id(self, proxy_id: int) -> Proxy | None:
        """
        Возвращает proxy по ID.
        """
        return self.db.query(Proxy).filter_by(id=proxy_id).first()

    def get_proxy_from_db(self, proxy: Proxy) -> Proxy | None:
        """
        Находит proxy по его реквизитам.
        """
        stmt = select(Proxy).where(
            and_(
                Proxy.username == proxy.username,
                Proxy.password == proxy.password,
                Proxy.addr == proxy.addr,
                Proxy.port == proxy.port,
            )
        )
        result = self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create_proxy_in_db(self, proxy: Proxy) -> Proxy:
        """
        Создает proxy в БД.
        """
        # Предполагается, что proxy имеет метод dict(), возвращающий словарь полей.
        new_proxy = Proxy(**proxy.dict())
        self.db.add(new_proxy)
        self.db.commit()
        self.db.refresh(new_proxy)
        return new_proxy

    def delete_proxy_by_id(self, proxy_id: int) -> None:
        """
        Удаляет proxy по ID.
        """
        self.db.execute(delete(Proxy).where(Proxy.id == proxy_id))
        self.db.commit()

    def get_all_proxies_from_db(self) -> Sequence[Proxy]:
        """
        Возвращает все proxy из БД.
        """
        return self.db.query(Proxy).all()
