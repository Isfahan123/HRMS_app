from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLabel, QMessageBox, QHeaderView
)
from PyQt5.QtCore import Qt
from services.supabase_service import record_clock_in, record_clock_out, get_attendance_history, get_attendance_settings, update_attendance_settings, KL_TZ, convert_utc_to_kl
from datetime import datetime, time

class EmployeeAttendanceTab(QWidget):
    def __init__(self, user_email=None):
        super().__init__()
        self.user_email = user_email.lower() if user_email else None
        # print(f"DEBUG: Starting EmployeeAttendanceTab.__init__ with user_email: {self.user_email}")
        self.attendance_settings = self.get_settings()
        try:
            self.init_ui()
            # print("DEBUG: EmployeeAttendanceTab.init_ui complete")
        except Exception as e:
            # print(f"DEBUG: Error in EmployeeAttendanceTab.init_ui: {str(e)}")
            raise

    def init_ui(self):
        # print("DEBUG: Starting EmployeeAttendanceTab.init_ui")
        layout = QVBoxLayout()

        button_layout = QHBoxLayout()
        self.clock_in_btn = QPushButton("🕒 Clock In")
        self.clock_out_btn = QPushButton("🕔 Clock Out")
        self.clock_in_btn.clicked.connect(self.handle_clock_in)
        self.clock_out_btn.clicked.connect(self.handle_clock_out)
        button_layout.addWidget(self.clock_in_btn)
        button_layout.addWidget(self.clock_out_btn)
        layout.addLayout(button_layout)

        layout.addWidget(QLabel("📅 My Attendance History"))
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Clock In", "Clock Out"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)
        self.load_attendance_history()

    def get_settings(self):
        try:
            settings = get_attendance_settings()
            if not settings:
                # print("DEBUG: No attendance settings found, using defaults")
                return {"work_start": "08:00:00", "work_end": "17:00:00", "clock_in_limit": "09:00:00"}
            return settings
        except Exception as e:
            # print(f"DEBUG: Error fetching attendance settings: {str(e)}")
            return {"work_start": "08:00:00", "work_end": "17:00:00", "clock_in_limit": "09:00:00"}

    def parse_time(self, time_str: str) -> time:
        try:
            return datetime.strptime(time_str, "%H:%M:%S").time()
        except (ValueError, TypeError) as e:
            # print(f"DEBUG: Invalid time format {time_str}: {str(e)}")
            return None

    def load_attendance_history(self):
        # print("DEBUG: Loading attendance history in EmployeeAttendanceTab")
        try:
            if not self.user_email:
                # print("DEBUG: No user_email set, skipping attendance history fetch")
                self.table.setRowCount(0)
                return
            records = get_attendance_history(self.user_email)
            # print(f"DEBUG: Fetched {len(records)} attendance records")
            self.table.setRowCount(len(records))
            for row, record in enumerate(records):
                for col, key in enumerate(["date", "clock_in", "clock_out"]):
                    value = record.get(key, "-")
                    if key in ["clock_in", "clock_out"] and value and value != "-":
                        try:
                            # convert_utc_to_kl now returns a string, not a datetime object
                            value = convert_utc_to_kl(value)
                        except (ValueError, TypeError) as e:
                            # print(f"DEBUG: Error formatting {key} timestamp {value}: {str(e)}")
                            value = str(value)
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)
            # print("DEBUG: Attendance history table populated")
        except Exception as e:
            # print(f"DEBUG: Error fetching attendance history: {str(e)}")
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Error", f"Failed to load attendance history: {str(e)}")

    def handle_clock_in(self):
        if not self.user_email:
            QMessageBox.critical(self, "Error", "User email is not set. Please log in again.")
            return

        try:
            now = datetime.now(KL_TZ)
            current_time = now.time()
            work_start = self.parse_time(self.attendance_settings.get('work_start'))
            work_end = self.parse_time(self.attendance_settings.get('work_end'))
            limit_time = self.parse_time(self.attendance_settings.get('clock_in_limit'))

            if not work_start or not work_end or not limit_time:
                QMessageBox.critical(self, "Error", "Invalid attendance settings. Contact administrator.")
                return

            if current_time > limit_time:
                QMessageBox.warning(self, "Error", f"Clock-in not allowed after {self.attendance_settings['clock_in_limit']}.")
                return

            if current_time < work_start:
                QMessageBox.warning(self, "Error", f"Clock-in not allowed before work starts at {self.attendance_settings['work_start']}.")
                return

            success = record_clock_in(self.user_email)
            if success:
                QMessageBox.information(self, "Success", "Clock-in recorded successfully.")
                self.load_attendance_history()
            else:
                QMessageBox.warning(self, "Error", "Failed to record clock-in. You may have already clocked in today.")
        except Exception as e:
            # print(f"DEBUG: Error in clock-in: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to record clock-in: {str(e)}")

    def handle_clock_out(self):
        if not self.user_email:
            QMessageBox.critical(self, "Error", "User email is not set. Please log in again.")
            return

        try:
            now = datetime.now(KL_TZ)
            current_time = now.time()
            work_start = self.parse_time(self.attendance_settings.get('work_start'))
            work_end = self.parse_time(self.attendance_settings.get('work_end'))

            if not work_start or not work_end:
                QMessageBox.critical(self, "Error", "Invalid attendance settings. Contact administrator.")
                return

            if current_time < work_start:
                QMessageBox.warning(self, "Error", f"Clock-out not allowed before work starts at {self.attendance_settings['work_start']}.")
                return

            work_end_dt = datetime.combine(now.date(), work_end)
            current_dt = datetime.combine(now.date(), current_time)
            if (work_end_dt - current_dt).total_seconds() > 1800:
                QMessageBox.warning(self, "Warning", f"Clock-out is early. Work ends at {self.attendance_settings['work_end']}.")

            success = record_clock_out(self.user_email)
            if success:
                QMessageBox.information(self, "Success", "Clock-out recorded successfully.")
                self.load_attendance_history()
            else:
                QMessageBox.warning(self, "Error", "Failed to record clock-out. You may not have clocked in or already clocked out today.")
        except Exception as e:
            # print(f"DEBUG: Error in clock-out: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to record clock-out: {str(e)}")