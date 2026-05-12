import sqlite3
import random
from database import DB_PATH

def seed_large_dataset():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear existing data
    cursor.execute("DELETE FROM Grades")
    cursor.execute("DELETE FROM Students")
    cursor.execute("DELETE FROM Users WHERE role != 'admin'")
    
    # 1. Teachers
    teachers = [
        ("john_teacher", "pass123", "John Smith", "john@school.edu"),
        ("sarah_jones", "pass123", "Sarah Jones", "sarah@school.edu"),
        ("ahmed_m", "pass123", "Ahmed Mohamed", "ahmed@school.edu"),
        ("lisa_brown", "pass123", "Lisa Brown", "lisa@school.edu"),
        ("david_wilson", "pass123", "David Wilson", "david@school.edu")
    ]
    for username, password, name, email in teachers:
        cursor.execute("INSERT INTO Users (username, password, role, full_name) VALUES (?, ?, 'teacher', ?)",
                       (username, password, name))

    # 2. Students
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
                   "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
                   "Omar", "Sara", "Khalid", "Laila", "Youssef", "Mona", "Hassan", "Nour", "Zaid", "Hoda"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
                  "Ali", "Hassan", "Ibrahim", "Abdel", "Mohamed", "Sayed", "Mansour", "Gad", "Farag", "Salim"]
    
    classes = ["10th Grade - Class A", "10th Grade - Class B", "11th Grade - Class A", "11th Grade - Class B", "12th Grade - Class A", "12th Grade - Class B"]
    
    subjects = ["Mathematics", "Physics", "Chemistry", "English", "History", "Biology", "Computer Science"]
    
    for i in range(1, 51):  # 50 Students
        username = f"student_{i}"
        full_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        cursor.execute("INSERT INTO Users (username, password, role, full_name) VALUES (?, 'stud123', 'student', ?)",
                       (username, full_name))
        uid = cursor.lastrowid
        
        class_name = random.choice(classes)
        study_hours = random.randint(5, 35)
        absences = random.randint(0, 15)
        fam_support = random.randint(1, 10)
        prev_score = random.randint(50, 95)
        
        cursor.execute('''INSERT INTO Students (user_id, class_name, study_hours, absences, family_support, previous_score)
                          VALUES (?, ?, ?, ?, ?, ?)''', (uid, class_name, study_hours, absences, fam_support, prev_score))
        sid = cursor.lastrowid
        
        # Grades
        for sub in subjects:
            grade = random.randint(40, 100)
            cursor.execute("INSERT INTO Grades (student_id, subject_name, grade) VALUES (?, ?, ?)", (sid, sub, grade))

    conn.commit()
    conn.close()
    print("Database seeded with 50 students, 5 teachers, and academic records.")

if __name__ == "__main__":
    seed_large_dataset()
