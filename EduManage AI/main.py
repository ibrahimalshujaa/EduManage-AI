import sys
import traceback
from PyQt6.QtWidgets import QApplication, QMessageBox
from auth import AuthManager
from ui.login import LoginWindow
from ui.admin_dashboard import AdminDashboard
from ui.teacher_dashboard import TeacherDashboard
from ui.student_portal import StudentPortal

class EduManageApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        # Initialize Auth
        self.auth_manager = AuthManager()
        
        # Load Styles
        try:
            with open("ui/styles.qss", "r") as f:
                self.app.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Warning: styles.qss not found.")

        self.login_window = None
        self.dashboard_window = None
        self.show_login()

    def show_login(self):
        """Initializes and shows the login window."""
        if self.dashboard_window:
            self.dashboard_window.close()
            self.dashboard_window = None
            
        self.login_window = LoginWindow(self.auth_manager)
        self.login_window.login_success.connect(self.handle_login_success)
        self.login_window.show()

    def handle_login_success(self, user):
        """Handles role-based routing after successful login."""
        try:
            role = user.get('role')
            print(f"Login successful for: {user['username']} ({role})")

            # Close login window
            self.login_window.close()
            self.login_window = None

            # Role Routing
            if role == "admin":
                self.dashboard_window = AdminDashboard(user)
            elif role == "teacher":
                self.dashboard_window = TeacherDashboard(user)
            elif role == "student":
                self.dashboard_window = StudentPortal(user)
            else:
                QMessageBox.critical(None, "Access Error", f"Unknown user role: {role}")
                self.show_login()
                return

            # Connect Logout Signal
            self.dashboard_window.logout_requested.connect(self.handle_logout)
            
            # Show Dashboard
            self.dashboard_window.show()

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"Critical error during dashboard initialization:\n{error_trace}")
            QMessageBox.critical(None, "Application Error", 
                                 f"Could not open dashboard: {str(e)}\n\nSee terminal for details.")
            self.show_login()

    def handle_logout(self):
        """Handles session logout and returns to login screen."""
        print("Logging out...")
        self.show_login()

    def run(self):
        sys.exit(self.app.exec())

if __name__ == "__main__":
    app = EduManageApp()
    app.run()
