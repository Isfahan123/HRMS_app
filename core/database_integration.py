"""
Integration module to connect admin_payroll_tab and payroll_dialog with Supabase database
"""
from services.supabase_service import (
    save_tax_rates_configuration, load_tax_rates_configuration,
    save_tax_relief_max_configuration, load_tax_relief_max_configuration,
    load_statutory_limits_configuration, save_statutory_limits_configuration,
    save_progressive_tax_brackets, load_progressive_tax_brackets,
    calculate_comprehensive_payroll, process_payroll_and_generate_payslip,
    save_payroll_information, load_payroll_information
)
from PyQt5.QtWidgets import QMessageBox
from datetime import datetime
import json

def integrate_admin_payroll_with_database(admin_payroll_tab):
    """Integrate admin payroll tab with database operations"""
    
    def save_admin_tax_rates():
        """Save current minimal tax policy and statutory ceilings to database"""
        try:
            # Persist tax brackets from Admin UI to DB first
            if hasattr(admin_payroll_tab, 'get_tax_brackets_data'):
                brackets = admin_payroll_tab.get_tax_brackets_data()
                ok = save_progressive_tax_brackets(brackets, config_name='default')
                if not ok:
                    QMessageBox.warning(admin_payroll_tab, "Warning", "Failed to save progressive tax brackets. Policy/ceilings will still be saved.")

            # Minimal tax policy into tax_rates_config
            policy_payload = {
                'config_name': 'default',
                'non_resident_rate': admin_payroll_tab.lhdn_non_resident_rate.value() if hasattr(admin_payroll_tab, 'lhdn_non_resident_rate') else 30.0,
                'individual_tax_rebate': admin_payroll_tab.individual_tax_rebate.value() if hasattr(admin_payroll_tab, 'individual_tax_rebate') else 400.0,
                'rebate_threshold': admin_payroll_tab.rebate_threshold.value() if hasattr(admin_payroll_tab, 'rebate_threshold') else 35000.0,
            }
            policy_ok = save_tax_rates_configuration(policy_payload)

            # Statutory ceilings into statutory_limits_config
            limits_payload = {
                'config_name': 'default',
                'epf_ceiling': admin_payroll_tab.epf_ceiling.value() if hasattr(admin_payroll_tab, 'epf_ceiling') else 6000.0,
                'socso_ceiling': admin_payroll_tab.socso_ceiling.value() if hasattr(admin_payroll_tab, 'socso_ceiling') else 6000.0,
                'eis_ceiling': 6000.0,
                'is_active': True,
            }
            limits_ok = save_statutory_limits_configuration(limits_payload)

            if policy_ok and limits_ok:
                QMessageBox.information(admin_payroll_tab, "Success", "Tax brackets, policy, and ceilings saved successfully.")
            elif policy_ok:
                QMessageBox.warning(admin_payroll_tab, "Partial Success", "Tax policy saved, but ceilings failed to save.")
            elif limits_ok:
                QMessageBox.warning(admin_payroll_tab, "Partial Success", "Ceilings saved, but tax policy failed to save.")
            else:
                QMessageBox.critical(admin_payroll_tab, "Error", "Failed to save both tax policy and ceilings.")
        except Exception as e:
            QMessageBox.critical(admin_payroll_tab, "Error", f"Error saving configurations: {e}")
    
    def save_admin_tax_relief_max():
        """Save current admin tax relief maximum configuration to database"""
        try:
            # Extract current configuration from admin panel
            config_data = {
                'config_name': 'current_admin_config',
                'personal_relief_max': 9000.0,  # Standard values - can be extracted from admin controls
                'spouse_relief_max': 4000.0,
                'child_relief_max': 2000.0,
                'disabled_child_relief_max': 8000.0,
                'parent_medical_max': getattr(admin_payroll_tab, 'parent_medical_max', {}).get('value', lambda: 8000.0)() if hasattr(admin_payroll_tab, 'parent_medical_max') else 8000.0,
                'medical_treatment_max': getattr(admin_payroll_tab, 'medical_treatment_max', {}).get('value', lambda: 10000.0)() if hasattr(admin_payroll_tab, 'medical_treatment_max') else 10000.0,
                'serious_disease_max': getattr(admin_payroll_tab, 'serious_disease_max', {}).get('value', lambda: 10000.0)() if hasattr(admin_payroll_tab, 'serious_disease_max') else 10000.0,
                'fertility_treatment_max': getattr(admin_payroll_tab, 'fertility_treatment_max', {}).get('value', lambda: 5000.0)() if hasattr(admin_payroll_tab, 'fertility_treatment_max') else 5000.0,
                'vaccination_max': getattr(admin_payroll_tab, 'vaccination_max', {}).get('value', lambda: 1000.0)() if hasattr(admin_payroll_tab, 'vaccination_max') else 1000.0,
                'dental_treatment_max': getattr(admin_payroll_tab, 'dental_treatment_max', {}).get('value', lambda: 1000.0)() if hasattr(admin_payroll_tab, 'dental_treatment_max') else 1000.0,
                'health_screening_max': getattr(admin_payroll_tab, 'health_screening_max', {}).get('value', lambda: 500.0)() if hasattr(admin_payroll_tab, 'health_screening_max') else 500.0,
                'child_learning_disability_max': getattr(admin_payroll_tab, 'child_learning_disability_max', {}).get('value', lambda: 3000.0)() if hasattr(admin_payroll_tab, 'child_learning_disability_max') else 3000.0,
                'education_max': getattr(admin_payroll_tab, 'education_max', {}).get('value', lambda: 8000.0)() if hasattr(admin_payroll_tab, 'education_max') else 8000.0,
                'skills_course_max': getattr(admin_payroll_tab, 'skills_course_max', {}).get('value', lambda: 1000.0)() if hasattr(admin_payroll_tab, 'skills_course_max') else 1000.0,
                'lifestyle_max': getattr(admin_payroll_tab, 'lifestyle_max', {}).get('value', lambda: 2500.0)() if hasattr(admin_payroll_tab, 'lifestyle_max') else 2500.0,
                'sports_equipment_max': getattr(admin_payroll_tab, 'sports_equipment_max', {}).get('value', lambda: 300.0)() if hasattr(admin_payroll_tab, 'sports_equipment_max') else 300.0,
                'gym_membership_max': getattr(admin_payroll_tab, 'gym_membership_max', {}).get('value', lambda: 300.0)() if hasattr(admin_payroll_tab, 'gym_membership_max') else 300.0,
                'checkup_vaccine_upper_limit': getattr(admin_payroll_tab, 'parent_checkup_vaccine_upper_limit', {}).get('value', lambda: 1000.0)() if hasattr(admin_payroll_tab, 'parent_checkup_vaccine_upper_limit') else 1000.0,
                'life_insurance_upper_limit': getattr(admin_payroll_tab, 'life_insurance_upper_limit', {}).get('value', lambda: 3000.0)() if hasattr(admin_payroll_tab, 'life_insurance_upper_limit') else 3000.0,
                'epf_shared_subcap': 4000.0,
                'combined_epf_insurance_limit': 7000.0
            }
            
            success = save_tax_relief_max_configuration(config_data)
            
            if success:
                QMessageBox.information(admin_payroll_tab, "Success", "Tax relief maximum configuration saved to database successfully!")
            else:
                QMessageBox.warning(admin_payroll_tab, "Error", "Failed to save tax relief configuration to database.")
                
        except Exception as e:
            QMessageBox.critical(admin_payroll_tab, "Error", f"Error saving tax relief configuration: {e}")
    
    def load_admin_configurations():
        """Load tax configurations from database to admin panel"""
        try:
            # Load minimal tax policy
            tax_rates = load_tax_rates_configuration()
            if tax_rates:
                # Update admin panel controls with loaded values
                if hasattr(admin_payroll_tab, 'lhdn_non_resident_rate'):
                    admin_payroll_tab.lhdn_non_resident_rate.setValue(tax_rates.get('non_resident_rate', 30.0))
                if hasattr(admin_payroll_tab, 'individual_tax_rebate'):
                    admin_payroll_tab.individual_tax_rebate.setValue(tax_rates.get('individual_tax_rebate', 400.0))
                if hasattr(admin_payroll_tab, 'rebate_threshold'):
                    admin_payroll_tab.rebate_threshold.setValue(int(tax_rates.get('rebate_threshold', 35000.0) or 35000))

            # Load statutory ceilings
            limits = load_statutory_limits_configuration()
            if limits:
                if hasattr(admin_payroll_tab, 'epf_ceiling'):
                    admin_payroll_tab.epf_ceiling.setValue(float(limits.get('epf_ceiling', 6000.0) or 6000.0))
                if hasattr(admin_payroll_tab, 'socso_ceiling'):
                    admin_payroll_tab.socso_ceiling.setValue(float(limits.get('socso_ceiling', 6000.0) or 6000.0))
            
            # Load progressive tax brackets (optional UI hydration)
            try:
                brackets = load_progressive_tax_brackets('default')
                if brackets and hasattr(admin_payroll_tab, 'tax_bracket_inputs'):
                    # If counts differ, skip detailed hydration to avoid UI rebuild complexity
                    if len(brackets) == len(admin_payroll_tab.tax_bracket_inputs):
                        for i, b in enumerate(brackets):
                            bi = admin_payroll_tab.tax_bracket_inputs[i]
                            bi['from'].setValue(float(b.get('from', 0.0) or 0.0))
                            bi['to'].setValue(float(b.get('to', 0.0) or 0.0))
                            bi['rate'].setValue(float(b.get('rate', 0.0) or 0.0))
                            # Optional fields preserved for UI; don't alter on_first/next/tax_first/tax_next
            except Exception:
                pass

            # Load tax relief maximums
            tax_relief = load_tax_relief_max_configuration()
            if tax_relief:
                # Update admin panel controls with loaded values
                # This would update the max cap controls if they exist
                pass
            
            QMessageBox.information(admin_payroll_tab, "Success", "Configurations loaded from database successfully!")
            
        except Exception as e:
            QMessageBox.warning(admin_payroll_tab, "Error", f"Error loading configurations: {e}")
    
    # Add methods to admin payroll tab
    admin_payroll_tab.save_tax_rates_to_db = save_admin_tax_rates
    admin_payroll_tab.save_tax_relief_max_to_db = save_admin_tax_relief_max
    admin_payroll_tab.load_configurations_from_db = load_admin_configurations

def integrate_payroll_dialog_with_database(payroll_dialog):
    """Integrate payroll dialog with database operations"""
    
    def save_payroll_data():
        """Save current payroll data to database"""
        try:
            # Extract employee data
            employee_data = {
                'employee_id': payroll_dialog.employee_data.get('employee_id', ''),
                'full_name': payroll_dialog.employee_data.get('full_name', ''),
                'email': payroll_dialog.employee_data.get('email', '')
            }
            
            # Extract payroll inputs from dialog fields
            payroll_inputs = {}
            
            # Basic income
            for field_name in ['basic_salary', 'overtime_pay', 'commission', 'bonus']:
                if field_name in payroll_dialog.fields:
                    payroll_inputs[field_name] = payroll_dialog.fields[field_name].value()
            
            # Allowances
            allowances = {}
            allowance_fields = ['housing_allowance', 'transport_allowance', 'meal_allowance', 'other_allowances']
            for field_name in allowance_fields:
                if field_name in payroll_dialog.fields:
                    value = payroll_dialog.fields[field_name].value()
                    if value > 0:
                        allowances[field_name] = value
            payroll_inputs['allowances'] = allowances
            
            # Monthly deductions (for residents only)
            monthly_deductions = {}
            if payroll_dialog.fields.get('tax_resident_status', {}).currentText() == 'Resident':
                deduction_fields = [
                    'parent_medical_treatment', 'parent_dental', 'serious_disease_treatment',
                    'fertility_treatment', 'vaccination', 'dental_treatment', 'health_screening',
                    'child_learning_disability', 'education_fees', 'skills_course', 'lifestyle_expenses',
                    'sports_equipment', 'gym_membership'
                ]
                for field_name in deduction_fields:
                    if field_name in payroll_dialog.fields:
                        value = payroll_dialog.fields[field_name].value()
                        if value > 0:
                            monthly_deductions[field_name] = value
            payroll_inputs['monthly_deductions'] = monthly_deductions
            
            # PCB calculation data (official LHDN formula)
            pcb_fields = [
                'accumulated_gross_ytd', 'accumulated_epf_ytd', 'accumulated_pcb_ytd', 'accumulated_zakat_ytd',
                'individual_relief', 'spouse_relief', 'child_relief', 'child_count', 'disabled_individual',
                'disabled_spouse', 'other_reliefs_ytd', 'other_reliefs_current', 'current_month_zakat'
            ]
            for field_name in pcb_fields:
                if field_name in payroll_dialog.fields:
                    payroll_inputs[field_name] = payroll_dialog.fields[field_name].value()
            
            # Annual tax reliefs (for residents only)
            annual_tax_reliefs = {}
            if payroll_dialog.fields.get('tax_resident_status', {}).currentText() == 'Resident':
                relief_fields = [
                    'breastfeeding_equipment', 'childcare_fees', 'sspn_savings', 'alimony',
                    'epf_voluntary', 'life_insurance', 'prs_annuity', 'education_medical_insurance',
                    'ev_charger', 'housing_loan_under_500k', 'housing_loan_500k_750k'
                ]
                for field_name in relief_fields:
                    if field_name in payroll_dialog.fields:
                        value = payroll_dialog.fields[field_name].value()
                        if value > 0:
                            annual_tax_reliefs[field_name] = value
            payroll_inputs['annual_tax_reliefs'] = annual_tax_reliefs
            
            # Other deductions
            other_deductions = {}
            other_fields = ['insurance_premium', 'loan_deduction', 'advance_salary']
            for field_name in other_fields:
                if field_name in payroll_dialog.fields:
                    value = payroll_dialog.fields[field_name].value()
                    if value > 0:
                        other_deductions[field_name] = value
            payroll_inputs['other_deductions'] = other_deductions
            
            # Tax resident status
            if 'tax_resident_status' in payroll_dialog.fields:
                payroll_inputs['tax_resident_status'] = payroll_dialog.fields['tax_resident_status'].currentText()
            
            # Current month/year: prefer Admin Payroll Tab's date picker if available, else system date
            try:
                parent_widget = payroll_dialog.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'date_input'):
                        qd = admin_dashboard.payroll_tab.date_input.date()
                        month_year = f"{int(qd.month()):02d}/{int(qd.year())}"
                    else:
                        current_date = datetime.now()
                        month_year = f"{current_date.month:02d}/{current_date.year}"
                else:
                    current_date = datetime.now()
                    month_year = f"{current_date.month:02d}/{current_date.year}"
            except Exception:
                current_date = datetime.now()
                month_year = f"{current_date.month:02d}/{current_date.year}"
            
            # Attach TP1 relief claims for this employee/month if saved via Quick TP1 dialog
            try:
                from services.supabase_service import supabase as _sb
                from services.supabase_service import _probe_table_exists as _probe
                emp_uuid = employee_data.get('id') or employee_data.get('employee_id')
                # Resolve code to UUID if needed
                def _looks_like_uuid(x: str) -> bool:
                    return isinstance(x, str) and '-' in x and len(x) >= 32
                if emp_uuid and not _looks_like_uuid(emp_uuid):
                    try:
                        r = _sb.table('employees').select('id').eq('employee_id', emp_uuid).limit(1).execute()
                        if r and getattr(r, 'data', None):
                            emp_uuid = r.data[0].get('id') or emp_uuid
                    except Exception:
                        pass
                if emp_uuid and _probe('tp1_monthly_details'):
                    try:
                        mm = int(month_year.split('/')[0]); yy = int(month_year.split('/')[1])
                    except Exception:
                        from datetime import datetime as _dt
                        _now = _dt.now(); mm, yy = _now.month, _now.year
                    q = _sb.table('tp1_monthly_details').select('details').eq('employee_id', emp_uuid).eq('year', yy).eq('month', mm).limit(1).execute()
                    _rows = getattr(q, 'data', None) or []
                    if _rows and isinstance(_rows[0].get('details'), dict):
                        payroll_inputs['tp1_relief_claims'] = _rows[0]['details']
            except Exception:
                pass

            # Process payroll and generate payslip
            result = process_payroll_and_generate_payslip(employee_data, payroll_inputs, month_year, generate_pdf=True)
            
            if result.get('success'):
                message = "Payroll processed and saved successfully!"
                if 'payslip_pdf' in result:
                    message += f"\nPayslip generated: {result['payslip_pdf']}"
                QMessageBox.information(payroll_dialog, "Success", message)
                return result['payroll_data']
            else:
                QMessageBox.warning(payroll_dialog, "Error", f"Failed to process payroll: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            QMessageBox.critical(payroll_dialog, "Error", f"Error processing payroll: {e}")
            return None
    
    def load_payroll_data(employee_id, month_year):
        """Load existing payroll data for employee and month"""
        try:
            payroll_data = load_payroll_information(employee_id, month_year)
            
            if payroll_data:
                # Populate dialog fields with loaded data
                if 'basic_salary' in payroll_dialog.fields:
                    payroll_dialog.fields['basic_salary'].setValue(payroll_data.get('basic_salary', 0.0))
                
                if 'overtime_pay' in payroll_dialog.fields:
                    payroll_dialog.fields['overtime_pay'].setValue(payroll_data.get('overtime_pay', 0.0))
                
                if 'commission' in payroll_dialog.fields:
                    payroll_dialog.fields['commission'].setValue(payroll_data.get('commission', 0.0))
                
                if 'bonus' in payroll_dialog.fields:
                    payroll_dialog.fields['bonus'].setValue(payroll_data.get('bonus', 0.0))
                
                # Load allowances
                allowances = payroll_data.get('allowances', {})
                for field_name, value in allowances.items():
                    if field_name in payroll_dialog.fields:
                        payroll_dialog.fields[field_name].setValue(value)
                
                # Load monthly deductions
                monthly_deductions = payroll_data.get('monthly_deductions', {})
                for field_name, value in monthly_deductions.items():
                    if field_name in payroll_dialog.fields:
                        payroll_dialog.fields[field_name].setValue(value)
                
                # Load annual tax reliefs
                annual_tax_reliefs = payroll_data.get('annual_tax_reliefs', {})
                for field_name, value in annual_tax_reliefs.items():
                    if field_name in payroll_dialog.fields:
                        payroll_dialog.fields[field_name].setValue(value)
                
                # Load other deductions
                other_deductions = payroll_data.get('other_deductions', {})
                for field_name, value in other_deductions.items():
                    if field_name in payroll_dialog.fields:
                        payroll_dialog.fields[field_name].setValue(value)
                
                # Set tax resident status
                if 'tax_resident_status' in payroll_dialog.fields:
                    status = payroll_data.get('tax_resident_status', 'Resident')
                    index = payroll_dialog.fields['tax_resident_status'].findText(status)
                    if index >= 0:
                        payroll_dialog.fields['tax_resident_status'].setCurrentIndex(index)
                
                QMessageBox.information(payroll_dialog, "Success", f"Payroll data loaded for {month_year}")
                return payroll_data
            else:
                QMessageBox.information(payroll_dialog, "Info", f"No existing payroll data found for {month_year}")
                return None
                
        except Exception as e:
            QMessageBox.warning(payroll_dialog, "Error", f"Error loading payroll data: {e}")
            return None
    
    # Add methods to payroll dialog
    payroll_dialog.save_payroll_to_db = save_payroll_data
    payroll_dialog.load_payroll_from_db = load_payroll_data

def create_database_integration_buttons(admin_payroll_tab, payroll_dialog):
    """Create buttons for database operations in both interfaces"""
    from PyQt5.QtWidgets import QPushButton, QHBoxLayout, QVBoxLayout
    
    # Admin payroll tab buttons
    if hasattr(admin_payroll_tab, 'layout'):
        admin_db_layout = QHBoxLayout()
        
        save_rates_btn = QPushButton("💾 Save Tax Rates to DB")
        save_rates_btn.clicked.connect(admin_payroll_tab.save_tax_rates_to_db)
        admin_db_layout.addWidget(save_rates_btn)
        
        save_relief_btn = QPushButton("💾 Save Tax Relief Max to DB")
        save_relief_btn.clicked.connect(admin_payroll_tab.save_tax_relief_max_to_db)
        admin_db_layout.addWidget(save_relief_btn)
        
        load_config_btn = QPushButton("📥 Load Configurations from DB")
        load_config_btn.clicked.connect(admin_payroll_tab.load_configurations_from_db)
        admin_db_layout.addWidget(load_config_btn)
        
        # Add to admin layout (this may need adjustment based on actual layout structure)
        try:
            admin_payroll_tab.layout().addLayout(admin_db_layout)
        except:
            pass  # Layout structure may vary
    
    # Payroll dialog buttons
    if hasattr(payroll_dialog, 'layout'):
        payroll_db_layout = QHBoxLayout()
        
        save_payroll_btn = QPushButton("💾 Process & Save Payroll")
        save_payroll_btn.clicked.connect(payroll_dialog.save_payroll_to_db)
        payroll_db_layout.addWidget(save_payroll_btn)
        
        load_payroll_btn = QPushButton("📥 Load Existing Payroll")
        load_payroll_btn.clicked.connect(lambda: payroll_dialog.load_payroll_from_db(
            payroll_dialog.employee_data.get('employee_id', ''), 
            f"{datetime.now().month:02d}/{datetime.now().year}"
        ))
        payroll_db_layout.addWidget(load_payroll_btn)
        
        # Add to payroll dialog layout
        try:
            payroll_dialog.layout().addLayout(payroll_db_layout)
        except:
            pass  # Layout structure may vary
