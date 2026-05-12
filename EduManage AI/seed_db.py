import sqlite3
import os
from database import DB_PATH, init_db

def seed_admin():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create Master Admin
    admin_email = 'admin@edumanage.com'
    admin_pass = 'admin123'
    
    try:
        c.execute("INSERT INTO Users (full_name, email, password, role) VALUES (?, ?, ?, ?)", 
                  ('Institutional Administrator', admin_email, admin_pass, 'admin'))
        conn.commit()
        print(f"Master Admin created: {admin_email} / {admin_pass}")
    except sqlite3.IntegrityError:
        print("Admin account already exists.")

    conn.close()

if __name__ == "__main__":
    seed_admin()
