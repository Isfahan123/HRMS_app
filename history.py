"""
Leave History Management Widget
Shows approved and rejected leave requests with filtering capabilities
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QDateEdit, QLineEdit, QLabel, QGroupBox, QPushButton,
    QMessageBox, QHeaderView, QFileDialog
)
from PyQt5.QtCore import QDate, pyqtSignal
from PyQt5.QtGui import QFont

from services.supabase_service import get_all_leave_requests, calculate_working_days, get_leave_request_states
import csv
from datetime import datetime

# Import time conversion function from supabase service
try:
    from services.supabase_service import convert_utc_to_kl
except ImportError:
    def convert_utc_to_kl(utc_time):
        """Fallback time conversion if utility not available"""
        try:
            if isinstance(utc_time, str):
                return datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
            return utc_time
        except:
            return datetime.now()

class LeaveHistoryWidget(QWidget):
    """Widget for displaying approved and rejected leave requests"""
    
    request_viewed = pyqtSignal(dict)  # Emitted when a request is viewed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("LeaveHistoryWidget")
        
        # Data storage
        self.original_records = []
        
        self.init_ui()
        self.load_history()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("📜 Leave Request History")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Filters section
        self.create_filters(layout)
        
        # History table
        self.create_history_table(layout)
        
        # Export button
        export_layout = QHBoxLayout()
        self.export_btn = QPushButton("📊 Export to CSV")
        self.export_btn.clicked.connect(self.export_to_csv)
        export_layout.addWidget(self.export_btn)
        export_layout.addStretch()
        layout.addLayout(export_layout)
    
    def create_filters(self, parent_layout):
        """Create filter controls"""
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()
        
        # Status filter
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Approved", "Rejected"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.status_filter)
        
        # Date range filters
        filter_layout.addWidget(QLabel("From:"))
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addMonths(-3))
        self.start_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("To:"))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.end_date)
        
        # Employee search
        filter_layout.addWidget(QLabel("Employee:"))
        self.employee_search = QLineEdit()
        self.employee_search.setPlaceholderText("Search by employee email...")
        self.employee_search.textChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.employee_search)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_history)
        filter_layout.addWidget(refresh_btn)
        
        filter_group.setLayout(filter_layout)
        parent_layout.addWidget(filter_group)
    
    def create_history_table(self, parent_layout):
        """Create the history table"""
        self.history_table = QTableWidget()
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Set up columns
        self.history_table.setColumnCount(11)
        self.history_table.setHorizontalHeaderLabels([
            "Email", "Leave Type", "Title", "Start Date", "End Date", "Days",
            "Status", "Submitted At", "Reviewed At", "Reviewer", "View Details"
        ])
        
        # Configure column widths
        header = self.history_table.horizontalHeader()
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
        
        # Set fixed width for button column
        self.history_table.setColumnWidth(10, 120)
        
        # Set row height for buttons
        self.history_table.verticalHeader().setDefaultSectionSize(45)
        
        parent_layout.addWidget(self.history_table)
    
    def load_history(self):
        """Load approved and rejected leave requests"""
        try:
            # Get all leave requests
            all_requests = get_all_leave_requests()
            
            # Filter for approved and rejected requests
            self.original_records = [
                request for request in all_requests 
                if request.get("status") in ["approved", "rejected"]
            ]
            
            print(f"DEBUG: Loaded {len(self.original_records)} history records")
            self.apply_filters()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load leave history: {str(e)}")
            print(f"ERROR: Failed to load leave history: {str(e)}")
    
    def apply_filters(self):
        """Apply current filters to the history data"""
        try:
            status_filter = self.status_filter.currentText().lower()
            search_text = self.employee_search.text().strip().lower()
            start_date = self.start_date.date().toPyDate()
            end_date = self.end_date.date().toPyDate()
            
            # Start with all history records
            filtered_records = self.original_records.copy()
            
            # Apply status filter
            if status_filter != "all":
                filtered_records = [r for r in filtered_records if r.get("status", "").lower() == status_filter]
            
            # Apply employee search filter
            if search_text:
                filtered_records = [r for r in filtered_records 
                                  if search_text in r.get("employee_email", "").lower()]
            
            # Apply date range filter (based on reviewed_at date)
            date_filtered_records = []
            for record in filtered_records:
                reviewed_at = record.get("reviewed_at")
                if reviewed_at and reviewed_at != "-":
                    try:
                        reviewed_date = convert_utc_to_kl(reviewed_at).date()
                        if start_date <= reviewed_date <= end_date:
                            date_filtered_records.append(record)
                    except:
                        # If date parsing fails, include the record
                        date_filtered_records.append(record)
                else:
                    # If no reviewed_at date, include the record
                    date_filtered_records.append(record)
            
            # Update the table
            self.populate_table(date_filtered_records)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply filters: {str(e)}")
    
    def populate_table(self, records):
        """Populate the table with history records"""
        try:
            self.history_table.setRowCount(len(records))
            
            for row, record in enumerate(records):
                # Email
                self.history_table.setItem(row, 0, QTableWidgetItem(str(record.get("employee_email", ""))))
                
                # Leave Type
                leave_type = record.get("leave_type", "")
                self.history_table.setItem(row, 1, QTableWidgetItem(leave_type))
                
                # Title
                title = record.get("title", "")
                self.history_table.setItem(row, 2, QTableWidgetItem(title))
                
                # Start Date
                start_date = record.get("start_date", "")
                self.history_table.setItem(row, 3, QTableWidgetItem(str(start_date)))
                
                # End Date
                end_date = record.get("end_date", "")
                self.history_table.setItem(row, 4, QTableWidgetItem(str(end_date)))
                
                # Days: prefer stored working_days (if present for approved), else compute
                days_val = 0
                try:
                    stored = record.get('working_days')
                    if stored not in (None, ""):
                        days_val = stored
                    else:
                        # Half day override
                        if record.get('is_half_day'):
                            days_val = 0.5
                        else:
                            sd = record.get('start_date')
                            ed = record.get('end_date')
                            if sd and ed:
                                # Use state selection if available
                                state = None
                                try:
                                    states = get_leave_request_states(record.get('id'))
                                    state = states[0] if states else None
                                except Exception:
                                    state = None
                                days_val = calculate_working_days(sd, ed, state=state)
                except Exception:
                    days_val = record.get("days", 0) or 0
                self.history_table.setItem(row, 5, QTableWidgetItem(str(days_val)))
                
                # Status
                status = record.get("status", "").title()
                status_item = QTableWidgetItem(status)
                if status == "Approved":
                    status_item.setBackground(self.palette().color(self.palette().ColorRole.AlternateBase))
                elif status == "Rejected":
                    status_item.setBackground(self.palette().color(self.palette().ColorRole.Mid))
                self.history_table.setItem(row, 6, status_item)
                
                # Submitted At
                submitted_at = record.get("submitted_at", "")
                if submitted_at:
                    try:
                        submitted_formatted = convert_utc_to_kl(submitted_at)  # This now returns formatted string
                    except:
                        submitted_formatted = str(submitted_at)
                else:
                    submitted_formatted = "-"
                self.history_table.setItem(row, 7, QTableWidgetItem(submitted_formatted))
                
                # Reviewed At
                reviewed_at = record.get("reviewed_at", "")
                if reviewed_at:
                    try:
                        reviewed_formatted = convert_utc_to_kl(reviewed_at)  # This now returns formatted string
                    except:
                        reviewed_formatted = str(reviewed_at)
                else:
                    reviewed_formatted = "-"
                self.history_table.setItem(row, 8, QTableWidgetItem(reviewed_formatted))
                
                # Reviewer
                reviewer = record.get("reviewed_by", "")
                self.history_table.setItem(row, 9, QTableWidgetItem(str(reviewer)))
                
                # View Details Button
                view_btn = QPushButton("👁️ View")
                view_btn.clicked.connect(lambda checked, r=record: self.view_request_details(r))
                self.history_table.setCellWidget(row, 10, view_btn)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate history table: {str(e)}")
    
    def view_request_details(self, record):
        """View detailed information about a leave request"""
        try:
            details = f"""
Leave Request Details:

Employee: {record.get('employee_email', 'N/A')}
Leave Type: {record.get('leave_type', 'N/A')}
Title: {record.get('title', 'N/A')}
Description: {record.get('description', 'N/A')}

Start Date: {record.get('start_date', 'N/A')}
End Date: {record.get('end_date', 'N/A')}
Duration: {record.get('days', 0)} days

Status: {record.get('status', 'N/A').title()}
Submitted: {record.get('submitted_at', 'N/A')}
Reviewed: {record.get('reviewed_at', 'N/A')}
Reviewed By: {record.get('reviewed_by', 'N/A')}

Comments: {record.get('admin_comments', 'No comments')}
"""
            
            QMessageBox.information(self, "Leave Request Details", details)
            self.request_viewed.emit(record)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to view request details: {str(e)}")
    
    def export_to_csv(self):
        """Export filtered history to CSV"""
        try:
            if self.history_table.rowCount() == 0:
                QMessageBox.information(self, "Export", "No data to export")
                return
            
            # Get file path
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Leave History", 
                f"leave_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # Write CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = []
                for col in range(self.history_table.columnCount() - 1):  # Exclude button column
                    headers.append(self.history_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.history_table.rowCount()):
                    row_data = []
                    for col in range(self.history_table.columnCount() - 1):  # Exclude button column
                        item = self.history_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Complete", f"History exported to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export history: {str(e)}")
    
    def refresh_data(self):
        """Refresh the history data"""
        self.load_history()
