"""
Пример использования драйвера postgres_driver.py.

Показывает: создание таблиц, добавление пользователей и заказов
(параметризованные запросы, транзакции), агрегирующий отчёт,
обработку исключений psycopg2.Error и гарантированное закрытие соединения.

Запуск: python main.py
"""

import psycopg2

from postgres_driver import PostgresDriver


def main():
    db = None
    try:
        with PostgresDriver() as db:
            # 1. Создаём таблицы users и orders (если их ещё нет)
            db.create_tables()
            print("Таблицы users и orders готовы\n")

            # 2. Добавляем пользователей (>= 3)
            users = [
                db.add_user("Иван", 30),
                db.add_user("Мария", 25),
                db.add_user("Пётр", 41),
            ]
            for u in users:
                print(f"Добавлен пользователь: {u['name']}, {u['age']} лет (id={u['id']})")

            # 3. Добавляем заказы (>= 2, у разных пользователей)
            orders = [
                db.add_order(users[0]["id"], 1500.00),
                db.add_order(users[0]["id"], 320.50),
                db.add_order(users[1]["id"], 9999.99),
            ]
            for o in orders:
                print(f"Добавлен заказ id={o['id']}: user_id={o['user_id']}, {o['amount']} руб.")

            # 4. Агрегирующий отчёт: сумма заказов по каждому пользователю
            #    (LEFT JOIN — все пользователи, включая тех, кто без заказов)
            print("\nСумма заказов по пользователям (по убыванию):")
            print(f"{'Пользователь':<15} {'Заказов':>8} {'Сумма, руб.':>12}")
            print("-" * 40)
            for r in db.get_user_totals():
                print(f"{r['name']:<15} {r['orders_count']:>8} {r['total_amount']:>12}")

    except psycopg2.Error as e:
        # Ошибки PostgreSQL: подключение, синтаксис, ограничения и т.д.
        print(f"Ошибка базы данных [{e.pgcode}]: {e.pgerror or e}")
    except ConnectionError as e:
        # Не удалось установить соединение
        print(f"Ошибка подключения: {e}")
    finally:
        # Гарантированное закрытие соединения — даже при исключении
        if db is not None:
            db.close()
            print("\nСоединение закрыто")


if __name__ == "__main__":
    main()