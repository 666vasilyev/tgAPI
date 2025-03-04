from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest

from src.core.config import Config

# Название (путь) для файла-сессии, где Telethon будет хранить авторизационные данные
session_name = '573181778435.session'

# Создаем клиент
client = TelegramClient(session_name, Config().API_ID, Config().API_HASH)

async def main():
    # Запускаем клиент (если сессия не авторизована, попросит код подтверждения)
    await client.start()

    # Название или @username канала, на который нужно подписаться
    channel_username = 'test_channel123451'  # Здесь укажите нужный канал

    # Выполняем подписку на канал
    await client(JoinChannelRequest(channel_username))
    print(f'Вы успешно подписались на канал: {channel_username}')

# Запускаем основной метод внутри контекста клиента
with client:
    client.loop.run_until_complete(main())
