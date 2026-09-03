"""
Тестовый скрипт для проверки подключения к PostgreSQL.
Запуск: python test_connection.py

Параметры подключения берутся из файла .env (см. .env.example).
"""

import os

import psycopg2
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}


def test_connection():
    try:
        # Подключаемся к базе
        with psycopg2.connect(**DB_CONFIG) as conn:
            with conn.cursor() as cur:
                # Проверяем версию сервера
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print("Подключение успешно!")
                print(f"Версия PostgreSQL: {version}")

                # Проверяем текущую базу и пользователя
                cur.execute("SELECT current_database(), current_user;")
                db, user = cur.fetchone()
                print(f"База данных: {db}, пользователь: {user}")

    except psycopg2.OperationalError as e:
        print("Ошибка подключения:", e)


if __name__ == "__main__":
    test_connection()