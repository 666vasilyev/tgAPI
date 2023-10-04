from datetime import datetime
import logging
from typing import Sequence
from sqlalchemy import and_, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Account, Channel, Comment, Post, Proxy
from .channels_table import channels_table


logging.basicConfig(level=logging.INFO)

def create_comment(session: Session, comment_id: int, message_id: int, text: str, user_id: int, date: datetime):
    try:
        new_comment = Comment(
            id=comment_id,
            post_id=message_id,
            text=text,
            user_id=user_id,
            time=date
        )
        session.add(new_comment)
        session.commit()
    except IntegrityError:
        logging.info('Comment already exists')

        

def get_comments(session: Session) -> list[Comment]:
    return session.query(Comment).all()
    


def create_post(session: Session, post_id: int, channel_id: str, url: str, text: str, media: str, reactions: str, 
                      date: datetime):
    try:
        new_post = Post(post_id=post_id,
            channel_id=channel_id,
            url=url,
            text=text,
            media=media,
            reactions=reactions,
            time=date)
        session.add(new_post)
        session.commit()
    except IntegrityError:
        logging.info('Post already exists')


def create_channels_table(session: Session, data: list = channels_table):
    try:
        for url, channel_type in data:
            channel = Channel(channel_id=url, type=channel_type)
            session.execute(insert(Channel).values(channel_id=channel.channel_id, type=channel.type))
        session.commit()
    except IntegrityError:
        logging.info('Table "Channels" already exists')


def get_proxy_by_id(session: Session, proxy_id: int) -> Proxy:
    return session.query(Proxy).filter_by(id=proxy_id).first()


def get_account(session: Session) -> Account:
    return session.query(Account).filter(
        Account.status == 'active'
    ).order_by(Account.requests).first()

def get_account_by_phone_number(session: Session, 
                                      phone_number: str) -> Account:
    return session.execute(select(Account).where(Account.login == phone_number)).scalar_one_or_none()


def get_proxy_from_db(session: Session, proxy: Proxy) -> Proxy:
        return (
        session.execute(
            select(Proxy).where(
                and_(
                    Proxy.username == proxy.username,
                    Proxy.password == proxy.password,
                    Proxy.addr == proxy.addr,
                    Proxy.port == proxy.port,
                )
            )
        )).scalar_one_or_none()


def create_account_in_db(session: Session, 
                         phone_number: str, 
                         proxy: Proxy | None, 
                         proxy_id: int | None) -> Account:
    account = Account(login=phone_number)

    if proxy is not None:
        proxy_db = get_proxy_from_db(
                                    session=session, 
                                    proxy=proxy)
        if proxy_db is None:
            proxy_db = Proxy(**proxy.dict())

        session.add(proxy_db)
        session.commit()
    else:
        proxy_db = get_proxy_by_id(session=session, 
                                proxy_id=proxy_id)

    account.proxy_id = proxy_db.id
    session.add(account)
    session.commit()
    return account


def get_account_by_id(session: Session, account_id: int) -> Account:
    return session.get(Account, account_id)
    
def delete_account_from_db(session: Session, account: Account) -> None:
    session.delete(account)
    session.commit()

def set_banned(session: Session, account: Account) -> None:
    account.status = 'banned'
    session.commit()


def get_accounts_by_status(session: Session, active: bool) -> Sequence[Account]:
    if active:
        return session.query(Account).filter(Account.status == 'active').all()
    else:
        return session.query(Account).all()
    
def create_proxy_in_db(session: Session, proxy: Proxy) -> Proxy:
    proxy_db = Proxy(**proxy.dict())
    session.add(proxy_db)
    session.commit()
    return proxy_db


def delete_proxy_by_id(session: Session, proxy_id: int) -> None:
    session.execute(delete(Proxy).where(Proxy.id == proxy_id))
    session.commit()


def get_all_proxies_from_db(session: Session) -> Sequence[Proxy]:
    return session.query(Proxy).all()


def increment_account_requests(session: Session, account: Account) -> None:
    account.requests += 1
    session.commit()


def get_posts(session: Session) -> list[Post]:
    return session.query(Post).all()
    

def get_comments_by_post_id(db_session, post_id) -> list[Comment]:
    comments = db_session.query(Comment).filter_by(post_id=post_id).all()
    return comments



def get_channel_type_by_id(session: Session, channel_id: str) -> str:
    channel = session.query(Channel).filter_by(channel_id=channel_id).first()
    return channel.type.value