import sqlite3
from database import DB_PATH

class AuthManager:
    def __init__(self):
        self.current_user = None

    def login(self, username, password):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, full_name, username, role FROM Users WHERE username = ? AND password = ?', 
                       (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            self.current_user = {
                'id': user[0],
                'full_name': user[1],
                'username': user[2],
                'role': user[3]
            }
            return self.current_user
        return None

    def logout(self):
        self.current_user = None

    def get_student_id(self, user_id):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM Students WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
