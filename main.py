"""
Демонстрация работы модуля-драйвера database.py.

Запуск: python main.py
"""

from database import Database


def main():
    # Подключаемся (параметры берутся из .env)
    with Database() as db:
        # CREATE — создаём таблицу для демонстрации
        db.create_table(
            "users",
            {
                "id": "SERIAL PRIMARY KEY",
                "name": "TEXT NOT NULL",
                "email": "TEXT UNIQUE NOT NULL",
            },
        )
        print("Таблица users готова")

        # INSERT — добавляем записи
        user1 = db.insert("users", {"name": "Иван", "email": "ivan@example.com"})
        user2 = db.insert("users", {"name": "Мария", "email": "maria@example.com"})
        print(f"Добавлены: {user1}, {user2}")

        # SELECT — читаем все записи
        print("\nВсе пользователи:")
        for row in db.select("users", order_by="id"):
            print(f"  {row['id']}: {row['name']} <{row['email']}>")

        # UPDATE — обновляем email Ивана
        updated = db.update(
            "users",
            {"email": "ivan.new@example.com"},
            {"name": "Иван"},
        )
        print(f"\nОбновлено строк: {updated}")

        # SELECT с фильтром — проверяем обновление
        ivan = db.select("users", where={"name": "Иван"})
        print(f"Иван после обновления: {ivan}")

        # DELETE — удаляем Марию
        deleted = db.delete("users", {"name": "Мария"})
        print(f"Удалено строк: {deleted}")

        # Итоговое состояние таблицы
        print("\nИтог:")
        for row in db.select("users"):
            print(f"  {row['id']}: {row['name']} <{row['email']}>")


if __name__ == "__main__":
    main()