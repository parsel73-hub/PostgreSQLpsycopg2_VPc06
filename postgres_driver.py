"""
Драйвер PostgreSQL: соединение и работа с таблицами users/orders.

Класс PostgresDriver инкапсулирует подключение (параметры из .env)
и предметные методы: create_tables, add_user, add_order, get_user_totals.

Поддерживает работу как менеджер контекста:

    with PostgresDriver() as db:
        db.add_user("Иван", 30)
"""

import os
from typing import Any

import psycopg2
import psycopg2.extras
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

# SQL-определения таблиц проекта
USERS_TABLE = {
    "id": "SERIAL PRIMARY KEY",
    "name": "TEXT NOT NULL",
    "age": "INT CHECK (age >= 0)",
}

ORDERS_TABLE = {
    "id": "SERIAL PRIMARY KEY",
    "user_id": "INT NOT NULL REFERENCES users(id) ON DELETE CASCADE",
    "amount": "NUMERIC(10,2) NOT NULL",
    "created_at": "TIMESTAMP DEFAULT NOW()",
}


class PostgresDriver:
    """Драйвер для работы с базой данных PostgreSQL (users/orders).

    Инкапсулирует соединение и предметные CRUD-методы.
    Все запросы параметризованы (%s) — защита от SQL-инъекций.
    """

    def __init__(self, config: dict[str, Any] | None = None):
        # Если конфиг не передан — используем настройки из .env
        self.config = config or DB_CONFIG
        self.conn = None
        self.connect()

    # ------------------------------------------------------------------
    # Соединение
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Открывает соединение с базой данных (если ещё не открыто)."""
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg2.connect(**self.config)
            except UnicodeDecodeError as e:
                # psycopg2 на Windows не может декодировать сообщение об ошибке
                # сервера (оно приходит в кодировке cp1251) — сообщаем понятно
                raise ConnectionError(
                    "Не удалось подключиться к базе (неверный пароль, пользователь "
                    "или сервер недоступен — точное сообщение сервера скрыто "
                    "ошибкой кодировки psycopg2 на Windows)"
                ) from e
            except psycopg2.OperationalError as e:
                raise ConnectionError(f"Не удалось подключиться к базе: {e}") from e

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def __enter__(self) -> "PostgresDriver":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Внутренний помощник
    # ------------------------------------------------------------------

    def _execute(self, query: str, params: tuple | list = (), *, fetch: bool = False):
        """Выполняет запрос. При fetch=True возвращает все строки результата."""
        self.connect()
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                # fetchall только если запрос вообще возвращает строки (SELECT/RETURNING)
                result = cur.fetchall() if fetch and cur.description else None
            # Фиксируем изменения, если это не SELECT
            if not query.strip().upper().startswith("SELECT"):
                self.conn.commit()
            return result
        except Exception:
            # При ошибке откатываем транзакцию, чтобы соединение осталось рабочим
            self.conn.rollback()
            raise

    # ------------------------------------------------------------------
    # Предметные методы
    # ------------------------------------------------------------------

    def create_tables(self) -> None:
        """Создаёт таблицы users и orders (если их ещё нет)."""
        users_cols = ",\n    ".join(f"{n} {d}" for n, d in USERS_TABLE.items())
        orders_cols = ",\n    ".join(f"{n} {d}" for n, d in ORDERS_TABLE.items())
        self._execute(f"CREATE TABLE IF NOT EXISTS users (\n    {users_cols}\n)")
        self._execute(f"CREATE TABLE IF NOT EXISTS orders (\n    {orders_cols}\n)")

    def add_user(self, name: str, age: int) -> dict:
        """Добавляет пользователя. Возвращает добавленную строку (с id)."""
        rows = self._execute(
            "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING *",
            (name, age),
            fetch=True,
        )
        return rows[0]

    def add_order(self, user_id: int, amount: float) -> dict:
        """Добавляет заказ для пользователя. Возвращает добавленную строку."""
        rows = self._execute(
            "INSERT INTO orders (user_id, amount) VALUES (%s, %s) RETURNING *",
            (user_id, amount),
            fetch=True,
        )
        return rows[0]

    def get_user_totals(self) -> list[dict]:
        """Сумма заказов по каждому пользователю.

        LEFT JOIN — показывает всех пользователей, даже без заказов.
        Сортировка по сумме по убыванию.
        """
        return self._execute(
            """
            SELECT
                u.id,
                u.name,
                COUNT(o.id)                AS orders_count,
                COALESCE(SUM(o.amount), 0) AS total_amount
            FROM users u
            LEFT JOIN orders o ON o.user_id = u.id
            GROUP BY u.id, u.name
            ORDER BY total_amount DESC
            """,
            fetch=True,
        )

    # ------------------------------------------------------------------
    # Универсальный метод
    # ------------------------------------------------------------------

    def execute(self, query: str, params: tuple | list = ()) -> list[dict]:
        """Выполняет произвольный SQL-запрос и возвращает результат (если есть)."""
        return self._execute(query, params, fetch=True)
