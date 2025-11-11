"""
Sick Leave Balance Management Widget
Manages employee sick leave and hospitalization balances
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QLabel, QGroupBox, QPushButton, QHeaderView,
    QMessageBox, QFileDialog, QDialog, QFormLayout, QDialogButtonBox, QDoubleSpinBox, QSpinBox, QWidget as QtWidget
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont

from datetime import datetime
import csv

# Import functions from supabase service
try:
    from services.supabase_service import (
        get_employee_sick_leave_balances,  # This is the actual function name
        get_individual_employee_sick_leave_balance,
        update_employee_sick_leave_balance
    )
except ImportError:
    def get_employee_sick_leave_balances(year):
        """Fallback function"""
        return []
    
    def get_individual_employee_sick_leave_balance(email, year):
        """Fallback function"""
        return {
            "sick_days_entitlement": 14, 
            "used_sick_days": 0,
            "hospitalization_days_entitlement": 60,
            "used_hospitalization_days": 0
        }
    
    def update_employee_sick_leave_balance(email, year, **kwargs):
        """Fallback function"""
        return True

class SickBalanceWidget(QWidget):
    """Widget for managing sick leave and hospitalization balances"""
    
    balance_viewed = pyqtSignal(str)   # Emitted when a balance is viewed (employee email)
    balance_updated = pyqtSignal(str)  # Emitted when a balance is updated (employee email)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SickBalanceWidget")
        
        # Data storage
        self.original_balances = []
        
        self.init_ui()
        self.load_balances()
    
    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("🏥 Sick Leave Balance Management")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Controls section
        self.create_controls(layout)
        
        # Balance table
        self.create_balance_table(layout)
        
        # Action buttons
        self.create_actions(layout)
    
    def create_controls(self, parent_layout):
        """Create control elements"""
        controls_group = QGroupBox("Sick Leave Balance Controls")
        controls_layout = QHBoxLayout()
        
        # Employee filter
        controls_layout.addWidget(QLabel("Employee:"))
        self.employee_filter = QLineEdit()
        self.employee_filter.setPlaceholderText("Search employee by email or name...")
        self.employee_filter.textChanged.connect(self.apply_filters)
        controls_layout.addWidget(self.employee_filter)
        
        # Year selector
        controls_layout.addWidget(QLabel("Year:"))
        self.year_selector = QComboBox()
        current_year = datetime.now().year
        for year in range(current_year - 2, current_year + 3):
            self.year_selector.addItem(str(year))
        self.year_selector.setCurrentText(str(current_year))
        self.year_selector.currentTextChanged.connect(self.load_balances)
        controls_layout.addWidget(self.year_selector)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self.load_balances)
        controls_layout.addWidget(refresh_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        parent_layout.addWidget(controls_group)
    
    def create_balance_table(self, parent_layout):
        """Create the balance table"""
        self.balance_table = QTableWidget()
        self.balance_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.balance_table.setAlternatingRowColors(True)
        self.balance_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.balance_table.setSortingEnabled(True)
        
        # Set up columns
        headers = [
            "Employee Email", "Employee Name", "Department", "Years of Service",
            "Sick Days Entitlement", "Used Sick Days", "Remaining Sick Days", 
            "Hospitalization Entitlement", "Used Hospitalization", "Remaining Hospitalization", "Actions"
        ]
        self.balance_table.setColumnCount(len(headers))
        self.balance_table.setHorizontalHeaderLabels(headers)
        
        # Configure column widths
        header = self.balance_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Email
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Name
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Department
        header.setSectionResizeMode(3, QHeaderView.Fixed)            # Years of Service
        header.setSectionResizeMode(4, QHeaderView.Fixed)            # Sick Days Entitlement
        header.setSectionResizeMode(5, QHeaderView.Fixed)            # Used Sick Days
        header.setSectionResizeMode(6, QHeaderView.Fixed)            # Remaining Sick Days
        header.setSectionResizeMode(7, QHeaderView.Fixed)            # Hospitalization Entitlement
        header.setSectionResizeMode(8, QHeaderView.Fixed)            # Used Hospitalization
        header.setSectionResizeMode(9, QHeaderView.Fixed)            # Remaining Hospitalization
        header.setSectionResizeMode(10, QHeaderView.Fixed)           # Actions
        
        # Set fixed widths for numeric columns
        self.balance_table.setColumnWidth(3, 100)  # Years of Service
        self.balance_table.setColumnWidth(4, 120)  # Sick Days Entitlement
        self.balance_table.setColumnWidth(5, 100)  # Used Sick Days
        self.balance_table.setColumnWidth(6, 120)  # Remaining Sick Days
        self.balance_table.setColumnWidth(7, 140)  # Hospitalization Entitlement
        self.balance_table.setColumnWidth(8, 140)  # Used Hospitalization
        self.balance_table.setColumnWidth(9, 140)  # Remaining Hospitalization
        self.balance_table.setColumnWidth(10, 100) # Actions
        
        # Set row height for buttons
        self.balance_table.verticalHeader().setDefaultSectionSize(55)
        self.balance_table.verticalHeader().setVisible(False)
        
        parent_layout.addWidget(self.balance_table)
    
    def create_actions(self, parent_layout):
        """Create action buttons"""
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()

        self.adjust_selected_btn = QPushButton("📝 Adjust Selected")
        self.adjust_selected_btn.clicked.connect(self.adjust_selected_balance)
        actions_layout.addWidget(self.adjust_selected_btn)

        self.export_btn = QPushButton("📊 Export Sick Leave Balances")
        self.export_btn.clicked.connect(self.export_balances)
        actions_layout.addWidget(self.export_btn)

        self.act_info_btn = QPushButton("📖 Employment Act 1955 Info")
        self.act_info_btn.clicked.connect(self.show_employment_act_info)
        actions_layout.addWidget(self.act_info_btn)

        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        parent_layout.addWidget(actions_group)
    
    def load_balances(self):
        """Load sick leave balances for the selected year"""
        try:
            year = int(self.year_selector.currentText())
            
            # Get all employees
            from services.supabase_service import supabase
            employees_response = supabase.table("employees").select(
                "employee_id, email, full_name, department, employment_type, date_joined"
            ).eq("status", "Active").execute()
            
            if not employees_response.data:
                print("DEBUG: No employees found")
                return
            
            self.original_balances = []
            
            for employee in employees_response.data:
                try:
                    # Calculate years of service
                    date_joined = datetime.strptime(employee['date_joined'], '%Y-%m-%d').date()
                    years_of_service = (datetime.now().date() - date_joined).days / 365.25
                    
                    # Get sick leave balance (falls back to policy defaults when missing)
                    balance = get_individual_employee_sick_leave_balance(employee['email'], year)
                    try:
                        from services.leave_caps_service import get_caps_for_years
                        policy_caps = get_caps_for_years(round(years_of_service, 2)) or {}
                    except Exception:
                        policy_caps = {}
                    
                    from core.employee_service import format_years

                    # Create balance record
                    balance_record = {
                        'email': employee['email'],
                        'full_name': employee['full_name'],
                        'department': employee['department'],
                        'employment_type': employee['employment_type'],
                        'years_of_service': round(years_of_service, 1),
                        'years_of_service_display': format_years(years_of_service) or f"{round(years_of_service,1):.1f}",
                        'sick_days_entitlement': balance.get('sick_days_entitlement', int(policy_caps.get('sick', 14))),
                        'used_sick_days': balance.get('used_sick_days', 0),
                        'hospitalization_days_entitlement': balance.get('hospitalization_days_entitlement', int(policy_caps.get('hospitalization', 60))),
                        'used_hospitalization_days': balance.get('used_hospitalization_days', 0),
                        'remaining_sick_days': 0,           # Will be calculated
                        'remaining_hospitalization': 0      # Will be calculated
                    }
                    
                    # Calculate remaining balances
                    balance_record['remaining_sick_days'] = max(0, 
                        balance_record['sick_days_entitlement'] - balance_record['used_sick_days']
                    )
                    balance_record['remaining_hospitalization'] = max(0,
                        balance_record['hospitalization_days_entitlement'] - balance_record['used_hospitalization_days']
                    )
                    
                    self.original_balances.append(balance_record)
                    
                except Exception as e:
                    print(f"Error processing employee {employee['email']}: {str(e)}")
                    continue
            
            print(f"DEBUG: Loaded {len(self.original_balances)} sick leave balance records")
            self.apply_filters()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load sick leave balances: {str(e)}")
            print(f"ERROR: Failed to load sick leave balances: {str(e)}")
    
    def apply_filters(self):
        """Apply current filters to the balance data"""
        try:
            search_text = self.employee_filter.text().strip().lower()
            
            # Filter balances
            filtered_balances = self.original_balances.copy()
            
            if search_text:
                filtered_balances = [
                    balance for balance in filtered_balances
                    if (search_text in balance['email'].lower() or 
                        search_text in balance['full_name'].lower())
                ]
            
            # Update table
            self.populate_table(filtered_balances)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to apply filters: {str(e)}")
    
    def populate_table(self, balances):
        """Populate the table with balance data"""
        try:
            self.balance_table.setRowCount(len(balances))
            
            for row, balance in enumerate(balances):
                # Employee Email
                self.balance_table.setItem(row, 0, QTableWidgetItem(balance['email']))
                
                # Employee Name
                self.balance_table.setItem(row, 1, QTableWidgetItem(balance['full_name']))
                
                # Department
                self.balance_table.setItem(row, 2, QTableWidgetItem(balance['department']))
                
                # Years of Service (display)
                yos_display = balance.get('years_of_service_display') if balance.get('years_of_service_display') is not None else str(balance['years_of_service'])
                self.balance_table.setItem(row, 3, QTableWidgetItem(str(yos_display)))
                
                # Sick Days Entitlement
                self.balance_table.setItem(row, 4, QTableWidgetItem(str(balance['sick_days_entitlement'])))
                
                # Used Sick Days
                self.balance_table.setItem(row, 5, QTableWidgetItem(str(balance['used_sick_days'])))
                
                # Remaining Sick Days
                self.balance_table.setItem(row, 6, QTableWidgetItem(str(balance['remaining_sick_days'])))
                
                # Hospitalization Entitlement
                self.balance_table.setItem(row, 7, QTableWidgetItem(str(balance['hospitalization_days_entitlement'])))
                
                # Used Hospitalization
                self.balance_table.setItem(row, 8, QTableWidgetItem(str(balance['used_hospitalization_days'])))
                
                # Remaining Hospitalization
                self.balance_table.setItem(row, 9, QTableWidgetItem(str(balance['remaining_hospitalization'])))
                
                # Actions cell with View + Adjust buttons
                cell_widget = QtWidget()
                cell_layout = QHBoxLayout(cell_widget)
                cell_layout.setContentsMargins(2, 2, 2, 2)
                view_btn = QPushButton("👁️ View")
                view_btn.setToolTip("View detailed sick & hospitalization leave balance")
                view_btn.clicked.connect(lambda checked, b=balance: self.view_balance_details(b))
                adj_btn = QPushButton("📝 Adjust")
                adj_btn.setToolTip("Adjust entitlement or used days for this employee")
                adj_btn.clicked.connect(lambda checked, b=balance: self.adjust_balance(b))
                cell_layout.addWidget(view_btn)
                cell_layout.addWidget(adj_btn)
                self.balance_table.setCellWidget(row, 10, cell_widget)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to populate sick leave balance table: {str(e)}")
    
    def view_balance_details(self, balance):
        """View detailed sick leave balance information"""
        try:
            details = f"""
Sick Leave Balance Details:

Employee: {balance['full_name']} ({balance['email']})
Department: {balance['department']}
Years of Service: {balance['years_of_service']} years

SICK LEAVE:
• Entitlement: {balance['sick_days_entitlement']} days
• Used: {balance['used_sick_days']} days
• Remaining: {balance['remaining_sick_days']} days

HOSPITALIZATION LEAVE:
• Entitlement: {balance['hospitalization_days_entitlement']} days
• Used: {balance['used_hospitalization_days']} days  
• Remaining: {balance['remaining_hospitalization']} days

MALAYSIAN EMPLOYMENT ACT 1955:
• Sick leave minimum: 14 days (less than 2 years service)
                    22 days (2+ years service)
• Hospitalization: Up to 60 days (inclusive of sick days)
• Medical certificate required for sick leave
"""
            
            QMessageBox.information(self, "Sick Leave Balance Details", details)
            self.balance_viewed.emit(balance['email'])
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to view balance details: {str(e)}")
    
    def export_balances(self):
        """Export sick leave balance data to CSV"""
        try:
            if self.balance_table.rowCount() == 0:
                QMessageBox.information(self, "Export", "No data to export")
                return
            
            # Get file path
            year = self.year_selector.currentText()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Sick Leave Balances", 
                f"sick_leave_balances_{year}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv)"
            )
            
            if not file_path:
                return
            
            # Write CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write headers
                headers = []
                for col in range(self.balance_table.columnCount() - 1):  # Exclude button column
                    headers.append(self.balance_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data
                for row in range(self.balance_table.rowCount()):
                    row_data = []
                    for col in range(self.balance_table.columnCount() - 1):  # Exclude button column
                        item = self.balance_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Complete", f"Sick leave balances exported to {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export balances: {str(e)}")
    
    def show_employment_act_info(self):
        """Show Malaysian Employment Act 1955 information for sick leave"""
        info_text = """
Malaysian Employment Act 1955 - Sick Leave Provisions

SICK LEAVE ENTITLEMENT:
• Less than 2 years of service: 14 days per calendar year
• 2 years or more of service: 22 days per calendar year
• Pro-rated for employees who join mid-year

HOSPITALIZATION LEAVE:
• Up to 60 days per calendar year
• Includes sick leave days (not additional to sick leave)
• For serious illness requiring hospitalization

MEDICAL CERTIFICATE REQUIREMENTS:
• Medical certificate from registered medical practitioner required
• Must be submitted within 48 hours (or as soon as reasonably possible)
• For hospitalization: Hospital discharge summary may be required

GENERAL PROVISIONS:
• Sick leave cannot be carried forward to the next year
• No payment in lieu of unused sick leave
• Employer may require medical examination
• False claims may result in disciplinary action

PAYMENT:
• Employee entitled to sick leave pay if on sick leave for 4+ consecutive days
• No payment for first 3 days of sick leave
• Payment subject to submission of medical certificate

Note: Company policy may provide more generous benefits than statutory minimums.
"""
        QMessageBox.information(self, "Employment Act 1955 - Sick Leave", info_text)
    
    def refresh_data(self):
        """Refresh the sick leave balance data"""
        self.load_balances()

    # ------------------------------------------------------------------
    # Adjustment logic
    # ------------------------------------------------------------------
    def adjust_selected_balance(self):
        """Adjust balance for the currently selected row"""
        current_row = self.balance_table.currentRow()
        if current_row < 0:
            QMessageBox.information(self, "No Selection", "Please select an employee row to adjust.")
            return
        email_item = self.balance_table.item(current_row, 0)
        if not email_item:
            QMessageBox.warning(self, "Error", "Selected row is invalid.")
            return
        email = email_item.text()
        balance = next((b for b in self.original_balances if b['email'] == email), None)
        if not balance:
            QMessageBox.warning(self, "Error", "Failed to resolve balance data for selected employee.")
            return
        self.adjust_balance(balance)

    def adjust_balance(self, balance):
        """Open adjustment dialog for a specific employee balance"""
        dialog = SickBalanceAdjustmentDialog(balance, self)
        if dialog.exec_() == QDialog.Accepted:
            adjustments = dialog.get_adjustments()
            try:
                year = int(self.year_selector.currentText())

                # Validation: used cannot be negative; warn if used exceeds entitlement
                used_sick = float(adjustments.get('used_sick_days', balance.get('used_sick_days', 0)))
                sick_ent = int(adjustments.get('sick_days_entitlement', balance.get('sick_days_entitlement', 0)))
                used_hosp = float(adjustments.get('used_hospitalization_days', balance.get('used_hospitalization_days', 0)))
                hosp_ent = int(adjustments.get('hospitalization_days_entitlement', balance.get('hospitalization_days_entitlement', 0)))

                warn_msgs = []
                if used_sick > sick_ent:
                    warn_msgs.append(f"Used sick days ({used_sick}) exceed entitlement ({sick_ent}).")
                if used_hosp > hosp_ent:
                    warn_msgs.append(f"Used hospitalization days ({used_hosp}) exceed entitlement ({hosp_ent}).")
                if warn_msgs:
                    reply = QMessageBox.question(
                        self,
                        "Confirm Over-Usage",
                        "\n".join(warn_msgs) + "\n\nDo you want to proceed anyway?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply != QMessageBox.Yes:
                        return

                success = update_employee_sick_leave_balance(balance['email'], year, **adjustments)
                if success:
                    QMessageBox.information(self, "Success", f"Sick balance adjusted for {balance['full_name']}")
                    self.load_balances()
                    self.balance_updated.emit(balance['email'])
                else:
                    QMessageBox.warning(self, "Update Failed", "Failed to update sick leave balance.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to adjust sick balance: {str(e)}")


class SickBalanceAdjustmentDialog(QDialog):
    """Dialog for adjusting sick & hospitalization leave balances"""
    def __init__(self, balance, parent=None):
        super().__init__(parent)
        self.balance = balance
        self.setWindowTitle(f"Adjust Sick Balance - {balance['full_name']}")
        self.setModal(True)
        self.resize(420, 360)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        info_lbl = QLabel(f"Employee: {self.balance['full_name']} ({self.balance['email']})")
        info_lbl.setStyleSheet("font-weight: bold; margin-bottom: 8px;")
        layout.addWidget(info_lbl)

        form = QFormLayout()

        # Sick entitlement
        self.sick_ent_spin = QSpinBox()
        self.sick_ent_spin.setRange(0, 90)
        try:
            self.sick_ent_spin.setValue(int(round(self.balance.get('sick_days_entitlement', 14))))
        except Exception:
            self.sick_ent_spin.setValue(14)
        form.addRow("Sick Entitlement (days):", self.sick_ent_spin)

        # Used sick days (allow half-days)
        self.used_sick_spin = QDoubleSpinBox()
        self.used_sick_spin.setDecimals(1)
        self.used_sick_spin.setSingleStep(0.5)
        self.used_sick_spin.setRange(0.0, 365.0)
        try:
            used_sick_val = float(self.balance.get('used_sick_days', 0.0))
        except Exception:
            used_sick_val = 0.0
        self.used_sick_spin.setValue(round(used_sick_val * 2) / 2.0)
        form.addRow("Used Sick Days:", self.used_sick_spin)

        # Hospitalization entitlement
        self.hosp_ent_spin = QSpinBox()
        self.hosp_ent_spin.setRange(0, 120)
        try:
            self.hosp_ent_spin.setValue(int(round(self.balance.get('hospitalization_days_entitlement', 60))))
        except Exception:
            self.hosp_ent_spin.setValue(60)
        form.addRow("Hospitalization Entitlement:", self.hosp_ent_spin)

        # Used hospitalization days (allow half-days)
        self.used_hosp_spin = QDoubleSpinBox()
        self.used_hosp_spin.setDecimals(1)
        self.used_hosp_spin.setSingleStep(0.5)
        self.used_hosp_spin.setRange(0.0, 365.0)
        try:
            used_hosp_val = float(self.balance.get('used_hospitalization_days', 0.0))
        except Exception:
            used_hosp_val = 0.0
        self.used_hosp_spin.setValue(round(used_hosp_val * 2) / 2.0)
        form.addRow("Used Hospitalization Days:", self.used_hosp_spin)

        layout.addLayout(form)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_adjustments(self):
        return {
            'sick_days_entitlement': self.sick_ent_spin.value(),
            'used_sick_days': float(self.used_sick_spin.value()),
            'hospitalization_days_entitlement': self.hosp_ent_spin.value(),
            'used_hospitalization_days': float(self.used_hosp_spin.value())
        }
