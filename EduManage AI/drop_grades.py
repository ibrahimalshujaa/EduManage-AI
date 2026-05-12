import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'edumanage.db')

def drop_grades():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS Grades;")
    conn.commit()
    conn.close()
    print("Grades table dropped.")

if __name__ == "__main__":
    drop_grades()
