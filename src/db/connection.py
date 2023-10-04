import asyncio
import sqlalchemy
from sqlalchemy.orm import Session, sessionmaker
import logging
from src.config import Config


logger = logging.getLogger(__name__)


class Connection:
	c: Session
	mutex: asyncio.Lock
	isActive: bool
	engine = sqlalchemy.create_engine(Config().SYNC_DB_URL,
				   connect_args={"timeout": 10},
				   )
	db_connection_singleton = None

	def __init__(self):
		self.mutex = asyncio.Lock()

	async def __aenter__(self):
		logging.info('aenter')
		await self.mutex.acquire()
		self.c = sessionmaker(self.engine, expire_on_commit=False, autoflush=True)
		return self.c()
	
	async def __aexit__(self, a, b, c):
		logging.info('aexit')
		# self.c.__exit__(a, b, c)
		self.mutex.release()

	@classmethod
	def getConnection(cls) -> "Connection":
		if not cls.db_connection_singleton:
			cls.db_connection_singleton = Connection()

		return cls.db_connection_singleton
