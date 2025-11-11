import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QComboBox, QDateEdit, QMessageBox, QGroupBox, 
                             QGridLayout, QLineEdit, QSpinBox, QDoubleSpinBox,
                             QTextEdit, QFrame, QSplitter, QAbstractItemView)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
from datetime import datetime, timedelta
import json

try:
    from services.supabase_service import supabase
except ImportError:
    print("Warning: Could not import supabase_service")
    supabase = None

class AdminSalaryHistoryTab(QWidget):
    """
    Admin tab for tracking salary history and changes for all employees.
    Shows salary increases, decreases, and timeline of changes.
    """
    
    # Signal emitted when an employee's salary is updated
    salary_updated = pyqtSignal(str)  # employee_id
    
    def __init__(self):
        super().__init__()
        self.employees_data = []
        self.salary_history_data = []
        self.init_ui()
        self.load_employees()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Employee Salary History Management")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Create splitter for employee list and salary history
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Employee selection and controls
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        
        # Employee selection group
        employee_group = QGroupBox("Employee Selection")
        employee_layout = QGridLayout()
        
        employee_layout.addWidget(QLabel("Employee:"), 0, 0)
        self.employee_combo = QComboBox()
        self.employee_combo.currentTextChanged.connect(self.on_employee_changed)
        employee_layout.addWidget(self.employee_combo, 0, 1, 1, 2)
        
        # Current salary info
        employee_layout.addWidget(QLabel("Current Basic Salary:"), 1, 0)
        self.current_salary_label = QLabel("RM 0.00")
        self.current_salary_label.setStyleSheet("font-weight: bold; color: #2e7d32;")
        employee_layout.addWidget(self.current_salary_label, 1, 1)
        
        employee_layout.addWidget(QLabel("Last Updated:"), 2, 0)
        self.last_updated_label = QLabel("Never")
        employee_layout.addWidget(self.last_updated_label, 2, 1)
        
        employee_group.setLayout(employee_layout)
        left_layout.addWidget(employee_group)
        
        # Add new salary entry group
        entry_group = QGroupBox("Add Salary Change")
        entry_layout = QGridLayout()
        
        entry_layout.addWidget(QLabel("Effective Date:"), 0, 0)
        self.effective_date = QDateEdit()
        self.effective_date.setDate(QDate.currentDate())
        self.effective_date.setCalendarPopup(True)
        entry_layout.addWidget(self.effective_date, 0, 1)
        
        entry_layout.addWidget(QLabel("New Basic Salary:"), 1, 0)
        self.new_salary_spinbox = QDoubleSpinBox()
        self.new_salary_spinbox.setRange(0, 999999.99)  # Increased salary cap to RM 999,999.99
        self.new_salary_spinbox.setDecimals(2)
        self.new_salary_spinbox.setSuffix(" RM")
        self.new_salary_spinbox.valueChanged.connect(self.calculate_change)
        entry_layout.addWidget(self.new_salary_spinbox, 1, 1)
        
        entry_layout.addWidget(QLabel("Change Amount:"), 2, 0)
        self.change_amount_label = QLabel("RM 0.00")
        entry_layout.addWidget(self.change_amount_label, 2, 1)
        
        entry_layout.addWidget(QLabel("Change Percentage:"), 3, 0)
        self.change_percentage_label = QLabel("0.00%")
        entry_layout.addWidget(self.change_percentage_label, 3, 1)
        
        entry_layout.addWidget(QLabel("Reason:"), 4, 0)
        self.reason_combo = QComboBox()
        self.reason_combo.addItems([
            "Annual Increment",
            "Promotion",
            "Performance Bonus",
            "Market Adjustment",
            "Cost of Living Adjustment",
            "Salary Review",
            "Probation Completion",
            "Skills Upgrade",
            "Salary Correction",
            "Other"
        ])
        entry_layout.addWidget(self.reason_combo, 4, 1)
        
        entry_layout.addWidget(QLabel("Notes:"), 5, 0)
        self.notes_text = QTextEdit()
        self.notes_text.setMaximumHeight(60)
        entry_layout.addWidget(self.notes_text, 5, 1)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.add_entry_button = QPushButton("Add Salary Change")
        self.add_entry_button.clicked.connect(self.add_salary_entry)
        self.add_entry_button.setStyleSheet("background-color: #1976d2; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.add_entry_button)
        
        self.update_current_button = QPushButton("Update Current Salary")
        self.update_current_button.clicked.connect(self.update_current_salary)
        self.update_current_button.setStyleSheet("background-color: #388e3c; color: white; font-weight: bold; padding: 8px;")
        button_layout.addWidget(self.update_current_button)
        
        entry_layout.addLayout(button_layout, 6, 0, 1, 2)
        entry_group.setLayout(entry_layout)
        left_layout.addWidget(entry_group)
        
        # Statistics group
        stats_group = QGroupBox("Salary Statistics")
        stats_layout = QGridLayout()
        
        stats_layout.addWidget(QLabel("Total Increases:"), 0, 0)
        self.total_increases_label = QLabel("0")
        stats_layout.addWidget(self.total_increases_label, 0, 1)
        
        stats_layout.addWidget(QLabel("Total Decreases:"), 1, 0)
        self.total_decreases_label = QLabel("0")
        stats_layout.addWidget(self.total_decreases_label, 1, 1)
        
        stats_layout.addWidget(QLabel("Largest Increase:"), 2, 0)
        self.largest_increase_label = QLabel("RM 0.00")
        stats_layout.addWidget(self.largest_increase_label, 2, 1)
        
        stats_layout.addWidget(QLabel("Average Annual Growth:"), 3, 0)
        self.avg_growth_label = QLabel("0.00%")
        stats_layout.addWidget(self.avg_growth_label, 3, 1)
        
        stats_group.setLayout(stats_layout)
        left_layout.addWidget(stats_group)
        
        left_layout.addStretch()
        left_widget.setLayout(left_layout)
        left_widget.setMaximumWidth(400)
        
        # Right side - Salary history table
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        
        # Table controls
        table_controls = QVBoxLayout()
        
        # Title and main controls row
        title_controls = QHBoxLayout()
        title_controls.addWidget(QLabel("Salary History:"))
        title_controls.addStretch()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_salary_history)
        title_controls.addWidget(self.refresh_button)
        
        self.export_button = QPushButton("Export History")
        self.export_button.clicked.connect(self.export_salary_history)
        title_controls.addWidget(self.export_button)
        
        table_controls.addLayout(title_controls)
        
        # Filtering and sorting controls
        filter_group = QGroupBox("Filter & Sort Options")
        filter_layout = QGridLayout()
        
        # Date range filters
        filter_layout.addWidget(QLabel("Date Range:"), 0, 0)
        self.date_from = QDateEdit()
        self.date_from.setDate(QDate.currentDate().addYears(-1))  # Default to 1 year ago
        self.date_from.setCalendarPopup(True)
        self.date_from.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("From:"), 0, 1)
        filter_layout.addWidget(self.date_from, 0, 2)
        
        self.date_to = QDateEdit()
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setCalendarPopup(True)
        self.date_to.dateChanged.connect(self.apply_filters)
        filter_layout.addWidget(QLabel("To:"), 0, 3)
        filter_layout.addWidget(self.date_to, 0, 4)
        
        # Quick date filters
        filter_layout.addWidget(QLabel("Quick Filter:"), 1, 0)
        self.quick_date_filter = QComboBox()
        self.quick_date_filter.addItems([
            "All Time",
            "This Year", 
            "Last Year",
            "This Month",
            "Last Month",
            "Last 3 Months",
            "Last 6 Months",
            "Last 12 Months"
        ])
        self.quick_date_filter.currentTextChanged.connect(self.apply_quick_date_filter)
        filter_layout.addWidget(self.quick_date_filter, 1, 1, 1, 2)
        
        # Reason filter
        filter_layout.addWidget(QLabel("Reason:"), 1, 3)
        self.reason_filter = QComboBox()
        self.reason_filter.addItems([
            "All Reasons",
            "Annual Increment",
            "Promotion", 
            "Performance Bonus",
            "Market Adjustment",
            "Cost of Living Adjustment",
            "Salary Review",
            "Probation Completion",
            "Skills Upgrade",
            "Salary Correction",
            "Other"
        ])
        self.reason_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.reason_filter, 1, 4)
        
        # Change type filter
        filter_layout.addWidget(QLabel("Change Type:"), 2, 0)
        self.change_type_filter = QComboBox()
        self.change_type_filter.addItems([
            "All Changes",
            "Increases Only",
            "Decreases Only",
            "No Change (0%)"
        ])
        self.change_type_filter.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.change_type_filter, 2, 1)
        
        # Sort options
        filter_layout.addWidget(QLabel("Sort By:"), 2, 2)
        self.sort_by_combo = QComboBox()
        self.sort_by_combo.addItems([
            "Date (Newest First)",
            "Date (Oldest First)",
            "Amount (Highest First)",
            "Amount (Lowest First)",
            "Percentage (Highest First)",
            "Percentage (Lowest First)",
            "Reason (A-Z)"
        ])
        self.sort_by_combo.currentTextChanged.connect(self.apply_filters)
        filter_layout.addWidget(self.sort_by_combo, 2, 3)
        
        # Clear filters button
        clear_filters_btn = QPushButton("Clear All Filters")
        clear_filters_btn.clicked.connect(self.clear_filters)
        clear_filters_btn.setStyleSheet("background-color: #ff9800; color: white; padding: 5px;")
        filter_layout.addWidget(clear_filters_btn, 2, 4)
        
        filter_group.setLayout(filter_layout)
        table_controls.addWidget(filter_group)
        
        right_layout.addLayout(table_controls)
        
        # Salary history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(7)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Previous Salary", "New Salary", "Change Amount", 
            "Change %", "Reason", "Notes"
        ])
        
        # Configure table
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Previous
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # New
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Change Amount
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Change %
        header.setSectionResizeMode(5, QHeaderView.Stretch)           # Reason
        header.setSectionResizeMode(6, QHeaderView.Stretch)           # Notes
        
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        right_layout.addWidget(self.history_table)
        right_widget.setLayout(right_layout)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([400, 800])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f5f5f5; border-top: 1px solid #ddd;")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
    
    def load_employees(self):
        """Load all employees into the combo box"""
        if not supabase:
            self.status_label.setText("Database connection not available")
            return
        
        try:
            self.status_label.setText("Loading employees...")
            
            # Get all active employees
            response = supabase.table("employees").select("id, full_name, employee_id, basic_salary, updated_at").eq("status", "Active").order("full_name").execute()
            
            if response.data:
                self.employees_data = response.data
                self.employee_combo.clear()
                self.employee_combo.addItem("Select an employee...", None)
                
                for employee in self.employees_data:
                    display_name = f"{employee['full_name']} ({employee['employee_id']})"
                    self.employee_combo.addItem(display_name, employee)
                
                self.status_label.setText(f"Loaded {len(self.employees_data)} employees")
            else:
                self.status_label.setText("No employees found")
                
        except Exception as e:
            self.status_label.setText(f"Error loading employees: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load employees: {e}")
    
    def on_employee_changed(self):
        """Handle employee selection change"""
        employee_data = self.employee_combo.currentData()
        if not employee_data:
            self.current_salary_label.setText("RM 0.00")
            self.last_updated_label.setText("Never")
            self.new_salary_spinbox.setValue(0)
            return
        
        # Update current salary display with null checking
        basic_salary = employee_data.get('basic_salary')
        if basic_salary is None or basic_salary == '':
            current_salary = 0.0
        else:
            try:
                current_salary = float(basic_salary)
            except (ValueError, TypeError):
                current_salary = 0.0
        
        self.current_salary_label.setText(f"RM {current_salary:,.2f}")
        
        # Update last updated
        updated_at = employee_data.get('updated_at', '')
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                self.last_updated_label.setText(formatted_date)
            except:
                self.last_updated_label.setText("Unknown")
        else:
            self.last_updated_label.setText("Never")
        
        # Set new salary spinbox to current salary
        self.new_salary_spinbox.setValue(current_salary)
        
        # Reset filters when changing employees
        self.quick_date_filter.setCurrentText("All Time")
        self.reason_filter.setCurrentText("All Reasons")
        self.change_type_filter.setCurrentText("All Changes")
        self.sort_by_combo.setCurrentText("Date (Newest First)")
        
        # Load salary history for this employee
        self.load_salary_history()
        self.calculate_statistics()
    
    def calculate_change(self):
        """Calculate salary change amount and percentage"""
        employee_data = self.employee_combo.currentData()
        if not employee_data:
            return
        
        # Get current salary with null checking
        basic_salary = employee_data.get('basic_salary')
        if basic_salary is None or basic_salary == '':
            current_salary = 0.0
        else:
            try:
                current_salary = float(basic_salary)
            except (ValueError, TypeError):
                current_salary = 0.0
        
        new_salary = self.new_salary_spinbox.value()
        
        change_amount = new_salary - current_salary
        change_percentage = (change_amount / current_salary * 100) if current_salary > 0 else 0
        
        # Update labels with color coding
        if change_amount > 0:
            self.change_amount_label.setText(f"+RM {change_amount:,.2f}")
            self.change_amount_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
            self.change_percentage_label.setText(f"+{change_percentage:.2f}%")
            self.change_percentage_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
        elif change_amount < 0:
            self.change_amount_label.setText(f"RM {change_amount:,.2f}")
            self.change_amount_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            self.change_percentage_label.setText(f"{change_percentage:.2f}%")
            self.change_percentage_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        else:
            self.change_amount_label.setText("RM 0.00")
            self.change_amount_label.setStyleSheet("color: #666; font-weight: normal;")
            self.change_percentage_label.setText("0.00%")
            self.change_percentage_label.setStyleSheet("color: #666; font-weight: normal;")
    
    def add_salary_entry(self):
        """Add a new salary history entry"""
        employee_data = self.employee_combo.currentData()
        if not employee_data:
            QMessageBox.warning(self, "Warning", "Please select an employee first")
            return
        
        if not supabase:
            QMessageBox.warning(self, "Error", "Database connection not available")
            return
        
        # Get form data
        employee_id = employee_data['id']
        effective_date = self.effective_date.date().toString("yyyy-MM-dd")
        
        # Get current salary with null checking
        basic_salary = employee_data.get('basic_salary')
        if basic_salary is None or basic_salary == '':
            current_salary = 0.0
        else:
            try:
                current_salary = float(basic_salary)
            except (ValueError, TypeError):
                current_salary = 0.0
        
        new_salary = self.new_salary_spinbox.value()
        reason = self.reason_combo.currentText()
        notes = self.notes_text.toPlainText().strip()
        
        if new_salary == current_salary:
            QMessageBox.information(self, "Info", "New salary is the same as current salary")
            return
        
        change_amount = new_salary - current_salary
        change_percentage = (change_amount / current_salary * 100) if current_salary > 0 else 0
        
        try:
            self.status_label.setText("Adding salary history entry...")
            
            # Create salary history entry
            history_entry = {
                "employee_id": employee_id,
                "effective_date": effective_date,
                "previous_salary": current_salary,
                "new_salary": new_salary,
                "change_amount": change_amount,
                "change_percentage": change_percentage,
                "reason": reason,
                "notes": notes,
                "created_by": "admin",
                "created_at": datetime.now().isoformat()
            }
            
            # Insert into salary_history table (create if doesn't exist)
            response = supabase.table("salary_history").insert(history_entry).execute()
            
            if response.data:
                self.status_label.setText("Salary history entry added successfully")
                
                # Ask if user wants to update current salary
                reply = QMessageBox.question(
                    self, "Update Current Salary",
                    f"Salary history entry added successfully.\n\n"
                    f"Do you want to update the employee's current salary to RM {new_salary:,.2f}?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.update_current_salary()
                
                # Refresh displays
                self.load_salary_history()
                self.calculate_statistics()
                
                # Clear form
                self.notes_text.clear()
                
            else:
                self.status_label.setText("Failed to add salary history entry")
                QMessageBox.warning(self, "Error", "Failed to add salary history entry")
                
        except Exception as e:
            self.status_label.setText(f"Error adding salary entry: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add salary entry: {e}")
    
    def update_current_salary(self):
        """Update the employee's current salary in the employees table"""
        employee_data = self.employee_combo.currentData()
        if not employee_data:
            QMessageBox.warning(self, "Warning", "Please select an employee first")
            return
        
        if not supabase:
            QMessageBox.warning(self, "Error", "Database connection not available")
            return
        
        employee_id = employee_data['id']
        new_salary = self.new_salary_spinbox.value()
        
        try:
            self.status_label.setText("Updating current salary...")
            
            # Update employee's basic salary
            response = supabase.table("employees").update({
                "basic_salary": new_salary,
                "updated_at": datetime.now().isoformat()
            }).eq("id", employee_id).execute()
            
            if response.data:
                self.status_label.setText("Current salary updated successfully")
                QMessageBox.information(self, "Success", f"Employee's current salary updated to RM {new_salary:,.2f}")
                
                # Emit signal to notify other components about salary update
                self.salary_updated.emit(employee_id)
                
                # Refresh employee data
                self.load_employees()
                
                # Re-select the same employee
                for i in range(self.employee_combo.count()):
                    if self.employee_combo.itemData(i) and self.employee_combo.itemData(i)['id'] == employee_id:
                        self.employee_combo.setCurrentIndex(i)
                        break
            else:
                self.status_label.setText("Failed to update current salary")
                QMessageBox.warning(self, "Error", "Failed to update current salary")
                
        except Exception as e:
            self.status_label.setText(f"Error updating salary: {e}")
            QMessageBox.warning(self, "Error", f"Failed to update salary: {e}")
    
    def load_salary_history(self):
        """Load salary history for selected employee"""
        employee_data = self.employee_combo.currentData()
        if not employee_data or not supabase:
            self.history_table.setRowCount(0)
            return
        
        try:
            self.status_label.setText("Loading salary history...")
            
            employee_id = employee_data['id']
            response = supabase.table("salary_history").select("*").eq("employee_id", employee_id).order("effective_date", desc=True).execute()
            
            if response.data:
                self.salary_history_data = response.data
                # Apply current filters to the loaded data
                self.apply_filters()
                self.status_label.setText(f"Loaded {len(response.data)} salary history entries")
            else:
                self.salary_history_data = []
                self.history_table.setRowCount(0)
                self.status_label.setText("No salary history found")
                
        except Exception as e:
            self.status_label.setText(f"Error loading salary history: {e}")
            self.history_table.setRowCount(0)
    
    def populate_history_table(self):
        """Populate the salary history table"""
        self.history_table.setRowCount(len(self.salary_history_data))
        
        for row, entry in enumerate(self.salary_history_data):
            # Date
            effective_date = entry.get('effective_date', '')
            self.history_table.setItem(row, 0, QTableWidgetItem(effective_date))
            
            # Previous salary
            previous_salary = float(entry.get('previous_salary', 0))
            prev_item = QTableWidgetItem(f"RM {previous_salary:,.2f}")
            self.history_table.setItem(row, 1, prev_item)
            
            # New salary
            new_salary = float(entry.get('new_salary', 0))
            new_item = QTableWidgetItem(f"RM {new_salary:,.2f}")
            self.history_table.setItem(row, 2, new_item)
            
            # Change amount
            change_amount = float(entry.get('change_amount', 0))
            change_item = QTableWidgetItem(f"RM {change_amount:+,.2f}")
            if change_amount > 0:
                change_item.setBackground(QColor("#e8f5e8"))
                change_item.setForeground(QColor("#2e7d32"))
            elif change_amount < 0:
                change_item.setBackground(QColor("#ffebee"))
                change_item.setForeground(QColor("#d32f2f"))
            self.history_table.setItem(row, 3, change_item)
            
            # Change percentage
            change_percentage = float(entry.get('change_percentage', 0))
            percent_item = QTableWidgetItem(f"{change_percentage:+.2f}%")
            if change_percentage > 0:
                percent_item.setBackground(QColor("#e8f5e8"))
                percent_item.setForeground(QColor("#2e7d32"))
            elif change_percentage < 0:
                percent_item.setBackground(QColor("#ffebee"))
                percent_item.setForeground(QColor("#d32f2f"))
            self.history_table.setItem(row, 4, percent_item)
            
            # Reason
            reason = entry.get('reason', '')
            self.history_table.setItem(row, 5, QTableWidgetItem(reason))
            
            # Notes
            notes = entry.get('notes', '')
            self.history_table.setItem(row, 6, QTableWidgetItem(notes))
    
    def calculate_statistics(self):
        """Calculate and display salary statistics"""
        if not self.salary_history_data:
            self.total_increases_label.setText("0")
            self.total_decreases_label.setText("0")
            self.largest_increase_label.setText("RM 0.00")
            self.avg_growth_label.setText("0.00%")
            return
        
        increases = [entry for entry in self.salary_history_data if float(entry.get('change_amount', 0)) > 0]
        decreases = [entry for entry in self.salary_history_data if float(entry.get('change_amount', 0)) < 0]
        
        self.total_increases_label.setText(str(len(increases)))
        self.total_decreases_label.setText(str(len(decreases)))
        
        if increases:
            largest_increase = max(increases, key=lambda x: float(x.get('change_amount', 0)))
            self.largest_increase_label.setText(f"RM {float(largest_increase.get('change_amount', 0)):,.2f}")
        else:
            self.largest_increase_label.setText("RM 0.00")
        
        # Calculate average annual growth
        if len(self.salary_history_data) > 1:
            total_change = sum(float(entry.get('change_amount', 0)) for entry in self.salary_history_data)
            employee_data = self.employee_combo.currentData()
            
            if employee_data:
                # Get current salary with null checking
                basic_salary = employee_data.get('basic_salary')
                if basic_salary is None or basic_salary == '':
                    current_salary = 0.0
                else:
                    try:
                        current_salary = float(basic_salary)
                    except (ValueError, TypeError):
                        current_salary = 0.0
                
                if current_salary > 0:
                    avg_growth = (total_change / current_salary) * 100 / len(self.salary_history_data)
                    self.avg_growth_label.setText(f"{avg_growth:.2f}%")
                else:
                    self.avg_growth_label.setText("0.00%")
            else:
                self.avg_growth_label.setText("0.00%")
        else:
            self.avg_growth_label.setText("0.00%")
    
    def export_salary_history(self):
        """Export salary history to file"""
        employee_data = self.employee_combo.currentData()
        if not employee_data:
            QMessageBox.warning(self, "Warning", "Please select an employee first")
            return
        
        if not self.salary_history_data:
            QMessageBox.information(self, "Info", "No salary history to export")
            return
        
        try:
            employee_name = employee_data['full_name'].replace(' ', '_')
            filename = f"salary_history_{employee_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Get current salary with null checking
            basic_salary = employee_data.get('basic_salary')
            if basic_salary is None or basic_salary == '':
                current_salary = 0.0
            else:
                try:
                    current_salary = float(basic_salary)
                except (ValueError, TypeError):
                    current_salary = 0.0
            
            export_data = {
                "employee": {
                    "name": employee_data['full_name'],
                    "employee_id": employee_data['employee_id'],
                    "current_salary": current_salary
                },
                "export_date": datetime.now().isoformat(),
                "salary_history": self.salary_history_data
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            QMessageBox.information(self, "Success", f"Salary history exported to {filename}")
            self.status_label.setText(f"Exported to {filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to export salary history: {e}")
            self.status_label.setText(f"Export failed: {e}")
    
    def apply_quick_date_filter(self):
        """Apply quick date filter selection"""
        selected = self.quick_date_filter.currentText()
        today = QDate.currentDate()
        
        if selected == "All Time":
            self.date_from.setDate(QDate(2020, 1, 1))  # Set to a far past date
            self.date_to.setDate(today)
        elif selected == "This Year":
            self.date_from.setDate(QDate(today.year(), 1, 1))
            self.date_to.setDate(today)
        elif selected == "Last Year":
            last_year = today.year() - 1
            self.date_from.setDate(QDate(last_year, 1, 1))
            self.date_to.setDate(QDate(last_year, 12, 31))
        elif selected == "This Month":
            self.date_from.setDate(QDate(today.year(), today.month(), 1))
            self.date_to.setDate(today)
        elif selected == "Last Month":
            last_month = today.addMonths(-1)
            self.date_from.setDate(QDate(last_month.year(), last_month.month(), 1))
            last_day = QDate(last_month.year(), last_month.month(), last_month.daysInMonth())
            self.date_to.setDate(last_day)
        elif selected == "Last 3 Months":
            self.date_from.setDate(today.addMonths(-3))
            self.date_to.setDate(today)
        elif selected == "Last 6 Months":
            self.date_from.setDate(today.addMonths(-6))
            self.date_to.setDate(today)
        elif selected == "Last 12 Months":
            self.date_from.setDate(today.addYears(-1))
            self.date_to.setDate(today)
        
        # Apply the filters after setting dates
        self.apply_filters()
    
    def apply_filters(self):
        """Apply all active filters to the salary history data"""
        employee_data = self.employee_combo.currentData()
        if not employee_data or not self.salary_history_data:
            return
        
        try:
            # Start with all data
            filtered_data = self.salary_history_data.copy()
            
            # Apply date range filter
            date_from_str = self.date_from.date().toString("yyyy-MM-dd")
            date_to_str = self.date_to.date().toString("yyyy-MM-dd")
            
            filtered_data = [
                entry for entry in filtered_data
                if date_from_str <= entry.get('effective_date', '') <= date_to_str
            ]
            
            # Apply reason filter
            reason_filter = self.reason_filter.currentText()
            if reason_filter != "All Reasons":
                filtered_data = [
                    entry for entry in filtered_data
                    if entry.get('reason', '') == reason_filter
                ]
            
            # Apply change type filter
            change_type_filter = self.change_type_filter.currentText()
            if change_type_filter == "Increases Only":
                filtered_data = [
                    entry for entry in filtered_data
                    if float(entry.get('change_amount', 0)) > 0
                ]
            elif change_type_filter == "Decreases Only":
                filtered_data = [
                    entry for entry in filtered_data
                    if float(entry.get('change_amount', 0)) < 0
                ]
            elif change_type_filter == "No Change (0%)":
                filtered_data = [
                    entry for entry in filtered_data
                    if float(entry.get('change_amount', 0)) == 0
                ]
            
            # Apply sorting
            sort_option = self.sort_by_combo.currentText()
            if sort_option == "Date (Newest First)":
                filtered_data.sort(key=lambda x: x.get('effective_date', ''), reverse=True)
            elif sort_option == "Date (Oldest First)":
                filtered_data.sort(key=lambda x: x.get('effective_date', ''))
            elif sort_option == "Amount (Highest First)":
                filtered_data.sort(key=lambda x: float(x.get('change_amount', 0)), reverse=True)
            elif sort_option == "Amount (Lowest First)":
                filtered_data.sort(key=lambda x: float(x.get('change_amount', 0)))
            elif sort_option == "Percentage (Highest First)":
                filtered_data.sort(key=lambda x: float(x.get('change_percentage', 0)), reverse=True)
            elif sort_option == "Percentage (Lowest First)":
                filtered_data.sort(key=lambda x: float(x.get('change_percentage', 0)))
            elif sort_option == "Reason (A-Z)":
                filtered_data.sort(key=lambda x: x.get('reason', ''))
            
            # Update the table with filtered data
            self.populate_filtered_history_table(filtered_data)
            
            # Update status
            total_count = len(self.salary_history_data)
            filtered_count = len(filtered_data)
            self.status_label.setText(f"Showing {filtered_count} of {total_count} salary history entries")
            
        except Exception as e:
            print(f"DEBUG: Error applying filters: {e}")
            self.status_label.setText(f"Error applying filters: {e}")
    
    def clear_filters(self):
        """Clear all filters and show all data"""
        # Reset all filter controls
        self.quick_date_filter.setCurrentText("All Time")
        self.reason_filter.setCurrentText("All Reasons")
        self.change_type_filter.setCurrentText("All Changes")
        self.sort_by_combo.setCurrentText("Date (Newest First)")
        
        # Reset date range to default (1 year)
        today = QDate.currentDate()
        self.date_from.setDate(today.addYears(-1))
        self.date_to.setDate(today)
        
        # Refresh the data
        self.load_salary_history()
    
    def populate_filtered_history_table(self, filtered_data):
        """Populate the salary history table with filtered data"""
        self.history_table.setRowCount(len(filtered_data))
        
        for row, entry in enumerate(filtered_data):
            # Date
            effective_date = entry.get('effective_date', '')
            self.history_table.setItem(row, 0, QTableWidgetItem(effective_date))
            
            # Previous salary
            previous_salary = float(entry.get('previous_salary', 0))
            prev_item = QTableWidgetItem(f"RM {previous_salary:,.2f}")
            self.history_table.setItem(row, 1, prev_item)
            
            # New salary
            new_salary = float(entry.get('new_salary', 0))
            new_item = QTableWidgetItem(f"RM {new_salary:,.2f}")
            self.history_table.setItem(row, 2, new_item)
            
            # Change amount
            change_amount = float(entry.get('change_amount', 0))
            change_item = QTableWidgetItem(f"RM {change_amount:+,.2f}")
            if change_amount > 0:
                change_item.setBackground(QColor("#e8f5e8"))
                change_item.setForeground(QColor("#2e7d32"))
            elif change_amount < 0:
                change_item.setBackground(QColor("#ffebee"))
                change_item.setForeground(QColor("#d32f2f"))
            self.history_table.setItem(row, 3, change_item)
            
            # Change percentage
            change_percentage = float(entry.get('change_percentage', 0))
            percent_item = QTableWidgetItem(f"{change_percentage:+.2f}%")
            if change_percentage > 0:
                percent_item.setBackground(QColor("#e8f5e8"))
                percent_item.setForeground(QColor("#2e7d32"))
            elif change_percentage < 0:
                percent_item.setBackground(QColor("#ffebee"))
                percent_item.setForeground(QColor("#d32f2f"))
            self.history_table.setItem(row, 4, percent_item)
            
            # Reason
            reason = entry.get('reason', '')
            self.history_table.setItem(row, 5, QTableWidgetItem(reason))
            
            # Notes
            notes = entry.get('notes', '')
            self.history_table.setItem(row, 6, QTableWidgetItem(notes))

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = AdminSalaryHistoryTab()
    widget.show()
    sys.exit(app.exec_())
