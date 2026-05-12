import sqlite3
import os
from database import DB_PATH

def check_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    tables = ['Predictions', 'Grades', 'Students', 'Classes']
    for table in tables:
        print(f"\n--- Schema for {table} ---")
        cursor.execute(f"PRAGMA table_info({table})")
        info = cursor.fetchall()
        for col in info:
            print(col)
    
    conn.close()

if __name__ == "__main__":
    check_schema()
