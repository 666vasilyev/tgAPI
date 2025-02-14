import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from src.db.models import Account, Proxy
from src.repositories.proxy import ProxyRepository

logger = logging.getLogger(__name__)


class AccountRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_account(self) -> Account:
        """
        Возвращает активный аккаунт с наименьшим количеством запросов.
        """
        return self.db.query(Account).filter(Account.status == 'active').order_by(Account.requests).first()

    def get_account_by_phone_number(self, phone_number: str) -> Account | None:
        """
        Получает аккаунт по номеру телефона.
        """
        result = self.db.execute(select(Account).where(Account.login == phone_number))
        return result.scalar_one_or_none()

    def create_account_in_db(self, phone_number: str, proxy: Proxy | None, proxy_id: int | None) -> Account:
        """
        Создает аккаунт. Если proxy передан, пытается найти его в БД или создать новый.
        Если proxy не передан, ищет по proxy_id.
        """
        account = Account(login=phone_number)
        proxy_repo = ProxyRepository(self.db)

        if proxy is not None:
            proxy_db = proxy_repo.get_proxy_from_db(proxy)
            if proxy_db is None:
                proxy_db = proxy_repo.create_proxy_in_db(proxy)
        else:
            proxy_db = proxy_repo.get_proxy_by_id(proxy_id)

        account.proxy_id = proxy_db.id
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    def get_account_by_id(self, account_id: int) -> Account:
        """
        Возвращает аккаунт по его ID.
        """
        return self.db.get(Account, account_id)

    def delete_account_from_db(self, account: Account) -> None:
        """
        Удаляет аккаунт из БД.
        """
        self.db.delete(account)
        self.db.commit()

    def set_banned(self, account: Account) -> None:
        """
        Помечает аккаунт как заблокированный.
        """
        account.status = 'banned'
        self.db.commit()

    def get_accounts_by_status(self, active: bool) -> list[Account]:
        """
        Возвращает аккаунты по статусу.
        Если active==True, возвращает только активные.
        """
        if active:
            return self.db.query(Account).filter(Account.status == 'active').all()
        else:
            return self.db.query(Account).all()

    def increment_account_requests(self, account: Account) -> None:
        """
        Увеличивает количество запросов аккаунта на 1.
        """
        account.requests += 1
        self.db.commit()
