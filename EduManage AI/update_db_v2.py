import sqlite3
import os
from database import DB_PATH

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Add class_id to Predictions table if it doesn't exist
        cursor.execute("ALTER TABLE Predictions ADD COLUMN class_id INTEGER")
        print("Added class_id to Predictions table.")
    except sqlite3.OperationalError:
        print("class_id already exists in Predictions table.")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    migrate()
