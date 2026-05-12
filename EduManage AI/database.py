import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'edumanage.db')

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        phone_number TEXT,
        address TEXT,
        profile_image TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Teachers Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        subject TEXT,
        teacher_number TEXT,
        department TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
    )
    ''')

    # Classes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT UNIQUE NOT NULL,
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES Teachers(id) ON DELETE SET NULL
    )
    ''')

    # Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        study_hours REAL DEFAULT 0,
        absences INTEGER DEFAULT 0,
        previous_score REAL DEFAULT 0,
        family_support INTEGER DEFAULT 5,
        teacher_note TEXT,
        student_number TEXT,
        parent_phone TEXT,
        last_updated_by TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES Users(id) ON DELETE CASCADE
    )
    ''')

    # New: StudentClasses Table (Many-to-Many Enrollment)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS StudentClasses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(student_id, class_id),
        FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES Classes(id) ON DELETE CASCADE
    )
    ''')

    # Grades Table (Enhanced)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER NOT NULL,
        subject_name TEXT NOT NULL,
        grade REAL DEFAULT 0,
        midterm REAL DEFAULT 0,
        final REAL DEFAULT 0,
        homework REAL DEFAULT 0,
        study_hours REAL DEFAULT 0,
        absences INTEGER DEFAULT 0,
        family_support INTEGER DEFAULT 5,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES Classes(id) ON DELETE CASCADE
    )
    ''')

    # Predictions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        class_id INTEGER,
        predicted_score REAL,
        success_probability REAL,
        risk_level TEXT,
        recommendation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (student_id) REFERENCES Students(id) ON DELETE CASCADE,
        FOREIGN KEY (class_id) REFERENCES Classes(id) ON DELETE CASCADE
    )
    ''')

    # Lessons Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Lessons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        subject TEXT,
        content TEXT,
        notes TEXT,
        attachment_path TEXT,
        attachment_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (class_id) REFERENCES Classes(id) ON DELETE CASCADE,
        FOREIGN KEY (teacher_id) REFERENCES Teachers(id) ON DELETE CASCADE
    )
    ''')

    # Quizzes Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lesson_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        quiz_url TEXT,
        due_date TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (lesson_id) REFERENCES Lessons(id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Multi-class enrollment schema initialized successfully.")
