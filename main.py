"""
Примерный проект: менеджер задач.

Демонстрирует использование модуля-драйвера database.py в реальном сценарии:
две связанные таблицы (users -> tasks), CRUD-операции, JOIN через execute().

Запуск: python main.py
"""

from database import Database

# SQL-определения таблиц проекта
USERS_TABLE = {
    "id": "SERIAL PRIMARY KEY",
    "name": "TEXT NOT NULL",
    "email": "TEXT UNIQUE NOT NULL",
}

TASKS_TABLE = {
    "id": "SERIAL PRIMARY KEY",
    "user_id": "INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE",
    "title": "TEXT NOT NULL",
    "done": "BOOLEAN NOT NULL DEFAULT FALSE",
    "created_at": "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP",
}


def seed(db: Database) -> list[int]:
    """Наполняет базу тестовыми данными. Возвращает id пользователей."""
    users = [
        {"name": "Иван", "email": "ivan@example.com"},
        {"name": "Мария", "email": "maria@example.com"},
    ]
    user_ids = [db.insert("users", u)["id"] for u in users]

    tasks = [
        {"user_id": user_ids[0], "title": "Изучить psycopg2", "done": True},
        {"user_id": user_ids[0], "title": "Написать драйвер БД", "done": True},
        {"user_id": user_ids[0], "title": "Сделать ДЗ по курсу", "done": False},
        {"user_id": user_ids[1], "title": "Пройти курс по PostgreSQL", "done": False},
    ]
    for t in tasks:
        db.insert("tasks", t)
    return user_ids


def show_user_tasks(db: Database, user_id: int) -> None:
    """Выводит задачи конкретного пользователя (JOIN через execute)."""
    rows = db.execute(
        "SELECT t.id, t.title, t.done "
        "FROM tasks t WHERE t.user_id = %s ORDER BY t.id",
        (user_id,),
    )
    for row in rows:
        status = "✓" if row["done"] else "✗"
        print(f"  [{status}] {row['id']}: {row['title']}")


def main():
    with Database() as db:
        # --- Инициализация схемы ---
        db.create_table("users", USERS_TABLE)
        db.create_table("tasks", TASKS_TABLE)
        print("Таблицы users и tasks готовы\n")

        # Если в базе уже есть данные — не дублируем
        if db.select("users", limit=1):
            print("В базе уже есть данные, пропускаю наполнение\n")
        else:
            user_ids = seed(db)
            print(f"Добавлены пользователи с id: {user_ids}\n")

        # --- SELECT: все пользователи ---
        print("Пользователи:")
        for u in db.select("users", order_by="id"):
            print(f"  {u['id']}: {u['name']} <{u['email']}>")

        # --- SELECT с фильтром: задачи Ивана ---
        ivan = db.select("users", where={"name": "Иван"})[0]
        print(f"\nЗадачи пользователя {ivan['name']}:")
        show_user_tasks(db, ivan["id"])

        # --- UPDATE: отмечаем задачу выполненной ---
        count = db.update("tasks", {"done": True}, {"title": "Сделать ДЗ по курсу"})
        print(f"\nОтмечено выполненных задач: {count}")

        # --- INSERT: новая задача для Марии ---
        maria = db.select("users", where={"name": "Мария"})[0]
        new_task = db.insert("tasks", {"user_id": maria["id"], "title": "Разобрать JOIN"})
        print(f"Добавлена задача: {new_task['title']} (id={new_task['id']})")

        # --- DELETE: удаляем выполненные задачи Ивана ---
        deleted = db.delete("tasks", {"user_id": ivan["id"], "done": True})
        print(f"Удалено выполненных задач Ивана: {deleted}")

        # --- Итоговая статистика (JOIN + агрегация через execute) ---
        print("\nСтатистика по пользователям:")
        stats = db.execute(
            "SELECT u.name, COUNT(t.id) AS total, "
            "COUNT(t.id) FILTER (WHERE t.done) AS done "
            "FROM users u LEFT JOIN tasks t ON t.user_id = u.id "
            "GROUP BY u.id, u.name ORDER BY u.id"
        )
        for s in stats:
            print(f"  {s['name']}: всего {s['total']}, выполнено {s['done']}")


if __name__ == "__main__":
    main()