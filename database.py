# database.py
import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = None
def get_db_path():
    return ""

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