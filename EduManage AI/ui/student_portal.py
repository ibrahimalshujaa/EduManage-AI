import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QGridLayout, QFrame, QScrollArea, QProgressBar, QPushButton, QStackedWidget, QTableWidget, QTableWidgetItem, QHeaderView, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QColor, QAction
from ui.components.widgets import AnalyticsCard, Sidebar, ModernNavbar
from database import DB_PATH
from ai_model import predict_student_performance

class StudentPortal(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, user):
        super().__init__()
        self.user = user
        self.init_ui()

    def init_ui(self):
        root_layout = QHBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0); root_layout.setSpacing(0)

        # Sidebar with functional profile
        self.sidebar = Sidebar(self.user['full_name'], "10th Grade - Class A")
        self.sidebar.profile_card.clicked.connect(self.show_profile_menu)
        
        btns = {
            "Dashboard": self.sidebar.add_nav_item("Dashboard", "🏠"),
            "My Grades": self.sidebar.add_nav_item("My Grades", "📝"),
            "My Prediction": self.sidebar.add_nav_item("My Prediction", "🧠"),
            "Recommendations": self.sidebar.add_nav_item("Recommendations", "💡"),
            "Study Plan": self.sidebar.add_nav_item("Study Plan", "📅"),
            "Profile": self.sidebar.add_nav_item("Profile", "👤"),
            "Settings": self.sidebar.add_nav_item("Settings", "⚙️")
        }
        root_layout.addWidget(self.sidebar)

        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0); content_layout.setSpacing(0)
        self.navbar = ModernNavbar("Student Portal", "Welcome back to your academic overview")
        content_layout.addWidget(self.navbar)

        self.stack = QStackedWidget()
        self.stack.addWidget(self.create_dashboard_page()) # 0
        for _ in range(5): self.stack.addWidget(QWidget()) # Placeholders
        self.stack.addWidget(self.create_settings_page())  # 6
        content_layout.addWidget(self.stack)
        root_layout.addWidget(content_area)

        for i, (name, btn) in enumerate(btns.items()):
            btn.clicked.connect(lambda checked, idx=i, n=name: self.switch_page(idx, n))

    def switch_page(self, index, name):
        if index < self.stack.count():
            self.stack.setCurrentIndex(index)
            self.navbar.title_lbl.setText(f"Student Portal")

    def show_profile_menu(self, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #1E293B; color: white; border: 1px solid #334155; border-radius: 8px; padding: 5px; }
            QMenu::item { padding: 8px 25px; border-radius: 4px; }
            QMenu::item:selected { background-color: #38BDF8; color: white; }
        """)
        menu.addAction(QAction("👤 View Profile", self, triggered=self.view_profile))
        menu.addAction(QAction("⚙️ Account Settings", self, triggered=lambda: self.switch_page(6, "Settings")))
        menu.addSeparator()
        menu.addAction(QAction("🚪 Logout", self, triggered=self.handle_logout))
        menu.exec(pos)

    def view_profile(self):
        QMessageBox.information(self, "Student Profile", f"Name: {self.user['full_name']}\nGrade: 10th Grade\nClass: A\nStatus: Active")

    def handle_logout(self):
        ret = QMessageBox.question(self, "Logout", "Are you sure you want to logout?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if ret == QMessageBox.StandardButton.Yes: self.logout_requested.emit()

    def create_dashboard_page(self):
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("border: none; background: transparent;")
        content = QWidget(); layout = QVBoxLayout(content); layout.setContentsMargins(30, 30, 30, 30); layout.setSpacing(25)
        stats = QHBoxLayout(); stats.setSpacing(20)
        stats.addWidget(AnalyticsCard("Average Grade", "73.5%", color="#38BDF8", icon_char="📊"))
        stats.addWidget(AnalyticsCard("Predicted Success", "82%", color="#34D399", icon_char="🧠"))
        stats.addWidget(AnalyticsCard("Class Rank", "12 / 28", color="#FBBF24", icon_char="🏆"))
        stats.addWidget(AnalyticsCard("Attendance", "90%", color="#818CF8", icon_char="📅"))
        layout.addLayout(stats); scroll.setWidget(content); return scroll

    def create_settings_page(self):
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(30, 30, 30, 30)
        logout = QPushButton("🚪 LOGOUT SESSION"); logout.setStyleSheet("background: #7F1D1D; color: white; padding: 12px; border-radius: 8px;")
        logout.clicked.connect(self.handle_logout)
        layout.addWidget(logout); layout.addStretch(); return page
