import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from database import DB_PATH
from ai_model import predict_student_performance
from reports_generator import generate_pdf_report
from translations import TRANSLATIONS

app = Flask(__name__)
app.secret_key = 'edumanage_secret_key'

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'profiles')
LESSONS_FOLDER = os.path.join('static', 'uploads', 'lessons')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LESSONS_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['LESSONS_FOLDER'] = LESSONS_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt'}

# Localization Context Processor
@app.context_processor
def inject_translations():
    lang = session.get('lang', 'en')
    def translate(key):
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)
    return dict(_=translate, current_lang=lang)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['en', 'tr']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('dashboard'))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.before_request
def log_request():
    # Only print interesting requests to avoid clutter
    if not request.path.startswith('/static'):
        print(f"DEBUG: Request to {request.path} [Role: {session.get('role', 'Guest')}]")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.context_processor
def inject_user():
    if 'user_id' in session:
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT profile_image, full_name FROM Users WHERE id = ?', (session['user_id'],)).fetchone()
            conn.close()
            if user:
                return {'current_user': user}
            else:
                session.clear()
        except: pass
    return {'current_user': {'profile_image': None, 'full_name': 'Guest User'}}

def sync_student_data(sid):
    try:
        conn = get_db_connection()
        student = conn.execute('SELECT * FROM Students WHERE id = ?', (sid,)).fetchone()
        if not student: return
        # Fetch detailed performance metrics for global sync
        stats = conn.execute('''
            SELECT 
                AVG(midterm), AVG(final), AVG(homework), 
                AVG(study_hours), SUM(absences), AVG(family_support) 
            FROM Grades WHERE student_id = ?
        ''', (sid,)).fetchone()
        
        avg_midterm = stats[0] or 0
        avg_final = stats[1] or 0
        avg_homework = stats[2] or 0
        avg_study = stats[3] or 0
        total_abs = stats[4] or 0
        avg_support = stats[5] or 5
        
        conn.execute('UPDATE Students SET study_hours=?, absences=?, family_support=? WHERE id=?', (avg_study, total_abs, avg_support, sid))
        
        # General prediction sync (legacy/background)
        score, prob, risk, conf = predict_student_performance(
            avg_study, total_abs, avg_support, student['previous_score'],
            midterm=avg_midterm, final=avg_final, homework=avg_homework
        )
        avg_g = (avg_midterm * 0.3 + avg_final * 0.5 + avg_homework * 0.2)
        from recommender import generate_recommendations
        recs = generate_recommendations(avg_study, total_abs, avg_g, student['previous_score'])
        rec_text = recs[0]['description'] if recs else "Maintain current study habits."
        
        existing = conn.execute('SELECT id FROM Predictions WHERE student_id = ? AND class_id IS NULL', (sid,)).fetchone()
        if existing: conn.execute('UPDATE Predictions SET predicted_score=?, success_probability=?, risk_level=?, recommendation=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (score, prob, risk, rec_text, existing['id']))
        else: conn.execute('INSERT INTO Predictions (student_id, predicted_score, success_probability, risk_level, recommendation) VALUES (?, ?, ?, ?, ?)', (sid, score, prob, risk, rec_text))
        
        conn.commit()
        conn.close()
    except Exception as e: print(f"DEBUG SYNC ERROR: {e}")

@app.route('/')
def index():
    if 'user_id' in session: return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM Users WHERE email = ? AND password = ?', (email, password)).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))
        else: flash('Invalid credentials.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session: return redirect(url_for('login'))
    role = session['role']
    conn = get_db_connection()
    if role == 'admin':
        stats = {'students': conn.execute('SELECT COUNT(*) FROM Students').fetchone()[0], 'teachers': conn.execute('SELECT COUNT(*) FROM Teachers').fetchone()[0], 'classes': conn.execute('SELECT COUNT(*) FROM Classes').fetchone()[0]}
        alerts = conn.execute('''SELECT u.full_name, c.class_name, ROUND(p.predicted_score, 1) as predicted_score, ROUND(p.success_probability, 1) as success_probability, p.risk_level FROM Predictions p JOIN Students s ON p.student_id = s.id JOIN Users u ON s.user_id = u.id JOIN Classes c ON p.class_id = c.id ORDER BY p.updated_at DESC LIMIT 5''').fetchall()
        conn.close()
        return render_template('admin_dashboard.html', active_page='dashboard', stats=stats, alerts=alerts)
    elif role == 'teacher':
        teacher = conn.execute('SELECT id FROM Teachers WHERE user_id = ?', (session['user_id'],)).fetchone()
        stats = {'students': 0, 'avg_grade': 0, 'at_risk': 0, 'success': 0}
        if teacher:
            tid = teacher['id']
            # Optimized Stats via SQL aggregation - NO more Python loops over AI models
            res = conn.execute('''
                SELECT 
                    COUNT(DISTINCT sc.student_id) as student_count,
                    AVG(COALESCE((g.midterm * 0.3 + g.final * 0.5 + g.homework * 0.2), 0)) as avg_grade,
                    SUM(CASE WHEN p.risk_level = 'High Risk' OR (COALESCE((g.midterm * 0.3 + g.final * 0.5 + g.homework * 0.2), 0) < 50) THEN 1 ELSE 0 END) as at_risk_count,
                    AVG(COALESCE(p.success_probability, 0)) as avg_success
                FROM StudentClasses sc
                JOIN Classes c ON c.id = sc.class_id
                LEFT JOIN Grades g ON g.student_id = sc.student_id AND g.class_id = sc.class_id
                LEFT JOIN Predictions p ON p.student_id = sc.student_id AND p.class_id = sc.class_id
                WHERE c.teacher_id = ?
            ''', (tid,)).fetchone()
            
            stats = {
                'students': res['student_count'] or 0,
                'avg_grade': round(res['avg_grade'] or 0, 1),
                'at_risk': res['at_risk_count'] or 0,
                'success': round(res['avg_success'] or 0, 1)
            }
        conn.close()
        return render_template('teacher_dashboard.html', active_page='dashboard', stats=stats, recent_grades=[], classes=[], risk_students=[], recs=[])
    elif role == 'student':
        student = conn.execute('SELECT id, absences, study_hours, previous_score FROM Students WHERE user_id = ?', (session['user_id'],)).fetchone()
        if not student: return "Record not found."
        sid = student['id']
        
        classes = conn.execute('SELECT c.class_name FROM StudentClasses sc JOIN Classes c ON sc.class_id = c.id WHERE sc.student_id = ?', (sid,)).fetchall()
        
        # Fetch Subject-specific Grades and Class Averages
        perf_data = conn.execute('''
            SELECT 
                c.class_name as subject,
                COALESCE((g.midterm * 0.3 + g.final * 0.5 + g.homework * 0.2), 0) as user_grade,
                (SELECT AVG(COALESCE((g2.midterm * 0.3 + g2.final * 0.5 + g2.homework * 0.2), 0)) 
                 FROM Grades g2 WHERE g2.class_id = c.id) as class_avg
            FROM StudentClasses sc
            JOIN Classes c ON sc.class_id = c.id
            LEFT JOIN Grades g ON g.student_id = sc.student_id AND g.class_id = sc.class_id
            WHERE sc.student_id = ?
        ''', (sid,)).fetchall()
        
        chart_labels = [row['subject'] for row in perf_data]
        chart_user_data = [round(row['user_grade'], 1) for row in perf_data]
        chart_avg_data = [round(row['class_avg'] or 0, 1) for row in perf_data]

        grade_stats = conn.execute('SELECT AVG(midterm * 0.3 + final * 0.5 + homework * 0.2) FROM Grades WHERE student_id = ?', (sid,)).fetchone()
        avg_g = grade_stats[0] or 0
        
        # Predictions
        score, prob, risk, conf = predict_student_performance(
            student['study_hours'], student['absences'], 5, student['previous_score'],
            midterm=avg_g, final=avg_g, homework=avg_g # Simplified for dashboard
        )
        conn.close()
        return render_template('student_dashboard.html', 
                               active_page='dashboard', 
                               student=student, 
                               avg_grade=round(avg_g, 1), 
                               prob=round(prob, 1), 
                               risk=risk, 
                               enrolled_classes=classes,
                               chart_labels=chart_labels,
                               chart_user_data=chart_user_data,
                               chart_avg_data=chart_avg_data)
    return redirect(url_for('login'))

@app.route('/admin/students')
def admin_students():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    students = conn.execute('''SELECT s.*, u.full_name, u.email, u.phone_number, u.address, c.class_name, tu.full_name as teacher_name FROM Students s JOIN Users u ON u.id = s.user_id LEFT JOIN StudentClasses sc ON sc.student_id = s.id LEFT JOIN Classes c ON c.id = sc.class_id LEFT JOIN Teachers t ON t.id = c.teacher_id LEFT JOIN Users tu ON tu.id = t.user_id WHERE u.role = "student" ORDER BY u.full_name ASC''').fetchall()
    classes = conn.execute('SELECT * FROM Classes').fetchall()
    conn.close()
    return render_template('admin_students.html', active_page='students', students=students, classes=classes)

@app.route('/admin/teachers')
def admin_teachers():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    teachers = conn.execute('SELECT t.*, u.full_name, u.email, u.phone_number, u.address FROM Teachers t JOIN Users u ON t.user_id = u.id').fetchall()
    conn.close()
    return render_template('admin_teachers.html', active_page='teachers', teachers=teachers)

@app.route('/admin/classes')
def admin_classes():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    classes = conn.execute('''SELECT c.*, u.full_name as teacher_name, t.subject FROM Classes c LEFT JOIN Teachers t ON c.teacher_id = t.id LEFT JOIN Users u ON t.user_id = u.id''').fetchall()
    teachers = conn.execute('SELECT t.id, u.full_name, t.subject FROM Teachers t JOIN Users u ON t.user_id = u.id').fetchall()
    conn.close()
    return render_template('admin_classes.html', active_page='classes', classes=classes, teachers=teachers)

@app.route('/admin/reports')
def admin_reports():
    if session.get('role') != 'admin': return redirect(url_for('login'))
    conn = get_db_connection()
    total_students = conn.execute('SELECT COUNT(*) FROM Students').fetchone()[0]
    total_teachers = conn.execute('SELECT COUNT(*) FROM Teachers').fetchone()[0]
    total_classes = conn.execute('SELECT COUNT(*) FROM Classes').fetchone()[0]
    avg_success = conn.execute('SELECT AVG(success_probability) FROM Predictions').fetchone()[0] or 0
    risk_data = conn.execute('SELECT risk_level, COUNT(*) as count FROM Predictions GROUP BY risk_level').fetchall()
    risks = {'Low Risk': 0, 'Medium Risk': 0, 'High Risk': 0}
    for r in risk_data:
        if r['risk_level'] in risks: risks[r['risk_level']] = r['count']
    class_perf = conn.execute('''SELECT c.id, c.class_name, tu.full_name as teacher_name, COUNT(DISTINCT sc.student_id) as student_count, AVG(g.grade) as avg_grade, AVG(p.success_probability) as avg_success FROM Classes c LEFT JOIN Teachers t ON t.id = c.teacher_id LEFT JOIN Users tu ON tu.id = t.user_id LEFT JOIN StudentClasses sc ON sc.class_id = c.id LEFT JOIN Grades g ON g.student_id = sc.student_id AND g.class_id = c.id LEFT JOIN Predictions p ON p.student_id = sc.student_id AND p.class_id = c.id GROUP BY c.id''').fetchall()
    student_perf = conn.execute('''SELECT u.full_name, c.class_name, tu.full_name as teacher_name, AVG(g.grade) as avg_grade, s.absences, p.success_probability, p.risk_level FROM Students s JOIN Users u ON s.user_id = u.id JOIN StudentClasses sc ON sc.student_id = s.id JOIN Classes c ON sc.class_id = c.id LEFT JOIN Teachers t ON c.teacher_id = t.id LEFT JOIN Users tu ON tu.id = t.user_id LEFT JOIN Grades g ON g.student_id = s.id AND g.class_id = c.id LEFT JOIN Predictions p ON p.student_id = s.id AND p.class_id = c.id GROUP BY s.id, c.id''').fetchall()
    all_classes = conn.execute('SELECT id, class_name FROM Classes').fetchall()
    all_students = conn.execute('SELECT s.id, u.full_name FROM Students s JOIN Users u ON s.user_id = u.id').fetchall()
    conn.close()
    return render_template('admin_reports.html', active_page='reports', stats={'students': total_students, 'teachers': total_teachers, 'classes': total_classes, 'success': avg_success}, risks=risks, class_perf=class_perf, student_perf=student_perf, classes=all_classes, students=all_students)

@app.route('/admin/reports/generate', methods=['POST'])
def admin_generate_report():
    role = session.get('role')
    if role not in ['admin', 'teacher']: return jsonify({'error': 'Unauthorized'}), 403
    # Teachers can only generate student or class reports
    if role == 'teacher' and request.json.get('type') == 'full': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    try:
        filename = generate_pdf_report(data.get('type'), data.get('id'))
        return jsonify({'success': True, 'filename': filename})
    except Exception as e: return jsonify({'error': str(e)}), 500

@app.route('/admin/reports/download/<filename>')
def admin_download_report(filename):
    if session.get('role') not in ['admin', 'teacher']: return redirect(url_for('login'))
    return send_from_directory(os.path.join(os.path.dirname(__file__), 'static', 'reports'), filename)

@app.route('/admin/users/add', methods=['POST'])
def admin_add_user():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        existing = conn.execute('SELECT id, role FROM Users WHERE email = ?', (data['email'],)).fetchone()
        if existing:
            if existing['role'] != 'student': return jsonify({'error': 'Email exists for non-student role.'}), 400
            sid = conn.execute('SELECT id FROM Students WHERE user_id = ?', (existing['id'],)).fetchone()[0]
            if conn.execute('SELECT id FROM StudentClasses WHERE student_id = ? AND class_id = ?', (sid, data.get('class_id'))).fetchone(): return jsonify({'error': 'Already enrolled.'}), 400
            conn.execute('INSERT INTO StudentClasses (student_id, class_id) VALUES (?, ?)', (sid, data.get('class_id')))
            conn.commit()
            return jsonify({'success': True, 'msg': 'Enrolled existing student.'})
        cursor.execute('INSERT INTO Users (full_name, email, password, role, phone_number, address) VALUES (?, ?, ?, ?, ?, ?)', (data['full_name'], data['email'], data['password'], data['role'], data.get('phone_number'), data.get('address')))
        uid = cursor.lastrowid
        if data['role'] == 'teacher': cursor.execute('INSERT INTO Teachers (user_id, subject, teacher_number, department) VALUES (?, ?, ?, ?)', (uid, data.get('subject', ''), data.get('teacher_number'), data.get('department')))
        elif data['role'] == 'student':
            cursor.execute('INSERT INTO Students (user_id, student_number, parent_phone) VALUES (?, ?, ?)', (uid, data.get('student_number'), data.get('parent_phone')))
            sid = cursor.lastrowid
            if data.get('class_id'): cursor.execute('INSERT INTO StudentClasses (student_id, class_id) VALUES (?, ?)', (sid, data['class_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500
    finally: conn.close()

@app.route('/admin/enrollment/remove', methods=['POST'])
def admin_remove_enrollment():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    conn.execute('DELETE FROM StudentClasses WHERE id = ?', (request.json.get('enrollment_id'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/student/delete', methods=['POST'])
def admin_delete_student():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    uid = conn.execute('SELECT user_id FROM Students WHERE id = ?', (request.json.get('student_id'),)).fetchone()[0]
    conn.execute('DELETE FROM Users WHERE id = ?', (uid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/classes/add', methods=['POST'])
def admin_add_class():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO Classes (class_name, teacher_id) VALUES (?, ?)', (data['class_name'], data['teacher_id']))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500
    finally: conn.close()

@app.route('/admin/class/delete', methods=['POST'])
def admin_delete_class():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    conn.execute('DELETE FROM Classes WHERE id = ?', (request.json.get('class_id'),))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- PROFILE & SETTINGS ---
@app.route('/settings')
def settings():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    uid = session['user_id']
    role = session['role']
    if role == 'student': user = conn.execute('SELECT u.*, s.student_number, s.parent_phone FROM Users u JOIN Students s ON s.user_id = u.id WHERE u.id = ?', (uid,)).fetchone()
    elif role == 'teacher': user = conn.execute('SELECT u.*, t.teacher_number, t.department FROM Users u JOIN Teachers t ON t.user_id = u.id WHERE u.id = ?', (uid,)).fetchone()
    else: user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
    conn.close()
    return render_template('settings.html', active_page='settings', user=user)

@app.route('/api/profile/update', methods=['POST'])
def api_update_profile():
    if 'user_id' not in session: return jsonify({'error': 'Unauthorized'}), 403
    uid = session['user_id']
    role = session['role']
    profile_image_path = None
    if 'profile_image' in request.files:
        file = request.files['profile_image']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"user_{uid}_{role}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            profile_image_path = f"/static/uploads/profiles/{filename}"
    conn = get_db_connection()
    try:
        current_user = conn.execute('SELECT * FROM Users WHERE id = ?', (uid,)).fetchone()
        conn.execute('''
            UPDATE Users 
            SET full_name = ?, email = ?, phone_number = ?, address = ?, profile_image = COALESCE(?, profile_image)
            WHERE id = ?
        ''', (request.form.get('full_name', current_user['full_name']), 
              request.form.get('email', current_user['email']),
              request.form.get('phone_number', current_user['phone_number']), 
              request.form.get('address', current_user['address']), 
              profile_image_path, 
              session['user_id']))
        
        session['email'] = request.form.get('email', current_user['email'])
        if role == 'student': conn.execute('UPDATE Students SET parent_phone=? WHERE user_id=?', (request.form.get('parent_phone'), uid))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500
    finally: conn.close()

# --- TEACHER ROUTES ---
@app.route('/teacher/grades')
def teacher_grades():
    if session.get('role') != 'teacher': return redirect(url_for('login'))
    conn = get_db_connection()
    enrollments = conn.execute('''SELECT s.id as student_id, u.full_name, c.id as class_id, c.class_name, t.subject FROM StudentClasses sc JOIN Students s ON sc.student_id = s.id JOIN Users u ON s.user_id = u.id JOIN Classes c ON sc.class_id = c.id JOIN Teachers t ON c.teacher_id = t.id WHERE t.user_id = ?''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('grades_management.html', active_page='grades', enrollments=enrollments)

@app.route('/teacher/prediction')
def teacher_prediction():
    if session.get('role') != 'teacher': return redirect(url_for('login'))
    conn = get_db_connection()
    enrollments = conn.execute('''SELECT s.id as student_id, u.full_name, c.id as class_id, c.class_name, t.subject FROM StudentClasses sc JOIN Students s ON sc.student_id = s.id JOIN Users u ON s.user_id = u.id JOIN Classes c ON sc.class_id = c.id JOIN Teachers t ON c.teacher_id = t.id WHERE t.user_id = ?''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('teacher_prediction.html', active_page='prediction', enrollments=enrollments)

@app.route('/api/teacher/predict', methods=['POST'])
def api_teacher_predict():
    if session.get('role') != 'teacher': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    sid = data.get('student_id')
    cid = data.get('class_id')
    conn = get_db_connection()
    try:
        class_check = conn.execute('SELECT c.class_name, t.subject FROM Classes c JOIN Teachers t ON c.teacher_id = t.id WHERE c.id = ? AND t.user_id = ?', (cid, session['user_id'])).fetchone()
        if not class_check: return jsonify({'error': 'Access denied to this class.'}), 403
        student = conn.execute('SELECT u.full_name, s.previous_score, s.study_hours, s.absences, s.family_support FROM Students s JOIN Users u ON s.user_id = u.id WHERE s.id = ?', (sid,)).fetchone()
        grades = conn.execute('SELECT * FROM Grades WHERE student_id = ? AND class_id = ?', (sid, cid)).fetchone()
        if not grades: return jsonify({'error': 'No grade data available for prediction.'}), 400
        score, prob, risk, conf = predict_student_performance(
            grades['study_hours'], grades['absences'], grades['family_support'], 
            student['previous_score'],
            midterm=grades['midterm'], final=grades['final'], homework=grades['homework']
        )
        from recommender import generate_recommendations
        recs = generate_recommendations(grades['study_hours'], grades['absences'], grades['grade'], student['previous_score'])
        rec_text = recs[0]['description'] if recs else "Maintain current study habits."
        existing = conn.execute('SELECT id FROM Predictions WHERE student_id = ? AND class_id = ?', (sid, cid)).fetchone()
        if existing: conn.execute('UPDATE Predictions SET predicted_score=?, success_probability=?, risk_level=?, recommendation=?, updated_at=CURRENT_TIMESTAMP WHERE id=?', (score, prob, risk, rec_text, existing['id']))
        else: conn.execute('INSERT INTO Predictions (student_id, class_id, predicted_score, success_probability, risk_level, recommendation) VALUES (?, ?, ?, ?, ?, ?)', (sid, cid, score, prob, risk, rec_text))
        conn.commit()
        result = {'full_name': student['full_name'], 'class_name': f"{class_check['class_name']} - {class_check['subject']}", 'score': round(score, 1), 'probability': round(prob, 1), 'risk': risk, 'confidence': round(conf, 1), 'recommendation': rec_text}
        factors = {'study_hours': min(100, (grades['study_hours'] / 20) * 100), 'absences': max(0, 100 - (grades['absences'] / 10) * 100), 'family_support': (grades['family_support'] / 10) * 100, 'midterm': grades['midterm'], 'final': grades['final'], 'homework': grades['homework'], 'previous_score': student['previous_score']}
        return jsonify({'success': True, 'prediction': result, 'factors': factors})
    except Exception as e: return jsonify({'error': str(e)}), 500
    finally: conn.close()

@app.route('/teacher/classes')
def teacher_classes():
    if session.get('role') != 'teacher': return redirect(url_for('login'))
    conn = get_db_connection()
    teacher = conn.execute('SELECT t.id, c.class_name, t.subject FROM Teachers t LEFT JOIN Classes c ON c.teacher_id = t.id WHERE t.user_id = ?', (session['user_id'],)).fetchone()
    classes = []
    if teacher:
        # Fetch all classes for this teacher with real-time metrics
        rows = conn.execute('''
            SELECT 
                c.id, c.class_name, t.subject,
                COUNT(DISTINCT sc.student_id) as student_count,
                AVG(COALESCE((g.midterm * 0.3 + g.final * 0.5 + g.homework * 0.2), 0)) as avg_grade,
                SUM(CASE WHEN p.risk_level = 'High Risk' THEN 1 ELSE 0 END) as at_risk_count,
                AVG(COALESCE(p.success_probability, 0)) as success_rate
            FROM Classes c
            JOIN Teachers t ON c.teacher_id = t.id
            LEFT JOIN StudentClasses sc ON sc.class_id = c.id
            LEFT JOIN Grades g ON g.student_id = sc.student_id AND g.class_id = c.id
            LEFT JOIN Predictions p ON p.student_id = sc.student_id AND p.class_id = c.id
            WHERE t.user_id = ?
            GROUP BY c.id
        ''', (session['user_id'],)).fetchall()
        
        for r in rows:
            classes.append({
                'name': r['class_name'],
                'subject': r['subject'],
                'student_count': r['student_count'] or 0,
                'avg_grade': round(r['avg_grade'] or 0, 1),
                'at_risk': r['at_risk_count'] or 0,
                'success': round(r['success_rate'] or 0, 1)
            })
    conn.close()
    return render_template('my_classes.html', active_page='classes', classes=classes)

@app.route('/teacher/reports')
def teacher_reports():
    if session.get('role') != 'teacher': return redirect(url_for('login'))
    conn = get_db_connection()
    students = conn.execute('''
        SELECT DISTINCT s.id, u.full_name, c.class_name 
        FROM Students s 
        JOIN Users u ON s.user_id = u.id 
        JOIN StudentClasses sc ON sc.student_id = s.id 
        JOIN Classes c ON sc.class_id = c.id 
        JOIN Teachers t ON c.teacher_id = t.id 
        WHERE t.user_id = ?
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('teacher_reports.html', active_page='reports', students=students)

@app.route('/api/student-report-data/<int:sid>')
def api_get_student_report_data(sid):
    if session.get('role') not in ['admin', 'teacher']: return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    student = conn.execute('''
        SELECT u.full_name, s.student_number, s.study_hours, s.absences, s.family_support, s.previous_score
        FROM Students s JOIN Users u ON s.user_id = u.id WHERE s.id = ?
    ''', (sid,)).fetchone()
    
    if not student: return jsonify({'error': 'Student not found'}), 404
    
    grades = conn.execute('''
        SELECT g.*, c.class_name 
        FROM Grades g JOIN Classes c ON g.class_id = c.id WHERE g.student_id = ?
    ''', (sid,)).fetchall()
    
    # Get latest prediction
    pred = conn.execute('SELECT success_probability, risk_level FROM Predictions WHERE student_id = ? ORDER BY updated_at DESC LIMIT 1', (sid,)).fetchone()
    
    conn.close()
    return jsonify({
        'student': dict(student),
        'grades': [dict(g) for g in grades],
        'prediction': dict(pred) if pred else None
    })

@app.route('/api/grades/<int:sid>/<int:cid>')
def api_get_student_grades(sid, cid):
    if session.get('role') != 'teacher': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    teacher = conn.execute('SELECT t.id, t.subject FROM Teachers t JOIN Classes c ON c.teacher_id = t.id WHERE t.user_id = ? AND c.id = ?', (session['user_id'], cid)).fetchone()
    if not teacher: return jsonify({'error': 'Permission denied.'}), 403
    row = conn.execute('SELECT * FROM Grades WHERE student_id = ? AND class_id = ?', (sid, cid)).fetchone()
    grades = []
    if row: grades.append(dict(row))
    else: grades.append({'subject_name': teacher['subject'], 'grade': 0, 'midterm': 0, 'final': 0, 'homework': 0, 'study_hours': 0, 'absences': 0, 'family_support': 5})
    conn.close()
    return jsonify({'grades': grades})

@app.route('/api/grades/save', methods=['POST'])
def api_save_grades():
    if session.get('role') != 'teacher': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    sid = data['student_id']
    cid = data['class_id']
    conn = get_db_connection()
    try:
        class_check = conn.execute('SELECT id FROM Classes WHERE id = ? AND teacher_id = (SELECT id FROM Teachers WHERE user_id = ?)', (cid, session['user_id'])).fetchone()
        if not class_check: return jsonify({'error': 'Unauthorized class edit.'}), 403
        for g in data['grades']:
            existing = conn.execute('SELECT id FROM Grades WHERE student_id = ? AND class_id = ?', (sid, cid)).fetchone()
            if existing: conn.execute('''UPDATE Grades SET grade=?, midterm=?, final=?, homework=?, study_hours=?, absences=?, family_support=?, updated_at=CURRENT_TIMESTAMP WHERE id=?''', (g['grade'], g['midterm'], g['final'], g['homework'], g['study_hours'], g['absences'], g['family_support'], existing['id']))
            else: conn.execute('''INSERT INTO Grades (student_id, class_id, subject_name, grade, midterm, final, homework, study_hours, absences, family_support) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (sid, cid, g['subject_name'], g['grade'], g['midterm'], g['final'], g['homework'], g['study_hours'], g['absences'], g['family_support']))
        conn.commit()
        conn.close()
        sync_student_data(sid)
        return jsonify({'success': True})
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/teacher/lessons')
def teacher_lessons():
    if session.get('role') != 'teacher': return redirect(url_for('login'))
    conn = get_db_connection()
    teacher = conn.execute('SELECT id FROM Teachers WHERE user_id = ?', (session['user_id'],)).fetchone()
    classes = []
    lessons = []
    if teacher:
        classes = conn.execute('SELECT id, class_name FROM Classes WHERE teacher_id = ?', (teacher['id'],)).fetchall()
        lessons = conn.execute('''
            SELECT l.*, c.class_name, (SELECT COUNT(*) FROM Quizzes WHERE lesson_id = l.id) as quiz_count
            FROM Lessons l JOIN Classes c ON l.class_id = c.id
            WHERE l.teacher_id = ? ORDER BY l.created_at DESC
        ''', (teacher['id'],)).fetchall()
    conn.close()
    return render_template('teacher_lessons.html', active_page='lessons', classes=classes, lessons=lessons)

@app.route('/api/teacher/lessons/add', methods=['POST'])
def api_add_lesson():
    if session.get('role') != 'teacher': return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_connection()
    try:
        teacher = conn.execute('SELECT id FROM Teachers WHERE user_id = ?', (session['user_id'],)).fetchone()
        cursor = conn.cursor()
        
        # Handle File Upload
        attachment_path = None
        attachment_name = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                filename = secure_filename(f"lesson_{teacher['id']}_{os.urandom(4).hex()}_{file.filename}")
                file_path = os.path.join(app.config['LESSONS_FOLDER'], filename)
                file.save(file_path)
                attachment_path = f"/static/uploads/lessons/{filename}"
                attachment_name = file.filename

        cursor.execute('''
            INSERT INTO Lessons (class_id, teacher_id, title, subject, content, notes, attachment_path, attachment_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request.form['class_id'], teacher['id'], request.form['title'], request.form['subject'], request.form['content'], request.form['notes'], attachment_path, attachment_name))
        lesson_id = cursor.lastrowid
        
        if request.form.get('quiz_title'):
            cursor.execute('INSERT INTO Quizzes (lesson_id, title, quiz_url) VALUES (?, ?, ?)', (lesson_id, request.form['quiz_title'], request.form.get('quiz_url')))
            
        conn.commit()
        return jsonify({'success': True})
    except Exception as e: return jsonify({'error': str(e)}), 500
    finally: conn.close()

@app.route('/api/teacher/lessons/delete', methods=['POST'])
def api_delete_lesson():
    if session.get('role') != 'teacher': return jsonify({'error': 'Unauthorized'}), 403
    data = request.json
    conn = get_db_connection()
    teacher = conn.execute('SELECT id FROM Teachers WHERE user_id = ?', (session['user_id'],)).fetchone()
    conn.execute('DELETE FROM Lessons WHERE id = ? AND teacher_id = ?', (data['lesson_id'], teacher['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/student/lessons')
def student_lessons():
    if session.get('role') != 'student': return redirect(url_for('login'))
    conn = get_db_connection()
    student = conn.execute('SELECT id FROM Students WHERE user_id = ?', (session['user_id'],)).fetchone()
    lessons = []
    if student:
        lessons = conn.execute('''
            SELECT l.*, u.full_name as teacher_name, q.title as quiz_title, q.quiz_url
            FROM Lessons l
            JOIN StudentClasses sc ON l.class_id = sc.class_id
            JOIN Teachers t ON l.teacher_id = t.id
            JOIN Users u ON t.user_id = u.id
            LEFT JOIN Quizzes q ON q.lesson_id = l.id
            WHERE sc.student_id = ?
            ORDER BY l.created_at DESC
        ''', (student['id'],)).fetchall()
    conn.close()
    return render_template('student_lessons.html', active_page='lessons', lessons=lessons)

@app.route('/teacher/students')
def teacher_students():
    if session.get('role') != 'teacher': return redirect(url_for('login'))
    conn = get_db_connection()
    try:
        teacher = conn.execute('SELECT c.id as class_id, c.class_name FROM Teachers t JOIN Classes c ON c.teacher_id = t.id WHERE t.user_id = ?', (session['user_id'],)).fetchone()
        students = []
        if teacher:
            rows = conn.execute('''
                SELECT s.*, u.full_name, p.success_probability as prob, p.risk_level as risk,
                       COALESCE((g.midterm * 0.3 + g.final * 0.5 + g.homework * 0.2), s.previous_score) as current_grade
                FROM Students s 
                JOIN Users u ON s.user_id = u.id 
                JOIN StudentClasses sc ON sc.student_id = s.id 
                LEFT JOIN Grades g ON g.student_id = s.id AND g.class_id = sc.class_id
                LEFT JOIN Predictions p ON p.student_id = s.id AND p.class_id = sc.class_id
                WHERE sc.class_id = ?
            ''', (teacher['class_id'],)).fetchall()
            for r in rows:
                students.append({**dict(r), 'prob': round(r['prob'] or 0, 1), 'risk': r['risk'] or 'N/A', 'class_name': teacher['class_name'], 'current_grade': round(r['current_grade'], 1)})
        conn.close()
        return render_template('teacher_students.html', active_page='students', students=students)
    except Exception as e:
        conn.close()
        return render_template('teacher_students.html', active_page='students', students=[])

@app.route('/student/grades')
def student_grades():
    if session.get('role') != 'student': return redirect(url_for('login'))
    conn = get_db_connection()
    student = conn.execute('SELECT id FROM Students WHERE user_id = ?', (session['user_id'],)).fetchone()
    if not student: return "Record not found."
    grades = conn.execute('''
        SELECT c.class_name, t.subject as subject_name, tu.full_name as teacher_name, 
               COALESCE(g.study_hours, 0) as study_hours, COALESCE(g.absences, 0) as absences, 
               COALESCE(g.midterm, 0) as midterm, COALESCE(g.final, 0) as final, 
               COALESCE(g.homework, 0) as homework, COALESCE(g.grade, 0) as grade, 
               p.success_probability as ai_success 
        FROM StudentClasses sc 
        JOIN Classes c ON sc.class_id = c.id 
        LEFT JOIN Teachers t ON c.teacher_id = t.id 
        LEFT JOIN Users tu ON tu.id = t.user_id 
        LEFT JOIN Grades g ON g.student_id = sc.student_id AND g.class_id = sc.class_id 
        LEFT JOIN Predictions p ON p.student_id = sc.student_id AND p.class_id = sc.class_id 
        WHERE sc.student_id = ?
    ''', (student['id'],)).fetchall()
    conn.close()
    return render_template('my_grades.html', active_page='grades', grades=grades)

@app.route('/student/prediction')
def student_prediction():
    if session.get('role') != 'student': return redirect(url_for('login'))
    conn = get_db_connection()
    student = conn.execute('SELECT id, absences, study_hours, previous_score FROM Students WHERE user_id = ?', (session['user_id'],)).fetchone()
    
    # Get aggregate grades for the student
    grades_agg = conn.execute('''
        SELECT AVG(midterm), AVG(final), AVG(homework)
        FROM Grades WHERE student_id = ?
    ''', (student['id'],)).fetchone()
    
    m_avg = grades_agg[0] or 0
    f_avg = grades_agg[1] or 0
    h_avg = grades_agg[2] or 0
    
    score, prob, risk, conf = predict_student_performance(
        student['study_hours'], student['absences'], 5, student['previous_score'],
        midterm=m_avg, final=f_avg, homework=h_avg
    )
    
    # Get all predictions across all classes for historical/detailed view
    preds = conn.execute('''
        SELECT p.*, c.class_name 
        FROM Predictions p JOIN Classes c ON p.class_id = c.id WHERE p.student_id = ?
    ''', (student['id'],)).fetchall()
    conn.close()
    return render_template('student_prediction.html', active_page='prediction', predictions=preds, student=student, prob=round(prob, 1), conf=round(conf, 1), risk=risk, score=round(score, 1))

@app.route('/student/recommendations')
def student_recommendations():
    if session.get('role') != 'student': return redirect(url_for('login'))
    conn = get_db_connection()
    student = conn.execute('SELECT id FROM Students WHERE user_id = ?', (session['user_id'],)).fetchone()
    preds = conn.execute('SELECT recommendation FROM Predictions WHERE student_id = ? ORDER BY updated_at DESC', (student['id'],)).fetchall()
    recs = [{'title': 'Academic Optimization', 'description': p['recommendation'], 'type': 'insight'} for p in preds if p['recommendation']]
    conn.close()
    return render_template('recommendations.html', active_page='recommendations', recs=recs)

if __name__ == '__main__':
    app.run(debug=True, port=8888, host='0.0.0.0')
