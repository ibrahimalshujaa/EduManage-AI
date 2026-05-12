from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QPushButton, QGraphicsDropShadowEffect, QSpacerItem, QSizePolicy, QLineEdit, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QColor, QIcon, QPixmap, QAction

class ClickableLabel(QLabel):
    clicked = pyqtSignal(QPoint)
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event.globalPosition().toPoint())
        super().mousePressEvent(event)

class ClickableProfileCard(QFrame):
    clicked = pyqtSignal(QPoint)
    def __init__(self, user_name, user_role):
        super().__init__()
        self.setObjectName("SidebarProfile")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(70)
        self.setMinimumWidth(240)
        self.setStyleSheet("""
            QFrame#SidebarProfile {
                background: rgba(30, 41, 59, 0.4);
                border-radius: 12px;
                border: 1px solid rgba(56, 189, 248, 0.1);
            }
            QFrame#SidebarProfile:hover {
                background: rgba(30, 41, 59, 0.6);
            }
        """)
        
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(10, 0, 10, 0)
        main_lay.setSpacing(10)
        
        # Avatar
        self.avatar = QLabel(user_name[0] if user_name else "U")
        self.avatar.setFixedSize(40, 40)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet("""
            background-color: #38BDF8;
            color: white;
            border-radius: 20px;
            font-weight: 800;
            font-size: 15px;
            border: none;
        """)
        main_lay.addWidget(self.avatar)
        
        # Text Info
        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        text_lay = QVBoxLayout(text_container)
        text_lay.setContentsMargins(0, 0, 0, 0)
        text_lay.setSpacing(1)
        text_lay.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        
        self.name_lbl = QLabel(user_name)
        self.name_lbl.setStyleSheet("color: white; font-weight: 700; font-size: 13px; background: transparent;")
        
        self.role_lbl = QLabel(user_role)
        self.role_lbl.setStyleSheet("color: #64748B; font-size: 11px; background: transparent;")
        
        text_lay.addWidget(self.name_lbl)
        text_lay.addWidget(self.role_lbl)
        main_lay.addWidget(text_container, 1) # Give it stretch
        
        # Arrow
        arrow = QLabel("⌵")
        arrow.setStyleSheet("color: #64748B; font-size: 16px; font-weight: bold; background: transparent;")
        main_lay.addWidget(arrow)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(event.globalPosition().toPoint())
        super().mousePressEvent(event)

class AnalyticsCard(QFrame):
    def __init__(self, title, value, growth="+0%", color="#38BDF8", icon_char="📊"):
        super().__init__()
        self.setObjectName("Card"); self.setMinimumHeight(110)
        layout = QHBoxLayout(self); layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(15)
        icon_box = QFrame(); icon_box.setFixedSize(50, 50); icon_box.setStyleSheet(f"background-color: {color}22; border-radius: 12px; border: 1px solid {color}44;")
        ib_lay = QVBoxLayout(icon_box); ib_lay.setContentsMargins(0, 0, 0, 0)
        il = QLabel(icon_char); il.setAlignment(Qt.AlignmentFlag.AlignCenter); il.setStyleSheet("font-size: 20px; color: white; background: transparent; border: none;"); ib_lay.addWidget(il)
        layout.addWidget(icon_box)
        info = QVBoxLayout(); info.setSpacing(2)
        t_lbl = QLabel(title); t_lbl.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: 600; background: transparent; border: none;")
        v_lbl = QLabel(str(value)); v_lbl.setStyleSheet("color: white; font-size: 22px; font-weight: 800; background: transparent; border: none;")
        g_lbl = QLabel(growth + " from last month"); g_lbl.setStyleSheet(f"color: {'#34D399' if '+' in growth else '#F87171'}; font-size: 10px; font-weight: 600; background: transparent; border: none;")
        info.addWidget(t_lbl); info.addWidget(v_lbl); info.addWidget(g_lbl); layout.addLayout(info); layout.addStretch()

class SidebarButton(QPushButton):
    def __init__(self, text, icon_char=""):
        super().__init__()
        self.setObjectName("NavButton"); self.setCheckable(True); self.setCursor(Qt.CursorShape.PointingHandCursor); self.setFixedHeight(46)
        lay = QHBoxLayout(self); lay.setContentsMargins(15, 0, 15, 0); lay.setSpacing(12)
        self.il = QLabel(icon_char); self.il.setStyleSheet("font-size: 16px; background: transparent; border: none;"); lay.addWidget(self.il)
        self.tl = QLabel(text); self.tl.setStyleSheet("font-size: 13px; font-weight: 500; background: transparent; border: none;"); lay.addWidget(self.tl); lay.addStretch()

    def set_active(self, active):
        self.setProperty("active", "true" if active else "false"); self.setStyle(self.style())
        color = "white" if active else "#94A3B8"
        self.tl.setStyleSheet(f"color: {color}; font-weight: {'700' if active else '500'}; background: transparent; border: none;")
        self.il.setStyleSheet(f"color: {color}; background: transparent; border: none;")

class Sidebar(QFrame):
    def __init__(self, user_name, user_role="Staff"):
        super().__init__()
        self.setObjectName("Sidebar"); self.setFixedWidth(260)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 30, 10, 20)
        self.main_layout.setSpacing(0)
        
        # Logo section
        logo_container = QWidget(); logo_container.setStyleSheet("background: transparent; border: none;")
        logo_lay = QHBoxLayout(logo_container); logo_lay.setContentsMargins(15, 0, 15, 30); logo_lay.setSpacing(10)
        logo_icon = QFrame(); logo_icon.setFixedSize(32, 32); logo_icon.setStyleSheet("background: #38BDF8; border-radius: 10px; border: none;")
        logo_text = QLabel("EduManage AI"); logo_text.setStyleSheet("color: white; font-size: 20px; font-weight: 800; background: transparent; border: none;")
        logo_lay.addWidget(logo_icon); logo_lay.addWidget(logo_text); logo_lay.addStretch()
        self.main_layout.addWidget(logo_container)
        
        # Navigation container
        self.buttons = []
        self.nav_container = QWidget(); self.nav_container.setStyleSheet("background: transparent; border: none;")
        self.nav_layout = QVBoxLayout(self.nav_container); self.nav_layout.setContentsMargins(0, 0, 0, 0); self.nav_layout.setSpacing(5)
        self.main_layout.addWidget(self.nav_container)
        
        self.main_layout.addStretch(1)
        
        # Profile Section
        self.profile_card = ClickableProfileCard(user_name, user_role)
        self.main_layout.addWidget(self.profile_card)

    def add_nav_item(self, text, icon=""):
        btn = SidebarButton(text, icon)
        btn.clicked.connect(lambda: self.set_active_btn(btn))
        self.nav_layout.addWidget(btn)
        self.buttons.append(btn)
        return btn

    def set_active_btn(self, active_btn):
        for b in self.buttons: b.set_active(b == active_btn)

class ModernNavbar(QFrame):
    search_changed = pyqtSignal(str)
    bell_clicked = pyqtSignal(QPoint)
    profile_clicked = pyqtSignal(QPoint)
    
    def __init__(self, title, subtitle="Overview"):
        super().__init__()
        self.setFixedHeight(80); self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self); lay.setContentsMargins(30, 0, 30, 0)
        hamburger = QLabel("≡"); hamburger.setStyleSheet("font-size: 24px; color: #94A3B8; margin-right: 15px; background: transparent; border: none;"); lay.addWidget(hamburger)
        t_box = QVBoxLayout(); t_box.setSpacing(0)
        self.title_lbl = QLabel(title); self.title_lbl.setStyleSheet("font-size: 22px; font-weight: 800; color: white; background: transparent; border: none;")
        t_sub = QLabel(subtitle); t_sub.setStyleSheet("font-size: 11px; color: #64748B; background: transparent; border: none;"); t_box.addWidget(self.title_lbl); t_box.addWidget(t_sub); lay.addLayout(t_box); lay.addStretch()
        
        search_cnt = QFrame(); search_cnt.setFixedWidth(250); search_cnt.setFixedHeight(38); search_cnt.setStyleSheet("background: #0F172A; border-radius: 10px; border: 1px solid #1E293B;")
        slay = QHBoxLayout(search_cnt); slay.addWidget(QLabel("🔍", styleSheet="background: transparent; border: none;"))
        self.search_in = QLineEdit(); self.search_in.setPlaceholderText("Search..."); self.search_in.setStyleSheet("background: transparent; border: none; color: white; font-size: 12px;")
        self.search_in.textChanged.connect(self.search_changed.emit)
        slay.addWidget(self.search_in); lay.addWidget(search_cnt); lay.addSpacing(15)
        
        self.bell = ClickableLabel("🔔"); self.bell.setStyleSheet("font-size: 18px; color: #94A3B8; cursor: pointer; background: transparent; border: none;")
        self.bell.clicked.connect(self.bell_clicked.emit); lay.addWidget(self.bell); lay.addSpacing(15)
        
        self.avatar = ClickableLabel(""); self.avatar.setFixedSize(35, 35); self.avatar.setStyleSheet("background: #1E293B; border-radius: 17px; border: 1px solid #38BDF8;")
        self.avatar.clicked.connect(self.profile_clicked.emit); lay.addWidget(self.avatar)
