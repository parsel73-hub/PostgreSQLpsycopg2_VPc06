"""Создаёт таблицы users и orders в схеме public (разовый скрипт)."""
from database import Database

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

db = Database()
db.create_table("users", USERS_TABLE)
db.create_table("orders", ORDERS_TABLE)

# Проверяем, что таблицы созданы
tables = db.execute(
    "SELECT table_name FROM information_schema.tables "
    "WHERE table_schema = 'public' ORDER BY table_name"
)
print("Таблицы в схеме public:")
for t in tables:
    print(f"  {t['table_name']}")
db.close()
