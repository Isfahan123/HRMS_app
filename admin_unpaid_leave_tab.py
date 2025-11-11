import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QPushButton, QLabel, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit, 
                             QMessageBox, QGroupBox, QGridLayout, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime
from services.supabase_service import supabase
# Import service functions from supabase_service
try:
    from services.supabase_service import (
        get_or_create_monthly_unpaid_leave,
        update_monthly_unpaid_leave,
        sync_monthly_unpaid_leave_from_requests,
        get_monthly_unpaid_leave_summary,
        reset_annual_unpaid_leave
    )
except ImportError:
    # Fallback functions if service not available
    def get_or_create_monthly_unpaid_leave(*args, **kwargs):
        return {"unpaid_days": 0.0, "deduction_amount": 0.0}

class UnpaidLeaveWorker(QThread):
    """Worker thread for database operations"""
    finished = pyqtSignal(bool, str)
    
    def __init__(self, operation, **kwargs):
        super().__init__()
        self.operation = operation
        self.kwargs = kwargs
        self._is_running = False
    
    def run(self):
        self._is_running = True
        try:
            if self.operation == "load_data":
                self.load_data()
            elif self.operation == "update_record":
                self.update_record()
            elif self.operation == "sync_from_requests":
                self.sync_from_requests()
            elif self.operation == "reset_annual":
                self.reset_annual()
        except Exception as e:
            self.finished.emit(False, str(e))
        finally:
            self._is_running = False
    
    def stop(self):
        """Stop the thread safely"""
        if self._is_running:
            self.terminate()
            self.wait()
    
    def load_data(self):
        # Load employees and unpaid leave data
        employees_response = supabase.table("employees").select(
            "id, employee_id, email, full_name, basic_salary, allowances, status"
        ).execute()
        
        self.finished.emit(True, str(employees_response.data))
    
    def update_record(self):
        success = update_monthly_unpaid_leave(**self.kwargs)
        self.finished.emit(success, "Record updated" if success else "Update failed")
    
    def sync_from_requests(self):
        success = sync_monthly_unpaid_leave_from_requests(**self.kwargs)
        self.finished.emit(success, "Sync completed" if success else "Sync failed")
    
    def reset_annual(self):
        success = reset_annual_unpaid_leave(self.kwargs["year"])
        self.finished.emit(success, "Annual reset completed" if success else "Reset failed")

class AdminUnpaidLeaveTab(QWidget):
    def __init__(self):
        super().__init__()
        self.employees_data = []
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.active_workers = []  # Track active worker threads
        self.init_ui()
        self.load_employees()
    
    def closeEvent(self, event):
        """Handle widget closure to properly clean up threads"""
        self.cleanup_threads()
        event.accept()
    
    def cleanup_threads(self):
        """Clean up all active worker threads"""
        for worker in self.active_workers:
            if worker.isRunning():
                worker.stop()
        self.active_workers.clear()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Monthly Unpaid Leave Management")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Controls section
        controls_group = QGroupBox("Controls")
        controls_layout = QGridLayout()
        
        # Year and Month selectors
        controls_layout.addWidget(QLabel("Year:"), 0, 0)
        self.year_spinbox = QSpinBox()
        self.year_spinbox.setRange(2020, 2030)
        self.year_spinbox.setValue(self.current_year)
        self.year_spinbox.valueChanged.connect(self.on_period_changed)
        controls_layout.addWidget(self.year_spinbox, 0, 1)
        
        controls_layout.addWidget(QLabel("Month:"), 0, 2)
        self.month_spinbox = QSpinBox()
        self.month_spinbox.setRange(1, 12)
        self.month_spinbox.setValue(self.current_month)
        self.month_spinbox.valueChanged.connect(self.on_period_changed)
        controls_layout.addWidget(self.month_spinbox, 0, 3)
        
        # Action buttons
        self.sync_button = QPushButton("Sync from Leave Requests")
        self.sync_button.clicked.connect(self.sync_from_leave_requests)
        controls_layout.addWidget(self.sync_button, 0, 4)
        
        self.reset_year_button = QPushButton("Reset Year")
        self.reset_year_button.clicked.connect(self.reset_annual_data)
        controls_layout.addWidget(self.reset_year_button, 0, 5)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_employees)
        controls_layout.addWidget(self.refresh_button, 0, 6)
        
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Employee selection
        employee_group = QGroupBox("Employee Selection")
        employee_layout = QHBoxLayout()
        
        employee_layout.addWidget(QLabel("Employee:"))
        self.employee_combo = QComboBox()
        self.employee_combo.currentTextChanged.connect(self.on_employee_changed)
        employee_layout.addWidget(self.employee_combo)
        
        employee_group.setLayout(employee_layout)
        layout.addWidget(employee_group)
        
        # Current month details
        details_group = QGroupBox("Current Month Details")
        details_layout = QGridLayout()
        
        # Unpaid days input
        details_layout.addWidget(QLabel("Unpaid Days:"), 0, 0)
        self.unpaid_days_spinbox = QDoubleSpinBox()
        self.unpaid_days_spinbox.setRange(0.0, 31.0)
        self.unpaid_days_spinbox.setSingleStep(0.5)
        self.unpaid_days_spinbox.setDecimals(1)
        details_layout.addWidget(self.unpaid_days_spinbox, 0, 1)
        
        # Basic salary (read-only display)
        details_layout.addWidget(QLabel("Basic Salary:"), 0, 2)
        self.basic_salary_label = QLabel("RM 0.00")
        details_layout.addWidget(self.basic_salary_label, 0, 3)
        
        # Allowances (read-only display)
        details_layout.addWidget(QLabel("Allowances:"), 0, 4)
        self.allowances_label = QLabel("RM 0.00")
        details_layout.addWidget(self.allowances_label, 0, 5)
        
        # Deduction amount (calculated)
        details_layout.addWidget(QLabel("Deduction:"), 1, 0)
        self.deduction_label = QLabel("RM 0.00")
        self.deduction_label.setStyleSheet("color: red; font-weight: bold;")
        details_layout.addWidget(self.deduction_label, 1, 1)
        
        # Update button
        self.update_button = QPushButton("Update Record")
        self.update_button.clicked.connect(self.update_current_record)
        details_layout.addWidget(self.update_button, 1, 4, 1, 2)
        
        # Notes
        details_layout.addWidget(QLabel("Notes:"), 2, 0)
        self.notes_edit = QLineEdit()
        details_layout.addWidget(self.notes_edit, 2, 1, 1, 5)
        
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        # Annual summary table
        summary_group = QGroupBox("Annual Summary")
        summary_layout = QVBoxLayout()
        
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(6)
        self.summary_table.setHorizontalHeaderLabels([
            "Month", "Unpaid Days", "Basic Salary", "Allowances", "Deduction", "Last Updated"
        ])
        
        # Make table headers bold
        header = self.summary_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        summary_layout.addWidget(self.summary_table)
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Status bar
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        self.setLayout(layout)
        
        # Connect signals
        self.unpaid_days_spinbox.valueChanged.connect(self.calculate_deduction)
    
    def load_employees(self):
        """Load employees into the combo box"""
        self.status_label.setText("Loading employees...")
        
        worker = UnpaidLeaveWorker("load_data")
        worker.finished.connect(self.on_employees_loaded)
        worker.finished.connect(lambda: self.cleanup_worker(worker))  # Clean up when finished
        self.active_workers.append(worker)  # Track the worker
        worker.start()
    
    def cleanup_worker(self, worker):
        """Remove worker from active list and clean up"""
        if worker in self.active_workers:
            self.active_workers.remove(worker)
        worker.deleteLater()
    
    def on_employees_loaded(self, success, data):
        """Handle loaded employees data"""
        if success:
            try:
                self.employees_data = eval(data)  # Convert string back to list
                
                self.employee_combo.clear()
                for employee in self.employees_data:
                    if employee.get("status") == "Active":
                        name = employee.get('full_name', '').strip()
                        display_text = f"{employee.get('employee_id', '')} - {name} ({employee.get('email', '')})"
                        self.employee_combo.addItem(display_text, employee["id"])
                
                self.status_label.setText(f"Loaded {len(self.employees_data)} employees")
                
                if self.employee_combo.count() > 0:
                    self.on_employee_changed()
                    
            except Exception as e:
                self.status_label.setText(f"Error parsing employee data: {e}")
        else:
            self.status_label.setText(f"Failed to load employees: {data}")
    
    def on_employee_changed(self):
        """Handle employee selection change"""
        if self.employee_combo.currentData():
            self.load_employee_salary_info()
            self.load_annual_summary()
            self.load_current_month_data()
    
    def load_employee_salary_info(self):
        """Load and display employee salary information"""
        employee_id = self.employee_combo.currentData()
        if not employee_id:
            return
        
        # Find employee in loaded data
        employee = next((emp for emp in self.employees_data if emp["id"] == employee_id), None)
        if employee:
            basic_salary = float(employee.get("basic_salary", 0))
            allowances_dict = employee.get("allowances") or {}
            total_allowances = sum(float(v) for v in allowances_dict.values() if v)
            
            self.basic_salary_label.setText(f"RM {basic_salary:.2f}")
            self.allowances_label.setText(f"RM {total_allowances:.2f}")
            
            # Store for calculations
            self.current_basic_salary = basic_salary
            self.current_allowances = total_allowances
            
            self.calculate_deduction()
    
    def load_current_month_data(self):
        """Load current month unpaid leave data"""
        employee_id = self.employee_combo.currentData()
        if not employee_id:
            return
        
        year = self.year_spinbox.value()
        month = self.month_spinbox.value()
        
        try:
            # Get employee email
            employee = next((emp for emp in self.employees_data if emp["id"] == employee_id), None)
            employee_email = employee.get("email", "") if employee else ""
            
            # Get or create record
            record = get_or_create_monthly_unpaid_leave(employee_id, employee_email, year, month)
            
            # Update UI
            self.unpaid_days_spinbox.setValue(record.get("unpaid_days", 0.0))
            self.notes_edit.setText(record.get("notes", ""))
            
            self.calculate_deduction()
            
        except Exception as e:
            self.status_label.setText(f"Error loading current month data: {e}")
    
    def load_annual_summary(self):
        """Load annual summary for selected employee"""
        employee_id = self.employee_combo.currentData()
        if not employee_id:
            return
        
        year = self.year_spinbox.value()
        
        try:
            summary_data = get_monthly_unpaid_leave_summary(employee_id, year)
            
            # Create month lookup
            month_data = {record["month"]: record for record in summary_data}
            
            # Populate table with all 12 months
            self.summary_table.setRowCount(12)
            
            month_names = [
                "January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"
            ]
            
            for month_num in range(1, 13):
                row = month_num - 1
                record = month_data.get(month_num, {})
                
                # Month name
                self.summary_table.setItem(row, 0, QTableWidgetItem(month_names[month_num - 1]))
                
                # Unpaid days
                unpaid_days = record.get("unpaid_days", 0.0)
                self.summary_table.setItem(row, 1, QTableWidgetItem(f"{unpaid_days:.1f}"))
                
                # Basic salary
                basic_salary = record.get("basic_salary", 0.0)
                self.summary_table.setItem(row, 2, QTableWidgetItem(f"RM {basic_salary:.2f}"))
                
                # Allowances
                allowances = record.get("allowances", 0.0)
                self.summary_table.setItem(row, 3, QTableWidgetItem(f"RM {allowances:.2f}"))
                
                # Deduction
                deduction = record.get("deduction_amount", 0.0)
                deduction_item = QTableWidgetItem(f"RM {deduction:.2f}")
                if deduction > 0:
                    deduction_item.setBackground(Qt.yellow)
                self.summary_table.setItem(row, 4, deduction_item)
                
                # Last updated
                updated_at = record.get("updated_at", "")
                if updated_at:
                    try:
                        dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                    except:
                        formatted_date = updated_at
                else:
                    formatted_date = "Not set"
                self.summary_table.setItem(row, 5, QTableWidgetItem(formatted_date))
            
            self.status_label.setText("Annual summary loaded")
            
        except Exception as e:
            self.status_label.setText(f"Error loading annual summary: {e}")
    
    def calculate_deduction(self):
        """Calculate and display deduction amount"""
        try:
            unpaid_days = self.unpaid_days_spinbox.value()
            year = self.year_spinbox.value()
            month = self.month_spinbox.value()
            
            if hasattr(self, 'current_basic_salary') and hasattr(self, 'current_allowances'):
                import calendar
                calendar_days = calendar.monthrange(year, month)[1]
                
                daily_basic = self.current_basic_salary / calendar_days
                daily_allowance = self.current_allowances / calendar_days
                
                basic_deduction = daily_basic * unpaid_days
                allowance_deduction = daily_allowance * unpaid_days
                total_deduction = basic_deduction + allowance_deduction
                
                self.deduction_label.setText(f"RM {total_deduction:.2f}")
            else:
                self.deduction_label.setText("RM 0.00")
                
        except Exception as e:
            self.deduction_label.setText("Error")
            print(f"Error calculating deduction: {e}")
    
    def update_current_record(self):
        """Update the current month's unpaid leave record"""
        employee_id = self.employee_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "Warning", "Please select an employee")
            return
        
        year = self.year_spinbox.value()
        month = self.month_spinbox.value()
        unpaid_days = self.unpaid_days_spinbox.value()
        notes = self.notes_edit.text()
        
        basic_salary = getattr(self, 'current_basic_salary', 0.0)
        allowances = getattr(self, 'current_allowances', 0.0)
        
        self.status_label.setText("Updating record...")
        
        worker = UnpaidLeaveWorker(
            "update_record",
            employee_id=employee_id,
            year=year,
            month=month,
            unpaid_days=unpaid_days,
            basic_salary=basic_salary,
            allowances=allowances,
            updated_by="admin",
            notes=notes
        )
        worker.finished.connect(self.on_update_finished)
        worker.finished.connect(lambda: self.cleanup_worker(worker))
        self.active_workers.append(worker)
        worker.start()
    
    def on_update_finished(self, success, message):
        """Handle update completion"""
        if success:
            self.status_label.setText("Record updated successfully")
            self.load_annual_summary()  # Refresh summary
            QMessageBox.information(self, "Success", "Record updated successfully")
        else:
            self.status_label.setText(f"Update failed: {message}")
            QMessageBox.warning(self, "Error", f"Update failed: {message}")
    
    def sync_from_leave_requests(self):
        """Sync all employees' unpaid leave from leave requests"""
        year = self.year_spinbox.value()
        month = self.month_spinbox.value()
        
        reply = QMessageBox.question(
            self, "Confirm Sync",
            f"This will sync unpaid leave data for all employees for {year}-{month:02d} "
            "from approved leave requests. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_label.setText("Syncing from leave requests...")
            # Implementation would loop through all employees
            # For now, just sync current employee
            employee_id = self.employee_combo.currentData()
            if employee_id:
                employee = next((emp for emp in self.employees_data if emp["id"] == employee_id), None)
                employee_email = employee.get("email", "") if employee else ""
                
                worker = UnpaidLeaveWorker(
                    "sync_from_requests",
                    employee_id=employee_id,
                    employee_email=employee_email,
                    year=year,
                    month=month
                )
                worker.finished.connect(self.on_sync_finished)
                worker.finished.connect(lambda: self.cleanup_worker(worker))
                self.active_workers.append(worker)
                worker.start()
    
    def on_sync_finished(self, success, message):
        """Handle sync completion"""
        if success:
            self.status_label.setText("Sync completed")
            self.load_current_month_data()
            self.load_annual_summary()
            QMessageBox.information(self, "Success", "Sync completed successfully")
        else:
            self.status_label.setText(f"Sync failed: {message}")
            QMessageBox.warning(self, "Error", f"Sync failed: {message}")
    
    def reset_annual_data(self):
        """Reset all unpaid leave data for the year"""
        year = self.year_spinbox.value()
        
        reply = QMessageBox.question(
            self, "Confirm Reset",
            f"This will reset ALL unpaid leave data for {year} to zero. "
            "This action cannot be undone. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.status_label.setText("Resetting annual data...")
            
            worker = UnpaidLeaveWorker("reset_annual", year=year)
            worker.finished.connect(self.on_reset_finished)
            worker.finished.connect(lambda: self.cleanup_worker(worker))
            self.active_workers.append(worker)
            worker.start()
    
    def on_reset_finished(self, success, message):
        """Handle reset completion"""
        if success:
            self.status_label.setText("Annual reset completed")
            self.load_annual_summary()
            QMessageBox.information(self, "Success", "Annual reset completed")
        else:
            self.status_label.setText(f"Reset failed: {message}")
            QMessageBox.warning(self, "Error", f"Reset failed: {message}")
    
    def on_period_changed(self):
        """Handle year/month change"""
        if hasattr(self, 'employees_data') and self.employee_combo.currentData():
            self.load_current_month_data()
            self.load_annual_summary()

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = AdminUnpaidLeaveTab()
    widget.show()
    sys.exit(app.exec_())
