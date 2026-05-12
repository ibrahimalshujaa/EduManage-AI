import sqlite3
import os

def fix_database():
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'edumanage.db')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if columns exist
    cursor.execute("PRAGMA table_info(Lessons)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'attachment_path' not in columns:
        print("Adding attachment_path...")
        cursor.execute("ALTER TABLE Lessons ADD COLUMN attachment_path TEXT")
    
    if 'attachment_name' not in columns:
        print("Adding attachment_name...")
        cursor.execute("ALTER TABLE Lessons ADD COLUMN attachment_name TEXT")
        
    conn.commit()
    conn.close()
    print("Database fixed successfully.")

if __name__ == "__main__":
    fix_database()
