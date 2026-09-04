"""
Добавляет пользователей и заказы через параметризованные запросы (%s)
и транзакции (with conn:).

Запуск: python insert_data.py
"""

from database import Database

USERS = [
    ("Иван", 30),
    ("Мария", 25),
    ("Пётр", 41),
]

ORDERS = [
    # (имя пользователя, сумма) — user_id подставим по имени
    ("Иван", 1500.00),
    ("Иван", 320.50),
    ("Мария", 9999.99),
]


def main():
    db = Database()

    # --- Пользователи: одна транзакция на весь пакет ---
    with db.conn as conn:
        with conn.cursor() as cur:
            for name, age in USERS:
                cur.execute(
                    "INSERT INTO users (name, age) VALUES (%s, %s) RETURNING id",
                    (name, age),  # параметризованный запрос
                )
                print(f"Добавлен пользователь: {name}, {age} лет (id={cur.fetchone()[0]})")
        # при выходе из with conn: — автоматический COMMIT
        # при исключении — автоматический ROLLBACK

    # --- Заказы: определяем user_id по имени и вставляем одной транзакцией ---
    with db.conn as conn:
        with conn.cursor() as cur:
            for username, amount in ORDERS:
                cur.execute("SELECT id FROM users WHERE name = %s", (username,))
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Пользователь '{username}' не найден")
                cur.execute(
                    "INSERT INTO orders (user_id, amount) VALUES (%s, %s) RETURNING id, created_at",
                    (row[0], amount),
                )
                order_id, created_at = cur.fetchone()
                print(f"Добавлен заказ id={order_id}: {username} — {amount} руб. ({created_at})")

    # --- Проверка результата ---
    print("\nПользователи:")
    for u in db.select("users", order_by="id"):
        print(f"  {u['id']}: {u['name']}, {u['age']} лет")

    print("\nЗаказы (JOIN):")
    rows = db.execute(
        "SELECT o.id, u.name, o.amount, o.created_at "
        "FROM orders o JOIN users u ON u.id = o.user_id ORDER BY o.id"
    )
    for r in rows:
        print(f"  {r['id']}: {r['name']} — {r['amount']} руб. от {r['created_at']:%d.%m.%Y %H:%M}")

    db.close()


if __name__ == "__main__":
    main()
