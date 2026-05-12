import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'edumanage.db')

def fix_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Students table columns
    cursor.execute("PRAGMA table_info(Students)")
    columns = [col[1] for col in cursor.fetchall()]
    
    required_students = [
        ('teacher_note', 'TEXT'),
        ('last_updated_by', 'TEXT'),
        ('updated_at', 'TIMESTAMP')
    ]
    
    for col_name, col_type in required_students:
        if col_name not in columns:
            print(f"Adding {col_name} to Students table...")
            cursor.execute(f"ALTER TABLE Students ADD COLUMN {col_name} {col_type}")

    # Check Grades table columns
    cursor.execute("PRAGMA table_info(Grades)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'updated_at' not in columns:
        print("Adding updated_at to Grades table...")
        cursor.execute("ALTER TABLE Grades ADD COLUMN updated_at TIMESTAMP")

    # Check Predictions table columns
    cursor.execute("PRAGMA table_info(Predictions)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'updated_at' not in columns:
        print("Adding updated_at to Predictions table...")
        cursor.execute("ALTER TABLE Predictions ADD COLUMN updated_at TIMESTAMP")

    conn.commit()
    conn.close()
    print("Database schema verified and updated.")

if __name__ == "__main__":
    fix_schema()
