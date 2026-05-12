from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                             QPushButton, QLabel, QFrame, QGraphicsDropShadowEffect)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PyQt6.QtGui import QColor, QFont

class LoginWindow(QWidget):
    login_success = pyqtSignal(dict)

    def __init__(self, auth_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("EduManage AI - Login")
        self.setFixedSize(1000, 700)
        
        # Main Container with shadow
        self.main_container = QFrame(self)
        self.main_container.setGeometry(100, 100, 800, 500)
        self.main_container.setStyleSheet("background-color: #0A0F1D; border-radius: 20px;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 150))
        self.main_container.setGraphicsEffect(shadow)
        
        layout = QHBoxLayout(self.main_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Left Branding Side
        left_frame = QFrame()
        left_frame.setFixedWidth(380)
        left_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E293B, stop:1 #0F172A);
            border-top-left-radius: 20px;
            border-bottom-left-radius: 20px;
            border-right: 1px solid #1E293B;
        """)
        
        left_layout = QVBoxLayout(left_frame)
        left_layout.addStretch()
        
        logo_icon = QLabel()
        logo_icon.setFixedSize(60, 60)
        logo_icon.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #38BDF8, stop:1 #818CF8); border-radius: 15px;")
        left_layout.addWidget(logo_icon, 0, Qt.AlignmentFlag.AlignCenter)
        
        logo_text = QLabel("EduManage AI")
        logo_text.setStyleSheet("color: white; font-size: 32px; font-weight: 800; margin-top: 15px;")
        logo_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(logo_text)
        
        tagline = QLabel("Predicting Success. Empowering Education.")
        tagline.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 500;")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(tagline)
        
        left_layout.addStretch()
        layout.addWidget(left_frame)

        # Right Login Form
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)
        right_layout.setContentsMargins(60, 60, 60, 60)
        
        title = QLabel("Welcome back")
        title.setStyleSheet("color: white; font-size: 28px; font-weight: 700;")
        right_layout.addWidget(title)
        
        subtitle = QLabel("Enter your credentials to access the platform")
        subtitle.setStyleSheet("color: #64748B; font-size: 14px; margin-bottom: 30px;")
        right_layout.addWidget(subtitle)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setFixedHeight(50)
        right_layout.addWidget(self.username_input)
        
        right_layout.addSpacing(15)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(50)
        right_layout.addWidget(self.password_input)
        
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #F87171; font-size: 12px; margin-top: 5px;")
        right_layout.addWidget(self.error_label)
        
        right_layout.addSpacing(30)
        
        self.login_btn = QPushButton("SIGN IN TO ACCOUNT")
        self.login_btn.setObjectName("GlowButton")
        self.login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)
        right_layout.addWidget(self.login_btn)
        
        right_layout.addStretch()
        layout.addWidget(right_frame)

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            self.error_label.setText("Please fill in all fields")
            return
            
        user = self.auth_manager.login(username, password)
        if user:
            self.login_success.emit(user)
        else:
            self.error_label.setText("Invalid username or password")
            self.shake_animation()

    def shake_animation(self):
        self.anim = QPropertyAnimation(self.main_container, b"pos")
        self.anim.setDuration(400)
        self.anim.setLoopCount(1)
        
        orig_pos = self.main_container.pos()
        self.anim.setKeyValueAt(0, orig_pos)
        self.anim.setKeyValueAt(0.1, orig_pos + QPoint(-10, 0))
        self.anim.setKeyValueAt(0.3, orig_pos + QPoint(10, 0))
        self.anim.setKeyValueAt(0.5, orig_pos + QPoint(-10, 0))
        self.anim.setKeyValueAt(0.7, orig_pos + QPoint(10, 0))
        self.anim.setKeyValueAt(1, orig_pos)
        
        self.anim.start()
