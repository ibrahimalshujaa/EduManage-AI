import sqlite3
import os

db_path = 'data/edumanage.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    users = conn.execute("SELECT email, password, role FROM Users WHERE role='admin'").fetchall()
    for u in users:
        print(f"Role: {u['role']} | Email: {u['email']} | Password: {u['password']}")
    conn.close()
else:
    print("Database not found.")
