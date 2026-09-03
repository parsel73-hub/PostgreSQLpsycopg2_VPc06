# PostgreSQL и psycopg2

Учебный проект по работе с базой данных PostgreSQL из Python с помощью библиотеки `psycopg2`.

## Структура проекта

| Файл | Описание |
|---|---|
| `test_connection.py` | Тестовый скрипт: проверяет подключение к PostgreSQL и выводит версию сервера |
| `main.py` | Основной файл проекта |
| `.env` | Локальные настройки подключения (не коммитится) |
| `.env.example` | Шаблон настроек — скопируйте его в `.env` и заполните своими значениями |
| `requirements.txt` | Список зависимостей |

## Требования

- Python 3.12+
- PostgreSQL 18 (запущенный локально, порт 5432 по умолчанию)

## Установка и запуск

1. Клонировать репозиторий и перейти в папку проекта.

2. Создать виртуальное окружение и активировать его:

   ```bash
   python -m venv venv
   .\venv\Scripts\activate        # Windows (PowerShell)
   source venv/bin/activate       # Linux / macOS
   ```

3. Установить зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Настроить подключение к базе — скопировать шаблон и указать свои значения:

   ```bash
   cp .env.example .env
   ```

   Пример содержимого `.env`:

   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=postgres
   DB_USER=postgres
   DB_PASSWORD=ваш_пароль
   ```

5. Запустить тест подключения:

   ```bash
   python test_connection.py
   ```

   Ожидаемый вывод:

   ```
   Подключение успешно!
   Версия PostgreSQL: PostgreSQL 18.6 on x86_64-windows, ...
   База данных: postgres, пользователь: postgres
   ```

## Зависимости

- `psycopg2-binary` — драйвер для подключения к PostgreSQL
- `python-dotenv` — загрузка настроек из файла `.env`
