from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QPushButton, QTimeEdit, QMessageBox, QLineEdit, QComboBox, QHeaderView, QDateEdit, QFileDialog
)
from PyQt5.QtCore import QTime, Qt, QDate
import csv
from services.supabase_service import (
    get_all_attendance_records,
    get_attendance_settings,
    update_attendance_settings,
    convert_utc_to_kl
)
import pytz
from datetime import datetime

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

class AdminAttendanceTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdminAttendanceTab")
        self.user_email = None
        # print("DEBUG: Starting AdminAttendanceTab.__init__")
        try:
            self.init_ui()
            # print("DEBUG: AdminAttendanceTab.init_ui complete")
        except Exception as e:
            # print(f"DEBUG: Error in AdminAttendanceTab.init_ui: {str(e)}")
            raise

    def init_ui(self):
        # print("DEBUG: Starting AdminAttendanceTab.init_ui")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("🗂️ All Employee Attendance Records"))

        filter_layout = QHBoxLayout()
        self.filter_field = QComboBox()
        self.filter_field.addItems(["Email", "Date"])
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Search...")
        self.filter_input.textChanged.connect(self.filter_attendance_records)
        
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-1))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        self.start_date.dateChanged.connect(self.filter_attendance_records)
        self.end_date.dateChanged.connect(self.filter_attendance_records)

        filter_layout.addWidget(QLabel("🗓️ From:"))
        filter_layout.addWidget(self.start_date)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.end_date)
        
        filter_layout.addWidget(QLabel("🔍 Filter by:"))
        filter_layout.addWidget(self.filter_field)
        filter_layout.addWidget(self.filter_input)
        
        self.export_btn = QPushButton("📤 Export to CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        filter_layout.addWidget(self.export_btn)

        self.layout.addLayout(filter_layout)
        
        self.attendance_table = QTableWidget()
        self.attendance_table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.SelectedClicked)
        self.layout.addWidget(self.attendance_table)

        self.layout.addWidget(QLabel("🛠️ Set Official Working Hours"))
        time_layout = QHBoxLayout()
        self.start_time_edit = QTimeEdit()
        self.end_time_edit = QTimeEdit()
        self.limit_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("hh:mm")
        self.end_time_edit.setDisplayFormat("hh:mm")
        self.limit_time_edit.setDisplayFormat("hh:mm")

        time_layout.addWidget(QLabel("Clock-in:"))
        time_layout.addWidget(self.start_time_edit)
        time_layout.addWidget(QLabel("Clock-out:"))
        time_layout.addWidget(self.end_time_edit)
        time_layout.addWidget(QLabel("Clock-in Limit:"))
        time_layout.addWidget(self.limit_time_edit)

        self.save_time_btn = QPushButton("Save")
        self.save_time_btn.clicked.connect(self.save_work_time)
        time_layout.addWidget(self.save_time_btn)
        self.layout.addLayout(time_layout)

        try:
            self.load_attendance_settings()
            self.load_attendance_records()
            # print("DEBUG: AdminAttendanceTab layout set")
        except Exception as e:
            # print(f"DEBUG: Error setting up AdminAttendanceTab: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to set up attendance tab: {str(e)}")

    def set_user_email(self, email):
        # print(f"DEBUG: Setting user email in AdminAttendanceTab: {email}")
        self.user_email = email.lower() if email else None
        try:
            self.load_attendance_records()
        except Exception as e:
            # print(f"DEBUG: Error in AdminAttendanceTab.set_user_email: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to load attendance records: {str(e)}")

    def load_attendance_settings(self):
        try:
            settings = get_attendance_settings()
            if settings:
                self.start_time_edit.setTime(QTime.fromString(settings["work_start"], "HH:mm:ss"))
                self.end_time_edit.setTime(QTime.fromString(settings["work_end"], "HH:mm:ss"))
                self.limit_time_edit.setTime(QTime.fromString(settings["clock_in_limit"], "HH:mm:ss"))
                # print("DEBUG: Attendance settings loaded")
            else:
                # print("DEBUG: No attendance settings found. Using defaults.")
                self.start_time_edit.setTime(QTime(8, 0))
                self.end_time_edit.setTime(QTime(17, 0))
                self.limit_time_edit.setTime(QTime(9, 0))
        except Exception as e:
            # print(f"DEBUG: Error loading attendance settings: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load attendance settings: {str(e)}")

    def load_attendance_records(self):
        # print("DEBUG: Loading attendance records in AdminAttendanceTab")
        try:
            start_date = self.start_date.date().toPyDate().isoformat()
            end_date = self.end_date.date().toPyDate().isoformat()
            filter_text = self.filter_input.text().strip().lower()
            filter_field = self.filter_field.currentText()

            records = get_all_attendance_records()
            # print(f"DEBUG: Fetched {len(records)} attendance records")

            filtered_records = records
            if filter_text:
                if filter_field == "Email":
                    filtered_records = [r for r in records if filter_text in r.get("email", "").lower()]
                elif filter_field == "Date":
                    filtered_records = [r for r in records if filter_text in r.get("date", "").lower()]

            filtered_records = [
                r for r in filtered_records
                if start_date <= r.get("date", "") <= end_date
            ]

            self.attendance_table.setRowCount(len(filtered_records))
            self.attendance_table.setColumnCount(4)
            self.attendance_table.setHorizontalHeaderLabels(["Email", "Date", "Clock In", "Clock Out"])
            self.attendance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            for row, record in enumerate(filtered_records):
                for col, key in enumerate(["email", "date", "clock_in", "clock_out"]):
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
                    self.attendance_table.setItem(row, col, item)

            # print("DEBUG: Attendance table populated")
        except Exception as e:
            # print(f"DEBUG: Error loading attendance records: {str(e)}")
            self.attendance_table.setRowCount(0)
            QMessageBox.warning(self, "Error", f"Failed to load attendance records: {str(e)}")

    def filter_attendance_records(self):
        self.load_attendance_records()

    def save_work_time(self):
        try:
            start_time = self.start_time_edit.time().toPyTime()
            end_time = self.end_time_edit.time().toPyTime()
            limit_time = self.limit_time_edit.time().toPyTime()

            start_time_str = start_time.strftime("%H:%M:%S")
            end_time_str = end_time.strftime("%H:%M:%S")
            limit_time_str = limit_time.strftime("%H:%M:%S")

            if start_time >= end_time:
                QMessageBox.warning(self, "Invalid", "Clock-in time must be before clock-out time.")
                return

            result = update_attendance_settings(start_time_str, end_time_str, limit_time_str)
            if result:
                QMessageBox.information(self, "Success", "Official working hours updated.")
            else:
                QMessageBox.warning(self, "Error", "Failed to update working hours.")
        except Exception as e:
            # print(f"DEBUG: Error saving work time: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save work time: {str(e)}")

    def export_to_csv(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
            if not path:
                return

            row_count = self.attendance_table.rowCount()
            col_count = self.attendance_table.columnCount()

            with open(path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = [self.attendance_table.horizontalHeaderItem(i).text() for i in range(col_count)]
                writer.writerow(headers)

                for row in range(row_count):
                    line = []
                    for col in range(col_count):
                        item = self.attendance_table.item(row, col)
                        line.append(item.text() if item else "")
                    writer.writerow(line)

            QMessageBox.information(self, "Exported", f"Attendance records exported to:\n{path}")
        except Exception as e:
            # print(f"DEBUG: Error exporting to CSV: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export attendance records: {str(e)}")