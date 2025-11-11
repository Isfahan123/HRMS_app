from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, 
    QHBoxLayout, QPushButton, QLineEdit, QComboBox, QHeaderView, QDateEdit, QMessageBox, QFileDialog, QGroupBox, QTabWidget, QDialog, QTextEdit, QDialogButtonBox, QFormLayout, QSpinBox, QScrollArea, QFrame, QCheckBox, QDoubleSpinBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QColor
import csv
import webbrowser
import pytz
from services.supabase_service import get_all_leave_requests, update_leave_request_status, cancel_approved_leave_request, convert_utc_to_kl, get_individual_employee_leave_balance, get_individual_employee_sick_leave_balance, calculate_working_days, get_leave_request_states
from datetime import datetime
from gui.calendar_tab import CalendarTab

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

class AdminLeaveTab(QWidget):
    def __init__(self, parent=None, admin_email=None):
        super().__init__(parent)
        self.setObjectName("AdminLeaveTab")
        self.current_admin_email = admin_email or "admin@example.com"
        # print(f"DEBUG: AdminLeaveTab initialized with admin_email: {self.current_admin_email}")
        try:
            self.init_ui()
            # print("DEBUG: AdminLeaveTab.init_ui complete")
        except Exception as e:
            # print(f"DEBUG: Error in AdminLeaveTab.init_ui: {str(e)}")
            raise

    def init_ui(self):
        # print("DEBUG: Starting AdminLeaveTab.init_ui")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.layout.addWidget(QLabel("📋 All Employee Leave Requests"))

        # Tab Widget for Pending, Approved/Rejected, and Leave Balance Management
        self.tab_widget = QTabWidget()
        self.pending_tab = QWidget()
        self.approved_rejected_tab = QWidget()
        self.submit_request_tab = QWidget()
        self.leave_balance_tab = QWidget()
        self.sick_leave_balance_tab = QWidget()
        self.unpaid_leave_tab = QWidget()  # New unpaid leave tab
        self.tab_widget.addTab(self.pending_tab, "Pending")
        self.tab_widget.addTab(self.approved_rejected_tab, "Approved/Rejected")
        self.tab_widget.addTab(self.submit_request_tab, "Submit Leave Request")
        self.tab_widget.addTab(self.leave_balance_tab, "Annual Leave Balance")
        self.tab_widget.addTab(self.sick_leave_balance_tab, "Sick Leave Balance")
        self.tab_widget.addTab(self.unpaid_leave_tab, "📊 Unpaid Leave")  # New tab
        # Calendar / Holidays management tab
        try:
            self.calendar_tab = CalendarTab()
            self.tab_widget.addTab(self.calendar_tab, "Calendar / Holidays")
        except Exception:
            # If UI creation fails, continue without calendar tab
            pass
        self.tab_widget.currentChanged.connect(self.populate_tables)

        # Setup Pending Tab with its own filter
        self.setup_pending_tab()

        # Approved/Rejected Table
        self.approved_rejected_table = QTableWidget()
        self.approved_rejected_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Create layout for approved/rejected tab with filters
        approved_rejected_layout = QVBoxLayout()
        
        # Add status filter for approved/rejected tab
        status_filter_group = QGroupBox("Status Filter")
        status_filter_layout = QHBoxLayout()
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Approved", "Rejected", "Cancelled"])
        self.status_filter.currentTextChanged.connect(self.filter_approved_rejected)
        
        # Date range filter for approved/rejected
        self.reviewed_start_date = QDateEdit()
        self.reviewed_start_date.setCalendarPopup(True)
        self.reviewed_start_date.setDate(QDate.currentDate().addMonths(-3))
        self.reviewed_start_date.dateChanged.connect(self.filter_approved_rejected)
        
        self.reviewed_end_date = QDateEdit()
        self.reviewed_end_date.setCalendarPopup(True)
        self.reviewed_end_date.setDate(QDate.currentDate())
        self.reviewed_end_date.dateChanged.connect(self.filter_approved_rejected)
        
        # Employee search for approved/rejected
        self.approved_rejected_search = QLineEdit()
        self.approved_rejected_search.setPlaceholderText("Search by employee email...")
        self.approved_rejected_search.textChanged.connect(self.filter_approved_rejected)
        
        status_filter_layout.addWidget(QLabel("Status:"))
        status_filter_layout.addWidget(self.status_filter)
        status_filter_layout.addWidget(QLabel("Reviewed From:"))
        status_filter_layout.addWidget(self.reviewed_start_date)
        status_filter_layout.addWidget(QLabel("To:"))
        status_filter_layout.addWidget(self.reviewed_end_date)
        status_filter_layout.addWidget(QLabel("Employee:"))
        status_filter_layout.addWidget(self.approved_rejected_search)
        
        status_filter_group.setLayout(status_filter_layout)
        approved_rejected_layout.addWidget(status_filter_group)
        approved_rejected_layout.addWidget(self.approved_rejected_table)
        self.approved_rejected_tab.setLayout(approved_rejected_layout)

        # Leave Balance Management Tab
        self.setup_leave_balance_tab()
        
        # Submit Leave Request Tab
        self.setup_submit_request_tab()
        
        # Sick Leave Balance Management Tab
        self.setup_sick_leave_balance_tab()
        
        # Unpaid Leave Management Tab
        self.setup_unpaid_leave_tab()

        self.layout.addWidget(self.tab_widget)

        try:
            self.load_leave_requests()
            # print("DEBUG: AdminLeaveTab layout set")
        except Exception as e:
            # print(f"DEBUG: Error setting up AdminLeaveTab: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to set up leave tab: {str(e)}")

    def setup_pending_tab(self):
        """Setup the pending tab with its own filter controls"""
        pending_layout = QVBoxLayout()
        
        # Pending tab filter controls
        pending_filter_group = QGroupBox("Pending Requests Filter")
        pending_filter_layout = QHBoxLayout()
        pending_filter_layout.setSpacing(10)

        self.pending_filter_field = QComboBox()
        self.pending_filter_field.addItems(["Email", "Leave Type"])
        self.pending_filter_input = QLineEdit()
        self.pending_filter_input.setPlaceholderText("Search pending requests...")
        self.pending_filter_input.textChanged.connect(self.filter_pending_requests)

        current_date = QDate.currentDate()
        self.pending_start_date = QDateEdit()
        self.pending_start_date.setCalendarPopup(True)
        self.pending_start_date.setDate(current_date.addMonths(-1))

        self.pending_end_date = QDateEdit()
        self.pending_end_date.setCalendarPopup(True)
        self.pending_end_date.setDate(current_date)

        self.pending_start_date.dateChanged.connect(self.filter_pending_requests)
        self.pending_end_date.dateChanged.connect(self.filter_pending_requests)

        pending_filter_layout.addWidget(QLabel("From:"))
        pending_filter_layout.addWidget(self.pending_start_date)
        pending_filter_layout.addWidget(QLabel("To:"))
        pending_filter_layout.addWidget(self.pending_end_date)
        pending_filter_layout.addWidget(QLabel("Filter by:"))
        pending_filter_layout.addWidget(self.pending_filter_field)
        pending_filter_layout.addWidget(self.pending_filter_input)

        self.pending_reset_btn = QPushButton("Reset Filters")
        self.pending_reset_btn.clicked.connect(self.reset_pending_filters)
        pending_filter_layout.addWidget(self.pending_reset_btn)

        self.pending_refresh_btn = QPushButton("🔄 Refresh")
        self.pending_refresh_btn.clicked.connect(self.load_leave_requests)
        pending_filter_layout.addWidget(self.pending_refresh_btn)

        self.pending_export_btn = QPushButton("Export to CSV")
        self.pending_export_btn.clicked.connect(self.export_pending_to_csv)
        pending_filter_layout.addWidget(self.pending_export_btn)

        pending_filter_group.setLayout(pending_filter_layout)
        pending_layout.addWidget(pending_filter_group)

        # Pending Table
        self.pending_table = QTableWidget()
        self.pending_table.setEditTriggers(QTableWidget.NoEditTriggers)
        pending_layout.addWidget(self.pending_table)
        
        self.pending_tab.setLayout(pending_layout)

    def load_leave_requests(self):
        # print("DEBUG: Loading leave requests in AdminLeaveTab")
        try:
            self.original_records = get_all_leave_requests()
            # print(f"DEBUG: Fetched {len(self.original_records)} leave requests")
            self.populate_tables()
        except Exception as e:
            # print(f"DEBUG: Error fetching leave requests: {str(e)}")
            self.original_records = []
            self.populate_tables()
            QMessageBox.warning(self, "Error", f"Failed to load leave requests: {str(e)}")

    def populate_tables(self, index=None):
        # print("DEBUG: Populating tables in AdminLeaveTab")
        try:
            # If the leave balance tab is selected, load leave balances instead
            current_tab_index = self.tab_widget.currentIndex()
            if current_tab_index == 2:  # Submit Leave Request tab
                return  # No data loading needed for the submit form
            elif current_tab_index == 3:  # Annual Leave Balance tab
                self.load_leave_balances()
                return
            elif current_tab_index == 4:  # Sick Leave Balance tab
                self.load_sick_leave_balances()
                return
            
            pending_records = [r for r in self.original_records if r.get("status") == "pending"]
            approved_rejected_records = [r for r in self.original_records if r.get("status") in ["approved", "rejected"]]

            # Populate Pending Table using the new dedicated method
            self.populate_pending_table(pending_records)

            # Populate Approved/Rejected Table
            self.populate_approved_rejected_table(approved_rejected_records)

            # print("DEBUG: Leave tables populated")
        except Exception as e:
            # print(f"DEBUG: Error populating leave tables: {str(e)}")
            self.pending_table.setRowCount(0)
            self.approved_rejected_table.setRowCount(0)
            QMessageBox.warning(self, "Error", f"Failed to populate leave tables: {str(e)}")

    def filter_approved_rejected(self):
        """Filter the approved/rejected table based on status, date range, and employee search"""
        try:
            current_tab_index = self.tab_widget.currentIndex()
            if current_tab_index != 1:  # Only filter if on approved/rejected tab
                return
                
            status_filter = self.status_filter.currentText().lower()
            search_text = self.approved_rejected_search.text().strip().lower()
            start_date = self.reviewed_start_date.date().toPyDate()
            end_date = self.reviewed_end_date.date().toPyDate()
            
            # Get all approved/rejected records
            approved_rejected_records = [r for r in self.original_records if r.get("status") in ["approved", "rejected"]]
            
            # Apply status filter
            if status_filter != "all":
                approved_rejected_records = [r for r in approved_rejected_records if r.get("status", "").lower() == status_filter]
            
            # Apply employee search filter
            if search_text:
                approved_rejected_records = [r for r in approved_rejected_records 
                                           if search_text in r.get("employee_email", "").lower()]
            
            # Apply date range filter (based on reviewed_at date)
            filtered_records = []
            for record in approved_rejected_records:
                reviewed_at = record.get("reviewed_at")
                if reviewed_at and reviewed_at != "-":
                    try:
                        # Parse the original UTC timestamp to get date for filtering
                        dt = datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
                        reviewed_date = dt.date()
                        if start_date <= reviewed_date <= end_date:
                            filtered_records.append(record)
                    except:
                        # If date parsing fails, include the record
                        filtered_records.append(record)
                else:
                    # If no reviewed_at date, include the record
                    filtered_records.append(record)
            
            # Update the table with filtered results
            self.populate_approved_rejected_table(filtered_records)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to filter approved/rejected requests: {str(e)}")

    def populate_approved_rejected_table(self, records):
        """Populate the approved/rejected table with the given records"""
        try:
            self.approved_rejected_table.setRowCount(len(records))
            self.approved_rejected_table.setColumnCount(12)
            self.approved_rejected_table.setHorizontalHeaderLabels([
                "Email", "Leave Type", "Title", "Start Date", "End Date", "Days",
                "Status", "Submitted At", "Reviewed At", "Reviewer", "View Details", "Actions"
            ])
            
            # Configure column widths for proper button containment
            header = self.approved_rejected_table.horizontalHeader()
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.Stretch)          # Email
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Leave Type
            header.setSectionResizeMode(2, QHeaderView.Stretch)          # Title
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Start Date
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # End Date
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Days
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Status
            header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # Submitted At
            header.setSectionResizeMode(8, QHeaderView.ResizeToContents) # Reviewed At
            header.setSectionResizeMode(9, QHeaderView.ResizeToContents) # Reviewer
            header.setSectionResizeMode(10, QHeaderView.Fixed)           # View Details
            header.setSectionResizeMode(11, QHeaderView.Fixed)           # Actions
            
            # Set fixed widths for button columns
            self.approved_rejected_table.setColumnWidth(10, 120) # View Details
            self.approved_rejected_table.setColumnWidth(11, 120) # Actions
            
            # Set minimum row height for buttons
            self.approved_rejected_table.verticalHeader().setDefaultSectionSize(45)

            for row, record in enumerate(records):
                # Calculate working days between start and end date
                try:
                    start_date = datetime.strptime(record.get("start_date", ""), "%Y-%m-%d")
                    end_date = datetime.strptime(record.get("end_date", ""), "%Y-%m-%d")
                    try:
                        states = get_leave_request_states(record.get('id'))
                        state = states[0] if states else None
                    except Exception:
                        state = None
                    days = calculate_working_days(start_date, end_date, state=state)
                except:
                    days = "-"

                for col, key in enumerate([
                    "employee_email", "leave_type", "title", "start_date", "end_date", None,  # None for days calculation
                    "status", "submitted_at", "reviewed_at", "reviewed_by"
                ]):
                    if col == 5:  # Days column
                        # Check if half-day and adjust display
                        is_half_day = record.get("is_half_day", False)
                        if is_half_day:
                            value = "0.5"
                        else:
                            value = str(days)
                    else:
                        value = record.get(key, "-")
                        
                        # Special handling for leave type to include half-day info
                        if key == "leave_type":
                            is_half_day = record.get("is_half_day", False)
                            half_day_period = record.get("half_day_period", "")
                            if is_half_day:
                                period = "Morning" if "Morning" in half_day_period else "Afternoon"
                                value = f"{value} (Half Day - {period})"
                    
                    if key in ["submitted_at", "reviewed_at"] and value not in ("-", None, ""):
                        # convert_utc_to_kl already returns a formatted string
                        value = convert_utc_to_kl(value)
                    
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Color coding for status
                    if col == 6:  # Status column
                        if value.lower() == "approved":
                            item.setBackground(QColor("#d4edda"))  # Light green
                            item.setForeground(QColor("#155724"))  # Dark green
                        elif value.lower() == "rejected":
                            item.setBackground(QColor("#f8d7da"))  # Light red
                            item.setForeground(QColor("#721c24"))  # Dark red
                    
                    self.approved_rejected_table.setItem(row, col, item)

                # View Details Button (includes title and document access)
                details_widget = QWidget()
                details_layout = QHBoxLayout(details_widget)
                details_layout.setContentsMargins(5, 2, 5, 2)
                details_layout.setSpacing(0)
                details_btn = QPushButton("📋 Details")
                details_btn.resize(100, 30)
                details_btn.clicked.connect(lambda _, r=record: self.view_details(r))
                details_layout.addWidget(details_btn)
                details_layout.addStretch()
                self.approved_rejected_table.setCellWidget(row, 10, details_widget)
                
                # Cancel Button (only for approved leaves that haven't started yet)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                actions_layout.setSpacing(0)
                
                # Check if this is an approved leave that can be cancelled
                can_cancel = False
                if record.get("status", "").lower() == "approved":
                    try:
                        start_date = datetime.strptime(record.get("start_date", ""), "%Y-%m-%d").date()
                        today = datetime.now().date()
                        can_cancel = start_date > today  # Can only cancel future leaves
                    except:
                        can_cancel = False
                
                if can_cancel:
                    cancel_btn = QPushButton("❌ Cancel")
                    cancel_btn.resize(100, 30)
                    cancel_btn.setStyleSheet("QPushButton { background-color: #dc3545; color: white; border: none; border-radius: 3px; } QPushButton:hover { background-color: #c82333; }")
                    cancel_btn.clicked.connect(lambda _, r=record: self.cancel_leave_request(r))
                    actions_layout.addWidget(cancel_btn)
                else:
                    # Add empty space if no cancel button
                    actions_layout.addStretch()
                
                actions_layout.addStretch()
                self.approved_rejected_table.setCellWidget(row, 11, actions_widget)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to populate approved/rejected table: {str(e)}")

    def filter_pending_requests(self):
        """Filter only the pending requests based on pending tab filters"""
        try:
            current_tab_index = self.tab_widget.currentIndex()
            if current_tab_index != 0:  # Only filter if on pending tab
                return
                
            filter_text = self.pending_filter_input.text().strip().lower()
            filter_field = self.pending_filter_field.currentText()
            start_date = self.pending_start_date.date().toPyDate().isoformat()
            end_date = self.pending_end_date.date().toPyDate().isoformat()

            # Get only pending records from original data
            pending_records = [r for r in self.original_records if r.get("status") == "pending"]
            
            # Apply text filter
            if filter_text:
                if filter_field == "Email":
                    pending_records = [r for r in pending_records if filter_text in r.get("employee_email", "").lower()]
                elif filter_field == "Leave Type":
                    pending_records = [r for r in pending_records if filter_text in r.get("leave_type", "").lower()]

            # Apply date filter
            pending_records = [
                r for r in pending_records
                if start_date <= r.get("start_date", "") <= end_date
            ]

            # Update only the pending table
            self.populate_pending_table(pending_records)
        except Exception as e:
            # print(f"DEBUG: Error filtering pending requests: {str(e)}")
            QMessageBox.warning(self, "Error", f"Failed to filter pending requests: {str(e)}")

    def reset_pending_filters(self):
        """Reset only the pending tab filters"""
        self.pending_filter_input.clear()
        self.pending_filter_field.setCurrentIndex(0)
        self.pending_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.pending_end_date.setDate(QDate.currentDate())
        # Refresh the pending table with unfiltered data
        if hasattr(self, 'original_records'):
            pending_records = [r for r in self.original_records if r.get("status") == "pending"]
            self.populate_pending_table(pending_records)

    def export_pending_to_csv(self):
        """Export only pending requests to CSV"""
        try:
            # Get filtered pending records
            pending_records = [r for r in self.original_records if r.get("status") == "pending"]
            
            # Apply current filters
            filter_text = self.pending_filter_input.text().strip().lower()
            filter_field = self.pending_filter_field.currentText()
            start_date = self.pending_start_date.date().toPyDate().isoformat()
            end_date = self.pending_end_date.date().toPyDate().isoformat()
            
            if filter_text:
                if filter_field == "Email":
                    pending_records = [r for r in pending_records if filter_text in r.get("employee_email", "").lower()]
                elif filter_field == "Leave Type":
                    pending_records = [r for r in pending_records if filter_text in r.get("leave_type", "").lower()]

            pending_records = [
                r for r in pending_records
                if start_date <= r.get("start_date", "") <= end_date
            ]
            
            filename, _ = QFileDialog.getSaveFileName(self, "Export Pending Requests", "pending_leave_requests.csv", "CSV Files (*.csv)")
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Employee Email", "Leave Type", "Title", "Start Date", "End Date", "Submitted At"])
                    for record in pending_records:
                        writer.writerow([
                            record.get("employee_email", ""),
                            record.get("leave_type", ""),
                            record.get("title", ""),
                            record.get("start_date", ""),
                            record.get("end_date", ""),
                            record.get("submitted_at", "")
                        ])
                QMessageBox.information(self, "Success", f"Pending requests exported to {filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export pending requests: {str(e)}")

    def populate_pending_table(self, pending_records):
        """Populate only the pending table with given records"""
        try:
            self.pending_table.setRowCount(len(pending_records))
            self.pending_table.setColumnCount(9)  # Reduced from 10 to 9
            self.pending_table.setHorizontalHeaderLabels([
                "Employee Email", "Leave Type", "Title", "Start Date", "End Date",
                "Status", "Submitted At", "Actions", "View Details"
            ])
            
            # Configure column widths for proper button containment
            header = self.pending_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)          # Email
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Leave Type
            header.setSectionResizeMode(2, QHeaderView.Stretch)          # Title
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # Start Date
            header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # End Date
            header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Status
            header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Submitted At
            header.setSectionResizeMode(7, QHeaderView.Fixed)            # Actions
            header.setSectionResizeMode(8, QHeaderView.Fixed)            # View Details
            
            # Set fixed widths for button columns
            self.pending_table.setColumnWidth(7, 180)  # Actions (needs more space for 2 buttons)
            self.pending_table.setColumnWidth(8, 120)  # View Details
            
            # Set minimum row height for buttons
            self.pending_table.verticalHeader().setDefaultSectionSize(45)

            for row, record in enumerate(pending_records):
                for col, key in enumerate([
                    "employee_email", "leave_type", "title", "start_date", "end_date",
                    "status", "submitted_at"
                ]):
                    value = record.get(key, "-")
                    
                    # Special handling for leave type to include half-day info
                    if key == "leave_type":
                        is_half_day = record.get("is_half_day", False)
                        half_day_period = record.get("half_day_period", "")
                        if is_half_day:
                            period = "Morning" if "Morning" in half_day_period else "Afternoon"
                            value = f"{value} (Half Day - {period})"
                    elif key in ["submitted_at", "reviewed_at"] and value != "-":
                        try:
                            # convert_utc_to_kl already returns a formatted string
                            value = convert_utc_to_kl(value)
                        except (ValueError, TypeError) as e:
                            # print(f"DEBUG: Error formatting {key} timestamp {value}: {str(e)}")
                            value = str(value)
                    
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.pending_table.setItem(row, col, item)

                # Action Buttons
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 2, 5, 2)
                action_layout.setSpacing(5)
                approve_btn = QPushButton("✓ Approve")
                approve_btn.resize(75, 30)
                approve_btn.clicked.connect(lambda _, r=record: self.update_status(r, "approved"))
                reject_btn = QPushButton("✗ Reject")
                reject_btn.resize(70, 30)
                reject_btn.clicked.connect(lambda _, r=record: self.update_status(r, "rejected"))
                action_layout.addWidget(approve_btn)
                action_layout.addWidget(reject_btn)
                action_layout.addStretch()
                self.pending_table.setCellWidget(row, 7, action_widget)  # Changed from row 8 to 7

                # View Details Button
                details_widget = QWidget()
                details_layout = QHBoxLayout(details_widget)
                details_layout.setContentsMargins(5, 2, 5, 2)
                details_layout.setSpacing(0)
                details_btn = QPushButton("📋 Details")
                details_btn.resize(100, 30)
                details_btn.clicked.connect(lambda _, r=record: self.view_details(r))
                details_layout.addWidget(details_btn)
                details_layout.addStretch()
                self.pending_table.setCellWidget(row, 8, details_widget)  # Changed from row 9 to 8
        except Exception as e:
            # print(f"DEBUG: Error populating pending table: {str(e)}")
            self.pending_table.setRowCount(0)
            QMessageBox.warning(self, "Error", f"Failed to populate pending table: {str(e)}")

    def open_document(self, url):
        if url:
            try:
                webbrowser.open(url)
            except Exception as e:
                # print(f"DEBUG: Error opening document: {str(e)}")
                QMessageBox.warning(self, "Error", f"Failed to open document: {str(e)}")

    def update_status(self, record, status):
        try:
            success = update_leave_request_status(record["id"], status, self.current_admin_email)
            if success:
                QMessageBox.information(self, "Success", f"Leave request {status}.")
                self.load_leave_requests()
            else:
                QMessageBox.warning(self, "Error", f"Failed to update leave request status to {status}.")
        except Exception as e:
            # print(f"DEBUG: Error updating leave status: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update leave status: {str(e)}")

    def view_details(self, record):
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 Leave Request Details")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Employee information
        info_group = QGroupBox("👤 Employee Information")
        info_layout = QFormLayout()
        info_layout.addRow("Employee Email:", QLabel(record.get("employee_email", "-")))
        info_layout.addRow("Leave Type:", QLabel(record.get("leave_type", "-")))
        info_layout.addRow("Title:", QLabel(record.get("title", "-")))
        info_layout.addRow("Start Date:", QLabel(record.get("start_date", "-")))
        info_layout.addRow("End Date:", QLabel(record.get("end_date", "-")))
        
        # Calculate working days
        try:
            start_date = datetime.strptime(record.get("start_date", ""), "%Y-%m-%d")
            end_date = datetime.strptime(record.get("end_date", ""), "%Y-%m-%d")
            try:
                states = get_leave_request_states(record.get('id'))
                state = states[0] if states else None
            except Exception:
                state = None
            days = calculate_working_days(start_date, end_date, state=state)
            info_layout.addRow("Working Days:", QLabel(str(days)))
        except:
            info_layout.addRow("Total Days:", QLabel("-"))
            
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Status information
        status_group = QGroupBox("📊 Status Information")
        status_layout = QFormLayout()
        
        status_label = QLabel(record.get("status", "-").title())
        if record.get("status", "").lower() == "approved":
            status_label
        elif record.get("status", "").lower() == "rejected":
            status_label
        status_layout.addRow("Status:", status_label)
        
        # Format timestamps
        submitted_at = record.get("submitted_at", "-")
        if submitted_at != "-":
            try:
                # convert_utc_to_kl already returns a formatted string
                submitted_at = convert_utc_to_kl(submitted_at)
            except:
                pass
        status_layout.addRow("Submitted At:", QLabel(submitted_at))
        
        reviewed_at = record.get("reviewed_at", "-")
        if reviewed_at != "-":
            try:
                # convert_utc_to_kl already returns a formatted string
                reviewed_at = convert_utc_to_kl(reviewed_at)
            except:
                pass
        status_layout.addRow("Reviewed At:", QLabel(reviewed_at))
        
        status_layout.addRow("Reviewed By:", QLabel(record.get("reviewed_by", "-")))
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Title section - only show for Annual Leave (not for Sick Leave)
        leave_type = record.get("leave_type", "").lower()
        if leave_type == "annual":
            title_group = QGroupBox("📝 Leave Request Title")
            title_layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(record.get("title", "No title provided"))
            text_edit.setMinimumHeight(150)
            title_layout.addWidget(text_edit)
            title_group.setLayout(title_layout)
            layout.addWidget(title_group)
        # No title section for sick leave - completely removed
        
        # Document information
        if record.get("document_url"):
            doc_group = QGroupBox("📎 Supporting Document")
            doc_layout = QHBoxLayout()
            doc_btn = QPushButton("📄 Open Document")
            doc_btn
            doc_btn.clicked.connect(lambda: self.open_document(record.get("document_url")))
            doc_layout.addWidget(doc_btn)
            doc_layout.addStretch()
            doc_group.setLayout(doc_layout)
            layout.addWidget(doc_group)
        else:
            # Show no document message
            doc_group = QGroupBox("📎 Supporting Document")
            doc_layout = QVBoxLayout()
            no_doc_label = QLabel("No supporting document attached")
            no_doc_label
            doc_layout.addWidget(no_doc_label)
            doc_group.setLayout(doc_layout)
            layout.addWidget(doc_group)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def cancel_leave_request(self, record):
        """Cancel an approved leave request with confirmation"""
        try:
            # Get leave details for confirmation
            employee_email = record.get("employee_email", "")
            leave_type = record.get("leave_type", "")
            start_date = record.get("start_date", "")
            end_date = record.get("end_date", "")
            leave_id = record.get("id", "")
            
            # Calculate days
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                try:
                    states = get_leave_request_states(record.get('id'))
                    state = states[0] if states else None
                except Exception:
                    state = None
                days = calculate_working_days(start_dt, end_dt, state=state)
            except:
                days = "N/A"
            
            # Confirmation dialog
            reply = QMessageBox.question(
                self, 
                "Cancel Leave Request",
                f"Are you sure you want to cancel this approved leave request?\n\n"
                f"Employee: {employee_email}\n"
                f"Leave Type: {leave_type}\n"
                f"Period: {start_date} to {end_date}\n"
                f"Working Days: {days}\n\n"
                f"This will restore the employee's leave balance.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Get cancellation reason
                reason_dialog = QDialog(self)
                reason_dialog.setWindowTitle("Cancellation Reason")
                reason_dialog.setMinimumSize(400, 200)
                
                layout = QVBoxLayout()
                
                layout.addWidget(QLabel("Please provide a reason for cancelling this leave request:"))
                
                reason_edit = QTextEdit()
                reason_edit.setMaximumHeight(100)
                reason_edit.setPlaceholderText("e.g., Employee requested cancellation due to changed circumstances...")
                layout.addWidget(reason_edit)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(reason_dialog.accept)
                buttons.rejected.connect(reason_dialog.reject)
                layout.addWidget(buttons)
                
                reason_dialog.setLayout(layout)
                
                if reason_dialog.exec_() == QDialog.Accepted:
                    reason = reason_edit.toPlainText().strip()
                    if not reason:
                        reason = "No reason provided"
                    
                    # Call the cancel function
                    success = cancel_approved_leave_request(leave_id, self.current_admin_email, reason)
                    
                    if success:
                        QMessageBox.information(
                            self, 
                            "Success", 
                            f"Leave request has been successfully cancelled.\n"
                            f"Employee's {leave_type.lower()} leave balance has been restored."
                        )
                        # Refresh the table
                        self.populate_tables()
                    else:
                        QMessageBox.critical(
                            self, 
                            "Error", 
                            "Failed to cancel the leave request. Please check if the leave has already started or try again."
                        )
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to cancel leave request: {str(e)}")

    def export_to_csv(self):
        try:
            path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
            if not path:
                return

            current_tab_index = self.tab_widget.currentIndex()
            if current_tab_index == 0:  # Pending tab
                current_table = self.pending_table
                # Exclude last 2 columns: Actions (8), View Details (9)
                col_count = current_table.columnCount() - 2
            elif current_tab_index == 1:  # Approved/Rejected tab
                current_table = self.approved_rejected_table
                # Exclude last 1 column: View Details (10)
                col_count = current_table.columnCount() - 1
            elif current_tab_index == 2:  # Annual Leave Balance tab
                current_table = self.leave_balance_table
                # Exclude last 1 column: Actions
                col_count = current_table.columnCount() - 1
            else:  # Sick Leave Balance tab
                current_table = self.sick_leave_balance_table
                # Exclude last 1 column: Actions
                col_count = current_table.columnCount() - 1
                
            row_count = current_table.rowCount()

            with open(path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = [current_table.horizontalHeaderItem(i).text() for i in range(col_count)]
                writer.writerow(headers)

                for row in range(row_count):
                    line = []
                    for col in range(col_count):
                        item = current_table.item(row, col)
                        text = item.text() if item else ""
                        if col in [2, 3, 6, 7]:  # Start Date, End Date, Submitted At, Reviewed At
                            if text and col in [6, 7]:  # Timestamp columns
                                try:
                                    date = datetime.fromisoformat(text.replace(" MYT", "+08:00"))
                                    text = date.strftime("%Y-%m-%d %H:%M:%S %Z")
                                except ValueError:
                                    pass
                            elif col in [2, 3]:  # Date columns
                                try:
                                    date = datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=KL_TZ)
                                    text = date.strftime("%Y-%m-%d %Z")
                                except ValueError:
                                    pass
                        line.append(text)
                    writer.writerow(line)

            QMessageBox.information(self, "Exported", f"Leave requests exported to:\n{path}")
        except Exception as e:
            # print(f"DEBUG: Error exporting to CSV: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to export leave requests: {str(e)}")

    def setup_submit_request_tab(self):
        """Set up the Submit Leave Request tab for admins"""
        submit_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("👨‍💼 Submit Leave Request (Admin)")
        title_label
        submit_layout.addWidget(title_label)
        
        # Create scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create content widget
        content_widget = QWidget()
        form_layout = QVBoxLayout(content_widget)
        
        # Employee selection section
        employee_group = QGroupBox("👤 Employee Selection")
        employee_group
        employee_form_layout = QFormLayout()
        
        self.admin_employee_combo = QComboBox()
        self.admin_employee_combo.setEditable(True)
        self.admin_employee_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.admin_employee_combo.setPlaceholderText("Select or search employee...")
        employee_form_layout.addRow(QLabel("Employee:"), self.admin_employee_combo)
        
        employee_group.setLayout(employee_form_layout)
        form_layout.addWidget(employee_group)
        
        # Add leave balance display section for selected employee
        balance_group = QGroupBox("📊 Employee Leave Balance")
        balance_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                padding-top: 15px;
                margin-top: 10px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        balance_layout = QVBoxLayout()
        balance_layout.setContentsMargins(16, 16, 16, 16)
        
        # Labels for balance information
        self.admin_annual_balance_label = QLabel("Annual Leave: Select an employee to view balance")
        self.admin_annual_balance_label.setStyleSheet("font-size: 14px; color: #2e7d32; margin: 5px 0;")
        
        self.admin_sick_balance_label = QLabel("Sick Leave: Select an employee to view balance")
        self.admin_sick_balance_label.setStyleSheet("font-size: 14px; color: #d32f2f; margin: 5px 0;")
        
        self.admin_refresh_balance_btn = QPushButton("🔄 Refresh Balance")
        self.admin_refresh_balance_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.admin_refresh_balance_btn.clicked.connect(self.load_admin_leave_balances)
        
        balance_layout.addWidget(self.admin_annual_balance_label)
        balance_layout.addWidget(self.admin_sick_balance_label)
        balance_layout.addWidget(self.admin_refresh_balance_btn)
        balance_group.setLayout(balance_layout)
        form_layout.addWidget(balance_group)
        
        # Connect employee selection to balance loading 
        self.admin_employee_combo.currentIndexChanged.connect(self.load_admin_leave_balances_simple)
        # Also connect to activated signal for when user selects from dropdown after typing
        self.admin_employee_combo.activated.connect(self.load_admin_leave_balances_simple)
        
        # Leave request details section
        request_group = QGroupBox("📝 Leave Request Details")
        request_group
        request_form_layout = QFormLayout()
        
        self.admin_leave_type = QComboBox()
        self.admin_leave_type.addItems(["Sick", "Hospitalization", "Annual", "Emergency", "Unpaid", "Others"])
        self.admin_leave_type.currentTextChanged.connect(self.on_admin_leave_type_changed)

        # State selector for the leave request (for holiday/deduction rules)
        self.admin_state_combo = QComboBox()
        self.admin_state_combo.addItems([
            "All Malaysia", "JOHORE", "KEDAH", "KELANTAN", "MELAKA", "NEGERI SEMBILAN",
            "PAHANG", "PERAK", "PERLIS", "PULAU PINANG", "SELANGOR", "TERENGGANU",
            "KUALA LUMPUR", "PUTRAJAYA", "LABUAN", "SABAH", "SARAWAK"
        ])
        
        # Half-day leave controls for admin
        self.admin_half_day_checkbox = QCheckBox("Half Day Leave (counts as 0.5 day)")
        self.admin_half_day_checkbox.setToolTip("Check this to mark the request as a half-day. The system will count it as 0.5 day.")
        self.admin_half_day_checkbox.toggled.connect(self.on_admin_half_day_toggled)

        self.admin_half_day_period = QComboBox()
        self.admin_half_day_period.addItems(["Morning (8:00 AM - 1:00 PM)", "Afternoon (1:00 PM - 6:00 PM)"])
        # Make the admin period combobox visible/enabled by default to improve discoverability
        self.admin_half_day_period.setEnabled(True)
        self.admin_half_day_period.setToolTip("Select Morning or Afternoon for half-day requests.")

        self.admin_leave_title = QLineEdit()
        self.admin_leave_title.setPlaceholderText("Enter a brief title for the leave request...")        # Date selection with number input option for admin
        self.admin_start_date = QDateEdit()
        self.admin_start_date.setCalendarPopup(True)
        self.admin_start_date.setDate(QDate.currentDate())
        self.admin_start_date.dateChanged.connect(self.validate_admin_start_date)

        # Add number input for leave duration (supports fractional when half-day)
        self.admin_leave_duration_input = QDoubleSpinBox()
        self.admin_leave_duration_input.setDecimals(1)
        self.admin_leave_duration_input.setSingleStep(0.5)
        self.admin_leave_duration_input.setMinimum(1.0)
        self.admin_leave_duration_input.setMaximum(10000.0)
        self.admin_leave_duration_input.setValue(1.0)
        self.admin_leave_duration_input.setSuffix(" working days")
        self.admin_leave_duration_input.valueChanged.connect(self.update_admin_dates_from_duration)

        self.admin_end_date = QDateEdit()
        self.admin_end_date.setCalendarPopup(True)
        self.admin_end_date.setDate(QDate.currentDate())
        self.admin_end_date.dateChanged.connect(self.validate_admin_end_date)

        request_form_layout.addRow(QLabel("Leave Type:"), self.admin_leave_type)
        request_form_layout.addRow(QLabel("State (for holiday rules):"), self.admin_state_combo)

        # Admin half-day controls
        admin_half_day_layout = QHBoxLayout()
        admin_half_day_layout.addWidget(self.admin_half_day_checkbox)
        admin_half_day_layout.addWidget(QLabel("Period:"))
        admin_half_day_layout.addWidget(self.admin_half_day_period)
        admin_half_day_layout.addStretch()
        
        admin_half_day_widget = QWidget()
        admin_half_day_widget.setLayout(admin_half_day_layout)
        request_form_layout.addRow(admin_half_day_widget)
        
        request_form_layout.addRow(QLabel("Leave Title:"), self.admin_leave_title)
        
        # Add sick leave information label for admin
        self.admin_sick_leave_info = QLabel()
        self.admin_sick_leave_info.setWordWrap(True)
        self.admin_sick_leave_info.hide()
        request_form_layout.addRow(self.admin_sick_leave_info)
        
        # Create admin date layout
        # First row: Leave duration input
        admin_duration_layout = QHBoxLayout()
        admin_duration_layout.addWidget(QLabel("Leave duration:"))
        admin_duration_layout.addWidget(self.admin_leave_duration_input)
        admin_duration_layout.addWidget(QLabel("(excludes weekends & holidays)"))
        admin_duration_layout.addStretch()
        
        admin_duration_widget = QWidget()
        admin_duration_widget.setLayout(admin_duration_layout)
        request_form_layout.addRow(admin_duration_widget)
        
        # Second row: Date pickers
        admin_dates_layout = QHBoxLayout()
        admin_dates_layout.addWidget(QLabel("Or select dates:"))
        admin_dates_layout.addWidget(QLabel("Start:"))
        admin_dates_layout.addWidget(self.admin_start_date)
        admin_dates_layout.addWidget(QLabel("End:"))
        admin_dates_layout.addWidget(self.admin_end_date)
        # Live display of working days between selected dates
        self.admin_date_days_label = QLabel("Working days: 1 (excludes weekends & holidays)")
        self.admin_date_days_label.setObjectName("adminDateDaysLabel")
        self.admin_date_days_label.setStyleSheet("color: #555;")
        admin_dates_layout.addWidget(self.admin_date_days_label)
        admin_dates_layout.addStretch()
        
        admin_dates_widget = QWidget()
        admin_dates_widget.setLayout(admin_dates_layout)
        request_form_layout.addRow(admin_dates_widget)
        
        request_group.setLayout(request_form_layout)
        form_layout.addWidget(request_group)
        
        # Document upload section
        doc_group = QGroupBox("📎 Supporting Documents")
        doc_group
        doc_layout = QHBoxLayout()
        
        self.admin_upload_btn = QPushButton("Upload Document")
        self.admin_upload_btn
        self.admin_upload_btn.clicked.connect(self.admin_upload_document)
        
        self.admin_remove_doc_btn = QPushButton("Remove")
        self.admin_remove_doc_btn
        self.admin_remove_doc_btn.clicked.connect(self.admin_remove_document)
        
        doc_layout.addWidget(self.admin_upload_btn)
        doc_layout.addWidget(self.admin_remove_doc_btn)
        doc_layout.addStretch()
        
        doc_group.setLayout(doc_layout)
        form_layout.addWidget(doc_group)
        
        # Submit button
        self.admin_submit_btn = QPushButton("Submit Request for Employee")
        self.admin_submit_btn
        self.admin_submit_btn.clicked.connect(self.admin_submit_request)
        form_layout.addWidget(self.admin_submit_btn)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        submit_layout.addWidget(scroll_area)
        
        self.submit_request_tab.setLayout(submit_layout)

        # Wire up live updates for working days label
        try:
            self.admin_start_date.dateChanged.connect(lambda _: self.on_admin_dates_changed_update_duration())
            self.admin_end_date.dateChanged.connect(lambda _: self.on_admin_dates_changed_update_duration())
            self.admin_state_combo.currentTextChanged.connect(lambda _: self.on_admin_dates_changed_update_duration())
        except Exception:
            pass
        
        # Load employees for the combo box
        self.load_employees_for_admin()
        
        # Initialize admin document URL
        self.admin_document_url = None
        
        # Initialize dates based on default duration
        self.update_admin_dates_from_duration(1)

    def update_admin_date_days_label(self, precomputed_days: int = None):
        """Update the inline label showing working days for admin start/end selection."""
        try:
            start_qd = self.admin_start_date.date()
            end_qd = self.admin_end_date.date()
            if end_qd < start_qd:
                self.admin_date_days_label.setText("Working days: -")
                return
            # Half-day override
            if hasattr(self, 'admin_half_day_checkbox') and self.admin_half_day_checkbox.isChecked():
                self.admin_date_days_label.setText("Working days: 0.5 (half-day)")
                return

            if precomputed_days is not None:
                days = precomputed_days
            else:
                state = None
                try:
                    st = self.admin_state_combo.currentText()
                    if st and st.strip().lower() != 'all malaysia':
                        state = st
                except Exception:
                    state = None
                start = start_qd.toPyDate().isoformat()
                end = end_qd.toPyDate().isoformat()
                days = calculate_working_days(start, end, state=state)
            self.admin_date_days_label.setText(f"Working days: {int(round(days))} (excludes weekends & holidays)")
        except Exception:
            try:
                self.admin_date_days_label.setText("")
            except Exception:
                pass

    def on_admin_dates_changed_update_duration(self):
        """When admin changes dates or state, recompute duration and update label."""
        try:
            # If half-day is selected, do not override the user's fractional input; just update label
            if hasattr(self, 'admin_half_day_checkbox') and self.admin_half_day_checkbox.isChecked():
                self.update_admin_date_days_label(precomputed_days=0.5)
                return
            start = self.admin_start_date.date().toPyDate().isoformat()
            end = self.admin_end_date.date().toPyDate().isoformat()
            state = None
            try:
                st = self.admin_state_combo.currentText()
                if st and st.strip().lower() != 'all malaysia':
                    state = st
            except Exception:
                state = None
            computed = calculate_working_days(start, end, state=state)
            self.admin_leave_duration_input.blockSignals(True)
            self.admin_leave_duration_input.setValue(float(int(round(computed))))
            self.admin_leave_duration_input.blockSignals(False)
            self.update_admin_date_days_label(precomputed_days=computed)
        except Exception:
            try:
                start_dt = self.admin_start_date.date().toPyDate()
                end_dt = self.admin_end_date.date().toPyDate()
                days = (end_dt - start_dt).days + 1
            except Exception:
                days = 1
            self.admin_leave_duration_input.blockSignals(True)
            self.admin_leave_duration_input.setValue(float(days))
            self.admin_leave_duration_input.blockSignals(False)
            self.update_admin_date_days_label(precomputed_days=days)

    def setup_leave_balance_tab(self):
        """Set up the Leave Balance Management tab"""
        leave_balance_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🏥 Annual Leave Balance Management")
        title_label
        leave_balance_layout.addWidget(title_label)
        
        # Controls section
        controls_group = QGroupBox("Leave Balance Controls")
        controls_layout = QHBoxLayout()
        
        # Employee filter
        self.employee_filter = QLineEdit()
        self.employee_filter.setPlaceholderText("Search employee by email or name...")
        self.employee_filter.textChanged.connect(self.filter_leave_balances)
        
        # Year selector
        self.year_selector = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 3):
            self.year_selector.addItem(str(year))
        self.year_selector.setCurrentText(str(current_year))
        self.year_selector.currentTextChanged.connect(self.load_leave_balances)
        
        # Refresh button
        self.refresh_balance_btn = QPushButton("Refresh")
        self.refresh_balance_btn
        self.refresh_balance_btn.clicked.connect(self.load_leave_balances)
        
        # Add controls to layout
        controls_layout.addWidget(QLabel("Employee:"))
        controls_layout.addWidget(self.employee_filter)
        controls_layout.addWidget(QLabel("Year:"))
        controls_layout.addWidget(self.year_selector)
        controls_layout.addWidget(self.refresh_balance_btn)
        controls_layout.addStretch()
        
        controls_group.setLayout(controls_layout)
        leave_balance_layout.addWidget(controls_group)
        
        # Leave Balance Table
        self.leave_balance_table = QTableWidget()
        self.leave_balance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.leave_balance_table
        
        # Set table headers
        headers = [
            "Employee Email", "Employee Name", "Department", "Employment Type", "Years of Service",
            "Annual Entitlement", "Used This Year", "Remaining Balance", 
            "Carried Forward", "Total Available", "Actions"
        ]
        self.leave_balance_table.setColumnCount(len(headers))
        self.leave_balance_table.setHorizontalHeaderLabels(headers)
        
        # Enable sorting
        self.leave_balance_table.setSortingEnabled(True)
        
        # Set minimum row height for better readability and button fit
        self.leave_balance_table.verticalHeader().setDefaultSectionSize(55)  # Increased for button fit
        self.leave_balance_table.verticalHeader().setVisible(False)
        
        # Configure column widths for better layout
        header = self.leave_balance_table.horizontalHeader()
        
        # Set specific column widths
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Department
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Employment Type
        header.setSectionResizeMode(4, QHeaderView.Fixed)            # Years of Service
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # Annual Entitlement
        header.setSectionResizeMode(6, QHeaderView.Fixed)            # Used This Year
        header.setSectionResizeMode(7, QHeaderView.Fixed)            # Remaining Balance
        header.setSectionResizeMode(8, QHeaderView.Fixed)            # Carried Forward
        header.setSectionResizeMode(9, QHeaderView.Fixed)            # Total Available
        header.setSectionResizeMode(10, QHeaderView.Fixed)           # Actions
        
        # Set fixed widths for numeric columns
        self.leave_balance_table.setColumnWidth(4, 100)  # Years of Service
        self.leave_balance_table.setColumnWidth(5, 120)  # Annual Entitlement
        self.leave_balance_table.setColumnWidth(6, 100)  # Used This Year
        self.leave_balance_table.setColumnWidth(7, 120)  # Remaining Balance
        self.leave_balance_table.setColumnWidth(8, 110)  # Carried Forward
        self.leave_balance_table.setColumnWidth(9, 110)  # Total Available
        self.leave_balance_table.setColumnWidth(10, 100)  # Actions - increased width
        
        leave_balance_layout.addWidget(self.leave_balance_table)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        
        self.adjust_balance_btn = QPushButton("Adjust Balance")
        self.adjust_balance_btn
        self.adjust_balance_btn.clicked.connect(self.adjust_leave_balance)
        
        self.carry_forward_btn = QPushButton("Process Year-End Carry Forward")
        self.carry_forward_btn
        self.carry_forward_btn.clicked.connect(self.process_year_end_carry_forward)
        # Quick set-all carried forward control
        self.set_all_cf_spin = QSpinBox()
        self.set_all_cf_spin.setRange(0, 30)
        self.set_all_cf_spin.setValue(0)
        self.set_all_cf_spin.setSuffix(" days")
        self.set_all_cf_btn = QPushButton("Set Carried Forward for All")
        self.set_all_cf_btn.clicked.connect(self.set_carried_forward_for_all_dialog)
        
        self.export_balance_btn = QPushButton("Export Balances")
        self.export_balance_btn
        self.export_balance_btn.clicked.connect(self.export_leave_balances)
        
        # Add policy configuration button
        self.policy_config_btn = QPushButton("Leave Policies")
        self.policy_config_btn
        self.policy_config_btn.clicked.connect(self.configure_leave_policies)
        
        # Add Malaysian Employment Act info button for annual leave
        self.annual_act_info_btn = QPushButton("Employment Act 1955 - Annual Leave")
        self.annual_act_info_btn
        self.annual_act_info_btn.clicked.connect(self.show_annual_leave_employment_act_info)
        
        actions_layout.addWidget(self.adjust_balance_btn)
        actions_layout.addWidget(self.carry_forward_btn)
        actions_layout.addWidget(QLabel("Set CF for all:"))
        actions_layout.addWidget(self.set_all_cf_spin)
        actions_layout.addWidget(self.set_all_cf_btn)
        actions_layout.addWidget(self.export_balance_btn)
        actions_layout.addWidget(self.policy_config_btn)
        actions_layout.addWidget(self.annual_act_info_btn)
        actions_layout.addStretch()
        
        actions_group.setLayout(actions_layout)
        leave_balance_layout.addWidget(actions_group)
        
        self.leave_balance_tab.setLayout(leave_balance_layout)
        
        # Load initial data
        self.load_leave_balances()
    
    def setup_sick_leave_balance_tab(self):
        """Set up the Sick Leave Balance Management tab"""
        sick_leave_balance_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("🏥 Sick Leave Balance Management")
        title_label
        sick_leave_balance_layout.addWidget(title_label)
        
        # Controls section
        controls_group = QGroupBox("Sick Leave Balance Controls")
        controls_layout = QHBoxLayout()
        
        # Employee filter
        self.sick_employee_filter = QLineEdit()
        self.sick_employee_filter.setPlaceholderText("Search employee by email or name...")
        self.sick_employee_filter.textChanged.connect(self.filter_sick_leave_balances)
        
        # Year selector
        self.sick_year_selector = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 3):
            self.sick_year_selector.addItem(str(year))
        self.sick_year_selector.setCurrentText(str(current_year))
        self.sick_year_selector.currentTextChanged.connect(self.load_sick_leave_balances)
        
        # Refresh button
        self.refresh_sick_balance_btn = QPushButton("Refresh")
        self.refresh_sick_balance_btn
        self.refresh_sick_balance_btn.clicked.connect(self.load_sick_leave_balances)
        
        # Add controls to layout
        controls_layout.addWidget(QLabel("Employee:"))
        controls_layout.addWidget(self.sick_employee_filter)
        controls_layout.addWidget(QLabel("Year:"))
        controls_layout.addWidget(self.sick_year_selector)
        controls_layout.addWidget(self.refresh_sick_balance_btn)
        controls_layout.addStretch()
        
        controls_group.setLayout(controls_layout)
        sick_leave_balance_layout.addWidget(controls_group)
        
        # Sick Leave Balance Table
        self.sick_leave_balance_table = QTableWidget()
        self.sick_leave_balance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.sick_leave_balance_table
        
        # Set table headers
        headers = [
            "Employee Email", "Employee Name", "Department", "Employment Type", "Years of Service",
            "Sick Days Entitlement", "Used Sick Days", "Remaining Sick Days", 
            "Hospitalization Entitlement", "Used Hospitalization", "Remaining Hospitalization", "Actions"
        ]
        self.sick_leave_balance_table.setColumnCount(len(headers))
        self.sick_leave_balance_table.setHorizontalHeaderLabels(headers)
        
        # Enable sorting
        self.sick_leave_balance_table.setSortingEnabled(True)
        
        # Set minimum row height for better readability and button fit
        self.sick_leave_balance_table.verticalHeader().setDefaultSectionSize(55)
        self.sick_leave_balance_table.verticalHeader().setVisible(False)
        
        # Configure column widths for better layout
        header = self.sick_leave_balance_table.horizontalHeader()
        
        # Set specific column widths
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Department
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Employment Type
        header.setSectionResizeMode(4, QHeaderView.Fixed)            # Years of Service
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # Sick Days Entitlement
        header.setSectionResizeMode(6, QHeaderView.Fixed)            # Used Sick Days
        header.setSectionResizeMode(7, QHeaderView.Fixed)            # Remaining Sick Days
        header.setSectionResizeMode(8, QHeaderView.Fixed)            # Hospitalization Entitlement
        header.setSectionResizeMode(9, QHeaderView.Fixed)            # Remaining Hospitalization
        header.setSectionResizeMode(10, QHeaderView.Fixed)           # Actions
        
        # Set fixed widths for numeric columns
        self.sick_leave_balance_table.setColumnWidth(4, 100)  # Years of Service
        self.sick_leave_balance_table.setColumnWidth(5, 120)  # Sick Days Entitlement
        self.sick_leave_balance_table.setColumnWidth(6, 100)  # Used Sick Days
        self.sick_leave_balance_table.setColumnWidth(7, 120)  # Remaining Sick Days
        self.sick_leave_balance_table.setColumnWidth(8, 140)  # Hospitalization Entitlement
        self.sick_leave_balance_table.setColumnWidth(9, 140)  # Remaining Hospitalization
        self.sick_leave_balance_table.setColumnWidth(10, 100) # Actions
        
        sick_leave_balance_layout.addWidget(self.sick_leave_balance_table)
        
        # Action buttons
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        
        self.export_sick_balance_btn = QPushButton("Export Sick Leave Balances")
        self.export_sick_balance_btn
        self.export_sick_balance_btn.clicked.connect(self.export_sick_leave_balances)
        
        # Add Malaysian Employment Act info button
        self.act_info_btn = QPushButton("Employment Act 1955 Info")
        self.act_info_btn
        self.act_info_btn.clicked.connect(self.show_employment_act_info)
        
        actions_layout.addWidget(self.export_sick_balance_btn)
        actions_layout.addWidget(self.act_info_btn)
        actions_layout.addStretch()
        
        actions_group.setLayout(actions_layout)
        sick_leave_balance_layout.addWidget(actions_group)
        
        self.sick_leave_balance_tab.setLayout(sick_leave_balance_layout)
        
        # Load initial data
        self.load_sick_leave_balances()

    def load_leave_balances(self):
        """Load leave balance data from database"""
        try:
            from services.supabase_service import get_employee_leave_balances
            
            # Clear existing data
            self.leave_balance_table.setRowCount(0)
            
            # Get selected year
            selected_year = int(self.year_selector.currentText())
            
            # Fetch leave balance data from database
            leave_balances = get_employee_leave_balances(selected_year)
            
            if not leave_balances:
                # Show message if no data found
                self.leave_balance_table.setRowCount(1)
                no_data_item = QTableWidgetItem("No leave balance data found for the selected year")
                no_data_item.setTextAlignment(Qt.AlignCenter)
                self.leave_balance_table.setItem(0, 0, no_data_item)
                # Span across all columns
                self.leave_balance_table.setSpan(0, 0, 1, self.leave_balance_table.columnCount())
                return
            
            self.leave_balance_table.setRowCount(len(leave_balances))
            
            for row, balance_data in enumerate(leave_balances):
                # Show employment type with special indicator for interns
                employment_display = balance_data.get("employment_type", "Full-time")
                if balance_data.get("is_intern", False):
                    employment_display = "🎓 Intern"
                
                # Prepare row data with better formatting
                from core.employee_service import format_years

                row_data = [
                    balance_data.get("email", ""),
                    balance_data.get("full_name", ""),
                    balance_data.get("department", ""),
                    employment_display,
                    format_years(balance_data.get('years_of_service', 0.0)) or f"{balance_data.get('years_of_service', 0):.1f}",
                    f"{balance_data.get('annual_entitlement', 0)} days",
                    f"{balance_data.get('used_days', 0)} days",
                    f"{balance_data.get('remaining_days', 0)} days",
                    f"{balance_data.get('carried_forward', 0)} days",
                    f"{balance_data.get('total_available', 0)} days"
                ]
                
                for col, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Color coding for better visual feedback
                    if col == 7:  # Remaining Balance column
                        remaining = balance_data.get('remaining_days', 0)
                        if remaining <= 2:
                            item.setBackground(QColor(255, 235, 238))  # Light red
                        elif remaining <= 5:
                            item.setBackground(QColor(255, 248, 225))  # Light yellow
                        else:
                            item.setBackground(QColor(232, 245, 233))  # Light green
                    
                    self.leave_balance_table.setItem(row, col, item)
                
                # Add edit button with proper sizing for the column
                action_btn = QPushButton("Edit")
                action_btn.resize(90, 35)  # Adjusted to fit 100px column width
                action_btn
                action_btn.clicked.connect(lambda checked, r=row: self.edit_employee_balance(r))
                
                # Set the button directly in the cell
                self.leave_balance_table.setCellWidget(row, len(row_data), action_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading leave balances: {str(e)}")
            # Fallback to show error in table
            self.leave_balance_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error loading data: {str(e)}")
            error_item.setTextAlignment(Qt.AlignCenter)
            self.leave_balance_table.setItem(0, 0, error_item)
            self.leave_balance_table.setSpan(0, 0, 1, self.leave_balance_table.columnCount())

    def load_sick_leave_balances(self):
        """Load sick leave balance data from database"""
        try:
            from services.supabase_service import get_employee_sick_leave_balances
            
            # Clear existing data
            self.sick_leave_balance_table.setRowCount(0)
            
            # Get selected year
            selected_year = int(self.sick_year_selector.currentText())
            
            # Fetch sick leave balance data from database
            sick_leave_balances = get_employee_sick_leave_balances(selected_year)
            
            if not sick_leave_balances:
                # Show message if no data found
                self.sick_leave_balance_table.setRowCount(1)
                no_data_item = QTableWidgetItem("No sick leave balance data found for the selected year")
                no_data_item.setTextAlignment(Qt.AlignCenter)
                self.sick_leave_balance_table.setItem(0, 0, no_data_item)
                # Span across all columns
                self.sick_leave_balance_table.setSpan(0, 0, 1, self.sick_leave_balance_table.columnCount())
                return
            
            self.sick_leave_balance_table.setRowCount(len(sick_leave_balances))
            
            for row, balance_data in enumerate(sick_leave_balances):
                # Show employment type with special indicator for interns
                employment_display = balance_data.get("employment_type", "Full-time")
                
                # Prepare row data with better formatting
                from core.employee_service import format_years

                row_data = [
                    balance_data.get("email", ""),
                    balance_data.get("full_name", ""),
                    balance_data.get("department", ""),
                    employment_display,
                    format_years(balance_data.get('years_of_service', 0.0)) or f"{balance_data.get('years_of_service', 0):.1f}",
                    f"{balance_data.get('sick_days_entitlement', 0)} days",
                    f"{balance_data.get('used_sick_days', 0)} days",
                    f"{balance_data.get('remaining_sick_days', 0)} days",
                    f"{balance_data.get('hospitalization_days_entitlement', 0)} days",
                    f"{balance_data.get('used_hospitalization_days', 0)} days",
                    f"{balance_data.get('remaining_hospitalization_days', 0)} days"
                ]
                
                for col, value in enumerate(row_data):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # Color coding for better visual feedback
                    if col == 7:  # Remaining Sick Days column
                        remaining = balance_data.get('remaining_sick_days', 0)
                        if remaining <= 2:
                            item.setBackground(QColor(255, 235, 238))  # Light red
                        elif remaining <= 5:
                            item.setBackground(QColor(255, 248, 225))  # Light yellow
                        else:
                            item.setBackground(QColor(232, 245, 233))  # Light green
                    elif col == 10:  # Remaining Hospitalization Days column (now column 10)
                        remaining_hosp = balance_data.get('remaining_hospitalization_days', 0)
                        if remaining_hosp <= 10:
                            item.setBackground(QColor(255, 235, 238))  # Light red
                        elif remaining_hosp <= 30:
                            item.setBackground(QColor(255, 248, 225))  # Light yellow
                        else:
                            item.setBackground(QColor(232, 245, 233))  # Light green
                    
                    self.sick_leave_balance_table.setItem(row, col, item)
                
                # Add view details button
                action_btn = QPushButton("View")
                action_btn.resize(90, 35)
                action_btn
                action_btn.clicked.connect(lambda checked, r=row: self.view_sick_leave_details(r))
                
                self.sick_leave_balance_table.setCellWidget(row, len(row_data), action_btn)
            
            # Show data count
            self.sick_leave_balance_table.resizeColumnsToContents()
            
        except Exception as e:
            # print(f"DEBUG: Error loading sick leave balances: {str(e)}")
            self.sick_leave_balance_table.setRowCount(1)
            error_item = QTableWidgetItem(f"Error loading data: {str(e)}")
            error_item.setTextAlignment(Qt.AlignCenter)
            self.sick_leave_balance_table.setItem(0, 0, error_item)
            self.sick_leave_balance_table.setSpan(0, 0, 1, self.sick_leave_balance_table.columnCount())

    def filter_sick_leave_balances(self):
        """Filter sick leave balances based on search text"""
        search_text = self.sick_employee_filter.text().lower()
        
        for row in range(self.sick_leave_balance_table.rowCount()):
            show_row = False
            
            # Check email (column 0) and name (column 1)
            for col in [0, 1]:
                item = self.sick_leave_balance_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            
            self.sick_leave_balance_table.setRowHidden(row, not show_row)

    def view_sick_leave_details(self, row):
        """View detailed sick leave information for an employee"""
        try:
            email_item = self.sick_leave_balance_table.item(row, 0)
            name_item = self.sick_leave_balance_table.item(row, 1)
            # Prefer numeric value from balance data (stored earlier in `sick_leave_balances`) rather than parsing the table cell
            years_item = self.sick_leave_balance_table.item(row, 4)
            balance_row = None
            try:
                from services.supabase_service import get_employee_sick_leave_balances
                selected_year = int(self.sick_year_selector.currentText())
                # try to fetch the specific balance for this row's email
                email_text = email_item.text() if email_item else None
                balances = get_employee_sick_leave_balances(selected_year)
                if balances and email_text:
                    for b in balances:
                        if b.get('email') == email_text:
                            balance_row = b
                            break
            except Exception:
                balance_row = None

            if not email_item or not name_item:
                return

            employee_email = email_item.text()
            employee_name = name_item.text()
            if balance_row:
                years_of_service = balance_row.get('years_of_service', 0.0)
            else:
                # fallback: try to parse numeric from cell (strip words)
                try:
                    years_of_service = float(re.sub(r"[^0-9\.]+", "", years_item.text()))
                except Exception:
                    years_of_service = 0.0
            
            # Create info dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Sick Leave Details - {employee_name}")
            dialog.resize(500, 400)
            dialog
            
            layout = QVBoxLayout()
            
            # Employee info
            info_text = f"""
<h3>🏥 Sick Leave Information</h3>
<p><b>Employee:</b> {employee_name} ({employee_email})</p>
<p><b>Years of Service:</b> {years_of_service:.1f} years</p>

<h4>Malaysian Employment Act 1955 Entitlements:</h4>
<ul>
<li><b>Sick Leave:</b> {self.sick_leave_balance_table.item(row, 5).text()}</li>
<li><b>Hospitalization Leave:</b> {self.sick_leave_balance_table.item(row, 8).text()}</li>
</ul>

<h4>Current Year Usage:</h4>
<ul>
<li><b>Used Sick Days:</b> {self.sick_leave_balance_table.item(row, 6).text()}</li>
<li><b>Remaining Sick Days:</b> {self.sick_leave_balance_table.item(row, 7).text()}</li>
<li><b>Remaining Hospitalization Days:</b> {self.sick_leave_balance_table.item(row, 9).text()}</li>
</ul>

<h4>Legal Requirements:</h4>
<ul>
<li>Medical certificate required for sick leave > 1 day</li>
<li>Hospitalization leave requires hospital documentation</li>
<li>No carry forward of unused sick leave to next year</li>
</ul>
            """
            
            text_widget = QTextEdit()
            text_widget.setHtml(info_text)
            text_widget.setReadOnly(True)
            layout.addWidget(text_widget)
            
            # Close button
            button_layout = QHBoxLayout()
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
            layout.addLayout(button_layout)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error viewing sick leave details: {str(e)}")

    def export_sick_leave_balances(self):
        """Export sick leave balances to CSV"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Sick Leave Balances", 
                f"sick_leave_balances_{self.sick_year_selector.currentText()}.csv",
                "CSV Files (*.csv)"
            )
            
            if file_path:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    headers = []
                    for col in range(self.sick_leave_balance_table.columnCount() - 1):  # Exclude Actions column
                        headers.append(self.sick_leave_balance_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.sick_leave_balance_table.rowCount()):
                        if not self.sick_leave_balance_table.isRowHidden(row):
                            row_data = []
                            for col in range(self.sick_leave_balance_table.columnCount() - 1):  # Exclude Actions column
                                item = self.sick_leave_balance_table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                
                QMessageBox.information(self, "Success", f"Sick leave balances exported to {file_path}")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export sick leave balances: {str(e)}")

    def show_employment_act_info(self):
        """Show Malaysian Employment Act 1955 information"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Malaysian Employment Act 1955 - Sick Leave")
        dialog.resize(600, 500)

        layout = QVBoxLayout()
        
        info_text = """
<h2>🇲🇾 Malaysian Employment Act 1955</h2>
<h3>Sick Leave Entitlements</h3>

<h4>Regular Sick Leave:</h4>
<ul>
<li><b>Less than 2 years service:</b> 14 days per year</li>
<li><b>2-5 years service:</b> 18 days per year</li>
<li><b>More than 5 years service:</b> 22 days per year</li>
</ul>

<h4>Hospitalization Leave:</h4>
<ul>
<li><b>All employees:</b> 60 days per year</li>
<li>Requires hospital documentation</li>
<li>Separate from regular sick leave</li>
</ul>

<h4>Medical Certificate Requirements:</h4>
<ul>
<li>Required for sick leave exceeding 1 consecutive day</li>
<li>Must be from registered medical practitioner</li>
<li>Hospital documentation required for hospitalization leave</li>
</ul>

<h4>Important Notes:</h4>
<ul>
<li>Unused sick leave does <b>NOT</b> carry forward to next year</li>
<li>Sick leave is calculated per calendar year</li>
<li>Pro-rated entitlement for employees joining mid-year</li>
<li>Medical certificates must be submitted within reasonable time</li>
</ul>

<p><i>This system automatically calculates entitlements based on years of service and enforces Malaysian employment law requirements.</i></p>
        """
        
        text_widget = QTextEdit()
        text_widget.setHtml(info_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def show_annual_leave_employment_act_info(self):
        """Show Malaysian Employment Act 1955 information for Annual Leave"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Malaysian Employment Act 1955 - Annual Leave")
        dialog.resize(600, 500)

        layout = QVBoxLayout()
        
        info_text = """
<h2>🇲🇾 Malaysian Employment Act 1955</h2>
<h3>Annual Leave Entitlements</h3>

<h4>Minimum Annual Leave:</h4>
<ul>
<li><b>Less than 2 years service:</b> 8 days per year</li>
<li><b>2-5 years service:</b> 12 days per year</li>
<li><b>More than 5 years service:</b> 16 days per year</li>
</ul>

<h4>Important Provisions:</h4>
<ul>
<li><b>Pro-rated entitlement</b> for employees joining mid-year</li>
<li><b>Minimum 3 consecutive days</b> must be granted if requested</li>
<li><b>Notice period:</b> Employee should give reasonable notice</li>
<li><b>Employer scheduling:</b> Employer may determine timing subject to business needs</li>
</ul>

<h4>Leave Carry Forward:</h4>
<ul>
<li>Unused annual leave may be carried forward to next year</li>
<li>Maximum carry forward typically limited by company policy</li>
<li>Must be taken within specified period (usually 12 months)</li>
<li>Payment in lieu allowed only upon termination</li>
</ul>

<h4>Public Holidays:</h4>
<ul>
<li>11 gazetted public holidays per year minimum</li>
<li>Public holidays are separate from annual leave entitlement</li>
<li>If public holiday falls on rest day, next working day becomes holiday</li>
</ul>

<h4>Documentation Requirements:</h4>
<ul>
<li>Leave application should be submitted in advance</li>
<li>Employer approval required</li>
<li>Proper records must be maintained</li>
<li>Leave balance tracking essential for compliance</li>
</ul>

<h4>Special Considerations:</h4>
<ul>
<li><b>Maternity Leave:</b> 98 days (separate entitlement)</li>
<li><b>Paternity Leave:</b> 7 days (separate entitlement)</li>
<li><b>Study Leave:</b> May be provided at employer's discretion</li>
<li><b>Emergency Leave:</b> Compassionate leave provisions</li>
</ul>

<p><i>This system automatically calculates minimum entitlements based on Malaysian Employment Act 1955. Companies may provide more generous leave policies above the statutory minimums.</i></p>
        """
        
        text_widget = QTextEdit()
        text_widget.setHtml(info_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def filter_leave_balances(self):
        """Filter leave balances based on search text"""
        search_text = self.employee_filter.text().lower()
        
        for row in range(self.leave_balance_table.rowCount()):
            show_row = False
            
            # Check email (column 0) and name (column 1)
            for col in [0, 1]:
                item = self.leave_balance_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            
            self.leave_balance_table.setRowHidden(row, not show_row)

    def adjust_leave_balance(self):
        """Open dialog to manually adjust leave balance"""
        current_row = self.leave_balance_table.currentRow()
        if current_row >= 0:
            self.edit_employee_balance(current_row)
        else:
            QMessageBox.information(self, "No Selection", "Please select an employee first.")

    def edit_employee_balance(self, row):
        """Edit an individual employee's leave balance"""
        email_item = self.leave_balance_table.item(row, 0)
        name_item = self.leave_balance_table.item(row, 1)
        
        if not email_item or not name_item:
            return
        
        email = email_item.text()
        name = name_item.text()
        
        # Create edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Leave Balance - {name}")
        dialog.setModal(True)
        dialog.resize(400, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Employee info
        info_label = QLabel(f"Employee: {name} ({email})")
        info_label
        layout.addWidget(info_label)
        
        # Current values
        current_group = QGroupBox("Current Values")
        current_layout = QFormLayout()
        
        # Get current values from table
        employment_type = self.leave_balance_table.item(row, 3).text()
        years_service = self.leave_balance_table.item(row, 4).text()
        annual_entitlement = self.leave_balance_table.item(row, 5).text()
        used_days = self.leave_balance_table.item(row, 6).text()
        carried_forward = self.leave_balance_table.item(row, 8).text()
        
        current_layout.addRow("Employment Type:", QLabel(employment_type))
        current_layout.addRow("Years of Service:", QLabel(years_service))
        current_layout.addRow("Annual Entitlement:", QLabel(f"{annual_entitlement} days"))
        current_layout.addRow("Used Days:", QLabel(f"{used_days} days"))
        current_layout.addRow("Carried Forward:", QLabel(f"{carried_forward} days"))
        
        current_group.setLayout(current_layout)
        layout.addWidget(current_group)
        
        # Adjustments
        adjust_group = QGroupBox("Adjustments")
        adjust_layout = QFormLayout()
        
        # Manual adjustments
        entitlement_edit = QSpinBox()
        entitlement_edit.setRange(0, 50)
        # Extract numeric value from text like "16 days"
        try:
            entitlement_value = int(annual_entitlement.split()[0]) if ' ' in annual_entitlement else int(annual_entitlement)
        except (ValueError, IndexError):
            entitlement_value = 0
        entitlement_edit.setValue(entitlement_value)
        
        from PyQt5.QtWidgets import QDoubleSpinBox
        used_edit = QDoubleSpinBox()
        used_edit.setDecimals(1)
        used_edit.setSingleStep(0.5)
        used_edit.setRange(0.0, 1000.0)
        # Extract numeric value from text like "5 days" or "0.5 days"
        try:
            used_value = float(used_days.split()[0]) if ' ' in used_days else float(used_days)
        except (ValueError, IndexError):
            used_value = 0.0
        used_edit.setValue(used_value)
        
        carried_edit = QSpinBox()
        carried_edit.setRange(0, 30)
        # Extract numeric value from text like "3 days"
        try:
            carried_value = int(carried_forward.split()[0]) if ' ' in carried_forward else int(carried_forward)
        except (ValueError, IndexError):
            carried_value = 0
        carried_edit.setValue(carried_value)
        
        notes_edit = QTextEdit()
        notes_edit.setMaximumHeight(80)
        notes_edit.setPlaceholderText("Enter reason for adjustment...")
        
        adjust_layout.addRow("Annual Entitlement:", entitlement_edit)
        adjust_layout.addRow("Used Days:", used_edit)
        adjust_layout.addRow("Carried Forward:", carried_edit)
        adjust_layout.addRow("Notes:", notes_edit)
        
        adjust_group.setLayout(adjust_layout)
        layout.addWidget(adjust_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        cancel_btn = QPushButton("Cancel")
        
        save_btn
        
        cancel_btn
        
        def save_changes():
            try:
                from services.supabase_service import update_employee_leave_balance, supabase
                
                # Get employee ID from email
                employee_response = supabase.table("employees").select("employee_id").eq("email", email).execute()
                if not employee_response.data:
                    QMessageBox.warning(dialog, "Error", "Employee not found in database")
                    return
                
                employee_id = employee_response.data[0]["employee_id"]
                selected_year = int(self.year_selector.currentText())
                
                # Prepare adjustment data
                adjustment_data = {
                    "annual_entitlement": entitlement_edit.value(),
                    "used_days": used_edit.value(),
                    "carried_forward": carried_edit.value(),
                    "adjustment_notes": notes_edit.toPlainText(),
                    "adjusted_by": getattr(self, 'current_admin_email', 'admin'),
                    "adjusted_date": datetime.now().isoformat()
                }
                
                # Update database (employee_id is already a string)
                success = update_employee_leave_balance(employee_id, selected_year, adjustment_data)
                
                if success:
                    QMessageBox.information(dialog, "Success", "Leave balance updated successfully")
                    dialog.accept()
                    self.load_leave_balances()  # Refresh table
                else:
                    QMessageBox.warning(dialog, "Error", "Failed to update leave balance")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error updating leave balance: {str(e)}")
        
        save_btn.clicked.connect(save_changes)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()

    def process_year_end_carry_forward(self):
        """Process year-end carry forward for all employees"""
        reply = QMessageBox.question(self, "Year-End Carry Forward", 
                                   "This will process year-end carry forward for all employees.\n\n"
                                   "This action will:\n"
                                   "• Calculate remaining leave for current year\n"
                                   "• Apply carry-forward policies (max limits, expiry)\n"
                                   "• Reset counters for new year\n"
                                   "• Generate audit trail\n\n"
                                   "Are you sure you want to continue?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                from services.supabase_service import process_year_end_carry_forward
                
                # Get current year
                current_year = int(self.year_selector.currentText())
                
                # Define carry forward rules (Malaysian standard)
                carry_forward_rules = {
                    "max_days": 10,  # Maximum 10 days can be carried forward
                    "expiry_months": 6  # Carried forward days expire after 6 months
                }
                
                # Process carry forward
                success = process_year_end_carry_forward(current_year, carry_forward_rules)
                
                if success:
                    QMessageBox.information(self, "Processing Complete", 
                                          "Year-end carry forward processing completed successfully.\n\n"
                                          "All employees have been processed according to company policy:\n"
                                          "• Maximum 10 days carry forward per employee\n"
                                          "• Carried forward days expire after 6 months\n"
                                          "• Audit trail has been created")
                else:
                    QMessageBox.warning(self, "Processing Failed", 
                                      "Year-end carry forward processing encountered errors.\n"
                                      "Please check the system logs and try again.")
                
                # Refresh the table to show updated balances
                self.load_leave_balances()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error processing year-end carry forward: {str(e)}")

    def set_carried_forward_for_all_dialog(self):
        """Prompt and apply a uniform carried_forward amount to all employees for next year."""
        try:
            days = int(self.set_all_cf_spin.value())
            if days <= 0:
                QMessageBox.information(self, "No-op", "Please choose a positive number of days to set.")
                return

            reply = QMessageBox.question(self, "Set Carried Forward for All",
                                         f"This will set carried_forward = {days} days for all employees for next year.\n\nProceed?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

            # Call service helper
            from services.supabase_service import set_carried_forward_for_all
            current_year = int(self.year_selector.currentText())
            next_year = current_year + 1
            # Map UI applies-to selection to short key the service expects
            applies_to_map = {
                'All employees': None,
                'Full-time employees only': 'Full-time',
                'All except interns': 'exclude_interns'
            }
            sel = self.carry_forward_applies_to.currentText() if hasattr(self, 'carry_forward_applies_to') else 'All employees'
            applies_to = applies_to_map.get(sel, None)
            success = set_carried_forward_for_all(next_year, days, applies_to=applies_to)
            if success:
                QMessageBox.information(self, "Success", f"Set carried_forward={days} for all employees for {next_year}.")
                self.load_leave_balances()
            else:
                QMessageBox.warning(self, "Failed", "Failed to set carried forward for all employees. Check logs.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting carried forward for all: {str(e)}")

    def export_leave_balances(self):
        """Export leave balances to CSV"""
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Leave Balances", 
                f"leave_balances_{datetime.now().strftime('%Y%m%d')}.csv", 
                "CSV files (*.csv)"
            )
            
            if not path:
                return
            
            with open(path, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write headers
                headers = []
                for col in range(self.leave_balance_table.columnCount() - 1):  # Exclude actions column
                    headers.append(self.leave_balance_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.leave_balance_table.rowCount()):
                    if not self.leave_balance_table.isRowHidden(row):
                        line = []
                        for col in range(self.leave_balance_table.columnCount() - 1):  # Exclude actions column
                            item = self.leave_balance_table.item(row, col)
                            line.append(item.text() if item else "")
                        writer.writerow(line)
            
            QMessageBox.information(self, "Exported", f"Leave balances exported to:\n{path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Error exporting leave balances: {str(e)}")

    def configure_leave_policies(self):
        """Open dialog to configure company leave policies"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Company Leave Policies")
        dialog.setModal(True)
        dialog.resize(600, 500)
        
        layout = QVBoxLayout(dialog)
        
        # Title
        title_label = QLabel("⚙️ Company Leave Policy Configuration")
        title_label
        layout.addWidget(title_label)
        
        # Carry Forward Settings
        carry_forward_group = QGroupBox("Annual Leave Carry Forward")
        carry_forward_layout = QFormLayout()
        
        # Enable/Disable carry forward
        self.carry_forward_enabled = QComboBox()
        self.carry_forward_enabled.addItems(["Enabled", "Disabled"])
        
        # Max carry forward days
        self.max_carry_forward = QSpinBox()
        self.max_carry_forward.setRange(0, 30)
        self.max_carry_forward.setValue(10)
        self.max_carry_forward.setSuffix(" days")
        
        # Expiry months
        self.expiry_months = QSpinBox()
        self.expiry_months.setRange(1, 24)
        self.expiry_months.setValue(6)
        self.expiry_months.setSuffix(" months")
        
        # Who can carry forward
        self.carry_forward_applies_to = QComboBox()
        self.carry_forward_applies_to.addItems([
            "All employees",
            "Full-time employees only", 
            "All except interns"
        ])
        
        carry_forward_layout.addRow("Carry Forward:", self.carry_forward_enabled)
        carry_forward_layout.addRow("Maximum Days:", self.max_carry_forward)
        carry_forward_layout.addRow("Expires After:", self.expiry_months)
        carry_forward_layout.addRow("Applies To:", self.carry_forward_applies_to)
        
        carry_forward_group.setLayout(carry_forward_layout)
        layout.addWidget(carry_forward_group)
        
        # Other Settings
        other_group = QGroupBox("Other Leave Settings")
        other_layout = QFormLayout()
        
        # Pro-rate entitlement
        self.pro_rate_entitlement = QComboBox()
        self.pro_rate_entitlement.addItems(["Enabled", "Disabled"])
        
        other_layout.addRow("Pro-rate for Partial Year:", self.pro_rate_entitlement)
        
        other_group.setLayout(other_layout)
        layout.addWidget(other_group)
        
        # Load current policies
        self.load_current_policies()
        
        # Enable/disable controls based on carry forward setting
        def on_carry_forward_changed():
            enabled = self.carry_forward_enabled.currentText() == "Enabled"
            self.max_carry_forward.setEnabled(enabled)
            self.expiry_months.setEnabled(enabled)
            self.carry_forward_applies_to.setEnabled(enabled)
        
        self.carry_forward_enabled.currentTextChanged.connect(on_carry_forward_changed)
        on_carry_forward_changed()  # Initial state
        
        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save Policies")
        cancel_btn = QPushButton("Cancel")
        reset_btn = QPushButton("Reset to Defaults")
        
        save_btn
        
        cancel_btn
        
        reset_btn
        
        def save_policies():
            try:
                from services.supabase_service import update_company_leave_policy
                
                # Map UI values to database values
                carry_forward_value = "true" if self.carry_forward_enabled.currentText() == "Enabled" else "false"
                applies_to_map = {
                    "All employees": "all",
                    "Full-time employees only": "full_time_only",
                    "All except interns": "exclude_interns"
                }
                applies_to_value = applies_to_map[self.carry_forward_applies_to.currentText()]
                pro_rate_value = "true" if self.pro_rate_entitlement.currentText() == "Enabled" else "false"
                
                # Save policies
                policies = [
                    ("carry_forward_enabled", carry_forward_value),
                    ("max_carry_forward_days", str(self.max_carry_forward.value())),
                    ("carry_forward_expiry_months", str(self.expiry_months.value())),
                    ("carry_forward_applies_to", applies_to_value),
                    ("pro_rate_entitlement", pro_rate_value)
                ]
                
                admin_email = getattr(self, 'current_admin_email', 'admin')
                success = True
                
                for policy_name, policy_value in policies:
                    if not update_company_leave_policy(policy_name, policy_value, admin_email):
                        success = False
                        break
                
                if success:
                    QMessageBox.information(dialog, "Success", "Leave policies updated successfully!\n\nChanges will take effect immediately for new balance calculations.")
                    dialog.accept()
                    self.load_leave_balances()  # Refresh the table
                else:
                    QMessageBox.warning(dialog, "Error", "Failed to update some policies")
                    
            except Exception as e:
                QMessageBox.critical(dialog, "Error", f"Error saving policies: {str(e)}")
        
        def reset_to_defaults():
            self.carry_forward_enabled.setCurrentText("Enabled")
            self.max_carry_forward.setValue(10)
            self.expiry_months.setValue(6)
            self.carry_forward_applies_to.setCurrentText("All employees")
            self.pro_rate_entitlement.setCurrentText("Enabled")
        
        save_btn.clicked.connect(save_policies)
        cancel_btn.clicked.connect(dialog.reject)
        reset_btn.clicked.connect(reset_to_defaults)
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
        
        dialog.exec_()
    
    def load_current_policies(self):
        """Load current policy values into the form"""
        try:
            from services.supabase_service import get_company_leave_policy
            
            # Load carry forward settings
            carry_forward_enabled = get_company_leave_policy("carry_forward_enabled", "true")
            self.carry_forward_enabled.setCurrentText("Enabled" if carry_forward_enabled == "true" else "Disabled")
            
            max_days = int(get_company_leave_policy("max_carry_forward_days", "10"))
            self.max_carry_forward.setValue(max_days)
            
            expiry_months = int(get_company_leave_policy("carry_forward_expiry_months", "6"))
            self.expiry_months.setValue(expiry_months)
            
            applies_to = get_company_leave_policy("carry_forward_applies_to", "all")
            applies_to_map = {
                "all": "All employees",
                "full_time_only": "Full-time employees only",
                "exclude_interns": "All except interns"
            }
            self.carry_forward_applies_to.setCurrentText(applies_to_map.get(applies_to, "All employees"))
            
            pro_rate = get_company_leave_policy("pro_rate_entitlement", "true")
            self.pro_rate_entitlement.setCurrentText("Enabled" if pro_rate == "true" else "Disabled")
            
        except Exception as e:
            # Use defaults if error loading
            print(f"Error loading policies: {str(e)}")
            self.carry_forward_enabled.setCurrentText("Enabled")
            self.max_carry_forward.setValue(10)
            self.expiry_months.setValue(6)
            self.carry_forward_applies_to.setCurrentText("All employees")
            self.pro_rate_entitlement.setCurrentText("Enabled")

    def load_employees_for_admin(self):
        """Load all active employees for admin leave request submission"""
        try:
            from services.supabase_service import supabase
            
            # Get all active employees
            employees_response = supabase.table("employees").select(
                "employee_id, email, full_name, department"
            ).eq("status", "Active").execute()
            
            if employees_response.data:
                self.admin_employee_combo.clear()
                for employee in employees_response.data:
                    display_text = f"{employee['full_name']} ({employee['email']}) - {employee['department']}"
                    self.admin_employee_combo.addItem(display_text, employee['email'])
                
                # Load balance for the first employee after populating dropdown
                if self.admin_employee_combo.count() > 0:
                    self.load_admin_leave_balances_simple()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to load employees: {str(e)}")

    def load_admin_leave_balances(self, highlight_type=None):
        """Load and display leave balances for the selected employee in admin form"""
        selected_employee = self.admin_employee_combo.currentData()
        
        if not selected_employee:
            self.admin_annual_balance_label.setText("Annual Leave: Select an employee to view balance")
            self.admin_sick_balance_label.setText("Sick Leave: Select an employee to view balance")
            return
        
        try:
            current_year = datetime.now().year
            
            # Get current leave type selection for highlighting
            if highlight_type is None and hasattr(self, 'admin_leave_type'):
                highlight_type = self.admin_leave_type.currentText()
            
            # Get annual leave balance
            annual_balance = get_individual_employee_leave_balance(selected_employee, current_year)
            if annual_balance:
                annual_entitlement = annual_balance.get('annual_entitlement', 0)
                annual_used = annual_balance.get('used_days', 0)
                annual_carried = annual_balance.get('carried_forward', 0)
                annual_remaining = annual_entitlement + annual_carried - annual_used
                
                annual_text = (
                    f"Annual Leave: {max(0, annual_remaining)} days remaining "
                    f"(Entitlement: {annual_entitlement}, Used: {annual_used}, Carried Forward: {annual_carried})"
                )
                
                # Highlight if this is the selected leave type
                if highlight_type == "Annual":
                    self.admin_annual_balance_label.setText(f"🔸 {annual_text}")
                    self.admin_annual_balance_label.setStyleSheet("font-size: 14px; color: #1976d2; margin: 5px 0; font-weight: bold;")
                else:
                    self.admin_annual_balance_label.setText(annual_text)
                    self.admin_annual_balance_label.setStyleSheet("font-size: 14px; color: #2e7d32; margin: 5px 0;")
            else:
                self.admin_annual_balance_label.setText("Annual Leave: Data not available")
                self.admin_annual_balance_label.setStyleSheet("font-size: 14px; color: #2e7d32; margin: 5px 0;")
            
            # Get sick leave balance
            sick_balance = get_individual_employee_sick_leave_balance(selected_employee, current_year)
            if sick_balance:
                sick_entitlement = sick_balance.get('sick_days_entitlement', 14)
                sick_used = sick_balance.get('used_sick_days', 0)
                sick_remaining = sick_entitlement - sick_used
                
                # Also show hospitalization days
                hosp_entitlement = sick_balance.get('hospitalization_days_entitlement', 60)
                hosp_used = sick_balance.get('used_hospitalization_days', 0)
                hosp_remaining = hosp_entitlement - hosp_used
                
                sick_text = (
                    f"Sick Leave: {max(0, sick_remaining)} days remaining "
                    f"(Entitlement: {sick_entitlement}, Used: {sick_used}) | "
                    f"Hospitalization: {max(0, hosp_remaining)} days"
                )
                
                # Highlight if this is the selected leave type
                if highlight_type == "Sick":
                    self.admin_sick_balance_label.setText(f"🔸 {sick_text}")
                    self.admin_sick_balance_label.setStyleSheet("font-size: 14px; color: #1976d2; margin: 5px 0; font-weight: bold;")
                else:
                    self.admin_sick_balance_label.setText(sick_text)
                    self.admin_sick_balance_label.setStyleSheet("font-size: 14px; color: #d32f2f; margin: 5px 0;")
            else:
                sick_text = "Sick Leave: 14 days remaining (Default)"
                if highlight_type == "Sick":
                    self.admin_sick_balance_label.setText(f"🔸 {sick_text}")
                    self.admin_sick_balance_label.setStyleSheet("font-size: 14px; color: #1976d2; margin: 5px 0; font-weight: bold;")
                else:
                    self.admin_sick_balance_label.setText(sick_text)
                    self.admin_sick_balance_label.setStyleSheet("font-size: 14px; color: #d32f2f; margin: 5px 0;")
                
        except Exception as e:
            print(f"Error loading admin leave balances: {str(e)}")
            self.admin_annual_balance_label.setText("Annual Leave: Error loading balance")
            self.admin_sick_balance_label.setText("Sick Leave: Error loading balance")

    def load_admin_leave_balances_simple(self):
        """Load and display leave balances for selected employee without highlighting"""
        self.load_admin_leave_balances(highlight_type=None)

    def on_admin_leave_type_changed(self, leave_type):
        """Handle admin leave type selection changes"""
        if leave_type == "Sick":
            self.admin_sick_leave_info.setText(
                "ℹ️ Sick Leave Requirements (Malaysian Employment Act 1955):\n"
                "• Medical Certificate (MC) from registered practitioner required\n"
                "• Entitlement: 14-22 days/year based on years of service\n"
                "• Hospitalization: Up to 60 days/year (inclusive of sick days)\n"
                "• Please attach MC document\n"
                "⚠️ Important: Sick leave requests without MC document will be deducted from Annual Leave balance instead"
            )
            self.admin_sick_leave_info.show()
        else:
            self.admin_sick_leave_info.hide()
        
        # Refresh balance display without highlighting (just update data)
        self.load_admin_leave_balances(highlight_type=None)

    def on_admin_half_day_toggled(self, checked):
        """Handle admin half-day checkbox toggle"""
        self.admin_half_day_period.setEnabled(checked)
        
        if checked:
            # For half-day, allow fractional input and default to 0.5 day
            try:
                self.admin_leave_duration_input.blockSignals(True)
                self.admin_leave_duration_input.setDecimals(1)
                self.admin_leave_duration_input.setSingleStep(0.5)
                self.admin_leave_duration_input.setMinimum(0.5)
                self.admin_leave_duration_input.setValue(0.5)
            finally:
                try:
                    self.admin_leave_duration_input.blockSignals(False)
                except Exception:
                    pass
            
            # Set end date to same as start date
            start_date = self.admin_start_date.date()
            self.admin_end_date.setDate(start_date)
            self.admin_end_date.setEnabled(False)
        else:
            # Re-enable end date and restore whole-day min/step for duration input
            self.admin_end_date.setEnabled(True)
            try:
                self.admin_leave_duration_input.blockSignals(True)
                self.admin_leave_duration_input.setMinimum(1.0)
                self.admin_leave_duration_input.setSingleStep(1.0)
                if self.admin_leave_duration_input.value() < 1.0:
                    self.admin_leave_duration_input.setValue(1.0)
            finally:
                try:
                    self.admin_leave_duration_input.blockSignals(False)
                except Exception:
                    pass

    def update_admin_dates_from_duration(self, working_days):
        """Update admin start and end dates based on working days duration (excluding state-specific weekends).

        Fractional values are supported by rounding up to whole working days for end-date calculation
        (e.g., 0.5 -> 1 day with same start/end; 2.5 -> 3 working-day span).
        """
        # Normalize fractional input to whole days for date computation
        try:
            import math
            req = float(working_days)
            whole_days = int(max(1, math.ceil(req)))
        except Exception:
            whole_days = int(working_days) if isinstance(working_days, int) else 1

        current_date = QDate.currentDate()
        # Determine state-specific weekend days for Qt (Fri=5, Sat=6, Sun=7)
        try:
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            from core.holidays_service import canonical_state_name
            qt_state = canonical_state_name(self.admin_state_combo.currentText()) if hasattr(self, 'admin_state_combo') else None
            weekend_qt_days = {5, 6} if (qt_state in fri_sat_states) else {6, 7}
        except Exception:
            weekend_qt_days = {6, 7}
        
        # Find next working day as start date
        start_date = current_date
        while start_date.dayOfWeek() in weekend_qt_days:
            start_date = start_date.addDays(1)
        
        # Calculate end date by adding working days (excluding weekends)
        end_date = start_date
        days_added = 0
        
        while days_added < whole_days - 1:  # -1 because start day counts as day 1
            end_date = end_date.addDays(1)
            # Only count weekdays (Monday=1 to Friday=5)
            if end_date.dayOfWeek() not in weekend_qt_days:
                days_added += 1
        
        self.admin_start_date.setDate(start_date)
        self.admin_end_date.setDate(end_date)
        
        # Refresh balance display when duration changes
        self.load_admin_leave_balances_simple()

    def validate_admin_start_date(self, date):
        """Validate admin start date to ensure it's not a weekend (state-specific)."""
        try:
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            from core.holidays_service import canonical_state_name
            qt_state = canonical_state_name(self.admin_state_combo.currentText()) if hasattr(self, 'admin_state_combo') else None
            weekend_qt_days = {5, 6} if (qt_state in fri_sat_states) else {6, 7}
        except Exception:
            weekend_qt_days = {6, 7}
        if date.dayOfWeek() in weekend_qt_days:  # Weekend
            # Find next working day
            while date.dayOfWeek() in weekend_qt_days:
                date = date.addDays(1)
            self.admin_start_date.setDate(date)
        
        # Refresh balance display when dates change
        self.load_admin_leave_balances_simple()
            
    def validate_admin_end_date(self, date):
        """Validate admin end date to ensure it's not a weekend (state-specific)."""
        try:
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            from core.holidays_service import canonical_state_name
            qt_state = canonical_state_name(self.admin_state_combo.currentText()) if hasattr(self, 'admin_state_combo') else None
            weekend_qt_days = {5, 6} if (qt_state in fri_sat_states) else {6, 7}
        except Exception:
            weekend_qt_days = {6, 7}
        if date.dayOfWeek() in weekend_qt_days:  # Weekend
            # Find previous working day
            while date.dayOfWeek() in weekend_qt_days:
                date = date.addDays(-1)
            self.admin_end_date.setDate(date)
        
        # Refresh balance display when dates change
        self.load_admin_leave_balances_simple()

    def admin_upload_document(self):
        """Upload document for admin leave request"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Document", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            try:
                from services.supabase_service import upload_document_to_bucket
                
                # Use a generic admin email for the upload path
                document_url = upload_document_to_bucket(file_path, "admin_upload", is_leave_request=True)
                if document_url:
                    self.admin_document_url = document_url
                    self.admin_upload_btn.setText(f"Document Uploaded ✓")
                    QMessageBox.information(self, "Success", "Document uploaded successfully.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to upload document. Please try again.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to upload document: {str(e)}")

    def admin_remove_document(self):
        """Remove uploaded document for admin leave request"""
        self.admin_document_url = None
        self.admin_upload_btn.setText("Upload Document")
        QMessageBox.information(self, "Removed", "Document removed.")

    def admin_submit_request(self):
        """Submit leave request on behalf of an employee"""
        try:
            # Get selected employee
            if self.admin_employee_combo.currentIndex() == -1:
                QMessageBox.warning(self, "Missing", "Please select an employee.")
                return
            
            employee_email = self.admin_employee_combo.currentData()
            if not employee_email:
                QMessageBox.warning(self, "Missing", "Please select a valid employee.")
                return
            
            # Get form data
            leave_type = self.admin_leave_type.currentText()
            title = self.admin_leave_title.text().strip()
            start = self.admin_start_date.date().toPyDate()
            end = self.admin_end_date.date().toPyDate()
            
            # Validate form data
            if not title:
                QMessageBox.warning(self, "Missing", "Please provide a title for the leave request.")
                return
            if start > end:
                QMessageBox.warning(self, "Invalid", "Start date cannot be after end date.")
                return
            
            # Calculate requested days
            requested_days = (end - start).days + 1
            
            # Check leave balance for annual and sick leave
            try:
                current_year = datetime.now().year
                
                if leave_type == "Annual":
                    annual_balance = get_individual_employee_leave_balance(employee_email, current_year)
                    if annual_balance:
                        annual_entitlement = annual_balance.get('annual_entitlement', 0)
                        annual_used = annual_balance.get('used_days', 0)
                        annual_carried = annual_balance.get('carried_forward', 0)
                        annual_remaining = annual_entitlement + annual_carried - annual_used
                        
                        if requested_days > annual_remaining:
                            reply = QMessageBox.question(
                                self,
                                "Insufficient Annual Leave Balance",
                                f"Employee is requesting {requested_days} days but only has {max(0, annual_remaining)} days remaining.\n\n"
                                f"Employee: {self.admin_employee_combo.currentText()}\n"
                                f"Details:\n"
                                f"• Entitlement: {annual_entitlement} days\n"
                                f"• Carried Forward: {annual_carried} days\n"
                                f"• Used: {annual_used} days\n"
                                f"• Remaining: {max(0, annual_remaining)} days\n\n"
                                f"Do you want to proceed anyway? (May result in unpaid leave)",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            if reply == QMessageBox.No:
                                return
                
                elif leave_type == "Sick":
                    sick_balance = get_individual_employee_sick_leave_balance(employee_email, current_year)
                    if sick_balance:
                        sick_entitlement = sick_balance.get('sick_days_entitlement', 14)
                        sick_used = sick_balance.get('used_sick_days', 0)
                        sick_remaining = sick_entitlement - sick_used
                        
                        if requested_days > sick_remaining:
                            reply = QMessageBox.question(
                                self,
                                "Insufficient Sick Leave Balance",
                                f"Employee is requesting {requested_days} days but only has {max(0, sick_remaining)} sick days remaining.\n\n"
                                f"Employee: {self.admin_employee_combo.currentText()}\n"
                                f"Details:\n"
                                f"• Entitlement: {sick_entitlement} days\n"
                                f"• Used: {sick_used} days\n"
                                f"• Remaining: {max(0, sick_remaining)} days\n\n"
                                f"Note: Employee also has {sick_balance.get('hospitalization_days_entitlement', 60)} hospitalization days available.\n\n"
                                f"Do you want to proceed anyway?",
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No
                            )
                            if reply == QMessageBox.No:
                                return
            except Exception as e:
                print(f"Warning: Could not verify leave balance: {str(e)}")
                # Continue with submission even if balance check fails
            
            # For sick leave, remind about document upload
            if leave_type == "Sick":
                if not self.admin_document_url:
                    reply = QMessageBox.question(
                        self, 
                        "Medical Certificate Required", 
                        "Sick leave requires medical certificate (MC) attachment.\n\n"
                        "Have you uploaded the MC document?\n"
                        "Click 'Yes' to proceed without document (not recommended)\n"
                        "Click 'No' to cancel and upload MC first",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
            
            # Submit the request without reason field
            from services.supabase_service import submit_leave_request
            
            # Get half-day information
            is_half_day = self.admin_half_day_checkbox.isChecked()
            half_day_period = self.admin_half_day_period.currentText() if is_half_day else None
            # Determine selected state (convert 'All Malaysia' to None so Calendar service treats as national)
            sel_state = self.admin_state_combo.currentText()
            states_payload = None
            if sel_state and sel_state.strip() and sel_state != 'All Malaysia':
                states_payload = [sel_state]

            success = submit_leave_request(
                employee_email, leave_type, start.isoformat(), end.isoformat(), 
                title or "", self.admin_document_url, self.current_admin_email, is_half_day, half_day_period, states=states_payload
            )
            
            if success:
                QMessageBox.information(
                    self, "Success", 
                    f"Leave request submitted successfully for {self.admin_employee_combo.currentText()}."
                )
                # Clear form
                self.admin_leave_title.clear()
                self.admin_document_url = None
                self.admin_upload_btn.setText("Upload Document")
                # Refresh the leave requests data
                self.load_leave_requests()
                # Refresh leave balances after successful submission
                self.load_admin_leave_balances()
            else:
                QMessageBox.warning(self, "Error", "Failed to submit leave request.")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit leave request: {str(e)}")
    
    def setup_unpaid_leave_tab(self):
        """Setup the unpaid leave management tab"""
        try:
            from gui.admin_unpaid_leave_tab_simple import SimpleAdminUnpaidLeaveTab
            
            # Create the unpaid leave tab widget
            self.unpaid_leave_widget = SimpleAdminUnpaidLeaveTab()
            
            # Set up the layout for the unpaid leave tab
            unpaid_leave_layout = QVBoxLayout()
            unpaid_leave_layout.addWidget(self.unpaid_leave_widget)
            self.unpaid_leave_tab.setLayout(unpaid_leave_layout)
            
        except Exception as e:
            # If the unpaid leave tab fails to load, show an error message
            error_layout = QVBoxLayout()
            error_label = QLabel(f"❌ Error loading unpaid leave tab: {str(e)}")
            error_label.setStyleSheet("color: red; font-weight: bold; padding: 20px;")
            error_layout.addWidget(error_label)
            
            # Add instructions
            instructions = QLabel(
                "To enable the unpaid leave management feature:\n"
                "1. Create the monthly_unpaid_leave table in your database\n"
                "2. Run the SQL from 'create_monthly_unpaid_leave_table.sql'\n"
                "3. Ensure all required Python modules are installed"
            )
            instructions.setStyleSheet("color: gray; padding: 10px;")
            error_layout.addWidget(instructions)
            
            self.unpaid_leave_tab.setLayout(error_layout)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to submit leave request: {str(e)}")