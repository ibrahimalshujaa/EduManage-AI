import sqlite3
from database import DB_PATH
print(f"Checking integrity of: {DB_PATH}")
try:
    conn = sqlite3.connect(DB_PATH)
    res = conn.execute("PRAGMA integrity_check;").fetchone()
    print(f"Integrity result: {res[0]}")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
