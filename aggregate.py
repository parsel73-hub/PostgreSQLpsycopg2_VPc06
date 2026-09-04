"""
Агрегирующий запрос: сумма заказов по каждому пользователю.

LEFT JOIN показывает всех пользователей, даже тех, у кого нет заказов.
Сортировка — по сумме по убыванию.

Обрабатываются исключения psycopg2.Error, соединение закрывается
гарантированно (finally / менеджер контекста).

Запуск: python aggregate.py
"""

import psycopg2

from database import Database

QUERY = """
    SELECT
        u.id,
        u.name,
        COUNT(o.id)            AS orders_count,
        COALESCE(SUM(o.amount), 0) AS total_amount
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id, u.name
    ORDER BY total_amount DESC
"""


def main():
    db = None
    try:
        db = Database()
        rows = db.execute(QUERY)

        print(f"{'Пользователь':<15} {'Заказов':>8} {'Сумма, руб.':>12}")
        print("-" * 40)
        for r in rows:
            print(f"{r['name']:<15} {r['orders_count']:>8} {r['total_amount']:>12}")

    except psycopg2.Error as e:
        # Ошибки PostgreSQL: проблемы подключения, синтаксиса, ограничений и т.д.
        print(f"Ошибка базы данных [{e.pgcode}]: {e.pgerror or e}")
    except ConnectionError as e:
        # Не удалось установить соединение (драйвер оборачивает OperationalError)
        print(f"Ошибка подключения: {e}")
    finally:
        # Гарантированное закрытие соединения — даже при исключении
        if db is not None:
            db.close()
            print("\nСоединение закрыто")


if __name__ == "__main__":
    main()
