import sqlite3
import os
import traceback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QScrollArea, QGridLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QFrame, QPushButton, QStackedWidget, QLineEdit, 
                             QComboBox, QMessageBox, QDialog, QFormLayout, QDialogButtonBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QFont, QAction
from ui.components.widgets import AnalyticsCard, Sidebar, ModernNavbar
from database import DB_PATH
from ai_model import predict_student_performance
from pdf_exporter import export_student_report

class StudentRiskItem(QFrame):
    def __init__(self, name, grade, risk_pct):
        super().__init__()
        self.setFixedHeight(60); self.setStyleSheet("background: transparent; border: none;")
        lay = QHBoxLayout(self); lay.setContentsMargins(0, 5, 0, 5)
        av = QFrame(); av.setFixedSize(35, 35); av.setStyleSheet("background: #1E293B; border-radius: 17px; border: 1px solid #F87171;")
        lay.addWidget(av); info = QVBoxLayout(); info.setSpacing(0)
        n_lbl = QLabel(name); n_lbl.setStyleSheet("color: white; font-weight: 700; font-size: 12px; background: transparent;")
        g_lbl = QLabel(grade); g_lbl.setStyleSheet("color: #64748B; font-size: 10px; background: transparent;")
        info.addWidget(n_lbl); info.addWidget(g_lbl); lay.addLayout(info); lay.addStretch()
        badge = QLabel(f"{risk_pct}%"); badge.setObjectName("BadgeRiskHigh"); badge.setFixedSize(45, 22); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); lay.addWidget(badge)

class TeacherFormDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent); self.setWindowTitle("Teacher Information"); self.setFixedWidth(400); self.setStyleSheet("background: #0F172A; color: white;")
        l = QFormLayout(self); l.setSpacing(15)
        self.ni = QLineEdit(data[1] if data else ""); self.ui = QLineEdit(data[2] if data else ""); self.ei = QLineEdit(data[3] if data else ""); self.si = QLineEdit(data[5] if data else ""); self.ci = QComboBox(); self.ci.addItems(["10th Grade - Class A", "10th Grade - Class B", "11th Grade - Class A", "11th Grade - Class B"])
        if data: self.ci.setCurrentText(data[4])
        l.addRow("Full Name:", self.ni); l.addRow("Username:", self.ui); l.addRow("Email:", self.ei); l.addRow("Subject:", self.si); l.addRow("Assigned Class:", self.ci)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addRow(b)
    def get_data(self): return {'name': self.ni.text(), 'user': self.ui.text(), 'email': self.ei.text(), 'subject': self.si.text(), 'class': self.ci.currentText()}

class StudentFormDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent); self.setWindowTitle("Student Information"); self.setFixedWidth(400); self.setStyleSheet("background: #0F172A; color: white;")
        l = QFormLayout(self); self.ni = QLineEdit(data[1] if data else ""); self.ci = QComboBox(); self.ci.addItems(["10th Grade - Class A", "10th Grade - Class B", "11th Grade - Class A", "11th Grade - Class B"])
        if data: self.ci.setCurrentText(data[2])
        self.sh = QLineEdit(str(data[5]) if data else "15"); self.ab = QLineEdit(str(data[4]) if data else "2"); self.ps = QLineEdit(str(data[7]) if data else "75")
        l.addRow("Full Name:", self.ni); l.addRow("Class:", self.ci); l.addRow("Study Hours/Week:", self.sh); l.addRow("Absences:", self.ab); l.addRow("Previous Score:", self.ps)
        b = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel); b.accepted.connect(self.accept); b.rejected.connect(self.reject); l.addRow(b)
    def get_data(self):
        try: return {'name': self.ni.text(), 'class': self.ci.currentText(), 'study': int(self.sh.text() or 0), 'abs': int(self.ab.text() or 0), 'prev': int(self.ps.text() or 0)}
        except: return None

class AdminDashboard(QWidget):
    logout_requested = pyqtSignal()
    
    def __init__(self, user):
        super().__init__(); self.user = user; self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0); main_layout.setSpacing(0)
        self.sidebar = Sidebar(self.user['full_name'], "Super Administrator"); self.sidebar.profile_card.clicked.connect(self.show_profile_menu)
        self.btns = {
            "Dashboard": self.sidebar.add_nav_item("Dashboard", "🏠"),
            "Students": self.sidebar.add_nav_item("Students", "👥"),
            "Teachers": self.sidebar.add_nav_item("Teachers", "👨‍🏫"),
            "Classes": self.sidebar.add_nav_item("Classes", "🏫"),
            "Reports": self.sidebar.add_nav_item("Reports", "📑"),
            "Settings": self.sidebar.add_nav_item("Settings", "⚙️")
        }
        main_layout.addWidget(self.sidebar)
        workspace = QWidget(); work_lay = QVBoxLayout(workspace); work_lay.setContentsMargins(0, 0, 0, 0); work_lay.setSpacing(0)
        self.navbar = ModernNavbar("Admin Dashboard", "Institutional Intelligence Dashboard")
        self.navbar.search_changed.connect(self.handle_global_search)
        self.navbar.bell_clicked.connect(self.show_notifications)
        self.navbar.profile_clicked.connect(self.show_profile_menu)
        work_lay.addWidget(self.navbar)
        
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_overview_page()) # 0
        self.stack.addWidget(self.create_students_page()) # 1
        self.stack.addWidget(self.create_teachers_page()) # 2
        self.stack.addWidget(self.create_placeholder("Classes Management")) # 3
        self.stack.addWidget(self.create_reports_page()) # 4
        self.stack.addWidget(self.create_settings_page()) # 5
        
        work_lay.addWidget(self.stack); main_layout.addWidget(workspace)
        for i, (name, btn) in enumerate(self.btns.items()):
            btn.clicked.connect(lambda checked, idx=i, n=name: self.switch_page(idx, n))
        self.btns["Dashboard"].set_active(True)

    def switch_page(self, idx, name):
        if idx < self.stack.count():
            self.stack.setCurrentIndex(idx); self.navbar.title_lbl.setText(f"Admin | {name}")
            for n, b in self.btns.items(): b.set_active(n == name)

    def handle_global_search(self, text): print(f"Global search: {text}")
    def show_notifications(self, pos):
        m = QMenu(self); m.setStyleSheet("background: #1E293B; color: white; padding: 10px;"); m.addAction("🔔 Institutional updates ready"); m.exec(pos)
    def show_profile_menu(self, pos):
        m = QMenu(self); m.setStyleSheet("background: #1E293B; color: white;")
        m.addAction(QAction("👤 View Profile", self, triggered=lambda: QMessageBox.information(self, "Profile", f"Admin: {self.user['full_name']}")))
        m.addAction(QAction("⚙️ Account Settings", self, triggered=lambda: self.switch_page(5, "Settings")))
        m.addSeparator(); m.addAction(QAction("🚪 Logout", self, triggered=lambda: self.logout_requested.emit())); m.exec(pos)

    def create_overview_page(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none; background: transparent;")
        content = QWidget(); layout = QVBoxLayout(content); layout.setContentsMargins(30, 20, 30, 30); layout.setSpacing(25)
        row1 = QHBoxLayout(); row1.setSpacing(20); row1.addWidget(AnalyticsCard("Total Students", "1,248", "+12%", "#38BDF8", "👥")); row1.addWidget(AnalyticsCard("Active Classes", "36", "+4", "#34D399", "🏫")); row1.addWidget(AnalyticsCard("Total Teachers", "78", "+7", "#818CF8", "👨‍🏫")); row1.addWidget(AnalyticsCard("Success", "78.4%", "+6.5%", "#FBBF24", "📊")); layout.addLayout(row1)
        mid = QHBoxLayout(); mid.setSpacing(20); c1 = QFrame(objectName="Card"); cv1 = QVBoxLayout(c1); cv1.addWidget(QLabel("Success Rate by Grade", styleSheet="color:white;font-weight:bold;")); fig, ax = plt.subplots(figsize=(6,4), dpi=100); fig.patch.set_facecolor('#0F172A'); ax.set_facecolor('#0F172A'); ax.bar(['7th','8th','9th','10th','11th','12th'],[72,75,81,77,74,82], color='#38BDF8'); ax.tick_params(colors='#64748B', labelsize=8); cv1.addWidget(FigureCanvas(fig)); mid.addWidget(c1, 2)
        c2 = QFrame(objectName="Card"); cv2 = QVBoxLayout(c2); cv2.addWidget(QLabel("At Risk Students", styleSheet="color:white;font-weight:bold;")); [cv2.addWidget(StudentRiskItem(n,g,p)) for n,g,p in [("Ahmed Mohamed","10-A",92), ("Sara Ali","9-B",85)]]; cv2.addStretch(); mid.addWidget(c2, 1); layout.addLayout(mid)
        scroll.setWidget(content); return scroll

    def create_students_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)
        header = QHBoxLayout(); header.addWidget(QLabel("STUDENT MANAGEMENT SYSTEM", styleSheet="font-size: 18px; font-weight: 800; color: white;")); header.addStretch()
        self.student_search = QLineEdit(); self.student_search.setPlaceholderText("Search students..."); self.student_search.setFixedWidth(250); self.student_search.textChanged.connect(self.refresh_students_table); header.addWidget(self.student_search)
        add_btn = QPushButton("+ ADD NEW STUDENT"); add_btn.setObjectName("PrimaryButton"); add_btn.clicked.connect(self.open_add_student_dialog); header.addWidget(add_btn); layout.addLayout(header)
        table_card = QFrame(objectName="Card"); tv = QVBoxLayout(table_card); self.student_table = QTableWidget(); self.student_table.setColumnCount(8); self.student_table.setHorizontalHeaderLabels(["ID", "NAME", "CLASS", "GPA", "ABSENCES", "RISK", "SUCCESS", "ACTIONS"]); self.student_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.student_table.verticalHeader().setVisible(False); tv.addWidget(self.student_table); layout.addWidget(table_card); self.refresh_students_table(); return page

    def refresh_students_table(self):
        query = "SELECT s.id, u.full_name, s.class_name, COALESCE(AVG(g.grade),0), s.absences, s.study_hours, s.family_support, s.previous_score FROM Students s JOIN Users u ON s.user_id = u.id LEFT JOIN Grades g ON s.id = g.student_id"
        params = []
        if self.student_search.text():
            query += " WHERE u.full_name LIKE ? OR s.class_name LIKE ? OR s.id LIKE ?"
            params = [f"%{self.student_search.text()}%"] * 3
        query += " GROUP BY s.id ORDER BY s.id DESC"
        try:
            conn = sqlite3.connect(DB_PATH); cur = conn.cursor(); cur.execute(query, params); rows = cur.fetchall(); self.student_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                sid, n, cl, g, ab, st, fm, pr = r; sc, pb, rk, cf = predict_student_performance(st, ab, fm, pr)
                [self.student_table.setItem(i, j, QTableWidgetItem(str(v))) for j, v in enumerate([sid, n, cl, f"{g:.1f}%", ab])]
                badge = QLabel(rk); badge.setObjectName(f"BadgeRisk{rk.split()[0]}"); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); self.student_table.setCellWidget(i, 5, badge)
                self.student_table.setItem(i, 6, QTableWidgetItem(f"{pb:.0f}%"))
            conn.close()
        except: pass

    def open_add_student_dialog(self):
        dlg = StudentFormDialog(self)
        if dlg.exec():
            d = dlg.get_data(); conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            try:
                c.execute("INSERT INTO Users (full_name, username, password, role) VALUES (?, ?, 'stud123', 'student')", (d['name'], d['name'].lower().replace(" ","_")))
                uid = c.lastrowid; c.execute("INSERT INTO Students (user_id, class_name, study_hours, absences, family_support, previous_score) VALUES (?, ?, ?, ?, 5, ?)", (uid, d['class'], d['study'], d['abs'], d['prev']))
                conn.commit(); self.refresh_students_table(); QMessageBox.information(self, "Success", "Student Added")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
            finally: conn.close()

    def create_teachers_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(20)
        header = QHBoxLayout(); header.addWidget(QLabel("TEACHER DIRECTORY", styleSheet="font-size: 18px; font-weight: 800; color: white;")); header.addStretch(); add_btn = QPushButton("+ ADD NEW TEACHER"); add_btn.setObjectName("PrimaryButton"); add_btn.clicked.connect(self.open_add_teacher_dialog); header.addWidget(add_btn); layout.addLayout(header)
        table_card = QFrame(objectName="Card"); tv = QVBoxLayout(table_card); self.teacher_table = QTableWidget(); self.teacher_table.setColumnCount(9); self.teacher_table.setHorizontalHeaderLabels(["ID", "NAME", "USER", "EMAIL", "CLASS", "SUBJECT", "STUDENTS", "STATUS", "ACTIONS"]); self.teacher_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.teacher_table.verticalHeader().setVisible(False); tv.addWidget(self.teacher_table); layout.addWidget(table_card); self.refresh_teachers_table(); return page

    def refresh_teachers_table(self):
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor(); cursor.execute("SELECT u.id, u.full_name, u.username, t.email, t.assigned_class, t.subject, 0, t.status FROM Users u LEFT JOIN Teachers t ON u.id = t.user_id WHERE u.role = 'teacher'")
            rows = cursor.fetchall(); self.teacher_table.setRowCount(len(rows))
            for i, r in enumerate(rows): [self.teacher_table.setItem(i, j, QTableWidgetItem(str(v))) for j, v in enumerate(r)]
            conn.close()
        except: pass

    def open_add_teacher_dialog(self):
        dlg = TeacherFormDialog(self)
        if dlg.exec():
            d = dlg.get_data(); conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            try:
                c.execute("INSERT INTO Users (full_name, username, password, role) VALUES (?, ?, 'pass123', 'teacher')", (d['name'], d['user']))
                uid = c.lastrowid; c.execute("INSERT INTO Teachers (user_id, email, subject, assigned_class) VALUES (?, ?, ?, ?)", (uid, d['email'], d['subject'], d['class']))
                conn.commit(); self.refresh_teachers_table(); QMessageBox.information(self, "Success", "Teacher Added")
            except Exception as e: QMessageBox.critical(self, "Error", str(e))
            finally: conn.close()

    def create_reports_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(25)
        top = QHBoxLayout(); top.addWidget(QLabel("REPORTS CENTER", styleSheet="font-size: 18px; font-weight: 800; color: white;")); top.addStretch(); exp_btn = QPushButton("📥 EXPORT ALL PDF"); exp_btn.setObjectName("PrimaryButton"); exp_btn.clicked.connect(self.export_all_pdf); top.addWidget(exp_btn); layout.addLayout(top)
        row1 = QHBoxLayout(); row1.setSpacing(20); row1.addWidget(AnalyticsCard("Reports Ready", "412", "+8%", "#38BDF8", "📑")); row1.addWidget(AnalyticsCard("Risk Alerts", "24", "-3", "#F87171", "⚠️")); layout.addLayout(row1)
        table_card = QFrame(objectName="Card"); tv = QVBoxLayout(table_card); tv.addWidget(QLabel("Academic Reports List")); self.report_table = QTableWidget(); self.report_table.setColumnCount(7); self.report_table.setHorizontalHeaderLabels(["STUDENT", "GPA", "ATTENDANCE", "PREDICTED", "RISK", "RECOMMENDATION", "ACTIONS"]); self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.report_table.verticalHeader().setVisible(False); tv.addWidget(self.report_table); layout.addWidget(table_card); self.load_report_data(); return page

    def load_report_data(self):
        try:
            conn = sqlite3.connect(DB_PATH); cursor = conn.cursor(); cursor.execute("SELECT s.id, u.full_name, s.class_name, COALESCE(AVG(g.grade),0), s.absences, s.study_hours, s.family_support, s.previous_score FROM Students s JOIN Users u ON s.user_id = u.id LEFT JOIN Grades g ON s.id = g.student_id GROUP BY s.id")
            rows = cursor.fetchall(); self.report_table.setRowCount(len(rows))
            for i, r in enumerate(rows):
                sid, n, cl, g, ab, st, fm, pr = r; sc, pb, rk, cf = predict_student_performance(st, ab, fm, pr)
                self.report_table.setItem(i,0,QTableWidgetItem(n)); self.report_table.setItem(i,1,QTableWidgetItem(f"{g:.1f}%")); self.report_table.setItem(i,2,QTableWidgetItem(f"{100-ab*2}%")); self.report_table.setItem(i,3,QTableWidgetItem(f"{pb:.0f}%"))
                badge = QLabel(rk); badge.setObjectName(f"BadgeRisk{rk.split()[0]}"); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); self.report_table.setCellWidget(i, 4, badge)
                self.report_table.setItem(i, 5, QTableWidgetItem("Maintain Study Time")); self.report_table.setItem(i, 6, QTableWidgetItem("Download PDF"))
            conn.close()
        except: pass

    def export_all_pdf(self):
        try:
            path = "Institutional_Performance_Report.pdf"
            export_student_report("School Overview", "All Classes", 78.4, 82, "Overall Low Risk", [("Avg GPA", 78.4)], [{"title":"Success", "description":"Stable performance."}], path)
            QMessageBox.information(self, "Exported", f"Report saved: {path}"); os.startfile(path)
        except Exception as e: QMessageBox.critical(self, "Export Failed", str(e))

    def create_settings_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30); logout = QPushButton("🚪 LOGOUT SESSION"); logout.setObjectName("DangerButton"); logout.clicked.connect(lambda: self.logout_requested.emit()); layout.addWidget(logout); layout.addStretch(); return page
    def create_placeholder(self, t): page = QWidget(); layout = QVBoxLayout(page); l = QLabel(t); l.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(l); return page
