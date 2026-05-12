import sqlite3
import traceback
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                             QSlider, QProgressBar, QFrame, QComboBox, QStackedWidget, 
                             QScrollArea, QPushButton, QMenu, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QAction, QFont
from ui.components.widgets import AnalyticsCard, Sidebar, ModernNavbar
from database import DB_PATH
from ai_model import predict_student_performance

class TeacherDashboard(QWidget):
    logout_requested = pyqtSignal()
    
    def __init__(self, user):
        super().__init__()
        self.user = user
        self.teacher_class = None
        self.load_teacher_class()
        self.init_ui()

    def load_teacher_class(self):
        try:
            conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
            cur.execute("SELECT assigned_class FROM Teachers WHERE user_id = ?", (self.user['id'],))
            res = cur.fetchone()
            if res: self.teacher_class = res[0]
            conn.close()
        except: pass

    def init_ui(self):
        root_layout = QHBoxLayout(self); root_layout.setContentsMargins(0, 0, 0, 0); root_layout.setSpacing(0)
        self.sidebar = Sidebar(self.user['full_name'], "Faculty Member"); self.sidebar.profile_card.clicked.connect(self.show_profile_menu)
        self.btns = {
            "Dashboard": self.sidebar.add_nav_item("Dashboard", "📊"),
            "My Classes": self.sidebar.add_nav_item("My Classes", "🏫"),
            "Students": self.sidebar.add_nav_item("Students", "👥"),
            "Grades": self.sidebar.add_nav_item("Grades", "📝"),
            "Reports": self.sidebar.add_nav_item("Reports", "📑"),
            "Settings": self.sidebar.add_nav_item("Settings", "⚙️")
        }
        root_layout.addWidget(self.sidebar)
        content_area = QWidget(); content_layout = QVBoxLayout(content_area); content_layout.setContentsMargins(0, 0, 0, 0); content_layout.setSpacing(0)
        self.navbar = ModernNavbar("Teacher Dashboard", f"Class Room: {self.teacher_class if self.teacher_class else 'General'}")
        content_layout.addWidget(self.navbar)
        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_dashboard_page()) # 0
        for _ in range(4): self.stack.addWidget(self.create_placeholder("Module Ready Soon")) 
        self.stack.addWidget(self.create_settings_page())  # 5
        content_layout.addWidget(self.stack); root_layout.addWidget(content_area)
        for i, (name, btn) in enumerate(self.btns.items()): btn.clicked.connect(lambda checked, idx=i, n=name: self.switch_page(idx, n))
        self.btns["Dashboard"].set_active(True)

    def switch_page(self, index, name):
        if index < self.stack.count():
            self.stack.setCurrentIndex(index); self.navbar.title_lbl.setText(f"Teacher | {name}")
            for n, b in self.btns.items(): b.set_active(n == name)

    def show_profile_menu(self, pos):
        menu = QMenu(self); menu.setStyleSheet("background: #1E293B; color: white;"); menu.addAction(QAction("👤 View Profile", self, triggered=self.view_profile)); menu.addSeparator(); menu.addAction(QAction("🚪 Logout", self, triggered=self.handle_logout)); menu.exec(pos)
    def view_profile(self): QMessageBox.information(self, "Profile", f"Teacher: {self.user['full_name']}")
    def handle_logout(self):
        if QMessageBox.question(self, "Logout", "Exit?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes: self.logout_requested.emit()

    def create_dashboard_page(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none; background: transparent;")
        content = QWidget(); layout = QVBoxLayout(content); layout.setContentsMargins(30, 20, 30, 30); layout.setSpacing(25)
        stats_lay = QHBoxLayout(); stats_lay.setSpacing(20); stats_lay.addWidget(AnalyticsCard("Students", "28", "+2", "#38BDF8", "👥")); stats_lay.addWidget(AnalyticsCard("Avg Grade", "74.6%", "+3.2%", "#818CF8", "📊")); stats_lay.addWidget(AnalyticsCard("At Risk", "6", "-2", "#F87171", "⚠️")); stats_lay.addWidget(AnalyticsCard("Success Rate", "76%", "+5.1%", "#34D399", "🧠")); layout.addLayout(stats_lay)
        mid_lay = QHBoxLayout(); mid_lay.setSpacing(20)
        table_card = QFrame(objectName="Card"); tv = QVBoxLayout(table_card); tv.setContentsMargins(20, 20, 20, 20); tv.addWidget(QLabel("Student Risk Analysis", styleSheet="color: white; font-weight: bold;")); self.risk_table = QTableWidget(); self.risk_table.setColumnCount(4); self.risk_table.setHorizontalHeaderLabels(["STUDENT", "SUCCESS", "RISK", "TREND"]); self.risk_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.risk_table.verticalHeader().setVisible(False); self.risk_table.setFixedHeight(300); tv.addWidget(self.risk_table); mid_lay.addWidget(table_card, 2)
        sim_card = QFrame(objectName="Card"); sv = QVBoxLayout(sim_card); sv.setContentsMargins(20, 20, 20, 20); sv.addWidget(QLabel("Improvement Simulator", styleSheet="color: white; font-weight: bold;"))
        self.sliders = {}
        for label, key, min_v, max_v, def_v in [("Study Hours", "study", 0, 50, 15), ("Absences", "abs", 0, 30, 2), ("Prev Grade", "prev", 0, 100, 75)]:
            row = QVBoxLayout(); lbl_lay = QHBoxLayout(); l1 = QLabel(label); self.sliders[key+"_v"] = QLabel(str(def_v)); l1.setStyleSheet("color: #94A3B8; font-size: 11px;"); self.sliders[key+"_v"].setStyleSheet("color: #38BDF8; font-weight: bold;"); lbl_lay.addWidget(l1); lbl_lay.addStretch(); lbl_lay.addWidget(self.sliders[key+"_v"]); row.addLayout(lbl_lay); s = QSlider(Qt.Orientation.Horizontal); s.setRange(min_v, max_v); s.setValue(def_v); s.valueChanged.connect(self.update_simulation); self.sliders[key] = s; row.addWidget(s); sv.addLayout(row)
        sv.addStretch(); self.sim_result = QLabel("76%"); self.sim_result.setAlignment(Qt.AlignmentFlag.AlignCenter); self.sim_result.setStyleSheet("color: #38BDF8; font-size: 32px; font-weight: 800;"); sv.addWidget(self.sim_result); mid_lay.addWidget(sim_card, 1); layout.addLayout(mid_lay)
        chart_card = QFrame(objectName="Card"); cv = QVBoxLayout(chart_card); cv.setContentsMargins(20, 20, 20, 20); cv.addWidget(QLabel("Prediction Change Over Time", styleSheet="color: white; font-weight: bold;")); fig, ax = plt.subplots(figsize=(6, 3), dpi=100); fig.patch.set_facecolor('#0F172A'); ax.set_facecolor('#0F172A'); ax.plot(['W1', 'W2', 'W3', 'W4', 'W5', 'W6'], [65, 68, 72, 70, 75, 76], color='#38BDF8', linewidth=2, marker='o'); ax.tick_params(colors='#64748B', labelsize=8); cv.addWidget(FigureCanvas(fig)); layout.addWidget(chart_card)
        self.load_risk_data(); scroll.setWidget(content); return scroll

    def load_risk_data(self):
        # 1. Try to load REAL students from DB for assigned class
        db_students = []
        if self.teacher_class:
            try:
                conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
                cur.execute("SELECT u.full_name, s.study_hours, s.absences, s.family_support, s.previous_score FROM Students s JOIN Users u ON s.user_id = u.id WHERE s.class_name = ?", (self.teacher_class,))
                rows = cur.fetchall(); conn.close()
                for r in rows:
                    n, st, ab, fm, pr = r; sc, pb, rk, cf = predict_student_performance(st, ab, fm, pr)
                    db_students.append((n, f"{pb:.0f}%", rk))
            except: pass
        
        # 2. If no DB students, use SAMPLES
        if not db_students:
            samples = [("Alice Smith", "88%", "Low"), ("Bob Johnson", "42%", "High"), ("Charlie Brown", "65%", "Medium"), ("Diana Ross", "92%", "Low")]
            db_students = samples
            
        self.risk_table.setRowCount(len(db_students))
        for i, (n, s, r) in enumerate(db_students):
            self.risk_table.setItem(i, 0, QTableWidgetItem(n)); self.risk_table.setItem(i, 1, QTableWidgetItem(s))
            badge = QLabel(r); badge.setObjectName(f"BadgeRisk{r}"); badge.setAlignment(Qt.AlignmentFlag.AlignCenter); self.risk_table.setCellWidget(i, 2, badge)
            self.risk_table.setItem(i, 3, QTableWidgetItem("↗" if "High" not in r else "↘"))

    def update_simulation(self):
        st, ab, pr = self.sliders['study'].value(), self.sliders['abs'].value(), self.sliders['prev'].value()
        self.sliders['study_v'].setText(str(st)); self.sliders['abs_v'].setText(str(ab)); self.sliders['prev_v'].setText(str(pr))
        sc, pb, rk, cf = predict_student_performance(st, ab, 5, pr); self.sim_result.setText(f"{pb:.0f}%")

    def create_settings_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30); card = QFrame(objectName="Card"); cv = QVBoxLayout(card); cv.addWidget(QLabel("ACCOUNT CONTROLS", styleSheet="font-weight: bold; color: white;")); logout = QPushButton("🚪 LOGOUT SESSION"); logout.setStyleSheet("background: #7F1D1D; color: white; padding: 12px; border-radius: 8px; font-weight: bold; margin-top: 20px;"); logout.clicked.connect(self.handle_logout); cv.addWidget(logout); cv.addStretch(); layout.addWidget(card); layout.addStretch(); return page
    def create_placeholder(self, t): page = QWidget(); layout = QVBoxLayout(page); l = QLabel(t); l.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(l); return page
