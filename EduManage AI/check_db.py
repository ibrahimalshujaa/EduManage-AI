import sqlite3
import os
from database import DB_PATH

print(f"Checking DB: {DB_PATH}")
try:
    conn = sqlite3.connect(DB_PATH, timeout=5)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f"Tables: {tables}")
    conn.close()
    print("DB check successful.")
except Exception as e:
    print(f"DB check failed: {e}")
