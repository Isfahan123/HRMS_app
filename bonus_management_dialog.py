from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QDateEdit, QTextEdit, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QMessageBox, QGroupBox, QCheckBox, QSpinBox, QDoubleSpinBox,
                             QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont
from datetime import datetime, date
import uuid

# Import supabase directly to avoid circular imports
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.supabase_service import supabase, get_variable_percentage_config, save_variable_percentage_config

class BonusManagementDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💰 Bonus Management")
        self.setModal(True)
        self.resize(800, 600)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("💰 Bonus Management System")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Controls section
        controls_group = QGroupBox("Bonus Controls")
        controls_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Add Bonus")
        self.add_btn
        self.add_btn.clicked.connect(self.add_bonus)
        controls_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Edit Bonus")
        self.edit_btn
        self.edit_btn.clicked.connect(self.edit_bonus)
        self.edit_btn.setEnabled(False)
        controls_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("🗑️ Delete Bonus")
        self.delete_btn
        self.delete_btn.clicked.connect(self.delete_bonus)
        self.delete_btn.setEnabled(False)
        controls_layout.addWidget(self.delete_btn)
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn
        self.refresh_btn.clicked.connect(self.load_data)
        controls_layout.addWidget(self.refresh_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Employee", "Bonus Type", "Amount (RM)", "Effective Date", 
            "Expiry Date", "Status", "Recurring", "Description"
        ])
        
        # Table settings
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # Description column
        
        # Connect selection change
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        layout.addWidget(self.table)
        
        # Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QHBoxLayout()
        
        self.total_label = QLabel("Total Bonuses: 0")
        self.active_label = QLabel("Active: 0")
        self.amount_label = QLabel("Total Amount: RM 0.00")
        
        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.active_label)
        summary_layout.addWidget(self.amount_label)
        summary_layout.addStretch()
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)

        # Global EPF Bonus Rules (editable) -------------------------------------------------
        self.epf_rules_group = QGroupBox("Global EPF Bonus Rules (affects payroll EPF calculation)")
        epf_rules_layout = QHBoxLayout()

        epf_rules_layout.addWidget(QLabel("Employer Rate (Part A, bonus rule):"))
        self.epf_part_a_employer_bonus = QDoubleSpinBox()
        self.epf_part_a_employer_bonus.setRange(0.0, 50.0)
        self.epf_part_a_employer_bonus.setSuffix(" %")
        self.epf_part_a_employer_bonus.setSingleStep(0.1)
        epf_rules_layout.addWidget(self.epf_part_a_employer_bonus)

        epf_rules_layout.addWidget(QLabel("Employer Rate (Part C, bonus rule):"))
        self.epf_part_c_employer_bonus = QDoubleSpinBox()
        self.epf_part_c_employer_bonus.setRange(0.0, 50.0)
        self.epf_part_c_employer_bonus.setSuffix(" %")
        self.epf_part_c_employer_bonus.setSingleStep(0.1)
        epf_rules_layout.addWidget(self.epf_part_c_employer_bonus)

        # Save button
        self.save_epf_rules_btn = QPushButton("💾 Save EPF Rules")
        self.save_epf_rules_btn.clicked.connect(self.save_epf_rules)
        epf_rules_layout.addWidget(self.save_epf_rules_btn)

        self.epf_rules_group.setLayout(epf_rules_layout)
        layout.addWidget(self.epf_rules_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

    def load_data(self):
        """Load bonuses from database"""
        try:
            # Update expired bonus statuses before loading data
            from services.supabase_service import update_expired_bonus_statuses
            updated_count = update_expired_bonus_statuses()
            if updated_count > 0:
                print(f"DEBUG: Updated {updated_count} expired bonuses to 'Expired' status")
            
            response = supabase.table("bonuses").select("""
                id, employee_id, bonus_type, amount, effective_date, expiry_date, 
                status, is_recurring, description
            """).execute()
            
            if response.data:
                # Manually enrich with employee data
                for bonus in response.data:
                    employee_id = bonus.get('employee_id')
                    if employee_id:
                        try:
                            emp_result = supabase.table("employees").select("full_name, employee_id, id").eq("id", employee_id).execute()
                            if emp_result.data:
                                bonus['employees'] = emp_result.data[0]
                            else:
                                bonus['employees'] = {'full_name': 'Unknown Employee', 'employee_id': 'Unknown', 'id': None}
                        except Exception:
                            bonus['employees'] = {'full_name': 'Unknown Employee', 'employee_id': 'Unknown', 'id': None}
                    else:
                        bonus['employees'] = {'full_name': 'Unknown Employee', 'employee_id': 'Unknown', 'id': None}
                
                self.table.setRowCount(len(response.data))
                total_amount = 0
                active_count = 0
                
                for row, bonus in enumerate(response.data):
                    employee_data = bonus.get('employees', {})
                    
                    # Store bonus ID in first column as user data
                    employee_item = QTableWidgetItem(employee_data.get('full_name', 'N/A'))
                    employee_item.setData(Qt.UserRole, bonus.get('id'))
                    self.table.setItem(row, 0, employee_item)
                    
                    self.table.setItem(row, 1, QTableWidgetItem(bonus.get('bonus_type', '')))
                    
                    amount = float(bonus.get('amount', 0))
                    self.table.setItem(row, 2, QTableWidgetItem(f"{amount:.2f}"))
                    
                    # Dates
                    effective_date = bonus.get('effective_date', '')
                    if effective_date:
                        date_obj = datetime.fromisoformat(effective_date.replace('Z', '+00:00'))
                        self.table.setItem(row, 3, QTableWidgetItem(date_obj.strftime('%Y-%m-%d')))
                    else:
                        self.table.setItem(row, 3, QTableWidgetItem('N/A'))
                    
                    expiry_date = bonus.get('expiry_date', '')
                    if expiry_date:
                        date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                        self.table.setItem(row, 4, QTableWidgetItem(date_obj.strftime('%Y-%m-%d')))
                    else:
                        self.table.setItem(row, 4, QTableWidgetItem('No Expiry'))
                    
                    status = bonus.get('status', 'Active')
                    self.table.setItem(row, 5, QTableWidgetItem(status))
                    
                    recurring = "Yes" if bonus.get('is_recurring', False) else "No"
                    self.table.setItem(row, 6, QTableWidgetItem(recurring))
                    
                    description = bonus.get('description', '')
                    self.table.setItem(row, 7, QTableWidgetItem(description))
                    
                    # Calculate summary
                    if status.lower() == 'active':
                        active_count += 1
                        total_amount += amount
                
                # Update summary
                self.total_label.setText(f"Total Bonuses: {len(response.data)}")
                self.active_label.setText(f"Active: {active_count}")
                self.amount_label.setText(f"Total Amount: RM {total_amount:.2f}")
                
            else:
                self.table.setRowCount(0)
                self.total_label.setText("Total Bonuses: 0")
                self.active_label.setText("Active: 0")
                self.amount_label.setText("Total Amount: RM 0.00")
            # Load EPF rules into the controls so the dialog shows current percentages
            try:
                self.load_epf_rules()
            except Exception:
                pass
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load bonuses: {str(e)}")
            # print(f"DEBUG: Error loading bonuses: {str(e)}")

    def load_epf_rules(self):
        """Load global EPF bonus-rule percentages into the dialog controls."""
        try:
            cfg = get_variable_percentage_config("default")
            if cfg:
                a = cfg.get('epf_part_a_employer_bonus')
                c = cfg.get('epf_part_c_employer_bonus')
                if a is not None:
                    try:
                        self.epf_part_a_employer_bonus.setValue(float(a))
                    except Exception:
                        pass
                if c is not None:
                    try:
                        self.epf_part_c_employer_bonus.setValue(float(c))
                    except Exception:
                        pass
            else:
                # Defaults if no config exists
                try:
                    self.epf_part_a_employer_bonus.setValue(13.0)
                    self.epf_part_c_employer_bonus.setValue(6.5)
                except Exception:
                    pass
        except Exception as e:
            print(f"DEBUG: Error loading EPF rules: {e}")

    def save_epf_rules(self):
        """Save the EPF bonus-rule percentages back to the variable percentage config."""
        try:
            val_a = float(self.epf_part_a_employer_bonus.value())
            val_c = float(self.epf_part_c_employer_bonus.value())
            payload = get_variable_percentage_config("default") or {}
            payload['epf_part_a_employer_bonus'] = val_a
            payload['epf_part_c_employer_bonus'] = val_c
            ok = save_variable_percentage_config(payload)
            if ok:
                QMessageBox.information(self, "Saved", "Global EPF bonus rules saved.")
            else:
                QMessageBox.warning(self, "Not Saved", "Failed to save EPF bonus rules.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to save EPF bonus rules: {e}")

    def on_selection_changed(self):
        """Enable/disable buttons based on selection"""
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)

    def add_bonus(self):
        """Add new bonus"""
        dialog = BonusEditDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def edit_bonus(self):
        """Edit selected bonus"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        bonus_id = self.table.item(row, 0).data(Qt.UserRole)
        
        dialog = BonusEditDialog(self, bonus_id)
        if dialog.exec_() == QDialog.Accepted:
            self.load_data()

    def delete_bonus(self):
        """Delete selected bonus"""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        row = selected_rows[0].row()
        bonus_id = self.table.item(row, 0).data(Qt.UserRole)
        employee_name = self.table.item(row, 0).text()
        bonus_type = self.table.item(row, 1).text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete the {bonus_type} bonus for {employee_name}?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                response = supabase.table("bonuses").delete().eq("id", bonus_id).execute()
                if response.data:
                    QMessageBox.information(self, "Success", "Bonus deleted successfully!")
                    self.load_data()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete bonus.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error deleting bonus: {str(e)}")

class BonusEditDialog(QDialog):
    def __init__(self, parent=None, bonus_id=None):
        super().__init__(parent)
        self.bonus_id = bonus_id
        self.setWindowTitle("Edit Bonus" if bonus_id else "Add Bonus")
        self.setModal(True)
        self.resize(500, 600)
        self.init_ui()
        if bonus_id:
            self.load_bonus_data()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Edit Bonus" if self.bonus_id else "Add New Bonus")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Employee selection
        layout.addWidget(QLabel("Employee:"))
        self.employee_combo = QComboBox()
        self.employee_combo.setEditable(True)
        self.employee_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.employee_combo.lineEdit().setPlaceholderText("Type to search or select employee...")
        self.load_employees()
        layout.addWidget(self.employee_combo)
        
        # Bonus type
        layout.addWidget(QLabel("Bonus Type:"))
        self.bonus_type_combo = QComboBox()
        self.bonus_type_combo.setEditable(True)
        self.bonus_type_combo.addItems([
            "Performance", "Annual", "Festival", "Sales Commission", 
            "Attendance", "Project", "Overtime", "Other"
        ])
        layout.addWidget(self.bonus_type_combo)
        
        # Amount
        layout.addWidget(QLabel("Amount (RM):"))
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        layout.addWidget(self.amount_edit)
        
        # Effective date
        layout.addWidget(QLabel("Effective Date:"))
        self.effective_date = QDateEdit()
        self.effective_date.setDate(QDate.currentDate())
        self.effective_date.setCalendarPopup(True)
        layout.addWidget(self.effective_date)
        
        # Expiry date
        layout.addWidget(QLabel("Expiry Date (Optional):"))
        expiry_layout = QHBoxLayout()
        self.has_expiry = QCheckBox("Set expiry date")
        self.expiry_date = QDateEdit()
        self.expiry_date.setDate(QDate.currentDate().addMonths(12))
        self.expiry_date.setCalendarPopup(True)
        self.expiry_date.setEnabled(False)
        
        self.has_expiry.toggled.connect(self.expiry_date.setEnabled)
        
        expiry_layout.addWidget(self.has_expiry)
        expiry_layout.addWidget(self.expiry_date)
        layout.addLayout(expiry_layout)
        
        # Status
        layout.addWidget(QLabel("Status:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Pending"])
        layout.addWidget(self.status_combo)
        
        # Recurring
        self.recurring_check = QCheckBox("Recurring bonus")
        layout.addWidget(self.recurring_check)
        
        # Description
        layout.addWidget(QLabel("Description (Optional):"))
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(80)
        layout.addWidget(self.description_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Save")
        save_btn
        save_btn.clicked.connect(self.save_bonus)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_employees(self):
        """Load employees into dropdown"""
        try:
            # Check if we need integer employee_id instead of UUID
            # Let's query the employees table to see its structure
            response = supabase.table("employees").select("*").limit(1).execute()
            if response.data:
                print(f"DEBUG: Sample employee record: {response.data[0]}")
                
            # Use both id (UUID) and any integer employee ID for proper referencing
            response = supabase.table("employees").select("*").execute()
            
            self.employee_combo.clear()
            if response.data:
                print(f"DEBUG: Loading {len(response.data)} employees")
                for employee in response.data:
                    # Check all fields to understand the structure
                    print(f"DEBUG: Employee record keys: {list(employee.keys())}")
                    
                    employee_uuid = employee.get('id')  # This might be UUID
                    employee_string_id = employee.get('employee_id')  # This is the string identifier
                    full_name = employee.get('full_name', 'N/A')
                    
                    # Look for any integer ID field that might be used for bonuses
                    integer_id = None
                    for key, value in employee.items():
                        if isinstance(value, int) and key.lower().endswith('id'):
                            integer_id = value
                            print(f"DEBUG: Found potential integer ID field: {key} = {value}")
                    
                    print(f"DEBUG: Employee UUID: {employee_uuid} (type: {type(employee_uuid)})")
                    print(f"DEBUG: Employee String ID: {employee_string_id} (type: {type(employee_string_id)})")
                    print(f"DEBUG: Integer ID: {integer_id}")
                    
                    # Use integer ID if available, otherwise use UUID
                    employee_ref_id = integer_id if integer_id is not None else employee_uuid
                    
                    # Validate UUID format only if we're using UUID
                    if integer_id is None:
                        import uuid as uuid_module
                        try:
                            if employee_uuid:
                                uuid_obj = uuid_module.UUID(str(employee_uuid))
                                valid_uuid = str(uuid_obj)
                                print(f"DEBUG: Valid UUID for {full_name}: {valid_uuid}")
                                employee_ref_id = valid_uuid
                            else:
                                print(f"DEBUG: Skipping employee {full_name} - no UUID")
                                continue
                        except (ValueError, TypeError) as e:
                            print(f"DEBUG: Skipping employee {full_name} - invalid UUID {employee_uuid}: {e}")
                            continue
                    
                    # Display string ID and name, store the appropriate ID for database reference
                    display_name = f"{full_name} ({employee_string_id})"
                    self.employee_combo.addItem(display_name, employee_ref_id)
                    print(f"DEBUG: Added employee {display_name} with ID {employee_ref_id}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load employees: {str(e)}")
            print(f"DEBUG: Error loading employees: {str(e)}")
            import traceback
            traceback.print_exc()

    def load_bonus_data(self):
        """Load existing bonus data for editing"""
        try:
            response = supabase.table("bonuses").select("""
                employee_id, bonus_type, amount, effective_date, expiry_date,
                status, is_recurring, description
            """).eq("id", self.bonus_id).execute()
            
            if response.data:
                bonus = response.data[0]
                
                # Find and select employee by UUID
                employee_uuid = bonus.get('employee_id')  # This should be a UUID
                # print(f"DEBUG: Looking for employee UUID: {employee_uuid}")
                
                for i in range(self.employee_combo.count()):
                    combo_uuid = self.employee_combo.itemData(i)
                    # print(f"DEBUG: Comparing {combo_uuid} with {employee_uuid}")
                    if combo_uuid == employee_uuid:
                        self.employee_combo.setCurrentIndex(i)
                        # print(f"DEBUG: Found matching employee at index {i}")
                        break
                
                # Set other fields
                self.bonus_type_combo.setCurrentText(bonus.get('bonus_type', ''))
                self.amount_edit.setText(str(bonus.get('amount', 0)))
                
                # Effective date
                effective_date = bonus.get('effective_date')
                if effective_date:
                    date_obj = datetime.fromisoformat(effective_date.replace('Z', '+00:00')).date()
                    self.effective_date.setDate(QDate(date_obj))
                
                # Expiry date
                expiry_date = bonus.get('expiry_date')
                if expiry_date:
                    self.has_expiry.setChecked(True)
                    date_obj = datetime.fromisoformat(expiry_date.replace('Z', '+00:00')).date()
                    self.expiry_date.setDate(QDate(date_obj))
                
                self.status_combo.setCurrentText(bonus.get('status', 'Active'))
                self.recurring_check.setChecked(bonus.get('is_recurring', False))
                self.description_edit.setPlainText(bonus.get('description', ''))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load bonus data: {str(e)}")
            # print(f"DEBUG: Error loading bonus data: {str(e)}")

    def save_bonus(self):
        """Save bonus to database"""
        try:
            # Validate inputs
            if not self.employee_combo.currentData():
                QMessageBox.warning(self, "Validation Error", "Please select an employee.")
                return
            
            if not self.bonus_type_combo.currentText().strip():
                QMessageBox.warning(self, "Validation Error", "Please enter a bonus type.")
                return
            
            try:
                amount = float(self.amount_edit.text())
                if amount <= 0:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid amount greater than 0.")
                return
            
            # Debug employee ID and validate UUID format
            employee_id = self.employee_combo.currentData()
            print(f"DEBUG: Saving bonus for employee_id: {employee_id} (type: {type(employee_id)})")
            
            # Validate that employee_id is a proper UUID format
            import uuid as uuid_module
            try:
                # Try to parse as UUID to validate format
                if isinstance(employee_id, str):
                    uuid_obj = uuid_module.UUID(employee_id)
                    employee_id = str(uuid_obj)  # Ensure proper format
                    print(f"DEBUG: Validated UUID: {employee_id}")
                else:
                    print(f"DEBUG: Invalid employee_id type: {type(employee_id)}")
                    QMessageBox.warning(self, "Error", "Invalid employee selection. Please select a valid employee.")
                    return
            except (ValueError, TypeError) as e:
                print(f"DEBUG: Invalid UUID format: {employee_id}, error: {e}")
                QMessageBox.warning(self, "Error", "Invalid employee selection. Please select a valid employee.")
                return
            
            # Prepare data
            bonus_data = {
                "employee_id": employee_id,
                "bonus_type": self.bonus_type_combo.currentText().strip(),
                "amount": amount,
                "effective_date": self.effective_date.date().toString("yyyy-MM-dd"),
                "status": self.status_combo.currentText(),
                "is_recurring": self.recurring_check.isChecked(),
                "description": self.description_edit.toPlainText().strip()
            }
            
            # Add expiry date if set
            if self.has_expiry.isChecked():
                bonus_data["expiry_date"] = self.expiry_date.date().toString("yyyy-MM-dd")
            else:
                bonus_data["expiry_date"] = None
            
            # print(f"DEBUG: Bonus data to save: {bonus_data}")
            
            # Save to database
            if self.bonus_id:
                # Update existing
                response = supabase.table("bonuses").update(bonus_data).eq("id", self.bonus_id).execute()
            else:
                # Create new - let database auto-generate the ID
                # Don't set bonus_data["id"] since it's auto-incrementing serial
                print(f"DEBUG: Inserting bonus data: {bonus_data}")
                response = supabase.table("bonuses").insert(bonus_data).execute()
            
            if response.data:
                QMessageBox.information(self, "Success", "Bonus saved successfully!")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to save bonus.")
                # print(f"DEBUG: Save response: {response}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving bonus: {str(e)}")
            # print(f"DEBUG: Exception saving bonus: {str(e)}")
            import traceback
            traceback.print_exc()
