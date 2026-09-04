# Инструкция к драйверу `database.py`

Модуль-драйвер для работы с базой данных PostgreSQL из внешних проектов.
Оборачивает `psycopg2` в простой класс с CRUD-методами и защищает от SQL-инъекций
(все значения передаются через параметры `%s`, а не склеиваются в строку SQL).

## 1. Подготовка

### Зависимости

```bash
pip install -r requirements.txt
```

(`psycopg2-binary` + `python-dotenv`)

### Настройки подключения

Драйвер читает параметры из файла `.env` в корне проекта (см. `.env.example`):

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=ваш_пароль
```

### Подключение

```python
from database import Database

# Вариант 1: настройки из .env
db = Database()

# Вариант 2: явный конфиг (приоритетнее .env)
db = Database({
    "host": "localhost",
    "port": 5432,
    "dbname": "mydb",
    "user": "postgres",
    "password": "secret",
})

# Вариант 3: как менеджер контекста — соединение закроется автоматически
with Database() as db:
    rows = db.select("users")

# Закрыть соединение вручную (для вариантов 1 и 2)
db.close()
```

## 2. Методы

### `create_table(table, columns, *, if_not_exists=True)`

Создаёт таблицу. `columns` — словарь `{имя_колонки: SQL-определение}`.

```python
db.create_table("users", {
    "id": "SERIAL PRIMARY KEY",
    "name": "TEXT NOT NULL",
    "email": "TEXT UNIQUE NOT NULL",
    "age": "INTEGER",
    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
})
```

### `insert(table, data) -> dict`

Вставляет строку, возвращает её целиком (включая сгенерированный `SERIAL id`).

```python
user = db.insert("users", {"name": "Иван", "email": "ivan@example.com"})
print(user["id"])  # 1
```

### `select(table, columns=None, where=None, order_by=None, limit=None) -> list[dict]`

Читает строки. Возвращает список словарей (`RealDictRow` — доступ по имени колонки).

```python
# Все строки, все колонки
rows = db.select("users")

# Только имена, отсортированные по age, первые 5
rows = db.select("users", columns=["name"], order_by="age DESC", limit=5)

# С фильтром (несколько условий объединяются через AND)
rows = db.select("users", where={"name": "Иван", "age": 30})
```

### `update(table, data, where) -> int`

Обновляет строки по условию, возвращает число обновлённых строк.
**Без `where` выбрасывает `ValueError`** — защита от случайного изменения всех строк.

```python
count = db.update("users", {"age": 31}, {"name": "Иван"})
```

### `delete(table, where) -> int`

Удаляет строки по условию, возвращает число удалённых строк.
**Без `where` выбрасывает `ValueError`.**

```python
count = db.delete("users", {"id": 5})
```

### `execute(query, params=()) -> list[dict]`

Универсальный метод для произвольных SQL-запросов (JOIN, агрегаты, DDL и т.д.).

```python
# JOIN
rows = db.execute(
    "SELECT u.name, COUNT(o.id) AS orders_count "
    "FROM users u LEFT JOIN orders o ON o.user_id = u.id "
    "GROUP BY u.name"
)

# С параметрами
rows = db.execute("SELECT * FROM users WHERE age > %s", (25,))
```

## 3. Важные особенности

- **Транзакции.** Изменяющие запросы автоматически получают `COMMIT`; при любой ошибке выполняется `ROLLBACK`, и соединение остаётся рабочим.
- **Возврат данных.** `insert`, `update`, `delete` используют `RETURNING *`, поэтому всегда известно, какие строки затронуты.
- **Защита от SQL-инъекций.** Значения подставляются через плейсхолдеры `%s`. Имена таблиц/колонок подставляются напрямую — не формируйте их из пользовательского ввода.
- **Переподключение.** Если соединение закрылось, драйвер автоматически откроет его заново при следующем запросе.
- **Результат.** Все выборки — список словарей: `row["column_name"]`.

## 4. Полный пример

См. `main.py` — примерный проект «менеджер задач»: создание таблиц, пользователи,
задачи с внешним ключом, статистика через JOIN.
