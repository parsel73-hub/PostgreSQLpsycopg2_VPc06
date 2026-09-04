"""
Модуль-драйвер для работы с PostgreSQL из внешних проектов.

Предоставляет класс Database с CRUD-методами. Параметры подключения
берутся из файла .env (см. .env.example) — так же, как в main.py.

Пример использования:

    from database import Database

    db = Database()
    db.create_table()
    db.insert("users", {"name": "Иван", "email": "ivan@example.com"})
    rows = db.select("users", where={"name": "Иван"})
    db.update("users", {"email": "new@example.com"}, {"name": "Иван"})
    db.delete("users", {"name": "Иван"})
    db.close()
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


class Database:
    """Драйвер для работы с базой данных PostgreSQL.

    Инкапсулирует подключение и CRUD-операции.
    Поддерживает работу как менеджер контекста:

        with Database() as db:
            db.select("users")
    """

    def __init__(self, config: dict[str, Any] | None = None):
        # Если конфиг не передан — используем настройки из .env
        self.config = config or DB_CONFIG
        self.conn = None
        self.connect()

    # ------------------------------------------------------------------
    # Подключение
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """Открывает соединение с базой данных (если ещё не открыто)."""
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg2.connect(**self.config)
            except psycopg2.OperationalError as e:
                raise ConnectionError(f"Не удалось подключиться к базе: {e}") from e

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def __enter__(self) -> "Database":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Внутренние помощники
    # ------------------------------------------------------------------

    @staticmethod
    def _build_where(where: dict[str, Any] | None) -> tuple[str, list[Any]]:
        """Собирает SQL-условие WHERE из словаря.

        Возвращает строку WHERE (может быть пустой) и список значений.
        """
        if not where:
            return "", []
        conditions = [f"{key} = %s" for key in where]
        return " WHERE " + " AND ".join(conditions), list(where.values())

    def _execute(self, query: str, params: tuple | list = (), *, fetch: bool = False):
        """Выполняет запрос. При fetch=True возвращает все строки результата."""
        self.connect()
        try:
            with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                result = cur.fetchall() if fetch else None
            # Фиксируем изменения, если это не SELECT
            if not query.strip().upper().startswith("SELECT"):
                self.conn.commit()
            return result
        except Exception:
            # При ошибке откатываем транзакцию, чтобы соединение осталось рабочим
            self.conn.rollback()
            raise

    # ------------------------------------------------------------------
    # CRUD-методы
    # ------------------------------------------------------------------

    def create_table(self, table: str, columns: dict[str, str], *, if_not_exists: bool = True) -> None:
        """Создаёт таблицу.

        :param table: имя таблицы
        :param columns: словарь {имя_колонки: SQL-определение},
                        например {"id": "SERIAL PRIMARY KEY", "name": "TEXT NOT NULL"}
        :param if_not_exists: добавить IF NOT EXISTS
        """
        cols = ",\n    ".join(f"{name} {definition}" for name, definition in columns.items())
        ine = "IF NOT EXISTS " if if_not_exists else ""
        self._execute(f"CREATE TABLE {ine}{table} (\n    {cols}\n)")

    def insert(self, table: str, data: dict[str, Any]) -> dict | None:
        """Вставляет строку. Возвращает вставленную строку (с SERIAL id)."""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING *"
        rows = self._execute(query, list(data.values()), fetch=True)
        return rows[0] if rows else None

    def select(
        self,
        table: str,
        columns: list[str] | None = None,
        where: dict[str, Any] | None = None,
        order_by: str | None = None,
        limit: int | None = None,
    ) -> list[dict]:
        """Читает строки из таблицы.

        :param columns: список колонок (по умолчанию все — *)
        :param where: условия фильтрации {колонка: значение}, объединяются через AND
        :param order_by: SQL-фрагмент сортировки, например "id DESC"
        :param limit: ограничение количества строк
        """
        cols = ", ".join(columns) if columns else "*"
        where_sql, params = self._build_where(where)
        query = f"SELECT {cols} FROM {table}{where_sql}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        return self._execute(query, params, fetch=True)

    def update(self, table: str, data: dict[str, Any], where: dict[str, Any]) -> int:
        """Обновляет строки по условию. Возвращает количество обновлённых строк."""
        if not where:
            raise ValueError("UPDATE без условия WHERE запрещён — это изменит все строки")
        set_sql = ", ".join(f"{key} = %s" for key in data)
        where_sql, where_params = self._build_where(where)
        query = f"UPDATE {table} SET {set_sql}{where_sql} RETURNING *"
        rows = self._execute(query, list(data.values()) + where_params, fetch=True)
        return len(rows)

    def delete(self, table: str, where: dict[str, Any]) -> int:
        """Удаляет строки по условию. Возвращает количество удалённых строк."""
        if not where:
            raise ValueError("DELETE без условия WHERE запрещён — это удалит все строки")
        where_sql, params = self._build_where(where)
        query = f"DELETE FROM {table}{where_sql} RETURNING *"
        rows = self._execute(query, params, fetch=True)
        return len(rows)

    # ------------------------------------------------------------------
    # Универсальный метод
    # ------------------------------------------------------------------

    def execute(self, query: str, params: tuple | list = ()) -> list[dict]:
        """Выполняет произвольный SQL-запрос и возвращает результат (если есть)."""
        return self._execute(query, params, fetch=True)
