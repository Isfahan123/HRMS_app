from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QSettings
from services.supabase_service import login_user_by_username, supabase, convert_utc_to_kl

class LoginWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.setWindowTitle("HRMS Login")
        self.init_ui()

    def init_ui(self):
        # Create main container with fixed size
        main_widget = QWidget()
        main_widget.resize(400, 300)
        
        form_layout = QVBoxLayout()
        form_layout.setContentsMargins(40, 40, 40, 40)
        form_layout.setSpacing(15)

        # Title
        title_label = QLabel("HRMS Login")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 20px;")
        title_label.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(35)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)

        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.handle_login)

        form_layout.addWidget(title_label)
        form_layout.addWidget(QLabel("Username:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Password:"))
        form_layout.addWidget(self.password_input)
        form_layout.addWidget(self.login_button)
        form_layout.addStretch()

        main_widget.setLayout(form_layout)

        # Center the form widget
        outer_layout = QVBoxLayout()
        outer_layout.addStretch()
        
        center_layout = QHBoxLayout()
        center_layout.addStretch()
        center_layout.addWidget(main_widget)
        center_layout.addStretch()
        
        outer_layout.addLayout(center_layout)
        outer_layout.addStretch()

        self.setLayout(outer_layout)

    def handle_login(self):
        print("DEBUG: Login button clicked")
        try:
            username = self.username_input.text().strip().lower()
            password = self.password_input.text()
            
            if not username or not password:
                QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
                return

            print(f"DEBUG: Attempting login with username: {username}")
            result = login_user_by_username(username, password)
            print(f"DEBUG: Login result: {result}")

            # If backend returned a locked_until timestamp, show explicit message to the user
            if result and result.get("locked_until"):
                locked = result.get("locked_until")
                try:
                    display_locked = convert_utc_to_kl(locked)
                except Exception:
                    display_locked = locked
                QMessageBox.warning(self, "Account Locked",
                                    f"Account is locked until {display_locked} (Malaysia Time). Please try again later or contact your administrator.")
                return

            if result and result.get("role"):
                result_email = (result.get("email") or "").lower()
                print(f"DEBUG: Password match for username {username} (email: {result_email})")
                role = result["role"].lower()
                if role == "admin":
                    try:
                        admin_page = getattr(self.stacked_widget, 'admin_dashboard_page', None)
                        if admin_page is None:
                            print("DEBUG: Admin page not present; creating on-demand")
                            from gui.admin_dashboard_window import AdminDashboardWindow
                            admin_page = AdminDashboardWindow(self.stacked_widget)
                            self.stacked_widget.admin_dashboard_page = admin_page
                            # Attach to stack if not already
                            if self.stacked_widget.indexOf(admin_page) == -1:
                                self.stacked_widget.addWidget(admin_page)
                        # Set context and switch
                        admin_page.set_user_email(result_email)
                        idx = self.stacked_widget.indexOf(admin_page)
                        if idx == -1:
                            self.stacked_widget.addWidget(admin_page)
                            idx = self.stacked_widget.indexOf(admin_page)
                        print(f"DEBUG: Switching to admin page at index {idx}")
                        self.stacked_widget.setCurrentIndex(idx)
                        return
                    except Exception as e:
                        print(f"DEBUG: Failed to initialize/switch to admin dashboard: {e}")
                        QMessageBox.critical(self, "Login Error", f"Failed to open admin dashboard: {e}")
                        return
                elif role == "employee":
                    try:
                        emp_page = getattr(self.stacked_widget, 'dashboard_page', None)
                        if emp_page is None:
                            print("DEBUG: Employee page not present; creating on-demand")
                            from gui.dashboard_window import DashboardWindow
                            emp_page = DashboardWindow(self.stacked_widget)
                            self.stacked_widget.dashboard_page = emp_page
                            if self.stacked_widget.indexOf(emp_page) == -1:
                                self.stacked_widget.addWidget(emp_page)
                        emp_page.set_user_email(result_email)
                        idx = self.stacked_widget.indexOf(emp_page)
                        if idx == -1:
                            self.stacked_widget.addWidget(emp_page)
                            idx = self.stacked_widget.indexOf(emp_page)
                        print(f"DEBUG: Switching to employee page at index {idx}")
                        self.stacked_widget.setCurrentIndex(idx)
                        return
                    except Exception as e:
                        print(f"DEBUG: Failed to initialize/switch to employee dashboard: {e}")
                        QMessageBox.critical(self, "Login Error", f"Failed to open employee dashboard: {e}")
                        return
                else:
                    QMessageBox.critical(self, "Login Error", f"Role {result['role']} not supported or page not initialized.")
            else:
                QMessageBox.critical(self, "Login Error", "Invalid username or password.")
                
        except Exception as e:
            print(f"DEBUG: Error in handle_login: {str(e)}")
            QMessageBox.critical(self, "Login Error", f"Login failed: {str(e)}")