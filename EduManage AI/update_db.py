import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'edumanage.db')

def update_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Update Users table
    try:
        cursor.execute("ALTER TABLE Users ADD COLUMN phone_number TEXT;")
        cursor.execute("ALTER TABLE Users ADD COLUMN address TEXT;")
        cursor.execute("ALTER TABLE Users ADD COLUMN profile_image TEXT;")
        print("Users table updated.")
    except sqlite3.OperationalError:
        print("Users table already updated or error occurred.")
        
    # Update Students table
    try:
        cursor.execute("ALTER TABLE Students ADD COLUMN student_number TEXT;")
        cursor.execute("ALTER TABLE Students ADD COLUMN parent_phone TEXT;")
        print("Students table updated.")
    except sqlite3.OperationalError:
        print("Students table already updated or error occurred.")
        
    # Update Teachers table
    try:
        cursor.execute("ALTER TABLE Teachers ADD COLUMN teacher_number TEXT;")
        cursor.execute("ALTER TABLE Teachers ADD COLUMN department TEXT;")
        print("Teachers table updated.")
    except sqlite3.OperationalError:
        print("Teachers table already updated or error occurred.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_schema()
