from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, 
                             QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox,
                             QCheckBox, QGroupBox, QScrollArea, QWidget, QPushButton,
                             QMessageBox, QTextEdit, QGridLayout, QTableWidget, QTableWidgetItem)
from PyQt5.QtCore import Qt, pyqtSlot
import json
from services.supabase_service import supabase, get_monthly_deductions, upsert_monthly_deductions, upsert_tp1_monthly_details
from gui.payroll_sections.additional_salary_section import build_additional_salary_section
from core.tax_relief_catalog import ITEMS as TP1_ITEMS

class PayrollInformationDialog(QDialog):
    def __init__(self, employee_data=None, parent=None, is_admin=False):
        super().__init__(parent)
        self.employee_data = employee_data
        self.is_admin = is_admin
        self.fields = {}
        self.tax_relief_maximums = {}  # Removed dynamic tax relief config
        self.setWindowTitle("� Borang Cukai Pendapatan - Payroll & Tax Relief Information")
        self.setModal(True)
        self.resize(1000, 700)  # Increased height for better tax relief section viewing
        self.load_admin_max_caps()  # Load admin MAX CAP settings first
        self.init_ui()
        self.connect_children_amount_helpers()
        self.connect_to_admin_signals()  # Connect to real-time admin updates
        self.load_payroll_data()

    def connect_to_admin_signals(self):
        """Connect to admin MAX CAP change signals for real-time updates"""
        try:
            # Get reference to admin payroll tab for signal connection
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                parent_widget = parent_widget.parent()
            
            if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                admin_dashboard = parent_widget.admin_dashboard_page
                if hasattr(admin_dashboard, 'payroll_tab'):
                    # Connect to admin MAX CAP change signals
                    admin_dashboard.payroll_tab.max_cap_changed.connect(self.update_field_range)
                    print("DEBUG: Connected to admin MAX CAP change signals")
            else:
                print("DEBUG: Could not find admin dashboard for signal connection")
        except Exception as e:
            print(f"DEBUG: Error connecting to admin signals: {e}")

    @pyqtSlot(str, float)
    def update_field_range(self, category_name, new_value):
        """Update field range in real-time when admin changes MAX CAP"""
        try:
            print(f"DEBUG: Received MAX CAP update: {category_name} = {new_value}")
            
            # Map category names to field names
            field_mapping = {
                'parent_medical_max_cap': 'parent_medical_max_cap',  # Main MAX CAP
                'parent_medical_treatment_max': 'parent_medical_treatment',
                'parent_dental_max': 'parent_dental',
                'parent_checkup_vaccine_max': 'parent_checkup_vaccine',
                'parent_checkup_vaccine_upper_limit': 'parent_checkup_vaccine_upper_limit',  # Special upper limit controller
                'basic_support_equipment_max': 'basic_support_equipment',
                'education_non_masters_max': 'education_non_masters',
                'education_masters_phd_max': 'education_masters_phd',
                'skills_course_max': 'skills_course',
                # Lifestyle complex subcap mappings
                'lifestyle_basic_max_cap': 'lifestyle_basic_max_cap',  # Main MAX CAP for lifestyle
                'lifestyle_books_max': 'lifestyle_books',
                'lifestyle_computer_max': 'lifestyle_computer', 
                'lifestyle_internet_max': 'lifestyle_internet',
                'lifestyle_skills_max': 'lifestyle_skills'
            }
            
            # Handle main MAX CAP changes (affects multiple subcategories)
            if category_name == 'parent_medical_max_cap':
                self.update_parent_medical_subcaps(new_value)
                return
            elif category_name == 'lifestyle_basic_max_cap':
                self.update_lifestyle_basic_subcaps(new_value)
                return
            elif category_name == 'parent_checkup_vaccine_upper_limit':
                # Special upper limit change affects checkup/vaccine range
                self.update_checkup_vaccine_special_limit(new_value)
                return
            elif category_name == 'skills_course_upper_limit':
                # Special upper limit change affects skills course range
                self.update_skills_course_special_limit(new_value)
                return
            elif category_name == 'vaccination_upper_limit':
                # Special upper limit change affects vaccination range
                self.update_vaccination_special_limit(new_value)
                return
            elif category_name == 'dental_treatment_upper_limit':
                # Special upper limit change affects dental treatment range
                self.update_dental_treatment_special_limit(new_value)
                return
            elif category_name == 'health_checkup_upper_limit':
                # Special upper limit change affects health checkup range
                self.update_health_checkup_special_limit(new_value)
                return
            elif category_name == 'child_learning_disability_upper_limit':
                # Special upper limit change affects child learning disability range
                self.update_child_learning_disability_special_limit(new_value)
                return
            
            field_name = field_mapping.get(category_name)
            if field_name and field_name in self.fields:
                # Update the range immediately
                current_value = self.fields[field_name].value()
                self.fields[field_name].setRange(0.0, new_value)
                
                # Update tooltip to show new limit
                lhdn_defaults = {
                    'parent_medical_treatment': 8000.0,
                    'parent_dental': 8000.0,
                    'parent_checkup_vaccine': 1000.0,
                    'basic_support_equipment': 6000.0,
                    'education_non_masters': 7000.0,
                    'education_masters_phd': 7000.0,
                    'skills_course': 2000.0,
                    # Lifestyle subcaps (each shares from the main RM2,500 allocation)
                    'lifestyle_books': 2500.0,
                    'lifestyle_computer': 2500.0,
                    'lifestyle_internet': 2500.0,
                    'lifestyle_skills': 2500.0
                }
                lhdn_default = lhdn_defaults.get(field_name, new_value)
                self.fields[field_name].setToolTip(f"LHDN default: RM{lhdn_default:,.0f}, Admin MAX CAP: RM{new_value:,.0f} (LIVE)")
                
                print(f"DEBUG: Updated {field_name} range to 0.0-{new_value} (current value: {current_value})")
                
                # Show notification for immediate feedback
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🔄 LIVE UPDATE: {category_name.replace('_', ' ').title()} limit updated to RM{new_value:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating field range: {e}")

    def update_parent_medical_subcaps(self, main_max_cap):
        """Update all parent medical subcategory ranges when main MAX CAP changes"""
        try:
            print(f"DEBUG: Updating parent medical subcaps based on main MAX CAP: RM{main_max_cap:,.0f}")
            
            # Update treatment subcap (can use full main MAX CAP)
            if 'parent_medical_treatment' in self.fields:
                current_value = self.fields['parent_medical_treatment'].value()
                self.fields['parent_medical_treatment'].setRange(0.0, main_max_cap)
                self.fields['parent_medical_treatment'].setToolTip(f"LHDN default: RM8,000, Admin MAX CAP: RM{main_max_cap:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > main_max_cap:
                    self.fields['parent_medical_treatment'].setValue(main_max_cap)
            
            # Update dental subcap (can use full main MAX CAP)
            if 'parent_dental' in self.fields:
                current_value = self.fields['parent_dental'].value()
                self.fields['parent_dental'].setRange(0.0, main_max_cap)
                self.fields['parent_dental'].setToolTip(f"LHDN default: RM8,000, Admin MAX CAP: RM{main_max_cap:,.0f} (LIVE)")
                
                if current_value > main_max_cap:
                    self.fields['parent_dental'].setValue(main_max_cap)
            
            # Update checkup/vaccine subcap (limited to special upper limit or main MAX CAP, whichever is lower)
            if 'parent_checkup_vaccine' in self.fields:
                current_value = self.fields['parent_checkup_vaccine'].value()
                
                # Get configurable special upper limit from admin (default 1000.0 if not available)
                special_upper_limit = 1000.0  # Default fallback
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'parent_checkup_vaccine_upper_limit'):
                        special_upper_limit = admin_dashboard.payroll_tab.parent_checkup_vaccine_upper_limit.value()
                
                checkup_limit = min(special_upper_limit, main_max_cap)
                self.fields['parent_checkup_vaccine'].setRange(0.0, checkup_limit)
                self.fields['parent_checkup_vaccine'].setToolTip(f"Special upper limit: RM{special_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{checkup_limit:,.0f} (LIVE)")
                
                if current_value > checkup_limit:
                    self.fields['parent_checkup_vaccine'].setValue(checkup_limit)
            
            # Update status to show the change
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"🔄 LIVE UPDATE: Parent medical main MAX CAP updated to RM{main_max_cap:,.0f}, all subcaps adjusted")
                
        except Exception as e:
            print(f"DEBUG: Error updating parent medical subcaps: {e}")

    def update_lifestyle_basic_subcaps(self, main_max_cap):
        """Update all lifestyle basic subcategory ranges when main MAX CAP changes (shared allocation model)"""
        try:
            print(f"DEBUG: Updating lifestyle basic subcaps based on main MAX CAP: RM{main_max_cap:,.0f}")
            
            # Lifestyle subcaps follow shared allocation model
            # Each subcap can be up to the main MAX CAP, but combined total cannot exceed main MAX CAP
            lifestyle_subcaps = [
                'lifestyle_books',
                'lifestyle_computer', 
                'lifestyle_internet',
                'lifestyle_skills'
            ]
            
            for subcap_name in lifestyle_subcaps:
                if subcap_name in self.fields:
                    current_value = self.fields[subcap_name].value()
                    # Each subcap can be up to the main MAX CAP (shared allocation)
                    self.fields[subcap_name].setRange(0.0, main_max_cap)
                    self.fields[subcap_name].setToolTip(f"LHDN default: RM2,500, Admin MAX CAP: RM{main_max_cap:,.0f} (SHARED ALLOCATION) (LIVE)")
                    
                    # Adjust value if it exceeds new limit
                    if current_value > main_max_cap:
                        self.fields[subcap_name].setValue(main_max_cap)
            
            # Update status to show the change
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"🔄 LIVE UPDATE: Lifestyle basic main MAX CAP updated to RM{main_max_cap:,.0f}, all subcaps adjusted (shared allocation)")
                
        except Exception as e:
            print(f"DEBUG: Error updating lifestyle basic subcaps: {e}")

    def update_checkup_vaccine_special_limit(self, new_upper_limit):
        """Update checkup/vaccine range when admin changes the special upper limit"""
        try:
            print(f"DEBUG: Updating checkup/vaccine special upper limit to: RM{new_upper_limit:,.0f}")
            
            if 'parent_checkup_vaccine' in self.fields:
                # Get current main MAX CAP from admin (if available)
                main_max_cap = 8000.0  # Default fallback
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'parent_medical_max_cap'):
                        main_max_cap = admin_dashboard.payroll_tab.parent_medical_max_cap.value()
                
                # Apply the same logic: min(special_upper_limit, main_max_cap)
                checkup_limit = min(new_upper_limit, main_max_cap)
                current_value = self.fields['parent_checkup_vaccine'].value()
                self.fields['parent_checkup_vaccine'].setRange(0.0, checkup_limit)
                self.fields['parent_checkup_vaccine'].setToolTip(f"Special upper limit: RM{new_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{checkup_limit:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > checkup_limit:
                    self.fields['parent_checkup_vaccine'].setValue(checkup_limit)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🎯 LIVE UPDATE: Checkup/vaccine special upper limit updated to RM{new_upper_limit:,.0f}, effective limit: RM{checkup_limit:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating checkup/vaccine special limit: {e}")

    def update_skills_course_special_limit(self, new_upper_limit):
        """Update skills course range when admin changes the special upper limit"""
        try:
            print(f"DEBUG: Updating skills course special upper limit to: RM{new_upper_limit:,.0f}")
            
            if 'skills_course' in self.fields:
                # Get current main MAX CAP from admin (if available)
                main_max_cap = 7000.0  # Default fallback for education
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'education_max_cap'):
                        main_max_cap = admin_dashboard.payroll_tab.education_max_cap.value()
                
                # Apply the same logic: min(special_upper_limit, main_max_cap)
                skills_limit = min(new_upper_limit, main_max_cap)
                current_value = self.fields['skills_course'].value()
                self.fields['skills_course'].setRange(0.0, skills_limit)
                self.fields['skills_course'].setToolTip(f"Special upper limit: RM{new_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{skills_limit:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > skills_limit:
                    self.fields['skills_course'].setValue(skills_limit)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🎯 LIVE UPDATE: Skills course special upper limit updated to RM{new_upper_limit:,.0f}, effective limit: RM{skills_limit:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating skills course special limit: {e}")

    def update_vaccination_special_limit(self, new_upper_limit):
        """Update vaccination range when admin changes the special upper limit"""
        try:
            print(f"DEBUG: Updating vaccination special upper limit to: RM{new_upper_limit:,.0f}")
            
            if 'vaccination' in self.fields:
                # Get current main MAX CAP from admin (if available)
                main_max_cap = 10000.0  # Default fallback for medical family
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'medical_family_max_cap'):
                        main_max_cap = admin_dashboard.payroll_tab.medical_family_max_cap.value()
                
                # Apply the same logic: min(special_upper_limit, main_max_cap)
                vaccination_limit = min(new_upper_limit, main_max_cap)
                current_value = self.fields['vaccination'].value()
                self.fields['vaccination'].setRange(0.0, vaccination_limit)
                self.fields['vaccination'].setToolTip(f"Special upper limit: RM{new_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{vaccination_limit:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > vaccination_limit:
                    self.fields['vaccination'].setValue(vaccination_limit)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🎯 LIVE UPDATE: Vaccination special upper limit updated to RM{new_upper_limit:,.0f}, effective limit: RM{vaccination_limit:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating vaccination special limit: {e}")

    def update_dental_treatment_special_limit(self, new_upper_limit):
        """Update dental treatment range when admin changes the special upper limit"""
        try:
            print(f"DEBUG: Updating dental treatment special upper limit to: RM{new_upper_limit:,.0f}")
            
            if 'dental_treatment' in self.fields:
                # Get current main MAX CAP from admin (if available)
                main_max_cap = 10000.0  # Default fallback for medical family
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'medical_family_max_cap'):
                        main_max_cap = admin_dashboard.payroll_tab.medical_family_max_cap.value()
                
                # Apply the same logic: min(special_upper_limit, main_max_cap)
                dental_limit = min(new_upper_limit, main_max_cap)
                current_value = self.fields['dental_treatment'].value()
                self.fields['dental_treatment'].setRange(0.0, dental_limit)
                self.fields['dental_treatment'].setToolTip(f"Special upper limit: RM{new_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{dental_limit:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > dental_limit:
                    self.fields['dental_treatment'].setValue(dental_limit)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🎯 LIVE UPDATE: Dental treatment special upper limit updated to RM{new_upper_limit:,.0f}, effective limit: RM{dental_limit:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating dental treatment special limit: {e}")

    def update_health_checkup_special_limit(self, new_upper_limit):
        """Update health checkup range when admin changes the special upper limit"""
        try:
            print(f"DEBUG: Updating health checkup special upper limit to: RM{new_upper_limit:,.0f}")
            
            if 'health_checkup' in self.fields:
                # Get current main MAX CAP from admin (if available)
                main_max_cap = 10000.0  # Default fallback for medical family
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'medical_family_max_cap'):
                        main_max_cap = admin_dashboard.payroll_tab.medical_family_max_cap.value()
                
                # Apply the same logic: min(special_upper_limit, main_max_cap)
                health_limit = min(new_upper_limit, main_max_cap)
                current_value = self.fields['health_checkup'].value()
                self.fields['health_checkup'].setRange(0.0, health_limit)
                self.fields['health_checkup'].setToolTip(f"Special upper limit: RM{new_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{health_limit:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > health_limit:
                    self.fields['health_checkup'].setValue(health_limit)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🎯 LIVE UPDATE: Health checkup special upper limit updated to RM{new_upper_limit:,.0f}, effective limit: RM{health_limit:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating health checkup special limit: {e}")

    def update_child_learning_disability_special_limit(self, new_upper_limit):
        """Update child learning disability range when admin changes the special upper limit"""
        try:
            print(f"DEBUG: Updating child learning disability special upper limit to: RM{new_upper_limit:,.0f}")
            
            if 'child_learning_disability' in self.fields:
                # Get current main MAX CAP from admin (if available)
                main_max_cap = 10000.0  # Default fallback for medical family
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'medical_family_max_cap'):
                        main_max_cap = admin_dashboard.payroll_tab.medical_family_max_cap.value()
                
                # Apply the same logic: min(special_upper_limit, main_max_cap)
                child_limit = min(new_upper_limit, main_max_cap)
                current_value = self.fields['child_learning_disability'].value()
                self.fields['child_learning_disability'].setRange(0.0, child_limit)
                self.fields['child_learning_disability'].setToolTip(f"Special upper limit: RM{new_upper_limit:,.0f}, Main MAX CAP: RM{main_max_cap:,.0f}, Effective limit: RM{child_limit:,.0f} (LIVE)")
                
                # Adjust value if it exceeds new limit
                if current_value > child_limit:
                    self.fields['child_learning_disability'].setValue(child_limit)
                
                # Update status
                if hasattr(self, 'status_label'):
                    self.status_label.setText(f"🎯 LIVE UPDATE: Child learning disability special upper limit updated to RM{new_upper_limit:,.0f}, effective limit: RM{child_limit:,.0f}")
                    
        except Exception as e:
            print(f"DEBUG: Error updating child learning disability special limit: {e}")

    def refresh_max_caps(self):
        """Refresh MAX CAP limits from current admin configuration (without requiring save)"""
        try:
            self.status_label.setText("🔄 Refreshing MAX CAP limits...")
            
            # Get current admin configuration (live values, not saved)
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                parent_widget = parent_widget.parent()
            
            if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                admin_dashboard = parent_widget.admin_dashboard_page
                if hasattr(admin_dashboard, 'payroll_tab'):
                    admin_payroll = admin_dashboard.payroll_tab
                    
                    # Get live values directly from admin spinboxes (no save required!)
                    live_max_caps = {}
                    
                    # Get main MAX CAP values
                    if hasattr(admin_payroll, 'parent_medical_max_cap'):
                        live_max_caps['parent_medical_max_cap'] = admin_payroll.parent_medical_max_cap.value()
                    if hasattr(admin_payroll, 'lifestyle_basic_max_cap'):
                        live_max_caps['lifestyle_basic_max_cap'] = admin_payroll.lifestyle_basic_max_cap.value()
                    
                    # Get special upper limit for checkup/vaccine
                    if hasattr(admin_payroll, 'parent_checkup_vaccine_upper_limit'):
                        live_max_caps['parent_checkup_vaccine_upper_limit'] = admin_payroll.parent_checkup_vaccine_upper_limit.value()
                    
                    # Get sub MAX CAP values
                    if hasattr(admin_payroll, 'parent_medical_treatment_max'):
                        live_max_caps['parent_medical_treatment_max'] = admin_payroll.parent_medical_treatment_max.value()
                    if hasattr(admin_payroll, 'parent_dental_max'):
                        live_max_caps['parent_dental_max'] = admin_payroll.parent_dental_max.value()
                    if hasattr(admin_payroll, 'parent_checkup_vaccine_max'):
                        live_max_caps['parent_checkup_vaccine_max'] = admin_payroll.parent_checkup_vaccine_max.value()
                    if hasattr(admin_payroll, 'basic_support_equipment_max'):
                        live_max_caps['basic_support_equipment_max'] = admin_payroll.basic_support_equipment_max.value()
                    
                    # Get lifestyle subcap values
                    if hasattr(admin_payroll, 'lifestyle_books_max'):
                        live_max_caps['lifestyle_books_max'] = admin_payroll.lifestyle_books_max.value()
                    if hasattr(admin_payroll, 'lifestyle_computer_max'):
                        live_max_caps['lifestyle_computer_max'] = admin_payroll.lifestyle_computer_max.value()
                    if hasattr(admin_payroll, 'lifestyle_internet_max'):
                        live_max_caps['lifestyle_internet_max'] = admin_payroll.lifestyle_internet_max.value()
                    if hasattr(admin_payroll, 'lifestyle_skills_max'):
                        live_max_caps['lifestyle_skills_max'] = admin_payroll.lifestyle_skills_max.value()
                    
                    # Update field ranges with live admin values
                    field_mapping = {
                        'parent_medical_treatment_max': 'parent_medical_treatment',
                        'parent_dental_max': 'parent_dental',
                        'parent_checkup_vaccine_max': 'parent_checkup_vaccine',
                        'basic_support_equipment_max': 'basic_support_equipment',
                        # Lifestyle subcap mapping
                        'lifestyle_books_max': 'lifestyle_books',
                        'lifestyle_computer_max': 'lifestyle_computer',
                        'lifestyle_internet_max': 'lifestyle_internet',
                        'lifestyle_skills_max': 'lifestyle_skills'
                    }
                    
                    updated_count = 0
                    
                    # Handle main MAX CAP first (affects subcaps)
                    if 'parent_medical_max_cap' in live_max_caps:
                        main_max_cap = live_max_caps['parent_medical_max_cap']
                        self.update_parent_medical_subcaps(main_max_cap)
                        updated_count += 3  # Treatment, dental, checkup/vaccine
                        print(f"DEBUG: Refreshed parent medical main MAX CAP: RM{main_max_cap:,.0f}")
                    
                    if 'lifestyle_basic_max_cap' in live_max_caps:
                        lifestyle_main_max = live_max_caps['lifestyle_basic_max_cap']
                        self.update_lifestyle_basic_subcaps(lifestyle_main_max)
                        updated_count += 4  # Books, computer, internet, skills
                        print(f"DEBUG: Refreshed lifestyle basic main MAX CAP: RM{lifestyle_main_max:,.0f}")
                    
                    if 'parent_checkup_vaccine_upper_limit' in live_max_caps:
                        special_upper_limit = live_max_caps['parent_checkup_vaccine_upper_limit']
                        self.update_checkup_vaccine_special_limit(special_upper_limit)
                        updated_count += 1  # Checkup/vaccine special limit
                        print(f"DEBUG: Refreshed checkup/vaccine special upper limit: RM{special_upper_limit:,.0f}")
                    
                    # Handle other individual MAX CAPs
                    for cap_name, new_value in live_max_caps.items():
                        # Skip main MAX CAPs (already handled above) and their subcaps (handled by main MAX CAP)
                        skip_caps = [
                            'parent_medical_max_cap', 'parent_medical_treatment_max', 'parent_dental_max', 'parent_checkup_vaccine_max',
                            'lifestyle_basic_max_cap', 'lifestyle_books_max', 'lifestyle_computer_max', 'lifestyle_internet_max', 'lifestyle_skills_max'
                        ]
                        if cap_name in skip_caps:
                            continue
                            
                        field_name = field_mapping.get(cap_name)
                        if field_name and field_name in self.fields:
                            old_max = self.fields[field_name].maximum()
                            self.fields[field_name].setRange(0.0, new_value)
                            
                            # Update tooltip
                            lhdn_defaults = {
                                'basic_support_equipment': 6000.0
                            }
                            lhdn_default = lhdn_defaults.get(field_name, new_value)
                            self.fields[field_name].setToolTip(f"LHDN default: RM{lhdn_default:,.0f}, Admin MAX CAP: RM{new_value:,.0f} (REFRESHED)")
                            
                            if old_max != new_value:
                                updated_count += 1
                                print(f"DEBUG: Refreshed {field_name}: {old_max} → {new_value}")
                    
                    if updated_count > 0:
                        self.status_label.setText(f"✅ Refreshed {updated_count} MAX CAP limits from admin (NO SAVE REQUIRED)")
                        self.status_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 12px;")
                    else:
                        self.status_label.setText("ℹ️ All MAX CAP limits already up-to-date")
                        self.status_label.setStyleSheet("color: #2196f3; font-weight: bold; font-size: 12px;")
                else:
                    self.status_label.setText("❌ Could not access admin payroll configuration")
                    self.status_label.setStyleSheet("color: #f44336; font-weight: bold; font-size: 12px;")
            else:
                # Fallback: reload from database
                self.load_admin_max_caps()
                self.status_label.setText("✅ Refreshed MAX CAP limits from database")
                self.status_label.setStyleSheet("color: #ff9800; font-weight: bold; font-size: 12px;")
                
        except Exception as e:
            print(f"DEBUG: Error refreshing MAX CAP limits: {e}")
            self.status_label.setText("❌ Error refreshing MAX CAP limits")
            self.status_label.setStyleSheet("color: #f44336; font-weight: bold; font-size: 12px;")

    def load_admin_max_caps(self):
        """Load admin MAX CAP settings to apply to subcap ranges"""
        try:
            # Decoupled from LHDN configs: use static defaults (can be overridden live via Admin tab signals)
            self.admin_max_caps = {
                'parent_medical_max': 8000.0,
                'parent_medical_treatment_max': 8000.0,
                'parent_dental_max': 8000.0,
                'parent_checkup_vaccine_max': 1000.0,
                'basic_support_equipment_max': 6000.0,
                'education_non_masters_max': 7000.0,
                'education_masters_phd_max': 7000.0,
                'skills_course_max': 2000.0,
                'serious_disease_max': 10000.0,
                'fertility_treatment_max': 1000.0,
                'vaccination_max': 1000.0,
                'dental_treatment_max': 1000.0,
                'health_checkup_max': 1000.0,
                'child_learning_disability_max': 6000.0,
                'lifestyle_books_max': 2500.0,
                'lifestyle_computer_max': 2500.0,
                'lifestyle_internet_max': 2500.0,
                'lifestyle_skills_max': 2500.0,
                'sports_equipment_max': 1000.0,
                'sports_facility_rent_max': 1000.0,
                'competition_fees_max': 1000.0,
                'gym_fees_max': 1000.0,
                'breastfeeding_equipment_max': 1000.0,
                'childcare_fees_max': 3000.0,
                'sspn_savings_max': 8000.0
            }
            print("DEBUG: Loaded static MAX CAP defaults (no LHDN DB dependency)")
                
        except Exception as e:
            print(f"DEBUG: Error loading admin MAX CAP settings: {e}")
            # Fallback to LHDN 2025 defaults
            self.admin_max_caps = {
                'parent_medical_max': 8000.0,
                'parent_medical_treatment_max': 8000.0,
                'parent_dental_max': 8000.0,
                'parent_checkup_vaccine_max': 1000.0,
                'basic_support_equipment_max': 6000.0,
                'education_non_masters_max': 7000.0,
                'education_masters_phd_max': 7000.0,
                'skills_course_max': 2000.0,
                'serious_disease_max': 10000.0,
                'fertility_treatment_max': 1000.0,
                'vaccination_max': 1000.0,
                'dental_treatment_max': 1000.0,
                'health_checkup_max': 1000.0,
                'child_learning_disability_max': 6000.0,
                'lifestyle_books_max': 2500.0,
                'lifestyle_computer_max': 2500.0,
                'lifestyle_internet_max': 2500.0,
                'lifestyle_skills_max': 2500.0,
                'sports_equipment_max': 1000.0,
                'sports_facility_rent_max': 1000.0,
                'competition_fees_max': 1000.0,
                'gym_fees_max': 1000.0,
                'breastfeeding_equipment_max': 1000.0,
                'childcare_fees_max': 3000.0,
                'sspn_savings_max': 8000.0
            }

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title_label = QLabel("� BORANG CUKAI PENDAPATAN - PAYROLL & TAX RELIEF INFORMATION")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        # Deprecation / guidance banner for TP1 relief entry
        banner = QLabel(
            "⚠️ TP1 Itemized Reliefs moved: Use Admin ▶ TP1 Reliefs to manage monthly claims. "
            "This dialog only captures base payroll, zakat & rebates. SOCSO+EIS auto-applied in PCB LP1."
        )
        banner.setWordWrap(True)
        banner.setStyleSheet(
            "background:#fff3cd; color:#856404; border:1px solid #ffeeba; padding:8px; border-radius:6px;"
            "font-size:12px; font-weight:bold;"
        )
        main_layout.addWidget(banner)

        # Real-time MAX CAP sync section
        sync_layout = QHBoxLayout()
        
        # Status label for live updates
        self.status_label = QLabel("✅ MAX CAP limits loaded from admin configuration")
        self.status_label.setStyleSheet("color: #4caf50; font-weight: bold; font-size: 12px;")
        sync_layout.addWidget(self.status_label)
        
        sync_layout.addStretch()
        
        # (removed duplicate Quick TP1 button connected to quick_tp1_reliefs)

        # Refresh button for on-demand updates (without saving)
        refresh_button = QPushButton("🔄 Refresh MAX CAP Limits")
        refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #2196f3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        refresh_button.clicked.connect(self.refresh_max_caps)
        refresh_button.setToolTip("Refresh MAX CAP limits from admin without requiring save")
        sync_layout.addWidget(refresh_button)

        # Quick TP1 Reliefs button (opens pre-filtered TP1 dialog for this employee/month)
        quick_tp1_btn = QPushButton("✨ Quick TP1 Reliefs")
        quick_tp1_btn.setStyleSheet("""
            QPushButton {
                background-color: #673ab7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5e35b1;
            }
        """)
        quick_tp1_btn.setToolTip("Open TP1 monthly relief claims for this employee and period")
        quick_tp1_btn.clicked.connect(self.open_quick_tp1_reliefs_dialog)
        sync_layout.addWidget(quick_tp1_btn)

        # (removed duplicate Quick TP1 button connected to open_quick_tp1_reliefs)
        
        main_layout.addLayout(sync_layout)

        # Create scroll area with optimized settings for extensive content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #d0d0d0;
                border-radius: 5px;
                background-color: #fafafa;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 15px;
                border-radius: 7px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a0a0a0;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)
        
        # Create scrollable widget with row-based layout
        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #2c3e50;
            }
        """)
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(25)  # Increased spacing for better section separation
        scroll_layout.setContentsMargins(20, 20, 20, 20)  # More generous margins

        # Create sections in rows (each section spans full width)
        # Row 1: Basic payroll information (with internal column layout)
        self.create_basic_payroll_section_rows(scroll_layout)
        
        # Row 2: Tax configuration sections
        self.create_tax_sections_row(scroll_layout)
        
        # Row 3: Additional benefits and deductions
        self.create_benefits_deductions_row(scroll_layout)
        
        # Note: Tax relief configuration removed - individual tax management via separate components
        
        # Set the scroll widget
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)

        # Buttons at the bottom (outside scroll area)
        self.create_buttons(main_layout)

    def open_quick_tp1_reliefs_dialog(self):
        """Open a compact TP1 claims dialog for the current employee and selected payroll period.
        Reuses the same items/caps as Admin ▶ TP1 Reliefs, but locks employee to this dialog's employee.
        """
        try:
            # Resolve employee ID
            emp = self.employee_data or {}
            emp_id = emp.get('id') or emp.get('employee_id')
            # Resolve to UUID if a human-readable employee code was provided
            try:
                def _looks_like_uuid(x: str) -> bool:
                    return isinstance(x, str) and '-' in x and len(x) >= 32
                if emp_id and not _looks_like_uuid(emp_id):
                    resp_uuid = supabase.table('employees').select('id').eq('employee_id', emp_id).limit(1).execute()
                    if resp_uuid and getattr(resp_uuid, 'data', None):
                        emp_id = resp_uuid.data[0].get('id') or emp_id
            except Exception:
                pass
            if not emp_id:
                QMessageBox.warning(self, "Missing employee", "Can't open TP1 Reliefs: no employee selected in this dialog.")
                return

            # Determine target year/month: prefer Admin Payroll Tab's date picker if available, else current date
            from datetime import datetime as _dt
            target_year, target_month = None, None
            try:
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'date_input'):
                        qd = admin_dashboard.payroll_tab.date_input.date()
                        target_year, target_month = qd.year(), qd.month()
            except Exception:
                pass
            if target_year is None or target_month is None:
                # If no admin-selected period, try to use the latest period with saved TP1 claims
                try:
                    resp_period = supabase.table('tp1_monthly_details') \
                        .select('year, month') \
                        .eq('employee_id', emp_id) \
                        .order('year', desc=True) \
                        .order('month', desc=True) \
                        .limit(1) \
                        .execute()
                    if resp_period and getattr(resp_period, 'data', None):
                        r0 = resp_period.data[0]
                        target_year = int(r0.get('year'))
                        target_month = int(r0.get('month'))
                    else:
                        now = _dt.now()
                        target_year, target_month = now.year, now.month
                except Exception:
                    now = _dt.now()
                    target_year, target_month = now.year, now.month

            # Build dialog UI
            dlg = QDialog(self)
            dlg.setWindowTitle("Quick TP1 Reliefs (This Employee)")
            layout = QVBoxLayout()

            # Header: employee and period
            header = QLabel(f"Employee: {emp.get('full_name') or emp.get('email') or emp_id} — Period: {target_month:02d}/{target_year}")
            header.setStyleSheet("font-weight: bold;")
            layout.addWidget(header)

            # Load effective TP1 catalog with overrides so UI reflects PCB? flips and caps
            try:
                from core.tax_relief_catalog import load_relief_overrides_from_db, get_effective_items, load_relief_group_overrides_from_db, get_effective_groups
                _ov = {}
                _gov = {}
                try:
                    _ov = load_relief_overrides_from_db(supabase)
                except Exception:
                    _ov = {}
                try:
                    _gov = load_relief_group_overrides_from_db(supabase)
                except Exception:
                    _gov = {}
                eff_items = get_effective_items(_ov)
                eff_groups = get_effective_groups(_gov) if _gov else None
            except Exception:
                eff_items = {i.key: i for i in TP1_ITEMS}
                eff_groups = None

            # Table setup
            table = QTableWidget()
            headers = ["Code", "Description", "Claimed", "Cap", "YTD", "Remaining", "PCB?", "Cycle"]
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            table.verticalHeader().setVisible(False)
            table.setRowCount(len(TP1_ITEMS))

            # Helper: fetch YTD map for this employee/year
            def fetch_ytd_map(emp_id_: str):
                try:
                    resp = supabase.table('relief_ytd_accumulated').select('item_key, claimed_ytd').eq('employee_id', emp_id_).eq('year', target_year).execute()
                    data = resp.data or []
                    return {r.get('item_key'): float(r.get('claimed_ytd') or 0.0) for r in data}
                except Exception:
                    return {}

            ytd_map = fetch_ytd_map(emp_id)

            # Load existing claims from tp1_monthly_details for this employee/period
            existing_claims = {}
            try:
                resp = supabase.table('tp1_monthly_details').select('details').eq('employee_id', emp_id).eq('year', target_year).eq('month', target_month).execute()
                if resp.data:
                    details = resp.data[0].get('details') or {}
                    if isinstance(details, dict):
                        existing_claims = {k: float(v) for k, v in details.items() if v}
            except Exception:
                existing_claims = {}

            for row, item in enumerate(TP1_ITEMS):
                eff = eff_items.get(item.key, item)
                # Determine cap using effective item and effective group overrides
                cap = None
                if eff.cap is not None:
                    cap = eff.cap
                elif eff.group is not None:
                    if eff_groups and eff.group in eff_groups and eff_groups[eff.group].cap is not None:
                        cap = eff_groups[eff.group].cap
                    else:
                        cap = eff.group_cap
                claimed_ytd = float(ytd_map.get(item.key, 0.0))
                remaining = None
                if eff.cap is not None:
                    remaining = max(0.0, float(eff.cap) - claimed_ytd)
                elif eff.group_cap is not None:
                    remaining = ''  # group-cap remaining depends on group aggregation

                code_item = QTableWidgetItem(eff.code)
                code_item.setFlags(code_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, code_item)

                desc_item = QTableWidgetItem(eff.description)
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, desc_item)

                spin = QDoubleSpinBox()
                spin.setDecimals(2)
                spin.setMaximum(9999999.0)
                # Set existing value if available
                existing_val = existing_claims.get(item.key, 0.0)
                spin.setValue(existing_val)
                table.setCellWidget(row, 2, spin)

                cap_text = (f"{cap:.2f}" if cap is not None else "-")
                cap_item = QTableWidgetItem(cap_text)
                cap_item.setFlags(cap_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, cap_item)

                ytd_item = QTableWidgetItem(f"{claimed_ytd:.2f}")
                ytd_item.setFlags(ytd_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 4, ytd_item)

                rem_item = QTableWidgetItem(f"{remaining:.2f}" if isinstance(remaining, float) else str(remaining))
                rem_item.setFlags(rem_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 5, rem_item)

                pcb_item = QTableWidgetItem("Yes" if getattr(eff, 'pcb_only', False) else "No")
                pcb_item.setFlags(pcb_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 6, pcb_item)

                cyc_item = QTableWidgetItem(str(eff.cycle_years) if eff.cycle_years else "-")
                cyc_item.setFlags(cyc_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 7, cyc_item)

            # Append SOCSO+EIS (B20) informational row
            try:
                extra_row = table.rowCount()
                table.insertRow(extra_row)
                socso_eis_label = QTableWidgetItem("B20 Auto (SOCSO+EIS)")
                socso_eis_label.setFlags(socso_eis_label.flags() & ~Qt.ItemIsEditable)
                table.setItem(extra_row, 0, socso_eis_label)
                desc_item = QTableWidgetItem("Auto-derived employee SOCSO+EIS (pcb-only, cap RM350/yr)")
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(extra_row, 1, desc_item)
                table.setItem(extra_row, 2, QTableWidgetItem("-"))
                table.setItem(extra_row, 3, QTableWidgetItem("350.00"))
                # Compute YTD SOCSO+EIS employee portion up to this period
                ytd_socso_eis = 0.0
                try:
                    resp = supabase.table('payroll_information').select('month_year, socso_employee, eis_employee').eq('employee_id', emp_id).execute()
                    if resp and resp.data:
                        for r in resp.data:
                            try:
                                mm_yy = str(r.get('month_year', ''))
                                if '/' in mm_yy:
                                    mm_str, yy_str = mm_yy.split('/')
                                    if int(yy_str) == target_year and int(mm_str) <= target_month:
                                        ytd_socso_eis += float(r.get('socso_employee') or 0.0) + float(r.get('eis_employee') or 0.0)
                            except Exception:
                                continue
                except Exception:
                    ytd_socso_eis = 0.0
                table.setItem(extra_row, 4, QTableWidgetItem(f"{ytd_socso_eis:.2f}"))
                remaining_cap = max(0.0, 350.0 - ytd_socso_eis)
                table.setItem(extra_row, 5, QTableWidgetItem(f"{remaining_cap:.2f}"))
                table.setItem(extra_row, 6, QTableWidgetItem("Yes"))
                table.setItem(extra_row, 7, QTableWidgetItem("-"))
            except Exception as _se_info_err:
                print(f"DEBUG: Quick TP1 could not append SOCSO+EIS info row: {_se_info_err}")

            layout.addWidget(table)

            # Buttons
            btn_row = QHBoxLayout()
            btn_row.addStretch()
            save_btn = QPushButton("Save Claims")
            close_btn = QPushButton("Close")
            btn_row.addWidget(save_btn)
            btn_row.addWidget(close_btn)
            layout.addLayout(btn_row)

            def do_save():
                try:
                    claims = {}
                    for row, item in enumerate(TP1_ITEMS):
                        spin = table.cellWidget(row, 2)
                        if not spin:
                            continue
                        val = float(spin.value())
                        if val > 0:
                            claims[item.key] = round(val, 2)

                    # Apply cap enforcement and trim values before saving
                    trimmed_claims = dict(claims)
                    try:
                        from core.tax_relief_catalog import (
                            load_relief_overrides_from_db, load_relief_group_overrides_from_db,
                            get_effective_items, get_effective_groups, apply_relief_caps
                        )
                        _ov = {}
                        _gov = {}
                        try:
                            _ov = load_relief_overrides_from_db(supabase)
                        except Exception:
                            _ov = {}
                        try:
                            _gov = load_relief_group_overrides_from_db(supabase)
                        except Exception:
                            _gov = {}
                        eff_items = get_effective_items(_ov)
                        eff_groups = get_effective_groups(_gov) if _gov else None
                        # First: enforce per-item caps using effective items
                        pretrim = {}
                        for k, v in claims.items():
                            it = eff_items.get(k)
                            if it and it.cap is not None:
                                pretrim[k] = min(v, float(it.cap))
                            else:
                                pretrim[k] = v
                        # Then: enforce group caps proportionally
                        total_lp1, per_item_applied, group_usage = apply_relief_caps(pretrim, groups=eff_groups)
                        # Build a simple diff summary if any trims occurred
                        diffs = []
                        for k, orig in claims.items():
                            applied = per_item_applied.get(k, 0.0)
                            if round(applied,2) < round(orig,2):
                                diffs.append(f"• {k}: entered {orig:,.2f} → will save {applied:,.2f}")
                        if diffs:
                            result = QMessageBox.question(dlg, "Caps Exceeded",
                                "Some entries exceed item/group caps and will be trimmed:\n\n"
                                + "\n".join(diffs) + "\n\nSave with trimmed values?",
                                QMessageBox.Yes | QMessageBox.No
                            )
                            if result == QMessageBox.No:
                                return
                        # Use trimmed values for saving
                        trimmed_claims = {k: v for k, v in per_item_applied.items() if v > 0}
                    except Exception:
                        pass

                    upsert_tp1_monthly_details(emp_id, target_year, target_month, trimmed_claims, {
                        'other_reliefs_monthly': 0.0,
                        'socso_eis_lp1_monthly': 0.0,
                        'zakat_monthly': 0.0
                    })
                    QMessageBox.information(dlg, "Saved", "TP1 relief claims saved. They will be applied on the next payroll run.")
                except Exception as e:
                    QMessageBox.warning(dlg, "Error", f"Failed to save claims: {e}")

            save_btn.clicked.connect(do_save)
            close_btn.clicked.connect(dlg.close)
            dlg.setLayout(layout)
            dlg.resize(900, 560)
            dlg.exec_()

        except Exception as e:
            QMessageBox.warning(self, "Quick TP1", f"Unable to open Quick TP1 dialog: {e}")

    def open_quick_tp1_reliefs(self):
        """Open Admin TP1 Reliefs dialog preselected to this employee (locked)."""
        try:
            emp_id = None
            if isinstance(self.employee_data, dict):
                emp_id = self.employee_data.get('id') or self.employee_data.get('employee_id')
            if not emp_id:
                QMessageBox.warning(self, "TP1 Reliefs", "No employee selected in this dialog.")
                return

            # Climb parents to find admin dashboard to access AdminPayrollTab
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                parent_widget = parent_widget.parent()

            if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                admin_dashboard = parent_widget.admin_dashboard_page
                if hasattr(admin_dashboard, 'payroll_tab') and hasattr(admin_dashboard.payroll_tab, 'open_tp1_relief_dialog'):
                    # Call with employee locked; let Admin tab's date_input define the period
                    try:
                        admin_dashboard.payroll_tab.open_tp1_relief_dialog(
                            default_employee_id=emp_id,
                            lock_employee=True
                        )
                        return
                    except Exception as call_err:
                        QMessageBox.warning(self, "TP1 Reliefs", f"Unable to open TP1 Reliefs: {call_err}")
                        return

            # Fallback: not found
            QMessageBox.information(
                self,
                "TP1 Reliefs",
                "Admin Payroll tab not found. Open Admin ▶ TP1 Reliefs from the dashboard."
            )
        except Exception as e:
            QMessageBox.critical(self, "TP1 Reliefs", f"Unexpected error: {e}")

    def create_basic_payroll_section_rows(self, parent_layout):
        """Create basic payroll information section with Malaysian tax form context"""
        payroll_group = QGroupBox("� SARAAN BULAN SEMASA - Monthly Salary")
        payroll_main_layout = QVBoxLayout()
        
        # Create a grid layout for form fields (2-3 columns)
        payroll_grid = QHBoxLayout()
        payroll_grid.setSpacing(30)
        
        # Left column of basic info
        left_form = QFormLayout()
        left_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # === MAKLUMAT PERIBADI - Personal Information ===
        # Note: Citizenship and marital status are managed in Employee Profile Dialog
        
        # Enhanced Individual Children Management with Custody Sharing
        children_main_layout = QVBoxLayout()
        
        # Add children button and management section
        add_child_button = QPushButton("➕ Add Child")
        add_child_button.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 5px; }")
        add_child_button.clicked.connect(self.add_child_entry)
        children_main_layout.addWidget(add_child_button)
        
        # Children list container (scrollable area for individual children)
        self.children_scroll = QScrollArea()
        self.children_scroll.setMaximumHeight(200)
        self.children_scroll.setWidgetResizable(True)
        self.children_widget = QWidget()
        self.children_layout = QVBoxLayout(self.children_widget)
        self.children_scroll.setWidget(self.children_widget)
        children_main_layout.addWidget(self.children_scroll)
        
        # Children list to track individual entries
        self.children_entries = []
        
        # Summary totals (read-only, calculated automatically)
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("📊 Summary:"))
        
        self.fields["total_children_under_18"] = QLabel("Normal <18: 0")
        self.fields["total_children_tertiary"] = QLabel("Normal 18+ matrikulasi: 0 | Normal 18+ diploma: 0") 
        self.fields["total_children_disabled"] = QLabel("OKU any age: 0 | OKU 18+ belajar: 0")
        
        summary_layout.addWidget(self.fields["total_children_under_18"])
        summary_layout.addWidget(self.fields["total_children_tertiary"])
        summary_layout.addWidget(self.fields["total_children_disabled"])
        
        children_main_layout.addLayout(summary_layout)
        
        # Explanation note
        custody_note = QLabel("📌 LHDN B16 Child Relief - All children must be UNMARRIED (belum berkahwin)\n• 100% = Only you claim | 50% = Shared with ex-spouse | 0% = Other parent claims\n• Normal: <18=RM2K | 18+ matrikulasi=RM2K | 18+ diploma=RM8K\n• OKU (no age limit): Any age=RM8K | 18+ belajar=RM8K+RM8K=RM16K total")
        custody_note.setStyleSheet("color: #666; font-size: 9px; font-style: italic;")
        children_main_layout.addWidget(custody_note)
        
        left_form.addRow("Individual Children Management:", children_main_layout)
        
        # === TAX & STATUTORY INFORMATION ===
        tax_info_group = QGroupBox("🏛️ Tax & Statutory Information")
        tax_grid = QGridLayout()
        tax_grid.setSpacing(10)
        
        # Column 1: Tax Number
        tax_grid.addWidget(QLabel("Tax Number:"), 0, 0)
        self.fields["income_tax_number"] = QLineEdit()
        self.fields["income_tax_number"].setMinimumWidth(120)
        tax_grid.addWidget(self.fields["income_tax_number"], 0, 1)
        
        # Column 2: EPF Number  
        tax_grid.addWidget(QLabel("EPF Number:"), 0, 2)
        self.fields["epf_number"] = QLineEdit()
        self.fields["epf_number"].setMinimumWidth(120)
        tax_grid.addWidget(self.fields["epf_number"], 0, 3)
        
        # Column 3: SOCSO Number
        tax_grid.addWidget(QLabel("SOCSO Number:"), 0, 4)
        self.fields["socso_number"] = QLineEdit()
        self.fields["socso_number"].setMinimumWidth(120)
        tax_grid.addWidget(self.fields["socso_number"], 0, 5)
        
        tax_info_group.setLayout(tax_grid)
        left_form.addRow(tax_info_group)
        
        # === DISABILITY STATUS - B4 & B15 Tax Relief ===
        disability_group = QGroupBox("🦽 Disability Status - Tax Relief Eligibility")
        disability_layout = QFormLayout()
        
        # B4 - Individual Disability Relief (RM6,000 automatic if checked)
        self.fields["is_individual_disabled"] = QCheckBox()
        self.fields["is_individual_disabled"].setToolTip("B4 - Check if you are registered as OKU with LHDN (automatic RM6,000 relief)")
        disability_layout.addRow("Individual Disabled (OKU):", self.fields["is_individual_disabled"])
        
        # B15 - Disabled Spouse Relief (RM5,000 automatic if checked)  
        self.fields["is_spouse_disabled"] = QCheckBox()
        self.fields["is_spouse_disabled"].setToolTip("B15 - Check if your spouse is registered as OKU with LHDN (automatic RM5,000 relief)")
        disability_layout.addRow("Spouse Disabled (OKU):", self.fields["is_spouse_disabled"])
        
        disability_note = QLabel("📝 Note: These are automatic LHDN reliefs - no amount input needed")
        disability_note.setStyleSheet("color: #666; font-size: 10px; font-style: italic; margin-top: 5px;")
        disability_layout.addRow(disability_note)
        
        disability_group.setLayout(disability_layout)
        left_form.addRow(disability_group)
        
        # Basic salary information
        self.fields["basic_salary"] = QDoubleSpinBox()
        self.fields["basic_salary"].setRange(0.0, 999999.99)
        self.fields["basic_salary"].setSuffix(" RM")
        self.fields["basic_salary"].setMinimumWidth(150)
        left_form.addRow("Gaji Pokok + Elaun Kena Cukai:", self.fields["basic_salary"])

        # Bank information with dropdown + custom option
        bank_layout = QVBoxLayout()
        
        self.fields["bank_name"] = QComboBox()
        self.fields["bank_name"].setMinimumWidth(150)
        self.fields["bank_name"].addItems([
            "Select Bank...",
            "Maybank (Malayan Banking Berhad)",
            "CIMB Bank",
            "Public Bank Berhad",
            "RHB Bank",
            "Hong Leong Bank",
            "AmBank (AmBank Group)",
            "OCBC Bank Malaysia",
            "Standard Chartered Bank Malaysia",
            "HSBC Bank Malaysia",
            "UOB Malaysia",
            "Bank Islam Malaysia",
            "CIMB Islamic Bank",
            "Maybank Islamic",
            "Public Islamic Bank",
            "RHB Islamic Bank",
            "Hong Leong Islamic Bank",
            "AmBank Islamic",
            "OCBC Al-Amin Bank",
            "Standard Chartered Saadiq",
            "HSBC Amanah Malaysia",
            "Bank Rakyat",
            "BSN (Bank Simpanan Nasional)",
            "Affin Bank",
            "Alliance Bank Malaysia",
            "Bank Muamalat Malaysia",
            "MBSB Bank (Malaysia Building Society)",
            "Agro Bank",
            "SME Bank",
            "Export-Import Bank of Malaysia",
            "Development Bank of Malaysia",
            "Other (Specify)"
        ])
        
        # Custom bank name input (initially hidden)
        self.fields["bank_name_custom"] = QLineEdit()
        self.fields["bank_name_custom"].setMinimumWidth(150)
        self.fields["bank_name_custom"].setPlaceholderText("Enter bank name...")
        self.fields["bank_name_custom"].setVisible(False)
        
        # Connect dropdown to show/hide custom input
        self.fields["bank_name"].currentTextChanged.connect(self.on_bank_selection_changed)
        
        bank_layout.addWidget(self.fields["bank_name"])
        bank_layout.addWidget(self.fields["bank_name_custom"])
        left_form.addRow("Bank Name:", bank_layout)

        self.fields["bank_account"] = QLineEdit()
        self.fields["bank_account"].setMinimumWidth(150)
        left_form.addRow("Account Number:", self.fields["bank_account"])
        
        # Right column of basic info
        right_form = QFormLayout()
        right_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        
        # Add form columns to grid
        payroll_grid.addLayout(left_form)
        payroll_grid.addLayout(right_form)
        
        payroll_main_layout.addLayout(payroll_grid)
        
        # Allowances section with 3-column layout
        allowances_group = QGroupBox("💰 Allowances")
        allowances_grid = QHBoxLayout()
        allowances_grid.setSpacing(20)
        
        # Column 1
        allow_col1 = QFormLayout()
        self.fields["meal_allowance"] = QDoubleSpinBox()
        self.fields["meal_allowance"].setRange(0.0, 99999.99)
        self.fields["meal_allowance"].setSuffix(" RM")
        self.fields["meal_allowance"].setMinimumWidth(120)
        allow_col1.addRow("Meal:", self.fields["meal_allowance"])
        
        self.fields["transport_allowance"] = QDoubleSpinBox()
        self.fields["transport_allowance"].setRange(0.0, 99999.99)
        self.fields["transport_allowance"].setSuffix(" RM")
        self.fields["transport_allowance"].setMinimumWidth(120)
        allow_col1.addRow("Transport:", self.fields["transport_allowance"])
        
        # Column 2
        allow_col2 = QFormLayout()
        self.fields["medical_allowance"] = QDoubleSpinBox()
        self.fields["medical_allowance"].setRange(0.0, 99999.99)
        self.fields["medical_allowance"].setSuffix(" RM")
        self.fields["medical_allowance"].setMinimumWidth(120)
        allow_col2.addRow("Medical:", self.fields["medical_allowance"])
        
        self.fields["phone_allowance"] = QDoubleSpinBox()
        self.fields["phone_allowance"].setRange(0.0, 99999.99)
        self.fields["phone_allowance"].setSuffix(" RM")
        self.fields["phone_allowance"].setMinimumWidth(120)
        allow_col2.addRow("Phone:", self.fields["phone_allowance"])
        
        # Column 3
        allow_col3 = QFormLayout()
        self.fields["other_allowance"] = QDoubleSpinBox()
        self.fields["other_allowance"].setRange(0.0, 99999.99)
        self.fields["other_allowance"].setSuffix(" RM")
        self.fields["other_allowance"].setMinimumWidth(120)
        allow_col3.addRow("Other:", self.fields["other_allowance"])
        
        # Tax resident status
        self.fields["tax_resident_status"] = QComboBox()
        self.fields["tax_resident_status"].addItems(["Resident", "Non-Resident"])
        self.fields["tax_resident_status"].setCurrentText("Resident")
        self.fields["tax_resident_status"].setMinimumWidth(120)
        self.fields["tax_resident_status"].setToolTip(
            "Tax resident status based on HASIL (LHDN) regulations:\n\n"
            "RESIDENT: Staying 182+ days in Malaysia in a year\n"
            "• Progressive tax rates (0%-30%)\n"
            "• Full access to all tax reliefs (B1-B21)\n"
            "• Uses standard tax forms (BE/B/BT/M)\n\n"
            "NON-RESIDENT: Staying less than 182 days in Malaysia in a year\n"
            "• Flat 30% tax rate on Malaysian income (Assessment Year 2020+)\n"
            "• Limited tax reliefs (EPF contributions only)\n"
            "• Must use M Form for tax declaration\n"
            "• Special rates: 15% (entertainment/interest), 10% (royalty)"
        )
        # Connect tax resident status change handler to enable/disable tax reliefs
        self.fields["tax_resident_status"].currentTextChanged.connect(self.handle_tax_resident_status_change)
        allow_col3.addRow("Tax Status:", self.fields["tax_resident_status"])

        # Add allowance columns to grid
        allowances_grid.addLayout(allow_col1)
        allowances_grid.addLayout(allow_col2)
        allowances_grid.addLayout(allow_col3)

        allowances_group.setLayout(allowances_grid)
        payroll_main_layout.addWidget(allowances_group)

        payroll_group.setLayout(payroll_main_layout)
        parent_layout.addWidget(payroll_group)

    # PCB calculation data section removed (redundant informational UI)

        # Add Malaysian additional salary section (extracted)
        build_additional_salary_section(self, parent_layout)

    def create_pcb_calculation_section(self, parent_layout):
        # Legacy method retained for compatibility; no longer builds UI
        pass

    def create_malaysian_additional_salary_section(self, parent_layout):
        # Legacy method kept for backward compatibility; now delegates to module
        build_additional_salary_section(self, parent_layout)

    def create_malaysian_monthly_deductions_section(self, parent_layout):
        # Legacy method no longer used; built via additional_salary_section module
        from gui.payroll_sections.monthly_deductions_section import build_monthly_deductions_section
        build_monthly_deductions_section(self, parent_layout)

    def create_tax_sections_row(self, parent_layout):
        """Create tax configuration sections in a horizontal row"""
        tax_row_widget = QWidget()
        tax_row_layout = QHBoxLayout(tax_row_widget)
        tax_row_layout.setSpacing(20)
        
        
        tax_row_layout.addStretch()
        
        parent_layout.addWidget(tax_row_widget)

    def create_benefits_deductions_row(self, parent_layout):
        """Create additional benefits (deductions removed)"""
        benefits_row_widget = QWidget()
        benefits_row_layout = QHBoxLayout(benefits_row_widget)
        benefits_row_layout.setSpacing(25)

        # Additional benefits container (full width)
        benefits_container = QWidget()
        benefits_container_layout = QVBoxLayout(benefits_container)
        self.create_additional_benefits_section(benefits_container_layout)

        benefits_row_layout.addWidget(benefits_container, 1)
        parent_layout.addWidget(benefits_row_widget)

    def create_basic_payroll_section_column(self, parent_layout):
        """Create basic payroll information section optimized for column layout"""
        payroll_group = QGroupBox("💼 Basic Payroll Information")
        payroll_layout = QFormLayout()

        # Basic salary information
        self.fields["basic_salary"] = QDoubleSpinBox()
        self.fields["basic_salary"].setRange(0.0, 999999.99)
        self.fields["basic_salary"].setSuffix(" RM")
        payroll_layout.addRow("Basic Salary:", self.fields["basic_salary"])

        # Bank information
        self.fields["bank_name"] = QLineEdit()
        payroll_layout.addRow("Bank Name:", self.fields["bank_name"])

        self.fields["bank_account"] = QLineEdit()
        payroll_layout.addRow("Account Number:", self.fields["bank_account"])

        # Tax information
        self.fields["income_tax_number"] = QLineEdit()
        payroll_layout.addRow("Tax Number:", self.fields["income_tax_number"])

        self.fields["epf_number"] = QLineEdit()
        payroll_layout.addRow("EPF Number:", self.fields["epf_number"])

        self.fields["socso_number"] = QLineEdit()
        payroll_layout.addRow("SOCSO Number:", self.fields["socso_number"])

        # --- Allowances Section ---
        allowances_group = QGroupBox("💰 Allowances")
        allowances_layout = QFormLayout()
        
        self.fields["meal_allowance"] = QDoubleSpinBox()
        self.fields["meal_allowance"].setRange(0.0, 99999.99)
        self.fields["meal_allowance"].setSuffix(" RM")
        allowances_layout.addRow("Meal:", self.fields["meal_allowance"])
        
        self.fields["transport_allowance"] = QDoubleSpinBox()
        self.fields["transport_allowance"].setRange(0.0, 99999.99)
        self.fields["transport_allowance"].setSuffix(" RM")
        allowances_layout.addRow("Transport:", self.fields["transport_allowance"])
        
        self.fields["medical_allowance"] = QDoubleSpinBox()
        self.fields["medical_allowance"].setRange(0.0, 99999.99)
        self.fields["medical_allowance"].setSuffix(" RM")
        allowances_layout.addRow("Medical:", self.fields["medical_allowance"])
        
        self.fields["phone_allowance"] = QDoubleSpinBox()
        self.fields["phone_allowance"].setRange(0.0, 99999.99)
        self.fields["phone_allowance"].setSuffix(" RM")
        allowances_layout.addRow("Phone:", self.fields["phone_allowance"])
        
        self.fields["other_allowance"] = QDoubleSpinBox()
        self.fields["other_allowance"].setRange(0.0, 99999.99)
        self.fields["other_allowance"].setSuffix(" RM")
        allowances_layout.addRow("Other:", self.fields["other_allowance"])
        
        allowances_group.setLayout(allowances_layout)
        payroll_layout.addRow(allowances_group)

        # Resident status for tax calculations
        self.fields["tax_resident_status"] = QComboBox()
        self.fields["tax_resident_status"].addItems([
            "Resident", 
            "Non-Resident"
        ])
        self.fields["tax_resident_status"].setCurrentText("Resident")  # Default to resident
        self.fields["tax_resident_status"].setToolTip(
            "Tax resident status based on HASIL (LHDN) regulations:\n\n"
            "RESIDENT: Staying 182+ days in Malaysia in a year\n"
            "• Progressive tax rates (0%-30%)\n"
            "• Full access to all tax reliefs (B1-B21)\n"
            "• Uses standard tax forms (BE/B/BT/M)\n\n"
            "NON-RESIDENT: Staying less than 182 days in Malaysia in a year\n"
            "• Flat 30% tax rate on Malaysian income (Assessment Year 2020+)\n"
            "• Limited tax reliefs (EPF contributions only)\n"
            "• Must use M Form for tax declaration\n"
            "• Special rates: 15% (entertainment/interest), 10% (royalty)"
        )
        # Prefill from employee master record (option 2 implementation)
        try:
            if self.employee_data:
                ts_val = self.employee_data.get('tax_resident_status')
                if isinstance(ts_val, str) and ts_val.strip():
                    normalized = ts_val.strip().title()
                    if normalized in ["Resident", "Non-Resident"]:
                        self.fields["tax_resident_status"].setCurrentText(normalized)
                else:
                    bool_val = self.employee_data.get('is_resident')
                    if isinstance(bool_val, bool):
                        self.fields["tax_resident_status"].setCurrentText('Resident' if bool_val else 'Non-Resident')
        except Exception as _prefill_err:
            print(f"DEBUG: tax_resident_status prefill failed: {_prefill_err}")
        # Connect signal to handle resident status changes
        # Tax resident status change handler removed
        payroll_layout.addRow("Tax Status:", self.fields["tax_resident_status"])

        payroll_group.setLayout(payroll_layout)
        parent_layout.addWidget(payroll_group)



    def create_additional_benefits_section(self, parent_layout):
        """Create additional benefits section (SIP, PRS, Additional EPF)"""
        benefits_group = QGroupBox("🏦 Additional Benefits & Contributions")
        benefits_layout = QVBoxLayout()
        
        # SIP Section
        sip_group = QGroupBox("📈 Share Investment Plan (SIP)")
        sip_layout = QFormLayout()
        
        self.fields["sip_participation"] = QComboBox()
        self.fields["sip_participation"].addItems(["No", "Yes"])
        sip_layout.addRow("SIP Participation:", self.fields["sip_participation"])
        
        self.fields["sip_type"] = QComboBox()
        self.fields["sip_type"].addItems(["None", "Fixed Amount", "Percentage"])
        sip_layout.addRow("SIP Type:", self.fields["sip_type"])
        
        self.fields["sip_amount_rate"] = QDoubleSpinBox()
        self.fields["sip_amount_rate"].setRange(0.0, 99999.99)
        self.fields["sip_amount_rate"].setSuffix(" RM/%)") 
        sip_layout.addRow("SIP Amount/Rate:", self.fields["sip_amount_rate"])
        
        sip_group.setLayout(sip_layout)
        benefits_layout.addWidget(sip_group)
        
        # Additional EPF Section
        epf_group = QGroupBox("💼 Additional EPF Contributions")
        epf_layout = QFormLayout()
        
        self.fields["additional_epf_enabled"] = QComboBox()
        self.fields["additional_epf_enabled"].addItems(["No", "Yes"])
        epf_layout.addRow("Additional EPF:", self.fields["additional_epf_enabled"])
        
        self.fields["additional_epf_amount"] = QDoubleSpinBox()
        self.fields["additional_epf_amount"].setRange(0.0, 99999.99)
        self.fields["additional_epf_amount"].setSuffix(" RM")
        epf_layout.addRow("Additional EPF Amount:", self.fields["additional_epf_amount"])
        
        epf_group.setLayout(epf_layout)
        benefits_layout.addWidget(epf_group)
        
        # PRS Section
        prs_group = QGroupBox("🎯 Private Retirement Scheme (PRS)")
        prs_layout = QFormLayout()
        
        self.fields["prs_participation"] = QComboBox()
        self.fields["prs_participation"].addItems(["No", "Yes"])
        prs_layout.addRow("PRS Participation:", self.fields["prs_participation"])
        
        self.fields["prs_amount"] = QDoubleSpinBox()
        self.fields["prs_amount"].setRange(0.0, 99999.99)
        self.fields["prs_amount"].setSuffix(" RM")
        prs_layout.addRow("PRS Amount:", self.fields["prs_amount"])
        
        prs_group.setLayout(prs_layout)
        benefits_layout.addWidget(prs_group)
        
        benefits_group.setLayout(benefits_layout)
        parent_layout.addWidget(benefits_group)

    # Removed create_deductions_section: Potongan Bulan Semasa UI deprecated in favor of TP1 dialog. Legacy inputs (insurance_premium, medical_premium, other_deductions_amount) eliminated.



    def create_buttons(self, parent_layout):
        """Create dialog buttons"""
        button_layout = QHBoxLayout()
        
        button_layout.addStretch()
        
        # Save button
        save_button = QPushButton("💾 Save")
        save_button.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; padding: 8px 16px; border-radius: 4px; }")
        save_button.clicked.connect(self.save_payroll_data)
        button_layout.addWidget(save_button)
        
        # Cancel button
        cancel_button = QPushButton("❌ Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        parent_layout.addLayout(button_layout)

    def connect_children_amount_helpers(self):
        """Initialize children management system"""
        # Initialize empty - children will be added manually or loaded from data
        pass

    def add_child_entry(self):
        """Add a new child entry"""
        child_index = len(self.children_entries)
        
        # Create child entry container
        child_frame = QWidget()
        child_frame.setStyleSheet("QWidget { border: 1px solid #ddd; border-radius: 5px; padding: 5px; margin: 2px; background-color: #f9f9f9; }")
        child_layout = QHBoxLayout(child_frame)
        child_layout.setContentsMargins(5, 5, 5, 5)
        
        # Child number label
        child_label = QLabel(f"Child {child_index + 1}:")
        child_label.setMinimumWidth(60)
        child_label.setStyleSheet("font-weight: bold; color: #333;")
        child_layout.addWidget(child_label)
        
        # Child category
        category_combo = QComboBox()
        category_combo.addItems([
            "Normal - Under 18 years (RM2,000)",
            "Normal - 18+ matrikulasi/A-Level Malaysia (RM2,000)", 
            "Normal - 18+ diploma/degree (RM8,000)",
            "OKU - Any age, not studying (RM8,000)",
            "OKU - 18+ studying diploma/degree (RM8,000 + RM8,000 = RM16,000)"
        ])
        category_combo.currentTextChanged.connect(self.update_children_summary)
        child_layout.addWidget(QLabel("Category:"))
        child_layout.addWidget(category_combo)
        
        # Custody sharing
        custody_combo = QComboBox()
        custody_combo.addItems(["100% (Full claim)", "50% (Shared)", "0% (Not claimed)"])
        child_layout.addWidget(QLabel("Custody:"))
        child_layout.addWidget(custody_combo)
        
        # Remove button
        remove_btn = QPushButton("🗑️")
        remove_btn.setMaximumWidth(30)
        remove_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        remove_btn.clicked.connect(lambda: self.remove_child_entry(child_frame))
        child_layout.addWidget(remove_btn)
        
        # Store entry data (no name field needed)
        child_entry = {
            'frame': child_frame,
            'label': child_label,
            'category': category_combo,
            'custody': custody_combo
        }
        
        self.children_entries.append(child_entry)
        self.children_layout.addWidget(child_frame)
        
        # Update summary
        self.update_children_summary()
        
    def remove_child_entry(self, child_frame):
        """Remove a child entry"""
        # Find and remove the entry
        for i, entry in enumerate(self.children_entries):
            if entry['frame'] == child_frame:
                self.children_entries.pop(i)
                child_frame.setParent(None)
                break
        
        # Update child labels (renumber remaining children)
        for i, entry in enumerate(self.children_entries):
            entry['label'].setText(f"Child {i + 1}:")
        
        # Update summary
        self.update_children_summary()
        
    def update_children_summary(self):
        """Update the summary totals based on individual children"""
        counts = {"normal_under18": 0, "normal_18_matrikulasi": 0, "normal_18_diploma": 0, 
                 "oku_any_age": 0, "oku_18_studying": 0}
        
        for entry in self.children_entries:
            category = entry['category'].currentText()
            if category.startswith("Normal - Under 18"):
                counts["normal_under18"] += 1
            elif category.startswith("Normal - 18+ matrikulasi"):
                counts["normal_18_matrikulasi"] += 1
            elif category.startswith("Normal - 18+ diploma"):
                counts["normal_18_diploma"] += 1
            elif category.startswith("OKU - Any age"):
                counts["oku_any_age"] += 1
            elif category.startswith("OKU - 18+ studying"):
                counts["oku_18_studying"] += 1
        
        # Update summary labels with correct categories and amounts
            elif category.startswith("OKU - 18+ studying"):
                counts["oku_18_studying"] += 1
        
        # Update summary labels with correct categories and amounts
        self.fields["total_children_under_18"].setText(f"Normal <18: {counts['normal_under18']}")
        self.fields["total_children_tertiary"].setText(f"Normal 18+ matrikulasi: {counts['normal_18_matrikulasi']} | Normal 18+ diploma: {counts['normal_18_diploma']}")
        self.fields["total_children_disabled"].setText(f"OKU any age: {counts['oku_any_age']} | OKU 18+ belajar: {counts['oku_18_studying']}")

    def on_bank_selection_changed(self, bank_name):
        """Show/hide custom bank name input based on selection"""
        if bank_name == "Other (Specify)":
            self.fields["bank_name_custom"].setVisible(True)
            self.fields["bank_name_custom"].setFocus()
        else:
            self.fields["bank_name_custom"].setVisible(False)
            self.fields["bank_name_custom"].clear()

    def quick_tp1_reliefs(self):
        """Open Admin TP1 Reliefs dialog pre-filtered to this employee and payroll period."""
        try:
            if not self.employee_data or 'id' not in self.employee_data:
                QMessageBox.information(self, "TP1 Reliefs", "No employee selected in this dialog.")
                return
            emp_id = self.employee_data['id']

            # Walk up to find admin dashboard with payroll tab
            parent_widget = self.parent()
            while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                parent_widget = parent_widget.parent()

            target_year = None
            target_month = None
            admin_tab = None
            if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                admin_dashboard = parent_widget.admin_dashboard_page
                if hasattr(admin_dashboard, 'payroll_tab'):
                    admin_tab = admin_dashboard.payroll_tab
                    try:
                        qd = admin_tab.date_input.date()
                        target_year = qd.year()
                        target_month = qd.month()
                    except Exception:
                        target_year = None
                        target_month = None

            # Fallback to current date if admin date not found
            if target_year is None or target_month is None:
                from datetime import datetime as _dt
                now = _dt.now()
                target_year, target_month = now.year, now.month

            if admin_tab and hasattr(admin_tab, 'open_tp1_relief_dialog'):
                admin_tab.open_tp1_relief_dialog(
                    default_employee_id=emp_id,
                    lock_employee=True,
                    target_year=target_year,
                    target_month=target_month
                )
            else:
                QMessageBox.information(self, "TP1 Reliefs", "Could not locate Admin ▶ TP1 Reliefs dialog. Please open Admin Payroll tab and try again.")
        except Exception as e:
            QMessageBox.warning(self, "TP1 Reliefs", f"Failed to open TP1 Reliefs: {e}")

    def save_payroll_data(self):
        """Save payroll data to payroll_configurations and monthly deductions/employee core fields"""
        try:
            if not self.employee_data or 'id' not in self.employee_data:
                QMessageBox.warning(self, "Error", "No employee selected")
                return
            
            employee_id = self.employee_data['id']
            
            # Prepare data for payroll_configurations table
            config_data = {
                'employee_id': employee_id
            }
            
            # Basic payroll information
            basic_fields = {
                'basic_salary': 'basic_salary',
                'bank_account': 'bank_account',
                'income_tax_number': 'income_tax_number',
            }
            
            # Handle bank name specially (dropdown vs. custom input)
            if 'bank_name' in self.fields:
                selected_bank = self.fields['bank_name'].currentText()
                if selected_bank == "Other (Specify)" and 'bank_name_custom' in self.fields:
                    config_data['bank_name'] = self.fields['bank_name_custom'].text()
                elif selected_bank != "Select Bank...":
                    config_data['bank_name'] = selected_bank
                else:
                    config_data['bank_name'] = ""
            
            for field_name, db_column in basic_fields.items():
                if field_name in self.fields:
                    widget = self.fields[field_name]
                    if isinstance(widget, QDoubleSpinBox):
                        config_data[db_column] = widget.value()
                    elif isinstance(widget, QComboBox):
                        config_data[db_column] = widget.currentText()
                    else:
                        config_data[db_column] = widget.text()
            
            # Additional fields from the new schema
            additional_fields = {
                'sip_participation': 'sip_participation',
                'sip_type': 'sip_type', 
                'sip_amount_rate': 'sip_amount_rate',
                'additional_epf_enabled': 'additional_epf_enabled',
                'additional_epf_amount': 'additional_epf_amount',
                'prs_participation': 'prs_participation',
                'prs_amount': 'prs_amount'
            }
            
            for field_name, db_column in additional_fields.items():
                if field_name in self.fields:
                    widget = self.fields[field_name]
                    if isinstance(widget, QDoubleSpinBox):
                        config_data[db_column] = widget.value()
                    elif isinstance(widget, QComboBox):
                        config_data[db_column] = widget.currentText()
                    else:
                        config_data[db_column] = widget.text()
            
            # Handle allowances (store in employees table as JSON for now)
            allowances_data = {}
            allowance_fields = ['meal_allowance', 'transport_allowance', 'medical_allowance', 'phone_allowance', 'other_allowance']
            for field in allowance_fields:
                if field in self.fields:
                    allowances_data[field.replace('_allowance', '')] = self.fields[field].value()
            
            # (Deprecated) Legacy monthly deductions removed. Capture only zakat/religious travel if still present for backward compat.
            monthly_deductions = {}
            for legacy_key in ['zakat_monthly', 'religious_travel_monthly']:
                if legacy_key in self.fields and isinstance(self.fields[legacy_key], QDoubleSpinBox):
                    monthly_deductions[legacy_key] = self.fields[legacy_key].value()
            if monthly_deductions:
                config_data['monthly_deductions'] = monthly_deductions
            
            # Disability status (B4 & B15 tax relief checkboxes)
            if 'is_individual_disabled' in self.fields:
                config_data['is_individual_disabled'] = self.fields['is_individual_disabled'].isChecked()
            if 'is_spouse_disabled' in self.fields:
                config_data['is_spouse_disabled'] = self.fields['is_spouse_disabled'].isChecked()

            # Snapshot TP1/relief inputs for persistence in payroll_configurations.tax_relief_data (if column exists)
            try:
                tax_fields = [
                    'parent_medical_treatment', 'parent_dental', 'parent_checkup_vaccine',
                    'basic_support_equipment',
                    'education_non_masters', 'education_masters_phd', 'skills_course',
                    'lifestyle_books', 'lifestyle_computer', 'lifestyle_internet', 'lifestyle_skills',
                    # EPF + Insurance related entries often used in Section 11
                    'epf_additional', 'epf_voluntary', 'life_insurance',
                    # Other common relief-like inputs captured in this dialog
                    'prs_amount', 'insurance_premium', 'medical_premium'
                ]
                tax_relief_data = {}
                for fname in tax_fields:
                    if fname in self.fields:
                        w = self.fields[fname]
                        try:
                            # Prefer numeric spin boxes; fallback to text
                            if hasattr(w, 'value'):
                                tax_relief_data[fname] = float(w.value())
                            elif hasattr(w, 'text'):
                                # Best-effort numeric cast
                                _t = w.text().strip()
                                tax_relief_data[fname] = float(_t) if _t else 0.0
                        except Exception:
                            # If cannot coerce, store raw text/value
                            try:
                                tax_relief_data[fname] = w.text()
                            except Exception:
                                pass
                # Include disability booleans in snapshot for completeness
                if 'is_individual_disabled' in self.fields:
                    tax_relief_data['is_individual_disabled'] = bool(self.fields['is_individual_disabled'].isChecked())
                if 'is_spouse_disabled' in self.fields:
                    tax_relief_data['is_spouse_disabled'] = bool(self.fields['is_spouse_disabled'].isChecked())
                # Attach snapshot; safe-save will strip if the column doesn't exist
                if tax_relief_data:
                    config_data['tax_relief_data'] = tax_relief_data
            except Exception as _txsnap:
                print(f"DEBUG: Could not build tax_relief_data snapshot: {_txsnap}")
            
            # Individual children data with custody sharing
            children_data = []
            full_claim_children_count = 0
            for i, entry in enumerate(self.children_entries):
                child_data = {
                    'child_number': i + 1,
                    'category': entry['category'].currentText(),
                    'custody_percentage': entry['custody'].currentText()
                }
                try:
                    if str(child_data['custody_percentage']).strip().lower().startswith('100'):
                        full_claim_children_count += 1
                except Exception:
                    pass
                children_data.append(child_data)
            
            # Store under legacy-compatible column name to match current DB schema
            # Note: Loader already supports both 'individual_children' and 'children_data'
            # Write to both keys so whichever column exists in DB will persist; the safe-save
            # helper will strip the unknown one if schema lacks it.
            config_data['children_data'] = children_data
            config_data['individual_children'] = children_data
            
            # Add metadata
            config_data['updated_by'] = 'system'  # You can update this with actual user info
            
            # Check if payroll configuration already exists
            existing = supabase.table('payroll_configurations').select('id').eq('employee_id', employee_id).execute()

            # Helper: attempt save with graceful fallback if schema lacks optional columns
            def _safe_save_config(payload: dict, mode: str):
                """Attempt to save config; if PostgREST reports missing columns (PGRST204),
                iteratively remove the reported column from payload and retry.
                """
                import re
                attempt_payload = dict(payload)
                removed = set()
                for _ in range(12):  # guard against infinite loops
                    try:
                        if mode == 'update':
                            return supabase.table('payroll_configurations').update(attempt_payload).eq('employee_id', employee_id).execute()
                        else:
                            return supabase.table('payroll_configurations').insert(attempt_payload).execute()
                    except Exception as e:
                        msg = str(e)
                        if 'PGRST204' not in msg:
                            raise
                        # Extract the missing column name from message
                        m = re.search(r"Could not find the '([^']+)' column of 'payroll_configurations'", msg)
                        missing = m.group(1) if m else None
                        if not missing:
                            raise
                        if missing in attempt_payload:
                            attempt_payload.pop(missing, None)
                            removed.add(missing)
                            continue
                        # If the missing field is nested or not directly in payload, try known optional keys too
                        # Fallback: remove common optional fields when generic match fails
                        fallback_keys = ['children_data', 'individual_children']
                        did = False
                        for k in fallback_keys:
                            if k in attempt_payload and k not in removed:
                                attempt_payload.pop(k, None)
                                removed.add(k)
                                did = True
                                break
                        if did:
                            continue
                        # Nothing else to strip; re-raise
                        raise

            if existing.data:
                # Update existing record
                response = _safe_save_config(config_data, 'update')
            else:
                # Create new record
                config_data['created_by'] = 'system'
                response = _safe_save_config(config_data, 'insert')
            
            # Also update employees table with allowances and core fields
            employee_update = {
                'allowances': allowances_data,
                'basic_salary': config_data.get('basic_salary'),
                'bank_account': config_data.get('bank_account'),
                'income_tax_number': config_data.get('income_tax_number'),
                'epf_number': config_data.get('epf_number'),
                'socso_number': config_data.get('socso_number'),
                'tax_resident_status': config_data.get('tax_resident_status'),
                'bank_name': config_data.get('bank_name', ''),
                # Best-effort: reflect children full-claim count into employees.number_of_children
                'number_of_children': full_claim_children_count,
            }
            # Robust update for employees table: strip unknown columns on PGRST204 and retry
            def _safe_update_employee(payload: dict):
                import re
                attempt = dict(payload)
                for _ in range(12):
                    try:
                        return supabase.table('employees').update(attempt).eq('id', employee_id).execute()
                    except Exception as e:
                        msg = str(e)
                        if 'PGRST204' not in msg:
                            raise
                        m = re.search(r"Could not find the '([^']+)' column of 'employees'", msg)
                        missing = m.group(1) if m else None
                        if missing and missing in attempt:
                            attempt.pop(missing, None)
                            continue
                        # Fallback: remove one-by-one common optional fields if error message couldn't be parsed
                        fallback = ['income_tax_number','epf_number','socso_number','tax_resident_status','allowances','bank_name','bank_account','basic_salary']
                        removed = False
                        for k in list(attempt.keys()):
                            if k in fallback:
                                attempt.pop(k, None)
                                removed = True
                                break
                        if removed:
                            continue
                        raise

            _safe_update_employee(employee_update)

            # Removed Potongan Bulan Semasa upsert; TP1 handled exclusively in Admin dialog.

            if response.data:
                QMessageBox.information(self, "Success", "Payroll configuration saved successfully!")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", "Failed to save payroll configuration")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving payroll configuration: {str(e)}")
            print(f"DEBUG: Save error: {str(e)}")

    def load_payroll_data(self):
        """Load existing payroll data, preferring employees for core fields and monthly deductions from pmd table"""
        try:
            if not self.employee_data or 'id' not in self.employee_data:
                return
            
            employee_id = self.employee_data['id']
            # Load employees row (preferred source for core fields)
            emp_response = supabase.table('employees').select('*').eq('id', employee_id).execute()
            emp_data = emp_response.data[0] if emp_response.data else {}
            
            # Legacy/fallback config
            config_response = supabase.table('payroll_configurations').select('*').eq('employee_id', employee_id).execute()
            config_data = config_response.data[0] if config_response.data else {}
            
            # Load basic payroll fields
            basic_fields = {
                'basic_salary': 'basic_salary',
                'bank_account': 'bank_account', 
                'income_tax_number': 'income_tax_number',
                'epf_number': 'epf_number',
                'socso_number': 'socso_number',
                'tax_resident_status': 'tax_resident_status'
            }
            
            # Handle bank name specially (prefer employees)
            bank_src = emp_data if 'bank_name' in emp_data and emp_data.get('bank_name') else config_data
            if 'bank_name' in bank_src and bank_src['bank_name']:
                bank_name = bank_src['bank_name']
                if 'bank_name' in self.fields:
                    # Try to find exact match in dropdown
                    index = self.fields['bank_name'].findText(bank_name)
                    if index >= 0:
                        self.fields['bank_name'].setCurrentIndex(index)
                    else:
                        # Bank not in dropdown, use "Other" option
                        self.fields['bank_name'].setCurrentText("Other (Specify)")
                        if 'bank_name_custom' in self.fields:
                            self.fields['bank_name_custom'].setText(bank_name)
                            self.fields['bank_name_custom'].setVisible(True)
            
            for field_name, db_column in basic_fields.items():
                src = emp_data if (db_column in emp_data and emp_data.get(db_column) is not None) else config_data
                if db_column in src and field_name in self.fields:
                    value = src[db_column]
                    if value is not None:
                        widget = self.fields[field_name]
                        if isinstance(widget, QDoubleSpinBox):
                            widget.setValue(float(value))
                        elif isinstance(widget, QComboBox):
                            index = widget.findText(str(value))
                            if index >= 0:
                                widget.setCurrentIndex(index)
                            else:
                                # Default values
                                if field_name == "tax_resident_status":
                                    widget.setCurrentText("Resident")
                        else:
                            widget.setText(str(value))
            
            # Load additional fields
            additional_fields = {
                'sip_participation': 'sip_participation',
                'sip_type': 'sip_type',
                'sip_amount_rate': 'sip_amount_rate',
                'additional_epf_enabled': 'additional_epf_enabled', 
                'additional_epf_amount': 'additional_epf_amount',
                'prs_participation': 'prs_participation',
                'prs_amount': 'prs_amount',
                'insurance_premium': 'insurance_premium',
                'medical_premium': 'medical_premium',
                'other_deductions_amount': 'other_deductions_amount'
            }
            
            for field_name, db_column in additional_fields.items():
                src = emp_data if (db_column in emp_data and emp_data.get(db_column) is not None) else config_data
                if db_column in src and field_name in self.fields:
                    value = src[db_column]
                    if value is not None:
                        widget = self.fields[field_name]
                        if isinstance(widget, QDoubleSpinBox):
                            widget.setValue(float(value))
                        elif isinstance(widget, QComboBox):
                            index = widget.findText(str(value))
                            if index >= 0:
                                widget.setCurrentIndex(index)
                        else:
                            widget.setText(str(value))

            # Load monthly deductions for current period from dedicated table
            try:
                from datetime import datetime as _dt
                now = _dt.now()
                md = get_monthly_deductions(employee_id, now.year, now.month)
                if 'zakat_monthly' in self.fields:
                    self.fields['zakat_monthly'].setValue(md.get('zakat_monthly', 0.0))
                if 'religious_travel_monthly' in self.fields:
                    self.fields['religious_travel_monthly'].setValue(md.get('religious_travel_monthly', 0.0))
                # Set other_deductions_amount if the UI field is intended for monthly capture
                if 'other_deductions_amount' in self.fields:
                    try:
                        self.fields['other_deductions_amount'].setValue(md.get('other_deductions_amount', 0.0))
                    except Exception:
                        pass
            except Exception as e:
                print(f"DEBUG: Load monthly deductions failed: {e}")

            # Load tax_relief_data snapshot if present and prefill matching fields
            try:
                if 'tax_relief_data' in config_data and config_data['tax_relief_data']:
                    trd = config_data['tax_relief_data']
                    # If stored as string JSON, decode
                    if isinstance(trd, str):
                        try:
                            trd = json.loads(trd)
                        except Exception:
                            trd = {}
                    if isinstance(trd, dict):
                        for k, v in trd.items():
                            if k in self.fields:
                                w = self.fields[k]
                                try:
                                    if isinstance(v, bool) and hasattr(w, 'setChecked'):
                                        w.setChecked(bool(v))
                                    elif hasattr(w, 'setValue'):
                                        # numeric-ish
                                        w.setValue(float(v or 0.0))
                                    elif hasattr(w, 'setText'):
                                        w.setText(str(v))
                                except Exception:
                                    # best-effort only
                                    pass
            except Exception as _trd_load_err:
                print(f"DEBUG: Could not prefill from tax_relief_data: {_trd_load_err}")
            
            # Load allowances from employees table
            if 'allowances' in self.employee_data and self.employee_data['allowances']:
                allowances = self.employee_data['allowances']
                if isinstance(allowances, str):
                    try:
                        allowances = json.loads(allowances)
                    except:
                        allowances = {}
                
                allowance_mapping = {
                    'meal': 'meal_allowance',
                    'transport': 'transport_allowance', 
                    'medical': 'medical_allowance',
                    'phone': 'phone_allowance',
                    'other': 'other_allowance'
                }
                
                for key, field_name in allowance_mapping.items():
                    if key in allowances and field_name in self.fields:
                        self.fields[field_name].setValue(float(allowances[key]))

            
            # Load monthly deductions data
            if 'monthly_deductions' in config_data and config_data['monthly_deductions']:
                try:
                    if isinstance(config_data['monthly_deductions'], dict):
                        deductions_data = config_data['monthly_deductions']
                    else:
                        deductions_data = json.loads(config_data['monthly_deductions'])
                    
                    for field_name, value in deductions_data.items():
                        if field_name in self.fields:
                            widget = self.fields[field_name]
                            if isinstance(widget, QDoubleSpinBox):
                                widget.setValue(float(value) if value else 0.0)
                                    
                except (json.JSONDecodeError, TypeError):
                    pass  # Invalid JSON, skip loading deductions data
            
            # Load disability status checkboxes (B4 & B15 tax relief)
            if 'is_individual_disabled' in config_data and 'is_individual_disabled' in self.fields:
                self.fields['is_individual_disabled'].setChecked(bool(config_data['is_individual_disabled']))
            if 'is_spouse_disabled' in config_data and 'is_spouse_disabled' in self.fields:
                self.fields['is_spouse_disabled'].setChecked(bool(config_data['is_spouse_disabled']))
            
            # Load individual children data
            if 'individual_children' in config_data and config_data['individual_children']:
                try:
                    if isinstance(config_data['individual_children'], list):
                        children_data = config_data['individual_children']
                    else:
                        children_data = json.loads(config_data['individual_children'])
                    
                    # Clear existing children entries
                    for entry in self.children_entries[:]:
                        self.remove_child_entry(entry['frame'])
                    
                    # Load individual children
                    for child_data in children_data:
                        self.add_child_entry()
                        entry = self.children_entries[-1]
                        
                        # Set category (with backwards compatibility)
                        category_text = child_data.get('category', 'Normal - Under 18 years (RM2,000)')
                        
                        # Map old format to new format for backwards compatibility
                        category_mapping = {
                            'B) Umur 18 tahun ke bawah': 'Normal - Under 18 years (RM2,000)',
                            'C) Umur 18 tahun dan ke atas yang masih belajar di Malaysia': 'Normal - 18+ matrikulasi/A-Level Malaysia (RM2,000)',
                            'D) Lebih 18 tahun dan sedang belajar sepenuh masa di peringkat diploma ke atas (Malaysia) atau di peringkat ijazah dan ke atas (luar Malaysia)': 'Normal - 18+ diploma/degree (RM8,000)',
                            'E) Kurang upaya': 'OKU - Any age, not studying (RM8,000)',
                            'F) Kurang upaya dan masih belajar di Malaysia dan Luar Negara': 'OKU - 18+ studying diploma/degree (RM8,000 + RM8,000 = RM16,000)',
                            'B16(a) - Belum berkahwin, umur di bawah 18 tahun': 'Normal - Under 18 years (RM2,000)',
                            'B16(b) - Belum berkahwin, 18+, matrikulasi/pra ijazah/A-Level di Malaysia': 'Normal - 18+ matrikulasi/A-Level Malaysia (RM2,000)',
                            'B16(c) - Belum berkahwin, pengajian tinggi/artikel/indentur/ijazah luar negara': 'Normal - 18+ diploma/degree (RM8,000)',
                            'B16(d) - Belum berkahwin, kurang upaya': 'OKU - Any age, not studying (RM8,000)',
                            'B16(e) - Belum berkahwin, kurang upaya + pengajian tinggi': 'OKU - 18+ studying diploma/degree (RM8,000 + RM8,000 = RM16,000)',
                            'OKU - Under 18 years (RM8,000 total)': 'OKU - Any age, not studying (RM8,000)',
                            'OKU - 18+ not studying (RM6,000)': 'OKU - Any age, not studying (RM8,000)',
                            'OKU - 18+ studying diploma/degree (RM16,000 flat)': 'OKU - 18+ studying diploma/degree (RM8,000 + RM8,000 = RM16,000)'
                        }
                        
                        # Convert old format to new format if needed
                        if category_text in category_mapping:
                            category_text = category_mapping[category_text]
                        
                        category_index = entry['category'].findText(category_text)
                        if category_index >= 0:
                            entry['category'].setCurrentIndex(category_index)
                        
                        # Set custody percentage
                        custody_text = child_data.get('custody_percentage', '100% (Full claim)')
                        custody_index = entry['custody'].findText(custody_text)
                        if custody_index >= 0:
                            entry['custody'].setCurrentIndex(custody_index)
                    
                    # Update summary after loading
                    self.update_children_summary()
                                    
                except (json.JSONDecodeError, TypeError):
                    pass  # Invalid JSON, skip loading children data
            
            # Handle legacy children data (backwards compatibility)
            elif 'children_data' in config_data and config_data['children_data']:
                try:
                    if isinstance(config_data['children_data'], dict):
                        legacy_children = config_data['children_data']
                    else:
                        legacy_children = json.loads(config_data['children_data'])
                    
                    # Clear existing entries
                    for entry in self.children_entries[:]:
                        self.remove_child_entry(entry['frame'])
                    
                    # Convert legacy data to individual children
                    categories = [
                        ('children_under_18', 'B) Umur 18 tahun ke bawah', 'child_a_sharing'),
                        ('children_tertiary', 'C) Umur 18 tahun dan ke atas yang masih belajar di Malaysia', 'child_b_sharing'),
                        ('children_disabled', 'E) Kurang upaya', 'child_c_sharing')
                    ]
                    
                    for count_field, category, sharing_field in categories:
                        count = legacy_children.get(count_field, 0)
                        sharing = legacy_children.get(sharing_field, '100% (Full claim)')
                        
                        for i in range(count):
                            self.add_child_entry()
                            entry = self.children_entries[-1]
                            
                            category_index = entry['category'].findText(category)
                            if category_index >= 0:
                                entry['category'].setCurrentIndex(category_index)
                            
                            custody_index = entry['custody'].findText(sharing)
                            if custody_index >= 0:
                                entry['custody'].setCurrentIndex(custody_index)
                    
                    self.update_children_summary()
                                    
                except (json.JSONDecodeError, TypeError):
                    pass  # Invalid JSON, skip loading legacy children data
                    
        except Exception as e:
            print(f"Error loading payroll data: {e}")

    def validate_epf_insurance_limit(self):
        """Validate combined RM7,000 limit with shared EPF subcap (mandatory + voluntary) and independent life insurance subcap"""
        try:
            # Get all EPF-related values
            compulsory_epf = self.fields["epf_additional"].value() if "epf_additional" in self.fields else 0.0
            voluntary_epf = self.fields["epf_voluntary"].value()
            life_insurance = self.fields["life_insurance"].value()
            
            # Get admin configured limits (fallback to LHDN defaults)
            epf_shared_subcap = 4000.0  # LHDN default for ALL EPF (mandatory + voluntary)
            life_insurance_subcap = 3000.0  # LHDN default for life insurance
            
            # Try to get admin configured values
            try:
                parent_widget = self.parent()
                while parent_widget and not hasattr(parent_widget, 'admin_dashboard_page'):
                    parent_widget = parent_widget.parent()
                
                if parent_widget and hasattr(parent_widget, 'admin_dashboard_page'):
                    admin_dashboard = parent_widget.admin_dashboard_page
                    if hasattr(admin_dashboard.payroll_tab, 'epf_shared_subcap'):
                        epf_shared_subcap = admin_dashboard.payroll_tab.epf_shared_subcap.value()
                    if hasattr(admin_dashboard.payroll_tab, 'life_insurance_max'):
                        life_insurance_subcap = admin_dashboard.payroll_tab.life_insurance_max.value()
            except:
                pass  # Use defaults if admin config unavailable
            
            # Calculate shared EPF total (this is the key insight!)
            total_epf = compulsory_epf + voluntary_epf
            effective_total_epf = min(total_epf, epf_shared_subcap)
            effective_life_insurance = min(life_insurance, life_insurance_subcap)
            
            # Calculate combined total (this is the REAL limit per LHDN law)
            total_combined = effective_total_epf + effective_life_insurance
            
            # Show real-time feedback
            if hasattr(self, 'status_label'):
                if total_epf > epf_shared_subcap:
                    self.status_label.setText(f"⚠️ Total EPF: RM{total_epf:,.0f} exceeds RM{epf_shared_subcap:,.0f} shared subcap!")
                    self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                elif life_insurance > life_insurance_subcap:
                    self.status_label.setText(f"⚠️ Life Insurance: RM{life_insurance:,.0f} exceeds RM{life_insurance_subcap:,.0f} subcap!")
                    self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                elif total_combined > 7000.0:
                    self.status_label.setText(f"⚠️ TOTAL: RM{total_combined:,.0f} exceeds RM7,000 limit!")
                    self.status_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
                else:
                    remaining = 7000.0 - total_combined
                    epf_remaining = epf_shared_subcap - total_epf
                    self.status_label.setText(f"✅ TOTAL: RM{total_combined:,.0f}/RM7,000 | EPF: RM{total_epf:,.0f}/RM{epf_shared_subcap:,.0f} | Insurance: RM{life_insurance:,.0f}/RM{life_insurance_subcap:,.0f}")
                    self.status_label.setStyleSheet("color: #388e3c; font-weight: bold;")
            
            # Update tooltips with shared EPF concept
            self.fields["epf_voluntary"].setToolTip(f"Voluntary EPF shares RM{epf_shared_subcap:,.0f} limit with mandatory EPF. Current total EPF: RM{total_epf:,.0f}")
            self.fields["life_insurance"].setToolTip(f"Life insurance (independent RM{life_insurance_subcap:,.0f} subcap). Total combined: RM{total_combined:,.0f}/RM7,000")
            
            # Update compulsory EPF tooltip if it exists
            if "epf_additional" in self.fields:
                self.fields["epf_additional"].setToolTip(f"Mandatory EPF shares RM{epf_shared_subcap:,.0f} limit with voluntary EPF. Current total EPF: RM{total_epf:,.0f}")
            
        except Exception as e:
            print(f"DEBUG: Error validating EPF+Insurance combined limit: {e}")

    def handle_tax_resident_status_change(self):
        """Handle change in tax resident status to enable/disable tax relief sections"""
        try:
            # Get current tax resident status
            status = self.fields["tax_resident_status"].currentText()
            
            # Determine if tax relief sections should be enabled
            is_resident = (status == "Resident")
            
            # Potongan Bulan Semasa section removed; no visibility toggling needed.
            
            # List of all tax relief group boxes (sections 7-16)
            tax_relief_groups = [
                self.breastfeeding_group,        # Section 7
                self.childcare_group,            # Section 8
                self.sspn_group,                 # Section 9
                self.alimony_group,              # Section 10
                self.epf_insurance_group,        # Section 11 (EPF + Life Insurance)
                self.prs_group,                  # Section 12
                self.education_medical_insurance_group,  # Section 13
                self.ev_group,                   # Section 14
                self.housing_group,              # Section 15
                self.mbb_group,                  # Section 16 (MBB - actually this should stay enabled)
            ]
            
            # Enable/disable tax relief sections based on residence status
            for group in tax_relief_groups:
                if hasattr(self, group.__class__.__name__.lower().replace('qgroupbox', '')):
                    # MBB (Manfaat Berupa Barangan) should always be enabled as it's taxable income
                    if group == self.mbb_group:
                        group.setEnabled(True)
                    else:
                        group.setEnabled(is_resident)
            
            # Update status message
            if not is_resident:
                # Show message about non-resident tax treatment
                if hasattr(self, 'status_label'):
                    self.status_label.setText("⚠️ Non-Resident: Tax relief & monthly deductions disabled (30% flat rate applies)")
                    self.status_label.setStyleSheet("color: #ff9800; font-weight: bold;")
            else:
                # Resident - trigger EPF+Insurance validation to show current status
                self.validate_epf_insurance_limit()
                
        except Exception as e:
            print(f"DEBUG: Error handling tax resident status change: {e}")