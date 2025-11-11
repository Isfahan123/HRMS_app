from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTabWidget, QPushButton, QHBoxLayout, QMessageBox
)
from gui.admin_profile_tab_mod import AdminProfileTab
from gui.admin_engagements_tab import AdminEngagementsTab
from gui.admin_attendance_tab_mod import AdminAttendanceTab
from gui.admin_leave_tab_mod import AdminLeaveTab
from gui.admin_payroll_tab_mod import AdminPayrollTab
from gui.admin_salary_history_tab_mod import AdminSalaryHistoryTab
from gui.employee_history_tab import EmployeeHistoryTab
from PyQt5.QtCore import QSettings, pyqtSignal
from services.supabase_service import supabase

class AdminDashboardWindow(QWidget):
    # Signal to notify when employee data is updated
    employee_data_updated = pyqtSignal(str)  # employee_id
    
    def __init__(self, stacked_widget):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.user_email = None
        self.setWindowTitle("Admin Dashboard")
        self.init_ui()
        self.setup_signal_connections()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)

        # Header: welcome label on left, action buttons on right
        header_layout = QHBoxLayout()
        self.welcome_label = QLabel("Welcome, Admin")
        header_layout.addWidget(self.welcome_label)
        header_layout.addStretch()
        # Prominent Open Calendar button (top-right)
        try:
            from gui.calendar_tab import CalendarTab
            self._calendar_tab_class = CalendarTab
            self.open_cal_btn = QPushButton('Open Calendar')
            self.open_cal_btn.setToolTip('Open Calendar / Holidays')
            self.open_cal_btn.clicked.connect(lambda: self.open_calendar_dialog())
            header_layout.addWidget(self.open_cal_btn)
            # Debug log to help verify presence at runtime
            print("DEBUG: AdminDashboardWindow - created header Open Calendar button")
        except Exception as e:
            # Surface the import error so it's visible in logs and provide a placeholder button
            self._calendar_tab_class = None
            print(f"DEBUG: AdminDashboardWindow - failed to import CalendarTab: {e}")
            try:
                placeholder_btn = QPushButton('Open Calendar (Unavailable)')
                placeholder_btn.setToolTip('Calendar module not available')
                placeholder_btn.clicked.connect(lambda _, err=e: QMessageBox.warning(self, 'Calendar Unavailable', f'Calendar module failed to import: {err}'))
                header_layout.addWidget(placeholder_btn)
            except Exception:
                # If even placeholder creation fails, continue silently
                pass

        main_layout.addLayout(header_layout)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.profile_tab = AdminProfileTab(self)
        self.attendance_tab = AdminAttendanceTab(self)
        self.leave_tab = AdminLeaveTab(self, admin_email=self.user_email)
        self.payroll_tab = AdminPayrollTab(self)

        self.salary_history_tab = AdminSalaryHistoryTab()
        self.engagements_tab = AdminEngagementsTab(self)
        self.employee_history_tab = EmployeeHistoryTab(self)

        self.tab_widget.addTab(self.profile_tab, "👥 Profiles")
        self.tab_widget.addTab(self.attendance_tab, "📋 Attendance")
        self.tab_widget.addTab(self.leave_tab, "📅 Leaves")
        self.tab_widget.addTab(self.payroll_tab, "💸 Payroll")

        self.tab_widget.addTab(self.salary_history_tab, "📈 Salary History")
        self.tab_widget.addTab(self.engagements_tab, "📚 Activities (Training & Trips)")
        self.tab_widget.addTab(self.employee_history_tab, "🧾 Employment History")
        # Note: single header Open Calendar button is used; no duplicate below tabs

        main_layout.addWidget(self.tab_widget)

        # Logout Button
        logout_layout = QHBoxLayout()
        self.logout_btn = QPushButton("🔒 Logout")
        self.logout_btn.clicked.connect(self.handle_logout)
        logout_layout.addStretch()
        logout_layout.addWidget(self.logout_btn)
        main_layout.addLayout(logout_layout)

        self.setLayout(main_layout)

    def setup_signal_connections(self):
        """Setup signal connections between tabs"""
        # Connect salary history updates to profile tab refresh
        if hasattr(self.salary_history_tab, 'salary_updated'):
            self.salary_history_tab.salary_updated.connect(self.on_salary_updated)
        # When an employee is selected in the profile tab, forward to the history tab and switch to it
        try:
            self.profile_tab.employee_selected.connect(self.on_profile_employee_selected)
        except Exception:
            pass
        # Allow EmployeeHistoryTab to request the profiles tab be shown
        try:
            if hasattr(self.employee_history_tab, 'request_choose_employee'):
                # Expose a named method the child will look for so it can
                # request the Profiles tab be shown. Do NOT set a 'parent'
                # attribute on the child object (that would shadow QObject.parent()).
                setattr(self, 'request_show_profiles_tab', self.show_profiles_tab)
        except Exception:
            pass
        # Connect history tab change notifications so profile dialogs refresh
        try:
            if hasattr(self.employee_history_tab, 'history_changed'):
                self.employee_history_tab.history_changed.connect(self.on_salary_updated)
        except Exception:
            pass

    def open_calendar_dialog(self):
        if not getattr(self, '_calendar_tab_class', None):
            QMessageBox.warning(self, 'Unavailable', 'Calendar module is not available.')
            return
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout
            dlg = QDialog(self)
            dlg.setWindowTitle('Calendar / Holidays')
            dlg.setModal(True)
            layout = QVBoxLayout()
            c = self._calendar_tab_class(dlg)
            layout.addWidget(c)
            dlg.setLayout(layout)
            dlg.exec_()
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to open Calendar: {e}')
    
    def on_salary_updated(self, employee_id):
        """Handle salary update notification"""
        try:
            # Notify profile tab to refresh any open dialogs
            if hasattr(self.profile_tab, 'refresh_employee_dialogs'):
                self.profile_tab.refresh_employee_dialogs(employee_id)
            
            # Emit signal for other components that might need it
            self.employee_data_updated.emit(employee_id)
            
        except Exception as e:
            print(f"DEBUG: Error handling salary update: {e}")

    def on_profile_employee_selected(self, employee):
        """Receive an employee dict from the profile tab, set it into the history tab, and switch to that tab."""
        try:
            # Pass the employee to the history tab
            if hasattr(self.employee_history_tab, 'set_employee'):
                self.employee_history_tab.set_employee(employee)
            # Switch to the Employment History tab index if present
            idx = self.tab_widget.indexOf(self.employee_history_tab)
            if idx != -1:
                self.tab_widget.setCurrentIndex(idx)
        except Exception as e:
            print(f"DEBUG: Failed to open history for employee: {e}")

    def show_profiles_tab(self):
        """Switch focus to the profiles tab so user can select an employee."""
        try:
            idx = self.tab_widget.indexOf(self.profile_tab)
            if idx != -1:
                self.tab_widget.setCurrentIndex(idx)
                # Optionally focus the table
                try:
                    self.profile_tab.table.setFocus()
                except Exception:
                    pass
        except Exception as e:
            print(f"DEBUG: Failed to switch to profiles tab: {e}")

    def showEvent(self, event):
        if self.user_email:
            self.welcome_label.setText(f"Welcome, Admin\n{self.user_email}")

    def set_user_email(self, email):
        self.user_email = email
        self.payroll_tab.set_user_email(email)
        if hasattr(self.leave_tab, 'set_admin_email'):
            self.leave_tab.set_admin_email(email)
        self.welcome_label.setText(f"Welcome, Admin\n{self.user_email}")

    def handle_logout(self):
        try:
            self.stacked_widget.setCurrentIndex(0)
            QSettings("MyCompany", "HRMS").remove("last_user_email")
        except Exception as e:
            print(f"DEBUG: Error during logout: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to logout: {str(e)}")