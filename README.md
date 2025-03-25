# Telegram's comments grabbing microservice

## Описание

Данный микросервис построен на **FastAPI**, с использованием **Celery**, **Telethon** и сопутствующих инструментов, таких как **Docker**. В качестве брокера был использован **Redis**, для backend **PostgreSQL**.<br />

### Для получения актуальной документации по взаимодействию с сервисом, запустите проект и перейдите по [ссылке](http://localhost:8000/redoc)

## Получение активной сессии telethon

Для получения тестовой сессии по имеющимся персональным данным (номер телефона\id бота) необходимо запустить файл `get_session.py`, 
выполнить вход в аккаунт и добавить его по endpoint `POST /account` с помощью [docs](http://localhost:8000/docs), либо с помощью 
CURL запроса 
```shell
curl -X 'POST' \
  'http://localhost:8145/account' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'session_file=@user_number.session'
  ```

## Описание алгоритма.

![1](https://user-images.githubusercontent.com/83702683/226186918-982655c6-962d-468d-a9f4-e74ca18213b3.jpg)
![2](https://user-images.githubusercontent.com/83702683/226186933-ea708e16-ae55-4f5d-b6a0-a01f612644c1.jpg)

## Установка и запуск

### Предварительные требования

- Docker и Docker Compose
- Python 3.8+
- Telegram API credentials (api_id и api_hash)

### Настройка окружения

1. Склонируйте репозиторий
2. Создайте файл `.env` в корневой директории проекта со следующими переменными:
   ```env
   API_PORT=8000
   LOG_LEVEL=INFO
   
   # PostgreSQL
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   POSTGRES_DB=your_db
   POSTGRES_HOST=db
   POSTGRES_PORT=5432
   
   # Telegram API
   API_ID=your_api_id
   API_HASH=your_api_hash
   ```

### Запуск проекта

1. Соберите и запустите контейнеры:
   ```bash
   docker-compose up -d --build
   ```
2. Проверьте работоспособность сервиса по адресу: http://localhost:8000/docs

## Структура проекта

```
├── accounts/           # Директория для хранения сессий Telethon
├── alembic/           # Миграции базы данных
├── media/             # Медиафайлы
├── output/            # Выходные данные
├── src/              # Исходный код приложения
├── .env              # Конфигурация окружения
├── alembic.ini       # Конфигурация Alembic
├── docker-compose.yaml # Docker конфигурация
├── Dockerfile        # Инструкции для сборки Docker образа
└── requirements.txt  # Зависимости Python
```

## Компоненты системы

- **FastAPI** - основной веб-фреймворк
- **Celery** - асинхронная очередь задач
- **Redis** - брокер сообщений для Celery
- **PostgreSQL** - основная база данных
- **Telethon** - клиент для работы с Telegram API
- **Alembic** - система миграций базы данных

## Мониторинг и логирование

Логи можно просматривать с помощью команды:
```bash
docker-compose logs -f [service_name]
```

Доступные сервисы:
- app
- celery
- redis
- db

## Дополнительная информация

- API документация доступна по адресу: http://localhost:8000/docs
- Подробная документация (ReDoc): http://localhost:8000/redoc
- База данных доступна на порту 5433

