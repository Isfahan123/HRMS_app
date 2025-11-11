from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QDialog, QFormLayout, QLineEdit, 
    QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QMessageBox,
    QGroupBox, QCheckBox, QFrame
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtGui import QFont
from datetime import datetime, date
from services.supabase_service import supabase, KL_TZ
import json

class BonusDialog(QDialog):
    def __init__(self, bonus_data=None, parent=None):
        super().__init__(parent)
        self.bonus_data = bonus_data
        self.setWindowTitle("Edit Bonus" if bonus_data else "Add Bonus")
        self.setModal(True)
        self.setMinimumSize(300, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Create form
        form_layout = QFormLayout()

        # Employee selection
        self.employee_combo = QComboBox()
        self.load_employees()
        form_layout.addRow("Employee:", self.employee_combo)

        # Bonus type
        self.bonus_type_combo = QComboBox()
        self.bonus_type_combo.addItems([
            "Annual Bonus", 
            "Performance Bonus", 
            "Festive Bonus", 
            "Quarterly Bonus",
            "Project Completion Bonus",
            "Retention Bonus",
            "Other"
        ])
        form_layout.addRow("Bonus Type:", self.bonus_type_combo)

        # Custom bonus type (for "Other")
        self.custom_type_edit = QLineEdit()
        self.custom_type_edit.setPlaceholderText("Enter custom bonus type")
        self.custom_type_edit.setEnabled(False)
        form_layout.addRow("Custom Type:", self.custom_type_edit)

        # Connect bonus type change to enable/disable custom type
        self.bonus_type_combo.currentTextChanged.connect(self.on_bonus_type_changed)

        # Amount
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.01, 999999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setSuffix(" RM")
        form_layout.addRow("Amount:", self.amount_spinbox)

        # Effective date
        self.effective_date = QDateEdit()
        self.effective_date.setDate(QDate.currentDate())
        self.effective_date.setCalendarPopup(True)
        form_layout.addRow("Effective Date:", self.effective_date)

        # Expiry date (optional)
        self.expiry_date = QDateEdit()
        self.expiry_date.setDate(QDate.currentDate().addYears(1))
        self.expiry_date.setCalendarPopup(True)
        self.has_expiry = QCheckBox("Set expiry date")
        self.has_expiry.toggled.connect(self.expiry_date.setEnabled)
        self.expiry_date.setEnabled(False)
        
        expiry_layout = QHBoxLayout()
        expiry_layout.addWidget(self.has_expiry)
        expiry_layout.addWidget(self.expiry_date)
        form_layout.addRow("Expiry:", expiry_layout)

        # Is recurring
        self.is_recurring = QCheckBox("Recurring bonus")
        form_layout.addRow("", self.is_recurring)

        # Recurrence frequency (only for recurring bonuses)
        self.recurrence_combo = QComboBox()
        self.recurrence_combo.addItems(["Monthly", "Quarterly", "Yearly"])
        self.recurrence_combo.setEnabled(False)
        self.is_recurring.toggled.connect(self.recurrence_combo.setEnabled)
        form_layout.addRow("Frequency:", self.recurrence_combo)

        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        self.description_edit.setPlaceholderText("Optional description or notes about this bonus")
        form_layout.addRow("Description:", self.description_edit)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Expired"])
        form_layout.addRow("Status:", self.status_combo)

        layout.addLayout(form_layout)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save")
        self.save_btn
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn
        
        self.save_btn.clicked.connect(self.save_bonus)
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Populate form if editing
        if self.bonus_data:
            self.populate_form()

    def load_employees(self):
        """Load all employees into the combo box"""
        try:
            response = supabase.table("employees").select("id, full_name, employee_id").execute()
            if response.data:
                for employee in response.data:
                    display_text = f"{employee['full_name']} ({employee['employee_id']})"
                    self.employee_combo.addItem(display_text, employee['id'])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load employees: {str(e)}")

    def on_bonus_type_changed(self, text):
        """Enable/disable custom type field based on bonus type selection"""
        self.custom_type_edit.setEnabled(text == "Other")
        if text != "Other":
            self.custom_type_edit.clear()

    def populate_form(self):
        """Populate form with existing bonus data"""
        if not self.bonus_data:
            return

        # Set employee
        employee_id = self.bonus_data.get('employee_id')
        for i in range(self.employee_combo.count()):
            if self.employee_combo.itemData(i) == employee_id:
                self.employee_combo.setCurrentIndex(i)
                break

        # Set bonus type
        bonus_type = self.bonus_data.get('bonus_type', '')
        index = self.bonus_type_combo.findText(bonus_type)
        if index >= 0:
            self.bonus_type_combo.setCurrentIndex(index)
        else:
            # Custom type
            self.bonus_type_combo.setCurrentText("Other")
            self.custom_type_edit.setText(bonus_type)

        # Set amount
        self.amount_spinbox.setValue(float(self.bonus_data.get('amount', 0)))

        # Set dates
        effective_date = self.bonus_data.get('effective_date')
        if effective_date:
            date_obj = datetime.fromisoformat(effective_date.replace('Z', '+00:00')).date()
            self.effective_date.setDate(QDate(date_obj))

        expiry_date = self.bonus_data.get('expiry_date')
        if expiry_date:
            self.has_expiry.setChecked(True)
            date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).date()
            self.expiry_date.setDate(QDate(date_obj))

        # Set recurring
        self.is_recurring.setChecked(self.bonus_data.get('is_recurring', False))
        
        recurrence = self.bonus_data.get('recurrence_frequency', 'Monthly')
        index = self.recurrence_combo.findText(recurrence)
        if index >= 0:
            self.recurrence_combo.setCurrentIndex(index)

        # Set description
        self.description_edit.setPlainText(self.bonus_data.get('description', ''))

        # Set status
        status = self.bonus_data.get('status', 'Active')
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)

    def save_bonus(self):
        """Save or update bonus"""
        try:
            # Validate required fields
            if self.employee_combo.currentIndex() == -1:
                QMessageBox.warning(self, "Validation Error", "Please select an employee.")
                return

            if self.amount_spinbox.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Amount must be greater than 0.")
                return

            # Get bonus type
            bonus_type = self.bonus_type_combo.currentText()
            if bonus_type == "Other":
                bonus_type = self.custom_type_edit.text().strip()
                if not bonus_type:
                    QMessageBox.warning(self, "Validation Error", "Please enter a custom bonus type.")
                    return

            # Prepare data
            bonus_data = {
                'employee_id': self.employee_combo.currentData(),
                'bonus_type': bonus_type,
                'amount': self.amount_spinbox.value(),
                'effective_date': self.effective_date.date().toString(Qt.ISODate),
                'expiry_date': self.expiry_date.date().toString(Qt.ISODate) if self.has_expiry.isChecked() else None,
                'is_recurring': self.is_recurring.isChecked(),
                'recurrence_frequency': self.recurrence_combo.currentText() if self.is_recurring.isChecked() else None,
                'description': self.description_edit.toPlainText().strip() or None,
                'status': self.status_combo.currentText(),
                'created_at': datetime.now(KL_TZ).isoformat(),
                'updated_at': datetime.now(KL_TZ).isoformat()
            }

            if self.bonus_data:
                # Update existing bonus
                response = supabase.table("bonuses").update(bonus_data).eq("id", self.bonus_data['id']).execute()
            else:
                # Create new bonus
                response = supabase.table("bonuses").insert(bonus_data).execute()

            if response.data:
                QMessageBox.information(self, "Success", "Bonus saved successfully!")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save bonus.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save bonus: {str(e)}")

class AdminBonusTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_bonuses()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("💰 Bonus Management")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Action buttons
        self.add_bonus_btn = QPushButton("➕ Add Bonus")
        self.add_bonus_btn
        self.edit_bonus_btn = QPushButton("✏️ Edit Bonus")
        self.edit_bonus_btn
        self.delete_bonus_btn = QPushButton("🗑️ Delete Bonus")
        self.delete_bonus_btn
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn

        self.add_bonus_btn.clicked.connect(self.add_bonus)
        self.edit_bonus_btn.clicked.connect(self.edit_bonus)
        self.delete_bonus_btn.clicked.connect(self.delete_bonus)
        self.refresh_btn.clicked.connect(self.load_bonuses)

        header_layout.addWidget(self.add_bonus_btn)
        header_layout.addWidget(self.edit_bonus_btn)
        header_layout.addWidget(self.delete_bonus_btn)
        header_layout.addWidget(self.refresh_btn)

        layout.addLayout(header_layout)

        # Filter section
        filter_group = QGroupBox("Filters")
        filter_layout = QHBoxLayout()

        # Status filter
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Active", "Inactive", "Expired"])
        self.status_filter.currentTextChanged.connect(self.load_bonuses)
        filter_layout.addWidget(self.status_filter)

        # Bonus type filter
        filter_layout.addWidget(QLabel("Type:"))
        self.type_filter = QComboBox()
        self.type_filter.addItem("All")
        self.type_filter.currentTextChanged.connect(self.load_bonuses)
        filter_layout.addWidget(self.type_filter)

        filter_layout.addStretch()
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)

        # Bonuses table
        self.bonuses_table = QTableWidget()
        self.bonuses_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.bonuses_table.setAlternatingRowColors(True)
        self.bonuses_table.setSortingEnabled(True)
        
        # Set up table headers
        headers = [
            "Employee", "Employee ID", "Bonus Type", "Amount (RM)", 
            "Effective Date", "Expiry Date", "Status", "Recurring", "Description"
        ]
        self.bonuses_table.setColumnCount(len(headers))
        self.bonuses_table.setHorizontalHeaderLabels(headers)
        
        # Adjust column widths
        header = self.bonuses_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Employee
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Employee ID
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Bonus Type
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Effective Date
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Expiry Date
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Recurring
        header.setSectionResizeMode(8, QHeaderView.Stretch)           # Description

        layout.addWidget(self.bonuses_table)

        # Summary section
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()
        
        self.total_bonuses_label = QLabel("Total Bonuses: 0")
        self.active_bonuses_label = QLabel("Active: 0")
        self.total_amount_label = QLabel("Total Amount: RM 0.00")
        
        summary_layout.addWidget(self.total_bonuses_label)
        summary_layout.addWidget(self.active_bonuses_label)
        summary_layout.addWidget(self.total_amount_label)
        summary_layout.addStretch()
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        self.setLayout(layout)

        # Initially disable edit/delete buttons
        self.edit_bonus_btn.setEnabled(False)
        self.delete_bonus_btn.setEnabled(False)

        # Connect table selection
        self.bonuses_table.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def load_bonuses(self):
        """Load bonuses from database"""
        try:
            # Build query with filters
            query = supabase.table("bonuses").select("""
                id, employee_id, bonus_type, amount, effective_date, expiry_date, 
                status, is_recurring, recurrence_frequency, description, created_at
            """)

            # Apply status filter
            status_filter = self.status_filter.currentText()
            if status_filter != "All":
                query = query.eq("status", status_filter)

            # Apply type filter
            type_filter = self.type_filter.currentText()
            if type_filter != "All":
                query = query.eq("bonus_type", type_filter)

            # Execute query and manually enrich with employee data
            response = query.order("created_at", desc=True).execute()
            if response.data:
                for bonus in response.data:
                    employee_id = bonus.get('employee_id')
                    if employee_id:
                        try:
                            emp_result = supabase.table("employees").select("full_name, employee_id").eq("id", employee_id).execute()
                            if emp_result.data:
                                bonus['employees'] = emp_result.data[0]
                            else:
                                bonus['employees'] = {'full_name': 'Unknown Employee', 'employee_id': 'Unknown'}
                        except Exception:
                            bonus['employees'] = {'full_name': 'Unknown Employee', 'employee_id': 'Unknown'}
                    else:
                        bonus['employees'] = {'full_name': 'Unknown Employee', 'employee_id': 'Unknown'}

                self.populate_bonuses_table(response.data)
                self.update_bonus_types_filter(response.data)
                self.update_summary(response.data)
            else:
                self.bonuses_table.setRowCount(0)
                self.update_summary([])

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load bonuses: {str(e)}")

    def populate_bonuses_table(self, bonuses):
        """Populate the bonuses table"""
        self.bonuses_table.setRowCount(len(bonuses))
        
        for row, bonus in enumerate(bonuses):
            employee_data = bonus.get('employees', {})
            
            # Employee name
            self.bonuses_table.setItem(row, 0, QTableWidgetItem(employee_data.get('full_name', 'N/A')))
            
            # Employee ID
            self.bonuses_table.setItem(row, 1, QTableWidgetItem(employee_data.get('employee_id', 'N/A')))
            
            # Bonus type
            self.bonuses_table.setItem(row, 2, QTableWidgetItem(bonus.get('bonus_type', '')))
            
            # Amount
            amount = float(bonus.get('amount', 0))
            self.bonuses_table.setItem(row, 3, QTableWidgetItem(f"{amount:.2f}"))
            
            # Effective date
            effective_date = bonus.get('effective_date', '')
            if effective_date:
                date_obj = datetime.fromisoformat(effective_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
                self.bonuses_table.setItem(row, 4, QTableWidgetItem(formatted_date))
            else:
                self.bonuses_table.setItem(row, 4, QTableWidgetItem('N/A'))
            
            # Expiry date
            expiry_date = bonus.get('expiry_date', '')
            if expiry_date:
                date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%Y-%m-%d')
                self.bonuses_table.setItem(row, 5, QTableWidgetItem(formatted_date))
            else:
                self.bonuses_table.setItem(row, 5, QTableWidgetItem('N/A'))
            
            # Status
            status = bonus.get('status', 'Active')
            status_item = QTableWidgetItem(status)
            if status == 'Active':
                status_item.setBackground(Qt.lightGray)
            elif status == 'Expired':
                status_item.setBackground(Qt.red)
            self.bonuses_table.setItem(row, 6, status_item)
            
            # Recurring
            is_recurring = bonus.get('is_recurring', False)
            recurring_text = "Yes" if is_recurring else "No"
            if is_recurring:
                frequency = bonus.get('recurrence_frequency', '')
                recurring_text += f" ({frequency})"
            self.bonuses_table.setItem(row, 7, QTableWidgetItem(recurring_text))
            
            # Description
            description = bonus.get('description', '')
            self.bonuses_table.setItem(row, 8, QTableWidgetItem(description))
            
            # Store bonus ID in the first column for reference
            self.bonuses_table.item(row, 0).setData(Qt.UserRole, bonus.get('id'))

    def update_bonus_types_filter(self, bonuses):
        """Update bonus types filter dropdown"""
        current_selection = self.type_filter.currentText()
        self.type_filter.clear()
        self.type_filter.addItem("All")
        
        # Get unique bonus types
        bonus_types = set()
        for bonus in bonuses:
            bonus_type = bonus.get('bonus_type', '')
            if bonus_type:
                bonus_types.add(bonus_type)
        
        for bonus_type in sorted(bonus_types):
            self.type_filter.addItem(bonus_type)
        
        # Restore selection if it still exists
        index = self.type_filter.findText(current_selection)
        if index >= 0:
            self.type_filter.setCurrentIndex(index)

    def update_summary(self, bonuses):
        """Update summary statistics"""
        total_bonuses = len(bonuses)
        active_bonuses = len([b for b in bonuses if b.get('status') == 'Active'])
        total_amount = sum(float(b.get('amount', 0)) for b in bonuses if b.get('status') == 'Active')
        
        self.total_bonuses_label.setText(f"Total Bonuses: {total_bonuses}")
        self.active_bonuses_label.setText(f"Active: {active_bonuses}")
        self.total_amount_label.setText(f"Total Amount: RM {total_amount:.2f}")

    def on_selection_changed(self):
        """Handle table selection changes"""
        selected_rows = self.bonuses_table.selectionModel().selectedRows()
        has_selection = len(selected_rows) > 0
        
        self.edit_bonus_btn.setEnabled(has_selection)
        self.delete_bonus_btn.setEnabled(has_selection)

    def add_bonus(self):
        """Add new bonus"""
        dialog = BonusDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_bonuses()

    def edit_bonus(self):
        """Edit selected bonus"""
        selected_rows = self.bonuses_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        bonus_id = self.bonuses_table.item(row, 0).data(Qt.UserRole)

        try:
            # Get bonus data
            response = supabase.table("bonuses").select("*").eq("id", bonus_id).execute()
            if response.data:
                bonus_data = response.data[0]
                dialog = BonusDialog(bonus_data, parent=self)
                if dialog.exec_() == QDialog.Accepted:
                    self.load_bonuses()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load bonus data: {str(e)}")

    def delete_bonus(self):
        """Delete selected bonus"""
        selected_rows = self.bonuses_table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        bonus_id = self.bonuses_table.item(row, 0).data(Qt.UserRole)
        employee_name = self.bonuses_table.item(row, 0).text()
        bonus_type = self.bonuses_table.item(row, 2).text()

        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete the {bonus_type} bonus for {employee_name}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                response = supabase.table("bonuses").delete().eq("id", bonus_id).execute()
                if response.data:
                    QMessageBox.information(self, "Success", "Bonus deleted successfully!")
                    self.load_bonuses()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete bonus.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete bonus: {str(e)}")
