from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QMessageBox, QHBoxLayout, QTabWidget, QGroupBox, QGridLayout
from gui.employee_profile_tab import EmployeeProfileTab
from gui.employee_engagements_tab import EmployeeEngagementsTab
from gui.employee_leave_tab import EmployeeLeaveTab
from gui.employee_attendance_tab import EmployeeAttendanceTab
from gui.employee_payroll_tab import EmployeePayrollTab
from PyQt5.QtCore import QSettings, Qt
from services.supabase_service import get_attendance_history, fetch_user_leave_requests, supabase

class DashboardWindow(QWidget):
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.user_email = None
        self.leave_tab = None
        self.attendance_tab = None
        self.profile_tab = None
        self.setWindowTitle("HRMS Dashboard")
        self.init_ui()
        
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)  # Consistent margins with AdminDashboardWindow

        # Welcome Label
        self.welcome_label = QLabel("Welcome")
        main_layout.addWidget(self.welcome_label, alignment=Qt.AlignCenter)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.init_home_tab()
        self.tab_widget.addTab(self.home_tab, "🏠 Home")
        main_layout.addWidget(self.tab_widget)

        # Logout Button
        logout_layout = QHBoxLayout()
        self.logout_btn = QPushButton("🔒 Logout")
        self.logout_btn.clicked.connect(self.handle_logout)
        logout_layout.addStretch()
        logout_layout.addWidget(self.logout_btn)
        main_layout.addLayout(logout_layout)

        self.setLayout(main_layout)

    def set_user_email(self, email):
        # print(f"DEBUG: Setting user_email to {email}")
        self.user_email = email

        # Fetch employee name for welcome message
        employee_data = self.fetch_employee_data()
        employee_name = employee_data.get("full_name", email) if employee_data else email
        self.welcome_label.setText(f"Welcome, {employee_name}")

        self.tab_widget.clear()
        self.tab_widget.addTab(self.home_tab, "🏠 Home")

        self.leave_tab = EmployeeLeaveTab(self.user_email)
        self.attendance_tab = EmployeeAttendanceTab(self.user_email)
        self.profile_tab = EmployeeProfileTab(self.stacked_widget, self.user_email)

        self.payroll_tab = EmployeePayrollTab(self.user_email)
        self.engagements_tab = EmployeeEngagementsTab(self.user_email)

        self.tab_widget.addTab(self.profile_tab, "👤 Profile")
        self.tab_widget.addTab(self.attendance_tab, "📅 Attendance")
        self.tab_widget.addTab(self.leave_tab, "📬 Leave Request")

        self.tab_widget.addTab(self.payroll_tab, "💸 Payroll")
        self.tab_widget.addTab(self.engagements_tab, "🗂 Engagements (Training & Trips)")

        # print(f"DEBUG: Initializing profile tab with email: {self.user_email}")
        # Data is automatically loaded in the employee_profile_tab __init__ method
        # self.profile_tab.load_employee_data() - already called in init
        pass

        # Update home tab with summary data
        self.update_home_summary()

    def init_home_tab(self):
        self.home_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setAlignment(Qt.AlignCenter)  # Center content vertically

        # Summary Section
        summary_group = QGroupBox("Your Summary")
        summary_layout = QGridLayout()
        summary_layout.setSpacing(10)

        self.attendance_summary = QLabel("Recent Attendance: No recent records")
        self.leave_summary = QLabel("Leave Status: No pending requests")
        summary_layout.addWidget(QLabel("📅 Attendance:"), 0, 0)
        summary_layout.addWidget(self.attendance_summary, 0, 1)
        summary_layout.addWidget(QLabel("📬 Leave Requests:"), 1, 0)
        summary_layout.addWidget(self.leave_summary, 1, 1)

        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Quick Navigation Buttons
        nav_group = QGroupBox("Quick Actions")
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)

        profile_btn = QPushButton("👤 Go to Profile")
        attendance_btn = QPushButton("📅 Go to Attendance")
        leave_btn = QPushButton("📬 Go to Leave Request")

        profile_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(1))
        attendance_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(2))
        leave_btn.clicked.connect(lambda: self.tab_widget.setCurrentIndex(3))

        nav_layout.addWidget(profile_btn)
        nav_layout.addWidget(attendance_btn)
        nav_layout.addWidget(leave_btn)
        nav_group.setLayout(nav_layout)

        layout.addWidget(nav_group)
        layout.addStretch()

        wrapper = QHBoxLayout()
        wrapper.addStretch()
        wrapper.addLayout(layout)
        wrapper.addStretch()

        self.home_tab.setLayout(wrapper)

    def fetch_employee_data(self):
        try:
            response = supabase.table("employees").select("full_name").eq("email", self.user_email).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            # print(f"DEBUG: Error fetching employee data: {str(e)}")
            return {}

    def update_home_summary(self):
        try:
            # Fetch recent attendance record
            records = get_attendance_history(self.user_email)
            attendance_text = "Recent Attendance: No recent records"
            if records and len(records) > 0:
                latest = records[0]
                clock_in = latest.get("clock_in", "-")
                clock_out = latest.get("clock_out", "-")
                date = latest.get("date", "")
                attendance_text = f"Recent Attendance: {date} (In: {clock_in}, Out: {clock_out})"
            self.attendance_summary.setText(attendance_text)

            # Fetch pending leave requests
            leave_requests = fetch_user_leave_requests(self.user_email)
            leave_text = "Leave Status: No pending requests"
            if leave_requests:
                pending = [req for req in leave_requests if req.get("status") == "pending"]
                leave_text = f"Leave Status: {len(pending)} pending request(s)"
            self.leave_summary.setText(leave_text)
        except Exception as e:
            # print(f"DEBUG: Error updating home summary: {str(e)}")
            QMessageBox.warning(self, "Error", "Failed to load summary data.")

    def showEvent(self, event):
        if self.user_email:
            employee_data = self.fetch_employee_data()
            employee_name = employee_data.get("full_name", self.user_email) if employee_data else self.user_email
            self.welcome_label.setText(f"Welcome, {employee_name}")
        self.update_home_summary()

    def handle_logout(self):
        try:
            self.stacked_widget.setCurrentIndex(0)
            QSettings("MyCompany", "HRMS").remove("last_user_email")
        except Exception as e:
            # print(f"DEBUG: Error during logout: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to logout: {str(e)}")