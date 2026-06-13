# database.py
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = "sql_agent.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS countries (
    country_id INTEGER PRIMARY KEY,
    country_name TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS customers (
    customer_id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    country_id INTEGER REFERENCES countries(country_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    status TEXT NOT NULL CHECK(status IN ('completed','cancelled','pending')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL
);
"""

COUNTRIES = [
    (1, "United States", "North America"),
    (2, "United Kingdom", "Europe"),
    (3, "Germany", "Europe"),
    (4, "France", "Europe"),
    (5, "Canada", "North America"),
    (6, "Australia", "Oceania"),
    (7, "India", "Asia"),
    (8, "Brazil", "South America"),
    (9, "Japan", "Asia"),
    (10, "Mexico", "North America"),
]

FIRST_NAMES = ["Alice","Bob","Carlos","Diana","Ethan","Fatima","George","Hannah",
               "Ivan","Julia","Kevin","Lena","Marco","Nina","Omar","Priya",
               "Quinn","Rosa","Sam","Tina","Umar","Vera","Will","Xia","Yara","Zoe"]

LAST_NAMES = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller",
              "Davis","Martinez","Wilson","Anderson","Taylor","Thomas","Moore",
              "Jackson","White","Harris","Clark","Lewis","Walker"]

PRODUCTS = [
    ("Solar Panel 100W", 120.00),
    ("Wind Sensor Kit", 85.50),
    ("CO2 Monitor", 210.00),
    ("Rain Gauge", 45.00),
    ("Temperature Logger", 65.00),
    ("Air Quality Sensor", 175.00),
    ("UV Index Meter", 55.00),
    ("Soil Moisture Probe", 40.00),
    ("Weather Station", 320.00),
    ("Data Logger Pro", 250.00),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    cur.execute("SELECT COUNT(*) FROM countries")
    if cur.fetchone()[0] > 0:
        conn.close()
        return  # already seeded

    cur.executemany("INSERT INTO countries VALUES (?,?,?)", COUNTRIES)

    random.seed(42)
    customers = []
    for i in range(1, 201):
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES)
        email = f"{fn.lower()}.{ln.lower()}{i}@example.com"
        country_id = random.randint(1, 10)
        created = datetime(2024, 1, 1) + timedelta(days=random.randint(0, 900))
        customers.append((i, fn, ln, email, country_id, created.strftime("%Y-%m-%d")))
    cur.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", customers)

    statuses = ["completed"] * 7 + ["cancelled"] * 2 + ["pending"] * 1
    order_id = 1
    item_id = 1
    for customer_id in range(1, 201):
        num_orders = random.randint(0, 6)
        for _ in range(num_orders):
            status = random.choice(statuses)
            created = datetime(2023, 1, 1) + timedelta(days=random.randint(0, 500))
            cur.execute("INSERT INTO orders VALUES (?,?,?,?)",
                        (order_id, customer_id, status, created.strftime("%Y-%m-%d")))
            num_items = random.randint(1, 4)
            for _ in range(num_items):
                product, price = random.choice(PRODUCTS)
                qty = random.randint(1, 5)
                cur.execute("INSERT INTO order_items VALUES (?,?,?,?,?)",
                            (item_id, order_id, product, qty, price))
                item_id += 1
            order_id += 1

    conn.commit()
    conn.close()
    print("Database seeded successfully.")


def get_schema_string():
    return """
Table: countries
  country_id INTEGER PRIMARY KEY
  country_name TEXT
  region TEXT

Table: customers
  customer_id INTEGER PRIMARY KEY
  first_name TEXT
  last_name TEXT
  email TEXT
  country_id INTEGER (FK -> countries.country_id)
  created_at TEXT (YYYY-MM-DD)

Table: orders
  order_id INTEGER PRIMARY KEY
  customer_id INTEGER (FK -> customers.customer_id)
  status TEXT ('completed', 'cancelled', 'pending')
  created_at TEXT (YYYY-MM-DD)

Table: order_items
  item_id INTEGER PRIMARY KEY
  order_id INTEGER (FK -> orders.order_id)
  product_name TEXT
  quantity INTEGER
  unit_price REAL
"""


def run_query(sql: str, db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = []
    for row in cur.fetchall():
        clean_row = {}
        for key in row.keys():
            value = row[key]
            if isinstance(value, bytes):
                clean_row[key] = f"<binary data, {len(value)} bytes>"
            else:
                clean_row[key] = value
        rows.append(clean_row)
    conn.close()
    return rows

def get_dynamic_schema(db_path: str) -> str:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cur.fetchall()]

    schema_lines = []
    for table in tables:
        cur.execute(f'PRAGMA table_info("{table}")')
        columns = cur.fetchall()
        schema_lines.append(f"Table: {table}")
        for col in columns:
            schema_lines.append(f"  {col[1]} {col[2]}")
        schema_lines.append("")

    conn.close()
    return "\n".join(schema_lines)

if __name__ == "__main__":
    seed()