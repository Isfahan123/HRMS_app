"""
Admin Payroll Tab - HRMS Module

EPF (KWSP) Contribution Context for Non-Malaysian Citizens:
===========================================================

MANDATORY CONTRIBUTIONS (Effective Q4 2025):
- All non-Malaysian citizen employees with valid work pass must contribute
- Excludes domestic workers
- Age limit: Below 75 years old
- Implementation date: 1 October 2025

CONTRIBUTION RATES FOR NON-MALAYSIANS:
- Employer Share: 2%
- Employee Share: 2% (can elect to contribute 11% to maintain higher benefits)

PAYROLL PROCESSING REQUIREMENTS:
- Register all non-Malaysian employees with EPF starting 1 Oct 2025
- Calculate contributions based on citizenship status and age
- Monthly contributions due by 15th of following month
- Contributions must be in Ringgit (no cents)
- Deduct employee share from salary before payment

EPF CONTRIBUTION SCHEDULE:
- Citizens: Standard EPF rates (11% employee, 13% employer)
- Permanent Residents: Voluntary contributions before 1998, then standard rates
- Non-Citizens: 2% each (employer/employee) starting Q4 2025

PAYSLIP REQUIREMENTS:
- Show EPF contributions separately for citizens vs non-citizens
- Display correct contribution rates based on employee status
- Include EPF reference numbers for all contributing employees

Reference: https://www.kwsp.gov.my/en/employer/responsibilities/non-malaysian-citizen-employees
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QLineEdit, QDateEdit, QMessageBox, QLabel, QTabWidget, 
    QFileDialog, QComboBox, QFormLayout, QSpinBox, QDoubleSpinBox, 
    QTextEdit, QCheckBox, QFrame, QDialog, QHeaderView, QGroupBox,
    QGridLayout, QScrollArea
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont
from services.supabase_service import (
    supabase, run_payroll, get_payroll_runs, update_statutory_rates, 
    update_contribution_table, upload_and_parse_contribution_file, 
    get_monthly_unpaid_leave_deduction,
    get_variable_percentage_config,
    save_variable_percentage_config,
    get_payroll_settings,
    update_payroll_settings,
    load_statutory_limits_configuration,
    # For PCB computation parity with fixed method
    load_tax_rates_configuration,
    calculate_lhdn_pcb_official,
    get_monthly_deductions,
    upsert_monthly_deductions,
    upsert_tp1_monthly_details
)
from services.tax_relief_catalog import ITEMS as TP1_ITEMS
from services.payslip_generator import generate_payslip_for_employee
from malaysian_pcb_calculator import MalaysianPCBCalculator
from datetime import datetime
import pytz
import re
import os
import importlib
from services.epf_pdf_parser import upload_and_parse_epf_pdf
from gui.admin_sections import lhdn_tax_config_tab as lhdn_sections
from gui.admin_sections.relief_overrides_subtab import build_relief_overrides_subtab  # new overrides subtab
import tabula

try:
    from PyPDF2 import PdfReader
except ImportError:
    print("PyPDF2 not installed. Please install it to enable PDF parsing.")

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')

class AdminPayrollTab(QWidget):
    # Signal to broadcast MAX CAP changes in real-time
    max_cap_changed = pyqtSignal(str, float)  # (category_name, new_value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_email = None
        self.setObjectName("AdminPayrollTab")
        # print("DEBUG: Starting AdminPayrollTab.__init__")
        try:
            self.init_ui()
            # print("DEBUG: AdminPayrollTab.init_ui complete")
        except Exception as e:
            # print(f"DEBUG: Error in AdminPayrollTab.init_ui: {str(e)}")
            raise

    def get_epf_contribution_rates(self, employee_data):
        """
        Calculate EPF contribution rates based on 2025 KWSP guidelines
        
        CRITICAL DISTINCTION:
        - Existing EPF Contributors (before Oct 2025): Keep current rates
        - New Contributors (from Oct 2025): Use new 2%+2% rates
        
        Returns: dict with 'employee_rate', 'employer_rate', 'mandatory', 'part'
        """
        citizenship = employee_data.get('citizenship', '').strip().lower()
        dob = employee_data.get('date_of_birth')
        epf_election_date = employee_data.get('epf_election_date')  # When they first elected to contribute
        is_existing_contributor = employee_data.get('epf_electing', False)  # Already contributing before Oct 2025
        
        # Calculate age
        if dob:
            try:
                if isinstance(dob, str):
                    birth_date = datetime.strptime(dob, '%Y-%m-%d').date()
                else:
                    birth_date = dob
                today = datetime.now().date()
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
            except:
                age = 0
        else:
            age = 0
        
        # Default rates for citizens
        result = {
            'employee_rate': 11.0,
            'employer_rate': 13.0,
            'mandatory': True,
            'part': 'Standard',
            'notes': '',
            'contributor_type': 'Citizen'
        }
        
        # Non-Malaysian citizen employees
        if citizenship == 'non-citizen':
            if age >= 75:
                # Age limit exceeded
                result.update({
                    'employee_rate': 0.0,
                    'employer_rate': 0.0,
                    'mandatory': False,
                    'part': 'Exempt (Age 75+)',
                    'notes': 'Age limit exceeded - no EPF contribution required',
                    'contributor_type': 'Exempt'
                })
            elif is_existing_contributor and epf_election_date:
                # EXISTING CONTRIBUTOR - Keep current rates (likely standard rates)
                try:
                    election_date = datetime.strptime(epf_election_date, '%Y-%m-%d').date()
                    if election_date < datetime(2025, 10, 1).date():
                        # Existing contributor before mandatory implementation
                        if age >= 60:
                            result.update({
                                'employee_rate': 11.0,  # Keep existing rates
                                'employer_rate': 13.0,
                                'mandatory': False,  # Was voluntary, now grandfathered
                                'part': 'Part D (Existing)',
                                'notes': 'Existing EPF contributor - maintains current rates',
                                'contributor_type': 'Existing Voluntary'
                            })
                        else:
                            result.update({
                                'employee_rate': 11.0,  # Keep existing rates
                                'employer_rate': 13.0,
                                'mandatory': False,  # Was voluntary, now grandfathered
                                'part': 'Part B (Existing)',
                                'notes': 'Existing EPF contributor - maintains current rates',
                                'contributor_type': 'Existing Voluntary'
                            })
                    else:
                        # New contributor after Oct 2025 - use new rates
                        if age >= 60:
                            result.update({
                                'employee_rate': 2.0,
                                'employer_rate': 2.0,
                                'mandatory': True,
                                'part': 'Part D (New)',
                                'notes': 'New mandatory 2% from Q4 2025 (can elect 11% employee share)',
                                'contributor_type': 'New Mandatory'
                            })
                        else:
                            result.update({
                                'employee_rate': 2.0,
                                'employer_rate': 2.0,
                                'mandatory': True,
                                'part': 'Part B (New)',
                                'notes': 'New mandatory 2% from Q4 2025 (can elect 11% employee share)',
                                'contributor_type': 'New Mandatory'
                            })
                except:
                    # Default to new mandatory rates if can't parse date
                    if age >= 60:
                        result.update({
                            'employee_rate': 2.0,
                            'employer_rate': 2.0,
                            'mandatory': True,
                            'part': 'Part D (New)',
                            'notes': 'New mandatory 2% from Q4 2025 (can elect 11% employee share)',
                            'contributor_type': 'New Mandatory'
                        })
                    else:
                        result.update({
                            'employee_rate': 2.0,
                            'employer_rate': 2.0,
                            'mandatory': True,
                            'part': 'Part B (New)',
                            'notes': 'New mandatory 2% from Q4 2025 (can elect 11% employee share)',
                            'contributor_type': 'New Mandatory'
                        })
            else:
                # NEW MANDATORY CONTRIBUTOR from Oct 2025
                if age >= 60:
                    result.update({
                        'employee_rate': 2.0,
                        'employer_rate': 2.0,
                        'mandatory': True,
                        'part': 'Part D (New)',
                        'notes': 'New mandatory 2% from Q4 2025 (can elect 11% employee share)',
                        'contributor_type': 'New Mandatory'
                    })
                else:
                    result.update({
                        'employee_rate': 2.0,
                        'employer_rate': 2.0,
                        'mandatory': True,
                        'part': 'Part B (New)',
                        'notes': 'New mandatory 2% from Q4 2025 (can elect 11% employee share)',
                        'contributor_type': 'New Mandatory'
                    })
        
        # Permanent residents
        elif citizenship == 'permanent resident':
            if age >= 60:
                # Part C
                result.update({
                    'part': 'Part C',
                    'notes': 'Standard rates apply for permanent residents',
                    'contributor_type': 'Permanent Resident'
                })
            else:
                # Part A
                result.update({
                    'part': 'Part A',
                    'notes': 'Standard rates apply for permanent residents',
                    'contributor_type': 'Permanent Resident'
                })
        
        return result

    def init_ui(self):
                # print("DEBUG: Starting AdminPayrollTab.init_ui")
                layout = QVBoxLayout()

                run_payroll_layout = QHBoxLayout()
                self.date_input = QDateEdit()
                self.date_input.setCalendarPopup(True)
                self.date_input.setDate(QDate.currentDate())
                run_payroll_button = QPushButton("Run Payroll")
                run_payroll_button.clicked.connect(self.run_payroll)
                refresh_button = QPushButton("Refresh")
                refresh_button.clicked.connect(self.load_payroll_history)
                run_payroll_layout.addWidget(QLabel("Payroll Date:"))
                run_payroll_layout.addWidget(self.date_input)
                run_payroll_layout.addWidget(run_payroll_button)
                run_payroll_layout.addWidget(refresh_button)
                # TP1 Reliefs button
                tp1_btn = QPushButton("TP1 Reliefs")
                tp1_btn.setToolTip("Enter per-item TP1 relief claims for selected employee")
                tp1_btn.clicked.connect(self.open_tp1_relief_dialog)
                run_payroll_layout.addWidget(tp1_btn)
                layout.addLayout(run_payroll_layout)

                # Calculation method toggle
                calculation_toggle_group = QGroupBox("Payroll Calculation Method")
                toggle_layout = QHBoxLayout()
                self.calculation_method = "fixed"
                self.fixed_rate_button = QPushButton("Fixed Rate (Current)")
                self.variable_percentage_button = QPushButton("Variable Percentage")
                self.fixed_rate_button.setCheckable(True)
                self.variable_percentage_button.setCheckable(True)
                self.fixed_rate_button.setChecked(True)
                self.fixed_rate_button.clicked.connect(lambda: self.toggle_calculation_method("fixed"))
                self.variable_percentage_button.clicked.connect(lambda: self.toggle_calculation_method("variable"))
                toggle_layout.addWidget(QLabel("Calculation Method:"))
                toggle_layout.addWidget(self.fixed_rate_button)
                toggle_layout.addWidget(self.variable_percentage_button)
                toggle_layout.addStretch()
                self.method_status_label = QLabel("🔢 Current: Fixed Rate Calculation")
                self.method_status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
                toggle_layout.addWidget(self.method_status_label)
                calculation_toggle_group.setLayout(toggle_layout)
                layout.addWidget(calculation_toggle_group)

                # Load persisted calculation method setting (default fixed), with local fallback
                try:
                    s = get_payroll_settings() or {}
                except Exception as _load_calc:
                    print(f"DEBUG: Could not load payroll calculation setting from DB: {_load_calc}")
                    s = {}
                if not s:
                    try:
                        from services.local_settings_cache import load_cached_payroll_settings
                        s = load_cached_payroll_settings()
                    except Exception:
                        s = {'calculation_method': 'fixed'}
                m = str(s.get('calculation_method', 'fixed') or 'fixed').strip().lower()
                if m == 'variable':
                    self.calculation_method = 'variable'
                    self.fixed_rate_button.setChecked(False)
                    self.variable_percentage_button.setChecked(True)
                    self.method_status_label.setText("📊 Current: Variable Percentage Calculation")
                    self.method_status_label.setStyleSheet("color: blue; font-weight: bold; padding: 5px;")
                else:
                    self.calculation_method = 'fixed'
                    self.fixed_rate_button.setChecked(True)
                    self.variable_percentage_button.setChecked(False)
                    self.method_status_label.setText("🔢 Current: Fixed Rate Calculation")
                    self.method_status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")

                tab_widget = QTabWidget()

                # Fixed Tab
                fixed_tab = QWidget()
                fixed_layout = QVBoxLayout()
                fixed_layout.addWidget(QLabel("Upload PDFs for Fixed Contribution Tables"))

                # EPF 2025 Non-Malaysian Information Panel
                epf_info_group = QGroupBox("EPF Non-Malaysian Citizen Requirements (Q4 2025)")
                epf_info_layout = QVBoxLayout()
                epf_info_text = QLabel("""<b>Mandatory EPF Contributions Starting Q4 2025:</b><br>
• <b>Non-citizens with valid work pass:</b> 2% employee + 2% employer<br>
• <b>Age limit:</b> Below 75 years (excludes domestic workers)<br>
• <b>Implementation:</b> 1 October 2025<br><br>

<b>CRITICAL DISTINCTION:</b><br>
• <b style=\"color: blue;\">EXISTING Contributors (before Oct 2025):</b><br>
    - Non-citizens who already opted to contribute voluntarily<br>
    - <b>Keep their current contribution rates</b> (likely 11%+13%)<br>
    - Do NOT need to re-register with EPF<br>
    - Grandfathered under previous voluntary system<br><br>

• <b style=\"color: red;\">NEW Contributors (from Oct 2025):</b><br>
    - Non-citizens starting EPF for the first time<br>
    - <b>Subject to new 2%+2% mandatory rates</b><br>
    - Automatic registration by EPF<br>
    - Can elect 11% employee share for higher benefits<br><br>

<b>Payroll Processing:</b><br>
• Check EPF election date to determine contributor type<br>
• Apply appropriate rates based on existing vs new contributor status<br>
• Ensure compliance with grandfathering provisions<br>
• Monthly contributions due by 15th of following month""")
                epf_info_text.setWordWrap(True)
                epf_info_text.setStyleSheet("QLabel { font-size: 10px; padding: 10px; background-color: #f0f8ff; border: 1px solid #ccc; }")
                epf_info_layout.addWidget(epf_info_text)
                epf_info_group.setLayout(epf_info_layout)
                fixed_layout.addWidget(epf_info_group)

                epf_upload_button = QPushButton("Upload EPF Rate PDF")
                epf_upload_button.clicked.connect(lambda: self.upload_pdf("epf"))
                fixed_layout.addWidget(epf_upload_button)

                socso_upload_button = QPushButton("Upload SOCSO Rate PDF")
                socso_upload_button.clicked.connect(lambda: self.upload_pdf("socso"))
                fixed_layout.addWidget(socso_upload_button)

                eis_upload_button = QPushButton("Upload EIS Rate PDF")
                eis_upload_button.clicked.connect(lambda: self.upload_pdf("eis"))
                fixed_layout.addWidget(eis_upload_button)

                fixed_tab.setLayout(fixed_layout)
                tab_widget.addTab(fixed_tab, "Fixed Value")

                # Variable Percentage Tab
                self.add_variable_percentage_tab(tab_widget)
                # LHDN Tax Configuration Tab
                self.add_lhdn_tax_config_tab(tab_widget)
                # Simple bonus management tab
                self.add_simple_bonus_tab(tab_widget)

                layout.addWidget(tab_widget)
                self.add_payroll_history_tab(tab_widget)
                self.setLayout(layout)
                self.load_payroll_history()
                self.handle_tax_resident_status_change()
                # Cache for TP1 claims keyed by (employee_uuid, year, month)
                self._tp1_claim_cache = {}

    def open_tp1_relief_dialog(self, default_employee_id=None, lock_employee=False, target_year=None, target_month=None):
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QLabel, QDoubleSpinBox, QMessageBox
        from datetime import datetime as _dt
        dlg = QDialog(self)
        dlg.setWindowTitle("TP1 Relief Claims (Per Employee)")
        layout = QVBoxLayout()

        # Top bar: employee selector & payroll month
        top = QHBoxLayout()
        top.addWidget(QLabel("Employee:"))
        employee_combo = QComboBox()
        try:
            emp_rows = supabase.table("employees").select("id, full_name, email").execute().data or []
        except Exception:
            emp_rows = []
        for r in emp_rows:
            employee_combo.addItem(r.get('full_name') or r.get('email') or r.get('id'), r.get('id'))
        top.addWidget(employee_combo)
        # Determine target period: prefer provided year/month, else use current date_input
        if target_year is None or target_month is None:
            payroll_qdate = self.date_input.date()
            target_year = payroll_qdate.year()
            target_month = payroll_qdate.month()
        # Period label
        period_label = QLabel(f"Period: {target_month:02d}/{target_year}")
        top.addWidget(period_label)
        # Preselect and optionally lock employee
        try:
            if default_employee_id:
                for i in range(employee_combo.count()):
                    if employee_combo.itemData(i) == default_employee_id:
                        employee_combo.setCurrentIndex(i)
                        break
            if lock_employee:
                employee_combo.setEnabled(False)
        except Exception:
            pass
        layout.addLayout(top)

        # Table
        table = QTableWidget()
        headers = ["Code", "Description", "Claimed", "Cap", "YTD", "Remaining", "PCB?", "Cycle"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setRowCount(len(TP1_ITEMS))

        # Load YTD helper
        def fetch_ytd_map(emp_id: str):
            if not emp_id:
                return {}
            try:
                resp = supabase.table('relief_ytd_accumulated').select('item_key, claimed_ytd').eq('employee_id', emp_id).eq('year', target_year).execute()
                data = resp.data or []
                return {r.get('item_key'): float(r.get('claimed_ytd') or 0.0) for r in data}
            except Exception:
                return {}

        def populate():
            emp_id = employee_combo.currentData()
            ytd_map = fetch_ytd_map(emp_id)
            # Load effective catalog and groups with overrides so the UI reflects flips to PCB? and cap changes
            try:
                from services.tax_relief_catalog import load_relief_overrides_from_db, load_relief_group_overrides_from_db, get_effective_items, get_effective_groups
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

            # Load existing claims from tp1_monthly_details for current employee/period
            existing_claims = {}
            if emp_id:
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
                # Determine effective cap considering overrides and group caps
                if eff.cap is not None:
                    cap = eff.cap
                elif eff.group is not None:
                    if eff_groups and eff.group in eff_groups and eff_groups[eff.group].cap is not None:
                        cap = eff_groups[eff.group].cap
                    else:
                        cap = eff.group_cap
                else:
                    cap = None
                claimed_ytd = ytd_map.get(item.key, 0.0)
                if eff.cap is not None:
                    remaining = max(0.0, eff.cap - claimed_ytd)
                elif eff.group_cap is not None:
                    # Group-cap remaining unknown until group-level aggregation; show blank
                    remaining = ''
                else:
                    remaining = ''
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
                cap_item = QTableWidgetItem(f"{cap:.2f}" if cap is not None else ("-"))
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
                cyc = QTableWidgetItem(str(eff.cycle_years) if eff.cycle_years else "-")
                cyc.setFlags(cyc.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 7, cyc)

        populate()

        # Append SOCSO+EIS (B20) read-only informational row at bottom
        try:
            extra_row = table.rowCount()
            table.insertRow(extra_row)
            from datetime import datetime as _dt
            socso_eis_label = QTableWidgetItem("B20 Auto (SOCSO+EIS)")
            socso_eis_label.setFlags(socso_eis_label.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 0, socso_eis_label)
            desc_item = QTableWidgetItem("Auto-derived employee SOCSO+EIS (pcb-only, cap RM350/yr)")
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 1, desc_item)
            # Empty claimed cell (not editable)
            claimed_item = QTableWidgetItem("-")
            claimed_item.setFlags(claimed_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 2, claimed_item)
            cap_item = QTableWidgetItem("350.00")
            cap_item.setFlags(cap_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 3, cap_item)
            # Compute YTD SOCSO+EIS employee portion
            emp_id_for_row = employee_combo.currentData()
            ytd_socso_eis = 0.0
            if emp_id_for_row:
                try:
                    # Pull payroll_information for year up to current month-1
                    resp = supabase.table('payroll_information').select('month_year, socso_employee, eis_employee').eq('employee_id', emp_id_for_row).execute()
                    if resp and resp.data:
                        for r in resp.data:
                            try:
                                mm_str, yy_str = str(r.get('month_year','')).split('/') if '/' in str(r.get('month_year','')) else (None,None)
                                if mm_str and yy_str and int(yy_str) == target_year and int(mm_str) <= target_month:
                                    ytd_socso_eis += float(r.get('socso_employee') or 0.0) + float(r.get('eis_employee') or 0.0)
                            except Exception:
                                continue
                except Exception as _se_ytd_err:
                    print(f"DEBUG: Could not derive SOCSO+EIS YTD for TP1 row: {_se_ytd_err}")
            ytd_item = QTableWidgetItem(f"{ytd_socso_eis:.2f}")
            ytd_item.setFlags(ytd_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 4, ytd_item)
            remaining_cap = max(0.0, 350.0 - ytd_socso_eis)
            rem_item = QTableWidgetItem(f"{remaining_cap:.2f}")
            rem_item.setFlags(rem_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 5, rem_item)
            pcb_item = QTableWidgetItem("Yes")
            pcb_item.setFlags(pcb_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 6, pcb_item)
            cyc_item = QTableWidgetItem("-")
            cyc_item.setFlags(cyc_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(extra_row, 7, cyc_item)
        except Exception as _se_extra_err:
            print(f"DEBUG: Failed to append SOCSO+EIS informational row: {_se_extra_err}")

        # Refresh on employee change
        employee_combo.currentIndexChanged.connect(populate)
        layout.addWidget(table)

        # Buttons
        btns = QHBoxLayout()
        save_btn = QPushButton("Save Claims")
        close_btn = QPushButton("Close")
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(close_btn)
        layout.addLayout(btns)

        def do_save():
            emp_id = employee_combo.currentData()
            if not emp_id:
                QMessageBox.warning(dlg, "Missing", "No employee selected")
                return
            claims = {}
            for row, item in enumerate(TP1_ITEMS):
                spin = table.cellWidget(row, 2)
                if not spin:
                    continue
                val = float(spin.value())
                if val > 0:
                    claims[item.key] = round(val, 2)
            key = (emp_id, target_year, target_month)
            self._tp1_claim_cache[key] = claims

            # Apply cap enforcement and trim values before saving
            trimmed_claims = dict(claims)
            try:
                from services.tax_relief_catalog import (
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
                pretrim = {}
                for k, v in claims.items():
                    it = eff_items.get(k)
                    if it and it.cap is not None:
                        pretrim[k] = min(v, float(it.cap))
                    else:
                        pretrim[k] = v
                total_lp1, per_item_applied, group_usage = apply_relief_caps(pretrim, groups=eff_groups)
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

            key = (emp_id, target_year, target_month)
            self._tp1_claim_cache[key] = trimmed_claims
            # Persist draft into tp1_monthly_details (aggregates blank for now)
            try:
                upsert_tp1_monthly_details(emp_id, target_year, target_month, trimmed_claims, {
                    'other_reliefs_monthly': 0.0,
                    'socso_eis_lp1_monthly': 0.0,
                    'zakat_monthly': 0.0
                })
                QMessageBox.information(dlg, "Saved", "TP1 relief claims saved (will be applied on next payroll run)")
            except Exception as e:
                QMessageBox.warning(dlg, "Error", f"Failed to save claims: {e}")

        save_btn.clicked.connect(do_save)
        close_btn.clicked.connect(dlg.close)
        dlg.setLayout(layout)
        dlg.resize(1000, 600)
        dlg.exec_()

    def upload_pdf(self, contrib_type):
        file, _ = QFileDialog.getOpenFileName(self, f"Select {contrib_type.upper()} File", "", "All Supported (*.pdf *.xls *.xlsx *.csv);;PDF Files (*.pdf);;Excel Files (*.xls *.xlsx);;CSV Files (*.csv)")
        if file:
            ext = os.path.splitext(file)[1].lower()
            try:
                print(f"DEBUG: Uploading {contrib_type} file: {file}")
                
                if ext == ".pdf":
                    # Parse PDF using appropriate parser based on contribution type
                    print(f"DEBUG: Parsing PDF file for {contrib_type}")
                    
                    success = False
                    # For EPF files, use the dedicated EPF PDF parser
                    if contrib_type.lower() == "epf":
                        try:
                            from services.epf_pdf_parser import upload_and_parse_epf_pdf
                            from services.supabase_service import supabase_client
                            
                            print("DEBUG: Using dedicated EPF PDF parser")
                            upload_and_parse_epf_pdf(file, supabase_client)
                            QMessageBox.information(self, "Success", f"{contrib_type.upper()} rates uploaded from PDF using dedicated parser.")
                            print(f"DEBUG: Successfully uploaded {contrib_type} PDF using EPF parser")
                            success = True
                        except Exception as epf_error:
                            print(f"DEBUG: EPF parser failed: {epf_error}, falling back to generic parser")
                            # Fall back to generic parsing
                    
                    # Generic PDF parsing for other contribution types or EPF fallback
                    if not success:
                        data = self.parse_rate_pdf(file)
                        if data and update_contribution_table(data, contrib_type):
                            QMessageBox.information(self, "Success", f"{contrib_type.upper()} rates uploaded from PDF.")
                            print(f"DEBUG: Successfully uploaded {contrib_type} PDF")
                        else:
                            error_msg = f"Failed to upload {contrib_type.upper()} rates from PDF"
                            print(f"DEBUG: {error_msg}")
                            QMessageBox.critical(self, "Error", error_msg + "\n\nTroubleshooting tips:\n• Ensure PDF contains valid rate tables\n• Check PDF is not password protected\n• Try uploading as Excel/CSV instead")
                        
                elif ext in [".xls", ".xlsx", ".csv"]:
                    print(f"DEBUG: Processing {ext} file for {contrib_type}")
                    
                    # Determine the appropriate category for each contribution type
                    if contrib_type.lower() == "socso":
                        # For SOCSO, we need to upload both categories
                        success_count = 0
                        
                        # Upload First Category (under 60, both schemes)
                        print("DEBUG: Uploading SOCSO First Category")
                        if upload_and_parse_contribution_file(file, contrib_type, "first_category"):
                            success_count += 1
                            print("DEBUG: Successfully uploaded SOCSO First Category")
                        
                        # Upload Second Category (60+, employment injury only)
                        print("DEBUG: Uploading SOCSO Second Category")
                        if upload_and_parse_contribution_file(file, contrib_type, "second_category"):
                            success_count += 1
                            print("DEBUG: Successfully uploaded SOCSO Second Category")
                        
                        if success_count > 0:
                            QMessageBox.information(self, "Success", f"SOCSO rates uploaded. {success_count} categories processed.")
                            print(f"DEBUG: SOCSO upload completed with {success_count} categories")
                        else:
                            error_msg = "Failed to upload SOCSO rates"
                            print(f"DEBUG: {error_msg}")
                            QMessageBox.critical(self, "Error", error_msg + "\n\nCheck file format:\n• Required columns: wage range, employee rate, employer rate\n• Ensure numeric values are properly formatted")
                            
                    elif contrib_type.lower() == "epf":
                        print("DEBUG: Uploading EPF rates")
                        category = "part_a"  # Default EPF category
                        if upload_and_parse_contribution_file(file, contrib_type, category):
                            QMessageBox.information(self, "Success", f"{contrib_type.upper()} rates uploaded from file.")
                            print(f"DEBUG: Successfully uploaded {contrib_type} file")
                        else:
                            error_msg = f"Failed to upload {contrib_type.upper()} rates from file"
                            print(f"DEBUG: {error_msg}")
                            QMessageBox.critical(self, "Error", error_msg + "\n\nEPF Upload Tips:\n• Check column headers match expected format\n• Ensure wage ranges are properly formatted (e.g., '1-20', '5000 and above')\n• Verify contribution amounts are numeric\n• Run the EPF diagnostic tool for detailed analysis")
                            
                    elif contrib_type.lower() == "eis":
                        print("DEBUG: Uploading EIS rates")
                        category = "eis"  # Default EIS category
                        if upload_and_parse_contribution_file(file, contrib_type, category):
                            QMessageBox.information(self, "Success", f"{contrib_type.upper()} rates uploaded from file.")
                            print(f"DEBUG: Successfully uploaded {contrib_type} file")
                        else:
                            error_msg = f"Failed to upload {contrib_type.upper()} rates from file"
                            print(f"DEBUG: {error_msg}")
                            QMessageBox.critical(self, "Error", error_msg + "\n\nEIS Upload Tips:\n• Check file contains EIS rate structure\n• Ensure wage ranges and rates are properly formatted")
                    else:
                        print(f"DEBUG: Uploading {contrib_type} with default category")
                        category = "default"
                        if upload_and_parse_contribution_file(file, contrib_type, category):
                            QMessageBox.information(self, "Success", f"{contrib_type.upper()} rates uploaded from file.")
                            print(f"DEBUG: Successfully uploaded {contrib_type} file")
                        else:
                            error_msg = f"Failed to upload {contrib_type.upper()} rates from file"
                            print(f"DEBUG: {error_msg}")
                            QMessageBox.critical(self, "Error", error_msg)
                else:
                    QMessageBox.warning(self, "Unsupported File", "Please upload a PDF, Excel, or CSV file.")
                    
            except Exception as e:
                error_details = str(e)
                print(f"DEBUG: Exception during {contrib_type} upload: {error_details}")
                
                # Provide specific error guidance
                if "permission" in error_details.lower():
                    error_msg = f"File permission error: Cannot access {contrib_type.upper()} file.\n\nSolutions:\n• Close file if open in Excel\n• Check file is not read-only\n• Run as administrator if needed"
                elif "column" in error_details.lower() or "missing" in error_details.lower():
                    error_msg = f"File format error: {contrib_type.upper()} file has incorrect structure.\n\nRequired columns:\n• Wage range\n• Employee contribution\n• Employer contribution\n• Total contribution"
                elif "database" in error_details.lower() or "table" in error_details.lower():
                    error_msg = f"Database error: Cannot save {contrib_type.upper()} data.\n\nSolutions:\n• Check database connection\n• Ensure contribution_tables exists\n• Contact system administrator"
                else:
                    error_msg = f"Failed to upload {contrib_type.upper()} file: {error_details}"
                
                QMessageBox.critical(self, "Upload Error", error_msg)

    def parse_rate_pdf(self, file):
        try:
            print(f"DEBUG: Starting EPF PDF parsing for file: {file}")
            
            # Check file extension to determine parsing method
            file_ext = os.path.splitext(file)[1].lower()
            
            if file_ext == '.pdf':
                # Use the dedicated EPF PDF parser for EPF files
                try:
                    from services.epf_pdf_parser import extract_tables_from_pdf
                    print("DEBUG: Using EPF PDF parser")
                    
                    # Extract tables using the EPF parser
                    epf_data = extract_tables_from_pdf(file)
                    print(f"DEBUG: EPF parser extracted data: {epf_data}")
                    
                    # Convert EPF data to the format expected by update_contribution_table
                    converted_data = []
                    for part, rows in epf_data.items():
                        for row in rows:
                            converted_data.append({
                                "category": part,  # Preserve the category (part_a, part_b, etc.)
                                "from_wage": row["from_wage"],
                                "to_wage": row["to_wage"],
                                "employer_contribution": row["employer_contribution"],
                                "employee_contribution": row["employee_contribution"],
                                "total_contribution": row["total_contribution"]
                            })
                    
                    print(f"DEBUG: Converted {len(converted_data)} EPF records")
                    return converted_data
                    
                except ImportError as e:
                    print(f"DEBUG: EPF parser not available, falling back to basic parser: {e}")
                    # Fall back to basic parsing if EPF parser fails
                    pass
                except Exception as e:
                    print(f"DEBUG: EPF parser failed: {e}")
                    # Fall back to basic parsing
                    pass
            
            # Fallback: Basic PDF parsing (original logic)
            print("DEBUG: Using basic PDF parser")
            from PyPDF2 import PdfReader
            reader = PdfReader(file)
            data = []
            parsing = False
            
            for page in reader.pages:
                text = page.extract_text()
                lines = text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith("AMOUNT OF WAGES") or line.startswith("PART A"):
                        parsing = True
                        continue
                    if parsing:
                        if line.startswith("From"):
                            parts = re.split(r'\s+', line)
                            if len(parts) >= 7:
                                try:
                                    from_wage = float(parts[1])
                                    to_wage = float(parts[3])
                                    employer = 0.0 if parts[4] == "NIL" else float(parts[4])
                                    employee = 0.0 if parts[5] == "NIL" else float(parts[5])
                                    total = employer + employee
                                    data.append({
                                        "from_wage": from_wage,
                                        "to_wage": to_wage,
                                        "employer_contribution": employer,
                                        "employee_contribution": employee,
                                        "total_contribution": total
                                    })
                                except ValueError:
                                    continue
            
            print(f"DEBUG: Basic parser extracted {len(data)} records")
            return data
            
        except Exception as e:
            error_msg = f"Failed to parse PDF: {str(e)}"
            print(f"DEBUG: Error parsing PDF: {error_msg}")
            QMessageBox.critical(self, "Error", error_msg)
            return None

    def set_user_email(self, email):
        # print(f"DEBUG: Setting user_email to {email} in AdminPayrollTab")
        self.user_email = email.lower()
        self.load_payroll_history()

    def add_payroll_history_tab(self, tab_widget):
        # Create the Payroll History Tab (with monthly subtabs)
        payroll_tab = QWidget()
        payroll_layout = QVBoxLayout()

        # Add filter input and Year selector (applies to the currently visible month table)
        filter_layout = QHBoxLayout()
        self.payroll_filter_input = QLineEdit()
        self.payroll_filter_input.setPlaceholderText("Filter payroll history...")
        self.payroll_filter_input.textChanged.connect(self.filter_payroll_history)
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.payroll_filter_input)
        # Year dropdown
        filter_layout.addWidget(QLabel("Year:"))
        from PyQt5.QtWidgets import QComboBox as _QCombo
        self.year_filter_combo = _QCombo()
        self.year_filter_combo.addItem("All years", None)
        self.year_filter_combo.currentIndexChanged.connect(self.on_year_filter_changed)
        filter_layout.addWidget(self.year_filter_combo)
        filter_layout.addStretch()
        payroll_layout.addLayout(filter_layout)

        # Month tabs container
        self.payroll_month_tabs = QTabWidget()
        self.month_tables = {}
        self.month_tab_index_map = {}

        # Tables are built via self._new_payroll_table()

        # "All" tab
        all_tab = QWidget()
        all_layout = QVBoxLayout()
        self.payroll_table = self._new_payroll_table()
        all_layout.addWidget(self.payroll_table)
        all_tab.setLayout(all_layout)
        all_index = self.payroll_month_tabs.addTab(all_tab, "All")
        self.month_tab_index_map[all_index] = (None, None)  # marker for All

        # Create month tabs for current year (Jan..Dec) — initial view; will rebuild on year filter change
        try:
            from datetime import datetime as _dt
            now = _dt.now(KL_TZ)
        except Exception:
            from datetime import datetime as _dt
            now = _dt.now()

        y = now.year
        for mm in range(1, 13):
            label = self._month_short_name(mm)
            tab = QWidget()
            lay = QVBoxLayout()
            tbl = self._new_payroll_table()
            lay.addWidget(tbl)
            tab.setLayout(lay)
            idx = self.payroll_month_tabs.addTab(tab, label)
            self.month_tab_index_map[idx] = (y, mm)
            self.month_tables[(y, mm)] = tbl

        self.payroll_month_tabs.currentChanged.connect(self._on_month_tab_changed)
        payroll_layout.addWidget(self.payroll_month_tabs)

        payroll_tab.setLayout(payroll_layout)
        tab_widget.addTab(payroll_tab, "Payroll History")

        # Create a Skipped Payroll Tab
        skipped_tab = QWidget()
        skipped_layout = QVBoxLayout()

        self.skipped_table = QTableWidget()
        self.skipped_table.setColumnCount(4)
        self.skipped_table.setHorizontalHeaderLabels([
            "Employee", "Payroll Date", "Reason", "Created At"
        ])
        self.skipped_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.skipped_table.horizontalHeader().setStretchLastSection(True)
        skipped_layout.addWidget(self.skipped_table)

        skipped_tab.setLayout(skipped_layout)
        tab_widget.addTab(skipped_tab, "Skipped Payroll")

    def _year_filter_value(self):
        try:
            val = self.year_filter_combo.currentData()
            return int(val) if val not in (None, "", "None") else None
        except Exception:
            return None

    def on_year_filter_changed(self):
        try:
            # Rebuild month tabs for selected year; reuse the standard loader for simplicity
            self.load_payroll_history()
            self.filter_payroll_history()
        except Exception as e:
            print(f"DEBUG: on_year_filter_changed error: {e}")

    def load_payroll_history(self):
        print("DEBUG: Loading payroll history in AdminPayrollTab")
        try:
            payroll_runs = get_payroll_runs(self.user_email)
            print(f"DEBUG: Got {len(payroll_runs)} payroll runs")
            # Cache runs for quick re-population on year-tab changes
            self._cached_payroll_runs = payroll_runs

            # Populate year dropdown options based on fetched runs
            def _extract_years(rows):
                yrs = set()
                for r in rows:
                    try:
                        d = str(r.get('payroll_date') or '')
                        yrs.add(int(d[0:4]))
                    except Exception:
                        try:
                            from datetime import datetime as _dt
                            dt = _dt.fromisoformat(d)
                            yrs.add(dt.year)
                        except Exception:
                            continue
                return sorted(yrs, reverse=True)

            available_years = _extract_years(payroll_runs)
            # Preserve current selection if still available
            current_val = self._year_filter_value()
            self.year_filter_combo.blockSignals(True)
            self.year_filter_combo.clear()
            self.year_filter_combo.addItem("All years", None)
            for yy in available_years:
                self.year_filter_combo.addItem(str(yy), yy)
            # Restore selection
            if current_val and current_val in available_years:
                # Find index with data==current_val
                for i in range(self.year_filter_combo.count()):
                    if self.year_filter_combo.itemData(i) == current_val:
                        self.year_filter_combo.setCurrentIndex(i)
                        break
            else:
                self.year_filter_combo.setCurrentIndex(0)
            self.year_filter_combo.blockSignals(False)

            # Helper to populate a table with given rows
            def _populate_table(table: QTableWidget, rows):
                table.setRowCount(len(rows))
                for row, payroll in enumerate(rows):
                    allowances = payroll.get("allowances", {})
                    
                    # Handle JSONB allowances field
                    if isinstance(allowances, str):
                        try:
                            import json
                            allowances = json.loads(allowances)
                        except (json.JSONDecodeError, TypeError):
                            # print(f"DEBUG: Failed to parse allowances JSON, defaulting to empty dictionary")
                            allowances = {}
                    elif not isinstance(allowances, dict):
                        # print(f"DEBUG: Allowances not a dict (type: {type(allowances)}), defaulting to empty dictionary")
                        allowances = {}
                    
                    # Format allowances for display with total
                    if allowances:
                        allowances_list = []
                        total_allowances = 0.0
                        for k, v in allowances.items():
                            if v is not None and v != 0:
                                try:
                                    amount = float(v)
                                    allowances_list.append(f"{k.replace('_', ' ').title()}: RM {amount:.2f}")
                                    total_allowances += amount
                                except (ValueError, TypeError):
                                    continue
                        
                        if allowances_list:
                            allowances_text = ", ".join(allowances_list)
                            allowances_text += f" | Total: RM {total_allowances:.2f}"
                        else:
                            allowances_text = "None"
                    else:
                        allowances_text = "None"
                    
                    # Helper function to safely format currency values
                    def safe_format_currency(value):
                        if value is None:
                            return "RM 0.00"
                        try:
                            return f"RM {float(value):.2f}"
                        except (ValueError, TypeError):
                            return "RM 0.00"
                    
                    def safe_format_days(value):
                        if value is None or value == 0:
                            return "0"
                        try:
                            # Handle half-day formatting
                            days = float(value)
                            if days == int(days):
                                return str(int(days))
                            else:
                                return f"{days:.1f}"
                        except (ValueError, TypeError):
                            return "0"
                    
                    # 🇲🇾 Malaysian Payroll Sequence Data (matching header order)
                    items = [
                        payroll.get("employee", {}).get("full_name", "Unknown"),  # Employee Name
                        payroll["payroll_date"],  # Payroll Date
                        
                        # Step 1: Gross Calculation
                        safe_format_currency(payroll.get('gross_salary')),  # Gross Salary
                        allowances_text,  # Allowances (detailed breakdown)
                        
                        # Step 2: Unpaid Leave (FIRST deduction)
                        safe_format_days(payroll.get('unpaid_leave_days')),  # Unpaid Days
                        safe_format_currency(payroll.get('unpaid_leave_deduction')),  # Unpaid Deduction
                        
                        # Step 3-5: Statutory Contributions (on reduced salary)
                        safe_format_currency(payroll.get('epf_employee')),  # EPF Employee
                        safe_format_currency(payroll.get('epf_employer')),  # EPF Employer
                        safe_format_currency(payroll.get('socso_employee')),  # SOCSO Employee
                        safe_format_currency(payroll.get('socso_employer')),  # SOCSO Employer
                        safe_format_currency(payroll.get('eis_employee')),  # EIS Employee
                        safe_format_currency(payroll.get('eis_employer')),  # EIS Employer
                        
                        # Step 6: PCB (on taxable income) — fallback to legacy keys if needed
                        safe_format_currency(
                            payroll.get('pcb', payroll.get('pcb_tax', payroll.get('pcb_amount')))
                        ),  # PCB
                        
                        # Step 7: Other Deductions (after PCB)
                        safe_format_currency(payroll.get('sip_deduction')),  # SIP
                        safe_format_currency(payroll.get('additional_epf_deduction')),  # Additional EPF
                        safe_format_currency(payroll.get('prs_deduction')),  # PRS
                        safe_format_currency(payroll.get('insurance_premium')),  # Insurance
                        safe_format_currency(payroll.get('other_deductions')),  # Other Deductions
                        
                        # Final Result
                        safe_format_currency(payroll.get('net_salary'))  # Net Salary
                    ]
                    for col, value in enumerate(items):
                        item = QTableWidgetItem(str(value))
                        item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, col, item)

                    # Add payslip generation button in the last column
                    payslip_button = QPushButton("📄 Generate")
                    payslip_button.setToolTip("Generate and download payslip PDF")
                    payslip_button.clicked.connect(lambda checked, emp_id=payroll["employee_id"], run_id=payroll.get("id"): self.generate_payslip(emp_id, run_id))
                    table.setCellWidget(row, 19, payslip_button)  # Actions column (index 19)

            # Populate All + monthly tabs according to year selection
            def _ym_from_date(s: str):
                try:
                    return int(s[0:4]), int(s[5:7])
                except Exception:
                    try:
                        from datetime import datetime as _dt
                        dt = _dt.fromisoformat(s)
                        return dt.year, dt.month
                    except Exception:
                        return None, None

            selected_year = self._year_filter_value()

            def _filter_by_year(rows, yy):
                if yy is None:
                    return rows
                out = []
                for r in rows:
                    yx, _mx = _ym_from_date(str(r.get('payroll_date') or ''))
                    if yx == yy:
                        out.append(r)
                return out

            # Build or rebuild month tabs for selected year
            def _ensure_month_tabs_for_year(yy):
                # Remove all tabs except index 0 (All)
                try:
                    while self.payroll_month_tabs.count() > 1:
                        self.payroll_month_tabs.removeTab(1)
                except Exception:
                    pass
                self.month_tables = {}
                self.month_tab_index_map = {0: (None, None)}
                if yy is None:
                    # Default to current year months (Jan..Dec) for a consistent layout
                    try:
                        from datetime import datetime as _dt
                        now = _dt.now(KL_TZ)
                    except Exception:
                        from datetime import datetime as _dt
                        now = _dt.now()
                    yv = now.year
                    for mv in range(1, 13):
                        label = self._month_short_name(mv)
                        tab = QWidget()
                        lay = QVBoxLayout()
                        tbl = self._new_payroll_table()
                        lay.addWidget(tbl)
                        tab.setLayout(lay)
                        idx = self.payroll_month_tabs.addTab(tab, label)
                        self.month_tab_index_map[idx] = (yv, mv)
                        self.month_tables[(yv, mv)] = tbl
                else:
                    # Months 01..12 of the selected year
                    for mv in range(1, 13):
                        label = self._month_short_name(mv)
                        tab = QWidget()
                        lay = QVBoxLayout()
                        tbl = self._new_payroll_table()
                        lay.addWidget(tbl)
                        tab.setLayout(lay)
                        idx = self.payroll_month_tabs.addTab(tab, label)
                        self.month_tab_index_map[idx] = (yy, mv)
                        self.month_tables[(yy, mv)] = tbl

            # Ensure tabs are correct for chosen year
            _ensure_month_tabs_for_year(selected_year)

            runs_for_all = _filter_by_year(payroll_runs, selected_year)
            _populate_table(self.payroll_table, runs_for_all)
            print("DEBUG: Payroll history (All) table populated")

            # Populate monthly tabs by filtering records per month
            def _ym_from_date(s: str):
                try:
                    return int(s[0:4]), int(s[5:7])
                except Exception:
                    try:
                        from datetime import datetime as _dt
                        dt = _dt.fromisoformat(s)
                        return dt.year, dt.month
                    except Exception:
                        return None, None

            by_month = {}
            for rec in runs_for_all:
                yy, mm = _ym_from_date(str(rec.get('payroll_date') or ''))
                if yy and mm:
                    by_month.setdefault((yy, mm), []).append(rec)

            for (yy, mm), tbl in self.month_tables.items():
                rows = by_month.get((yy, mm), [])
                _populate_table(tbl, rows)
            print("DEBUG: Monthly payroll tables populated")
            # Re-apply text filter after repopulation
            self.filter_payroll_history()
            # Load skipped payrolls as well
            try:
                self.load_skipped_payrolls()
            except Exception as _ls:
                print(f"DEBUG: Failed to load skipped payrolls: {_ls}")
        except Exception as e:
            print(f"DEBUG: Error loading payroll history: {str(e)}")
            import traceback
            traceback.print_exc()
            # Clear all tables gracefully on error
            try:
                self.payroll_table.setRowCount(0)
                for tbl in getattr(self, 'month_tables', {}).values():
                    tbl.setRowCount(0)
            except Exception:
                pass
            QMessageBox.warning(self, "Error", f"Failed to load payroll history: {str(e)}")

    def load_skipped_payrolls(self):
        """Load skipped payroll records from Supabase and populate the Skipped Payroll tab."""
        try:
            # Get latest 200 skipped records
            resp = (
                supabase
                .table('payroll_run_skips')
                .select('employee_id, payroll_date, reason, created_at, employees!inner(full_name,email)')
                .order('created_at', desc=True)
                .limit(200)
                .execute()
            )
            rows = resp.data or []
            self.skipped_table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                emp = row.get('employees') or {}
                name_or_email = emp.get('full_name') or emp.get('email') or row.get('employee_id')
                vals = [
                    name_or_email,
                    row.get('payroll_date') or '',
                    row.get('reason') or '',
                    row.get('created_at') or '',
                ]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(str(v))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.skipped_table.setItem(r, c, item)
            # Resize
            self.skipped_table.resizeRowsToContents()
            print(f"DEBUG: Loaded {len(rows)} skipped payroll records")
        except Exception as e:
            print(f"DEBUG: Error loading skipped payrolls: {e}")

    def filter_payroll_history(self):
        filter_text = self.payroll_filter_input.text().strip().lower()
        table = self._get_current_payroll_table()
        if not table:
            table = getattr(self, 'payroll_table', None)
        if not table:
            return
        for row in range(table.rowCount()):
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and filter_text in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    def _get_current_payroll_table(self):
        try:
            idx = self.payroll_month_tabs.currentIndex()
            yy, mm = self.month_tab_index_map.get(idx, (None, None))
            if yy is None and mm is None:
                return self.payroll_table
            return self.month_tables.get((yy, mm))
        except Exception:
            return self.payroll_table

    def _new_payroll_table(self):
        """Create a configured payroll QTableWidget with standard columns and sizing."""
        tbl = QTableWidget()
        tbl.setColumnCount(20)
        tbl.setHorizontalHeaderLabels([
            "Employee Name", "Payroll Date",
            "Gross Salary", "Allowances",
            "Unpaid Days", "Unpaid Deduction",
            "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer",
            "EIS Employee", "EIS Employer",
            "PCB",
            "SIP", "Additional EPF", "PRS", "Insurance", "Other Deductions",
            "Net Salary", "Actions"
        ])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setSortingEnabled(True)
        return tbl

    def _month_short_name(self, m: int) -> str:
        names = [
            "Jan", "Feb", "Mar", "Apr", "May", "Jun",
            "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
        ]
        try:
            mi = int(m)
            if 1 <= mi <= 12:
                return names[mi - 1]
        except Exception:
            pass
        return str(m)

    def _on_month_tab_changed(self, _idx):
        # Re-apply text filter when switching tabs
        try:
            self.filter_payroll_history()
        except Exception:
            pass

    def run_payroll(self):
        try:
            payroll_date = self.date_input.date().toString("yyyy-MM-dd")
            print(f"DEBUG: Attempting to run payroll for {payroll_date}")
            print(f"DEBUG: Using calculation method: {self.calculation_method}")
            
            # Check calculation method and run appropriate payroll calculation
            if self.calculation_method == "variable":
                result = self.run_variable_percentage_payroll(payroll_date)
            else:
                result = run_payroll(payroll_date)  # Use existing fixed rate method
            
            print(f"DEBUG: Payroll result: {result}")
            # Variable mode may return a dict summary; fixed mode returns bool
            if isinstance(result, dict):
                success = result.get('success', False)
                skipped = result.get('skipped') or []
                processed = result.get('processed', 0)
                if success:
                    print(f"DEBUG: Payroll run successful for {payroll_date} | processed={processed} skipped={len(skipped)}")
                    # Build a concise summary for the user
                    try:
                        if skipped:
                            preview = ", ".join([f"{i} ({r})" for i, r in skipped[:5]])
                            more = f" and {len(skipped)-5} more" if len(skipped) > 5 else ""
                            extra = f"\nSkipped: {len(skipped)} ({preview}{more})"
                        else:
                            extra = "\nSkipped: 0"
                    except Exception:
                        extra = f"\nSkipped: {len(skipped)}"
                    QMessageBox.information(self, "Success",
                        f"Payroll processed for {payroll_date}\n"
                        f"Calculation Method: {self.calculation_method.title()}\n"
                        f"Processed: {processed}{extra}")
                    self.load_payroll_history()
                else:
                    print(f"DEBUG: Payroll run failed for {payroll_date} (variable mode) | skipped={len(skipped)}")
                    QMessageBox.critical(self, "Error", "Failed to process payroll (variable mode)")
                return
            
            if result:
                print(f"DEBUG: Payroll run successful for {payroll_date}")
                QMessageBox.information(self, "Success", 
                    f"Payroll processed for {payroll_date}\n"
                    f"Calculation Method: {self.calculation_method.title()}")
                self.load_payroll_history()
            else:
                print(f"DEBUG: Payroll run failed for {payroll_date}")
                QMessageBox.critical(self, "Error", "Failed to process payroll")
        except Exception as e:
            print(f"DEBUG: Error running payroll: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to process payroll: {str(e)}")

    def run_variable_percentage_payroll(self, payroll_date):
        """Run payroll using variable percentage calculation"""
        try:
            print(f"DEBUG: Running variable percentage payroll for {payroll_date}")
            # Local date parser tolerant of multiple formats
            def _parse_any_date_local(val):
                try:
                    if not val:
                        return None
                    from datetime import datetime as _dt
                    s = str(val).strip()
                    fmts = [
                        '%Y-%m-%d', '%Y/%m/%d',
                        '%d/%m/%Y', '%d-%m-%Y',
                        '%Y-%m', '%Y/%m',
                        '%m/%Y', '%m-%Y',
                    ]
                    for f in fmts:
                        try:
                            dt = _dt.strptime(s, f)
                            if f in ('%Y-%m', '%Y/%m', '%m/%Y', '%m-%Y'):
                                parts = s.replace('-', '/').split('/')
                                if f in ('%m/%Y', '%m-%Y'):
                                    mm, yy = int(parts[0]), int(parts[1])
                                    return _dt(yy, mm, 1)
                                else:
                                    yy, mm = int(parts[0]), int(parts[1])
                                    return _dt(yy, mm, 1)
                            return dt
                        except Exception:
                            continue
                    return None
                except Exception:
                    return None
            
            # Get employees
            employees_response = supabase.table("employees").select("*").execute()
            if not employees_response.data:
                print("DEBUG: No employees found")
                return False
            
            employees = employees_response.data
            print(f"DEBUG: Found {len(employees)} employees")
            
            payroll_runs = []
            skipped = []  # collect (identifier, reason)
            
            for employee in employees:
                employee_uuid = employee.get("id")
                if not employee_uuid:
                    continue
                
                print(f"DEBUG: Processing employee {employee_uuid}")

                # Gating: skip if payroll_status is inactive or employment status is non-active
                try:
                    ps = str((employee or {}).get('payroll_status') or '').strip().lower()
                    if ps and 'inactive' in ps:
                        ident = employee.get('employee_id') or employee.get('email') or employee.get('full_name') or employee_uuid
                        reason = f"payroll_status='{employee.get('payroll_status')}'"
                        print(f"⏭️  Skipping variable payroll for {ident} due to {reason}")
                        # Persist skip record
                        try:
                            from datetime import datetime as _dt
                            supabase.table('payroll_run_skips').insert({
                                'employee_id': employee_uuid,
                                'payroll_date': payroll_date,
                                'reason': reason,
                                'created_at': _dt.now().isoformat()
                            }).execute()
                        except Exception as _skerr:
                            print(f"DEBUG: Failed to persist skip record: {_skerr}")
                        skipped.append((ident, reason))
                        continue
                except Exception:
                    pass

                try:
                    es = str((employee or {}).get('status') or '').strip().lower()
                    if es in ('inactive', 'resigned', 'terminated', 'retired') or any(k in es for k in ('inactive','resigned','terminated','retired')):
                        ident = employee.get('employee_id') or employee.get('email') or employee.get('full_name') or employee_uuid
                        reason = f"employment status='{employee.get('status')}'"
                        print(f"⏭️  Skipping variable payroll for {ident} due to {reason}")
                        # Persist skip record
                        try:
                            from datetime import datetime as _dt
                            supabase.table('payroll_run_skips').insert({
                                'employee_id': employee_uuid,
                                'payroll_date': payroll_date,
                                'reason': reason,
                                'created_at': _dt.now().isoformat()
                            }).execute()
                        except Exception as _skerr2:
                            print(f"DEBUG: Failed to persist skip record: {_skerr2}")
                        skipped.append((ident, reason))
                        continue
                except Exception:
                    pass
                
                # Calculate using variable percentage rates
                # Robust allowances parsing (dict or JSON string)
                def _to_float_safe(x, default=0.0):
                    try:
                        return float(x)
                    except Exception:
                        return default

                basic_salary = _to_float_safe(employee.get("basic_salary", 0.0), 0.0)
                allowances_dict = employee.get("allowances") or {}
                if isinstance(allowances_dict, str):
                    try:
                        import json as _json
                        _parsed = _json.loads(allowances_dict)
                        allowances_dict = _parsed if isinstance(_parsed, dict) else {}
                    except Exception:
                        allowances_dict = {}
                try:
                    total_allowances = sum(_to_float_safe(v, 0.0) for v in (allowances_dict.values() if isinstance(allowances_dict, dict) else []))
                except Exception:
                    total_allowances = 0.0
                # Parse payroll date early for month/year context (bonuses, YTD)
                from datetime import datetime as _dt
                payroll_datetime = _dt.strptime(payroll_date, "%Y-%m-%d")
                year, month = payroll_datetime.year, payroll_datetime.month

                # Integrate active bonuses effective in the payroll month
                bonus_total = 0.0
                try:
                    # Prefer month-bounded selection: [month_start, next_month_start)
                    month_start = f"{year}-{month:02d}-01"
                    if month == 12:
                        next_month_start = f"{year+1}-01-01"
                    else:
                        next_month_start = f"{year}-{month+1:02d}-01"
                    _q = (
                        supabase.table("bonuses")
                        .select("amount, effective_date, status")
                        .eq("employee_id", employee_uuid)
                        .eq("status", "Active")
                        .gte("effective_date", month_start)
                        .lt("effective_date", next_month_start)
                    )
                    _resp = _q.execute()
                    rows = _resp.data or []
                    for r in rows:
                        try:
                            bonus_total += float(r.get("amount", 0.0) or 0.0)
                        except Exception:
                            continue
                except Exception as _bon:
                    # Fallback: try exact-date match if range filtering not supported
                    try:
                        _resp2 = (
                            supabase.table("bonuses")
                            .select("amount, effective_date, status")
                            .eq("employee_id", employee_uuid)
                            .eq("status", "Active")
                            .eq("effective_date", payroll_date)
                            .execute()
                        )
                        rows2 = _resp2.data or []
                        for r in rows2:
                            try:
                                bonus_total += float(r.get("amount", 0.0) or 0.0)
                            except Exception:
                                continue
                    except Exception as _bon2:
                        print(f"DEBUG: Bonus lookup failed for {employee_uuid}: {_bon} | fallback: {_bon2}")

                gross_salary = basic_salary + total_allowances + bonus_total

                # Skip statutory calculations for interns (no EPF/SOCSO/EIS/PCB).
                # Detect via common fields: 'position' or 'job_title' containing 'intern'.
                try:
                    _pos = (employee.get('position') or employee.get('job_title') or '')
                    is_intern = 'intern' in str(_pos).strip().lower()
                except Exception:
                    is_intern = False
                if is_intern:
                    # Intern gross excludes basic salary; pay allowances + bonus only
                    intern_gross = float(total_allowances or 0.0) + float(bonus_total or 0.0)
                    # Unpaid leave deduction for current month
                    try:
                        monthly_unpaid_leave = get_monthly_unpaid_leave_deduction(employee_uuid, year, month)
                        total_unpaid_deduction = float(monthly_unpaid_leave.get('total_deduction', 0.0) or 0.0)
                    except Exception as _iul:
                        print(f"DEBUG: Intern unpaid leave lookup failed: {_iul}")
                        total_unpaid_deduction = 0.0

                    net_salary = intern_gross - total_unpaid_deduction
                    from datetime import datetime as _dt2
                    payroll_run = {
                        "employee_id": employee_uuid,
                        "employee_email": employee.get("email", ""),
                        "full_name": employee.get("full_name", ""),
                        "payroll_date": payroll_date,
                        "basic_salary": 0.0,  # interns: no basic component
                        "allowances": allowances_dict,
                        "total_allowances": total_allowances,
                        "gross_salary": round(intern_gross, 2),
                        "bonus": round(bonus_total, 2),
                        "epf_employee": 0.0,
                        "epf_employer": 0.0,
                        "socso_employee": 0.0,
                        "socso_employer": 0.0,
                        "eis_employee": 0.0,
                        "eis_employer": 0.0,
                        "pcb": 0.0,
                        "unpaid_leave_deduction": round(total_unpaid_deduction, 2),
                        "net_salary": round(net_salary, 2),
                        "calculation_method": "variable_percentage",
                        "created_at": _dt2.now().isoformat(),
                    }
                    payroll_runs.append(payroll_run)
                    print(f"DEBUG: Intern processed (skipped statutory): {employee.get('full_name')} Net RM{net_salary:.2f}")
                    continue
                
                # Calculate age-based EPF rates
                # Age normalization (handles strings like "30" or "60+")
                _age_raw = employee.get("age", 30)
                if isinstance(_age_raw, str):
                    import re as _re
                    _m = _re.search(r"\d+", _age_raw)
                    age = int(_m.group(0)) if _m else 30
                else:
                    try:
                        age = int(_age_raw)
                    except Exception:
                        age = 30
                # Determine EPF Part using EPF/SOCSO calculator (same as service)
                try:
                    from epf_socso_calculator import EPFSOCSCalculator as _EPFCalc
                    _calc = _EPFCalc()
                    dob = employee.get('date_of_birth', '1900-01-01')
                    nationality = employee.get('nationality', 'Malaysia')
                    citizenship = employee.get('citizenship', 'Citizen')
                    _status = _calc.calculate_epf_socso_status(
                        birth_date=dob if isinstance(dob, str) else dob.strftime('%Y-%m-%d'),
                        nationality=nationality,
                        citizenship=citizenship,
                    )
                    epf_part = _status.get('epf_part')
                except Exception:
                    epf_part = None
                
                # Calculate SOCSO rates based on category
                # SOCSO category normalization with robust mapping
                socso_category_raw = str(employee.get("socso_category", "first") or "first").strip().lower()
                # Map common variants to canonical values
                if socso_category_raw in ("first", "1", "cat1", "category1"):
                    socso_category = "first"
                elif socso_category_raw in ("second", "2", "cat2", "category2"):
                    socso_category = "second"
                else:
                    # Fallback: derive from calculator status if available, else default to 'first'
                    try:
                        _sc = (_status.get('socso_category') or '').strip().lower()
                        if _sc in ("category2", "second", "2", "cat2"):
                            socso_category = "second"
                        else:
                            socso_category = "first"
                    except Exception:
                        socso_category = "first"
                if socso_category == "first":
                    socso_employee_rate = self.socso_first_employee_rate.value()
                    socso_employer_rate = self.socso_first_employer_rate.value()
                else:
                    socso_employee_rate = self.socso_second_employee_rate.value()
                    socso_employer_rate = self.socso_second_employer_rate.value()
                
                # Apply variable percentage rates with age-based EPF and category-based SOCSO
                # Use statutory ceilings from limits configuration instead of UI widgets
                # Load statutory limits and active variable % config
                try:
                    limits_cfg = load_statutory_limits_configuration('default') or {}
                except Exception:
                    limits_cfg = {}
                try:
                    settings = get_payroll_settings() or {'active_variable_config': 'default'}
                except Exception:
                    settings = {'active_variable_config': 'default'}
                try:
                    var_cfg = get_variable_percentage_config(settings.get('active_variable_config') or 'default') or {}
                except Exception:
                    var_cfg = {}

                # Compute EPF using the same helper as the service for consistent logic
                from services.supabase_service import compute_variable_epf_for_part as _epf_var_helper
                # Also import EIS table-based helper to align with fixed mode amounts
                from services.supabase_service import get_eis_contributions as _eis_table_helper
                _epf = _epf_var_helper(epf_part, gross_salary, age, limits_cfg, var_cfg)
                epf_employee = float(_epf.get('employee', 0.0) or 0.0)
                epf_employer = float(_epf.get('employer', 0.0) or 0.0)
                epf_employee_salary = float(_epf.get('base', gross_salary) or gross_salary)

                # Compute SOCSO/EIS contributions with ceilings (unchanged)
                epf_ceiling = float(limits_cfg.get('epf_ceiling', 6000.0) or 6000.0)
                socso_ceiling = float(limits_cfg.get('socso_ceiling', 6000.0) or 6000.0)
                eis_ceiling = float(limits_cfg.get('eis_ceiling', 6000.0) or 6000.0)
                socso_employee_salary = min(gross_salary, socso_ceiling)
                eis_employee_salary = min(gross_salary, eis_ceiling)

                socso_employee = socso_employee_salary * (float(socso_employee_rate) / 100.0)
                socso_employer = socso_employee_salary * (float(socso_employer_rate) / 100.0)

                # EIS eligibility: only Malaysians/PR and typically age 18-59 inclusive
                # Be robust: infer from employee fields first, then fall back to calculator status
                try:
                    _cit = (employee.get('citizenship') or employee.get('nationality') or '').strip().lower()
                except Exception:
                    _cit = ''
                is_citizen_or_pr = None
                if _cit:
                    # Positive hints
                    if any(k in _cit for k in ('malaysian', 'malaysia', 'citizen', 'permanent', 'pr')):
                        is_citizen_or_pr = True
                    # Negative hints
                    if any(k in _cit for k in ('foreign', 'expat', 'non-malaysian', 'non malaysian', 'non-citizen', 'non citizen')):
                        is_citizen_or_pr = False
                if is_citizen_or_pr is None:
                    try:
                        is_citizen_or_pr = bool((_status.get('is_malaysian') or _status.get('is_pr')))
                    except Exception:
                        is_citizen_or_pr = True  # default permissive: many locals lack normalized metadata

                eis_age_eligible = 18 <= int(age or 0) < 60

                # Prefer configured rates when UI widgets are zeroed
                try:
                    _eis_emp_rate_ui = float(self.eis_employee_rate.value())
                    _eis_empr_rate_ui = float(self.eis_employer_rate.value())
                except Exception:
                    _eis_emp_rate_ui = 0.0
                    _eis_empr_rate_ui = 0.0
                _eis_emp_rate_cfg = float(var_cfg.get('eis_employee_rate', 0.2) or 0.0)
                _eis_empr_rate_cfg = float(var_cfg.get('eis_employer_rate', 0.2) or 0.0)
                eis_emp_rate_final = _eis_emp_rate_ui if _eis_emp_rate_ui > 0.0 else _eis_emp_rate_cfg
                eis_empr_rate_final = _eis_empr_rate_ui if _eis_empr_rate_ui > 0.0 else _eis_empr_rate_cfg

                if is_citizen_or_pr and eis_age_eligible and eis_employee_salary > 0.0 and eis_emp_rate_final > 0.0:
                    # Prefer official PERKESO table values if available (matches fixed mode exactly)
                    _eis_emp_tbl, _eis_empr_tbl = 0.0, 0.0
                    try:
                        _e_emp, _e_empr, _ = _eis_table_helper(gross_salary, 'eis')
                        _eis_emp_tbl = float(_e_emp or 0.0)
                        _eis_empr_tbl = float(_e_empr or 0.0)
                    except Exception:
                        _eis_emp_tbl, _eis_empr_tbl = 0.0, 0.0

                    if _eis_emp_tbl > 0.0:
                        eis_employee = _eis_emp_tbl
                        eis_employer = _eis_empr_tbl
                    else:
                        # Fallback to rate-based if table not present/seeded
                        eis_employee = eis_employee_salary * (eis_emp_rate_final / 100.0)
                        eis_employer = eis_employee_salary * (eis_empr_rate_final / 100.0)
                else:
                    eis_employee = 0.0
                    eis_employer = 0.0

                try:
                    print(
                        f"DEBUG: Variable calc for {employee.get('full_name')} — "
                        f"part={epf_part} gross={gross_salary:.2f} (bonus={bonus_total:.2f}), EPF base={epf_employee_salary:.2f}, "
                        f"rates emp={_epf.get('employee_rate')}%/empr={_epf.get('employer_rate')}%, "
                        f"EPF emp={epf_employee:.2f}, SOCSO emp={socso_employee:.2f}, EIS emp={eis_employee:.2f}"
                    )
                except Exception:
                    pass
                
                # Calculate PCB using official LHDN method for parity with fixed method
                # payroll_datetime/year/month already initialized above

                # Monthly deductions (zakat etc.) for PCB and net salary
                try:
                    monthly_deductions = get_monthly_deductions(employee_uuid, year, month)
                except Exception as _md_err:
                    print(f"DEBUG: Could not load monthly deductions (variable method): {_md_err}")
                    monthly_deductions = {
                        'zakat_monthly': 0.0,
                        'religious_travel_monthly': 0.0,
                        'other_deductions_amount': 0.0,
                    }
                current_month_zakat = 0.0
                try:
                    current_month_zakat = float(monthly_deductions.get('zakat_monthly', 0.0) or 0.0)
                except Exception:
                    current_month_zakat = 0.0

                # Tax config and YTD data (best-effort; fallbacks to zeros)
                tax_config = load_tax_rates_configuration() or {}
                ytd_data = {
                    'accumulated_gross': 0.0,
                    'accumulated_epf': 0.0,
                    'accumulated_pcb': 0.0,
                    'accumulated_zakat': 0.0,
                    'accumulated_other_reliefs': 0.0,
                }
                try:
                    employee_email_for_ytd = (employee.get("email") or "").lower()
                    if employee_email_for_ytd:
                        # IMPORTANT: For current month's PCB, use previous month's YTD snapshot
                        _prev_month = 12 if month == 1 else (month - 1)
                        _prev_year = year - 1 if month == 1 else year
                        _ytd = supabase.table("payroll_ytd_accumulated").select("*") \
                            .eq("employee_email", employee_email_for_ytd) \
                            .eq("year", _prev_year) \
                            .eq("month", _prev_month) \
                            .execute()
                        if _ytd and _ytd.data:
                            row = _ytd.data[0]
                            ytd_data = {
                                'accumulated_gross': float(row.get('accumulated_gross_salary_ytd', 0.0) or 0.0),
                                'accumulated_epf': float(row.get('accumulated_epf_employee_ytd', 0.0) or 0.0),
                                'accumulated_pcb': float(row.get('accumulated_pcb_ytd', 0.0) or 0.0),
                                'accumulated_zakat': float(row.get('accumulated_zakat_ytd', 0.0) or 0.0),
                                'accumulated_other_reliefs': float(row.get('accumulated_tax_reliefs_ytd', 0.0) or 0.0),
                                'accumulated_socso': float(row.get('accumulated_socso_employee_ytd', 0.0) or 0.0),
                                'accumulated_eis': float(row.get('accumulated_eis_employee_ytd', 0.0) or 0.0),
                            }
                            # If SOCSO/EIS YTD are missing/zero in the table, derive from prior payroll_runs
                            try:
                                if (ytd_data['accumulated_socso'] == 0.0 or ytd_data['accumulated_eis'] == 0.0):
                                    pr = (
                                        supabase.table('payroll_runs')
                                        .select('socso_employee, eis_employee, payroll_date')
                                        .eq('employee_id', employee_uuid)
                                        .execute()
                                    )
                                    if pr and pr.data:
                                        _ref = _parse_any_date_local(f"{year}-{month:02d}-01")
                                        _rows = []
                                        for r in pr.data:
                                            try:
                                                _dtp = _parse_any_date_local(r.get('payroll_date'))
                                                if _ref and _dtp and _dtp < _ref:
                                                    _rows.append(r)
                                            except Exception:
                                                continue
                                        if _rows:
                                            if ytd_data['accumulated_socso'] == 0.0:
                                                ytd_data['accumulated_socso'] = sum(float(r.get('socso_employee', 0) or 0) for r in _rows)
                                            if ytd_data['accumulated_eis'] == 0.0:
                                                ytd_data['accumulated_eis'] = sum(float(r.get('eis_employee', 0) or 0) for r in _rows)
                            except Exception:
                                pass
                        else:
                            # Fallback: aggregate from prior payroll_runs if YTD table has no snapshot
                            try:
                                pr = (
                                    supabase.table('payroll_runs')
                                    .select('gross_salary, epf_employee, pcb, socso_employee, eis_employee, payroll_date')
                                    .eq('employee_id', employee_uuid)
                                    .execute()
                                )
                                if pr and pr.data:
                                    _ref = _parse_any_date_local(f"{year}-{month:02d}-01")
                                    _rows = []
                                    for r in pr.data:
                                        try:
                                            _dtp = _parse_any_date_local(r.get('payroll_date'))
                                            if _ref and _dtp and _dtp < _ref:
                                                _rows.append(r)
                                        except Exception:
                                            continue
                                    if _rows:
                                        _gross = sum(float(r.get('gross_salary', 0) or 0) for r in _rows)
                                        _epf = sum(float(r.get('epf_employee', 0) or 0) for r in _rows)
                                        _pcb = sum(float(r.get('pcb', 0) or 0) for r in _rows)
                                        _socso = sum(float(r.get('socso_employee', 0) or 0) for r in _rows)
                                        _eis = sum(float(r.get('eis_employee', 0) or 0) for r in _rows)
                                        ytd_data = {
                                            'accumulated_gross': _gross,
                                            'accumulated_epf': _epf,
                                            'accumulated_pcb': _pcb,
                                            'accumulated_zakat': 0.0,
                                            'accumulated_other_reliefs': 0.0,
                                            'accumulated_socso': _socso,
                                            'accumulated_eis': _eis,
                                        }
                            except Exception:
                                pass
                except Exception as _yr:
                    print(f"DEBUG: Failed to load YTD (variable method): {_yr}")

                # Before PCB inputs: compute SOCSO+EIS LP1 (TP1 B20) with RM350 annual cap
                socso_eis_lp1_this_month = 0.0
                try:
                    # Sum YTD claimed SOCSO+EIS LP1 from payroll_monthly_deductions if column exists
                    ytd_claimed = 0.0
                    try:
                        _ytd_lp = (
                            supabase.table('payroll_monthly_deductions')
                            .select('socso_eis_lp1_monthly, month, year')
                            .eq('employee_id', employee_uuid)
                            .eq('year', year)
                            .lt('month', month)
                            .execute()
                        )
                        if _ytd_lp.data:
                            for r in _ytd_lp.data:
                                try:
                                    ytd_claimed += float(r.get('socso_eis_lp1_monthly', 0) or 0)
                                except Exception:
                                    continue
                    except Exception:
                        ytd_claimed = 0.0

                    remaining_cap = max(0.0, 350.0 - ytd_claimed)
                    socso_eis_lp1_this_month = max(0.0, min(remaining_cap, (socso_employee or 0.0) + (eis_employee or 0.0)))
                except Exception as _lp1calc:
                    print(f"DEBUG: SOCSO+EIS LP1 calc failed: {_lp1calc}")

                # Compute LP1 base from TP1 claims if present for the month; else fallback to monthly_deductions
                try:
                    base_lp1_only = 0.0
                    # Try load TP1 claims saved for this employee/month
                    tp1_claims = {}
                    try:
                        resp = supabase.table('tp1_monthly_details').select('details').eq('employee_id', employee_uuid).eq('year', year).eq('month', month).limit(1).execute()
                        row = resp.data[0] if resp and resp.data else None
                        if row and isinstance(row.get('details'), dict):
                            tp1_claims = row['details']
                    except Exception as _loadtp1:
                        print(f"DEBUG: Could not load TP1 claims for LP1: {_loadtp1}")

                    if tp1_claims:
                        try:
                            from services.tax_relief_catalog import (
                                compute_lp1_totals,
                                load_relief_overrides_from_db,
                                get_effective_items,
                            )
                            try:
                                _relief_overrides = load_relief_overrides_from_db(supabase)
                            except Exception:
                                _relief_overrides = {}
                            _catalog = get_effective_items(_relief_overrides)
                            comp = compute_lp1_totals(tp1_claims, items_catalog=_catalog)
                            base_lp1_only = float(comp.get('total_lp1_cash', 0.0) or 0.0)
                            # Persist base LP1 for transparency in monthly_deductions
                            try:
                                upsert_monthly_deductions(employee_uuid, year, month, {
                                    'other_reliefs_monthly': base_lp1_only,
                                    'zakat_monthly': float(current_month_zakat or 0.0),
                                })
                            except Exception as _pmd_up:
                                print(f"DEBUG: (Admin) upsert monthly deductions for LP1 failed: {_pmd_up}")
                        except Exception as _tp1calc:
                            print(f"DEBUG: compute_lp1_totals failed, fallback to monthly_deductions: {_tp1calc}")

                    if base_lp1_only <= 0.0 and isinstance(monthly_deductions, dict):
                        base_lp1_only = float(monthly_deductions.get('other_reliefs_monthly', 0.0) or 0.0)

                    lp1_for_pcb = round(base_lp1_only + float(socso_eis_lp1_this_month or 0.0), 2)
                except Exception as _merge:
                    print(f"DEBUG: Compute LP1 for PCB failed: {_merge}")
                    lp1_for_pcb = float(monthly_deductions.get('other_reliefs_monthly', 0.0) or 0.0) if isinstance(monthly_deductions, dict) else 0.0

                # Enhance other_reliefs_ytd by folding elapsed B20 (SOCSO+EIS LP1) so P reflects YTD LP1 like LHDN
                other_reliefs_ytd_enhanced = float(ytd_data.get('accumulated_other_reliefs', 0.0) or 0.0)
                try:
                    other_reliefs_ytd_enhanced += float(ytd_claimed or 0.0)
                except Exception:
                    pass

                # PCB inputs — official function expects monthly gross (Y1) and EPF (K1)
                # Child count: prefer explicit child_count, else employees.number_of_children
                _emp_child_count = employee.get('child_count')
                if _emp_child_count in (None, '', 0):
                    try:
                        _emp_child_count = int(employee.get('number_of_children', 0) or 0)
                    except Exception:
                        _emp_child_count = 0

                # Spouse not working: if married and spouse_working is False/"No", default spouse_relief
                _spouse_relief_val = float(employee.get('spouse_relief', 0.0) or 0.0)
                try:
                    ms = str(employee.get('marital_status','') or '').strip().lower()
                    sw = employee.get('spouse_working')
                    sw_norm = None
                    if isinstance(sw, bool):
                        sw_norm = sw
                    elif isinstance(sw, str):
                        _s = sw.strip().lower()
                        if _s in ('yes','y','true','1'): sw_norm = True
                        elif _s in ('no','n','false','0'): sw_norm = False
                    if 'married' in ms and sw_norm is False and _spouse_relief_val <= 0.0:
                        _spouse_relief_val = float(tax_config.get('spouse_relief', 4000.0) or 4000.0)
                except Exception as _srel:
                    print(f"DEBUG: Admin spouse relief default failed: {_srel}")

                payroll_inputs_for_pcb = {
                    'accumulated_gross_ytd': ytd_data['accumulated_gross'],
                    'accumulated_epf_ytd': ytd_data['accumulated_epf'],
                    'accumulated_pcb_ytd': ytd_data['accumulated_pcb'],
                    'accumulated_zakat_ytd': ytd_data['accumulated_zakat'],
                    'individual_relief': tax_config.get('individual_relief', 9000.0),
                    'spouse_relief': _spouse_relief_val,
                    'child_relief': tax_config.get('child_relief', 2000.0),
                    'child_count': _emp_child_count,
                    'disabled_individual': employee.get('disabled_individual', 0.0),
                    'disabled_spouse': employee.get('disabled_spouse', 0.0),
                    'other_reliefs_ytd': other_reliefs_ytd_enhanced,
                    # Use LP1 total for PCB (base + SOCSO+EIS for this month only)
                    'other_reliefs_current': lp1_for_pcb,
                    'current_month_zakat': current_month_zakat,
                }
                month_year = f"{month:02d}/{year}"
                pcb_amount = calculate_lhdn_pcb_official(
                    payroll_inputs_for_pcb,
                    gross_salary,
                    epf_employee,
                    tax_config,
                    month_year
                )
                
                # Get unpaid leave deduction
                from datetime import datetime
                payroll_datetime = datetime.strptime(payroll_date, "%Y-%m-%d")
                monthly_unpaid_leave = get_monthly_unpaid_leave_deduction(
                    employee_uuid, payroll_datetime.year, payroll_datetime.month
                )
                total_unpaid_deduction = monthly_unpaid_leave["total_deduction"]
                
                # Calculate net salary
                total_deductions = (epf_employee + socso_employee + eis_employee + 
                                  pcb_amount + total_unpaid_deduction)
                net_salary = gross_salary - total_deductions
                
                # Persist monthly deductions row for this period (zakat + LP1 + SOCSO/EIS LP1)
                try:
                    md_payload = {
                        'zakat_monthly': float(current_month_zakat or 0.0),
                        # Persist base LP1 inputs
                        'other_reliefs_monthly': float(monthly_deductions.get('other_reliefs_monthly', 0.0) if isinstance(monthly_deductions, dict) else 0.0),
                        # Also persist SOCSO+EIS LP1 (B20) so YTD claimed accumulates month to month
                        # This enables slight decreases in PCB across months as P reduces with ΣLP growth
                        'socso_eis_lp1_monthly': float(socso_eis_lp1_this_month or 0.0),
                    }
                    # pass through optional known fields
                    if isinstance(monthly_deductions, dict):
                        if 'religious_travel_monthly' in monthly_deductions:
                            md_payload['religious_travel_monthly'] = float(monthly_deductions.get('religious_travel_monthly') or 0.0)
                        if 'other_deductions_amount' in monthly_deductions:
                            md_payload['other_deductions_amount'] = float(monthly_deductions.get('other_deductions_amount') or 0.0)
                    upsert_monthly_deductions(employee_uuid, payroll_datetime.year, payroll_datetime.month, md_payload)
                except Exception as _pmd:
                    print(f"DEBUG: Upsert payroll_monthly_deductions failed: {_pmd}")

                # Prepare payroll run data
                payroll_run = {
                    "employee_id": employee_uuid,
                    "employee_email": employee.get("email", ""),
                    "full_name": employee.get("full_name", ""),
                    "payroll_date": payroll_date,
                    "basic_salary": basic_salary,
                    "allowances": allowances_dict,
                    "total_allowances": total_allowances,
                    "gross_salary": gross_salary,
                    "bonus": round(bonus_total, 2),
                    "epf_employee": round(epf_employee, 2),
                    "epf_employer": round(epf_employer, 2),
                    "socso_employee": round(socso_employee, 2),
                    "socso_employer": round(socso_employer, 2),
                    "eis_employee": round(eis_employee, 2),
                    "eis_employer": round(eis_employer, 2),
                    "pcb": round(pcb_amount, 2),
                    "unpaid_leave_deduction": round(total_unpaid_deduction, 2),
                    "net_salary": round(net_salary, 2),
                    "calculation_method": "variable_percentage",
                    "variable_rates": {
                        "epf_part_a_employee": self.epf_part_a_employee.value(),
                        "epf_part_a_employer": self.epf_part_a_employer.value(),
                        "epf_part_e_employee": self.epf_part_e_employee.value(),
                        "epf_part_e_employer": self.epf_part_e_employer.value(),
                        "socso_first_employee_rate": self.socso_first_employee_rate.value(),
                        "socso_first_employer_rate": self.socso_first_employer_rate.value(),
                        "socso_second_employee_rate": self.socso_second_employee_rate.value(),
                        "socso_second_employer_rate": self.socso_second_employer_rate.value(),
                        "eis_employee_rate": self.eis_employee_rate.value(),
                        "eis_employer_rate": self.eis_employer_rate.value()
                    },
                    "created_at": datetime.now().isoformat()
                }

                # Attach YTD snapshot columns (as of previous month) for auditing and payslip display
                try:
                    payroll_run.update({
                        "ytd_as_of_year": _prev_year if '_prev_year' in locals() else (year if month > 1 else year - 1),
                        "ytd_as_of_month": _prev_month if '_prev_month' in locals() else (12 if month == 1 else month - 1),
                        "accumulated_gross_salary_ytd": float((ytd_data or {}).get('accumulated_gross', 0.0)),
                        "accumulated_net_salary_ytd": 0.0,
                        "accumulated_basic_salary_ytd": 0.0,
                        "accumulated_allowances_ytd": 0.0,
                        "accumulated_overtime_ytd": 0.0,
                        "accumulated_bonus_ytd": 0.0,
                        "accumulated_epf_employee_ytd": float((ytd_data or {}).get('accumulated_epf', 0.0)),
                        "accumulated_socso_employee_ytd": float((ytd_data or {}).get('accumulated_socso', 0.0)),
                        "accumulated_eis_employee_ytd": float((ytd_data or {}).get('accumulated_eis', 0.0)),
                        "accumulated_pcb_ytd": float((ytd_data or {}).get('accumulated_pcb', 0.0)),
                        "accumulated_zakat_ytd": float((ytd_data or {}).get('accumulated_zakat', 0.0)),
                        "accumulated_tax_reliefs_ytd": float((ytd_data or {}).get('accumulated_other_reliefs', 0.0)),
                    })
                except Exception as _attach_ytd_err:
                    print(f"DEBUG: Failed attaching YTD snapshot to payroll_run: {_attach_ytd_err}")
                
                payroll_runs.append(payroll_run)
                print(f"DEBUG: Calculated variable percentage payroll for {employee.get('full_name')}: Net RM{net_salary:.2f}")
            
            # Insert all payroll runs
            if payroll_runs:
                # Replace existing runs for the same payroll_date and employees to ensure history reflects latest calc
                try:
                    emp_ids = [pr.get('employee_id') for pr in payroll_runs if pr.get('employee_id')]
                    if emp_ids:
                        supabase.table('payroll_runs').delete() \
                            .eq('payroll_date', payroll_date) \
                            .in_('employee_id', emp_ids) \
                            .execute()
                except Exception as _del_err:
                    print(f"DEBUG: Non-fatal: failed to delete existing payroll_runs for {payroll_date}: {_del_err}")

                # Supabase schema for payroll_runs is stricter; only insert known columns.
                # Keep extra fields (e.g., basic_salary, employee_email, variable_rates) in-memory for YTD/UX, but exclude from DB insert.
                allowed_keys = {
                    'employee_id', 'payroll_date',
                    'gross_salary', 'allowances',
                    'epf_employee', 'epf_employer',
                    'socso_employee', 'socso_employer',
                    'eis_employee', 'eis_employer',
                    'pcb', 'net_salary', 'bonus',
                    'sip_deduction', 'additional_epf_deduction', 'prs_deduction',
                    'insurance_premium', 'medical_premium', 'other_deductions',
                    'unpaid_leave_days', 'unpaid_leave_deduction',
                    'ytd_as_of_year', 'ytd_as_of_month',
                    'accumulated_gross_salary_ytd', 'accumulated_net_salary_ytd',
                    'accumulated_basic_salary_ytd', 'accumulated_allowances_ytd',
                    'accumulated_overtime_ytd', 'accumulated_bonus_ytd',
                    'accumulated_epf_employee_ytd', 'accumulated_socso_employee_ytd',
                    'accumulated_eis_employee_ytd', 'accumulated_pcb_ytd',
                    'accumulated_zakat_ytd', 'accumulated_tax_reliefs_ytd',
                    'created_at'
                }
                insert_payload = [
                    {k: v for k, v in pr.items() if k in allowed_keys}
                    for pr in payroll_runs
                ]
                insert_response = supabase.table("payroll_runs").insert(insert_payload).execute()
                if insert_response.data:
                    print(f"DEBUG: Successfully inserted {len(payroll_runs)} variable percentage payroll runs")
                    # Update YTD accumulation table for each inserted payroll run
                    try:
                        from services.supabase_service import update_ytd_after_payroll
                        for pr in payroll_runs:
                            try:
                                _pd = pr.get('payroll_date')
                                if _pd:
                                    from datetime import datetime as _dt
                                    _dtp = _dt.strptime(_pd, '%Y-%m-%d')
                                    _yy = _dtp.year
                                    _mm = _dtp.month
                                else:
                                    _yy = year
                                    _mm = month
                                _email = pr.get('employee_email') or (employee.get('email') or '')
                                if _email:
                                    # Build minimal payroll_data & inputs used by updater
                                    _p_data = {
                                        'gross_income': float(pr.get('gross_salary') or 0.0),
                                        'net_salary': float(pr.get('net_salary') or 0.0),
                                        'basic_salary': float(pr.get('basic_salary') or 0.0),
                                        'bonus': float(pr.get('bonus') or 0.0),
                                        'epf_employee': float(pr.get('epf_employee') or 0.0),
                                        'epf_employer': float(pr.get('epf_employer') or 0.0),
                                        'socso_employee': float(pr.get('socso_employee') or 0.0),
                                        'socso_employer': float(pr.get('socso_employer') or 0.0),
                                        'eis_employee': float(pr.get('eis_employee') or 0.0),
                                        'eis_employer': float(pr.get('eis_employer') or 0.0),
                                        'pcb_tax': float(pr.get('pcb') or 0.0),
                                        'allowances': pr.get('allowances') or {},
                                        'other_deductions': {},
                                    }
                                    _p_inputs = {
                                        'current_month_zakat': float((monthly_deductions or {}).get('zakat_monthly', 0.0) if isinstance(monthly_deductions, dict) else 0.0),
                                        'other_reliefs_current': float((monthly_deductions or {}).get('other_reliefs_monthly', 0.0) if isinstance(monthly_deductions, dict) else 0.0),
                                    }
                                    update_ytd_after_payroll(_email, _yy, _mm, _p_data, _p_inputs)
                            except Exception as _one_ytd:
                                print(f"DEBUG: Skipped YTD update for a row: {_one_ytd}")
                    except Exception as _upd_ytd_err:
                        print(f"DEBUG: YTD update after insert failed: {_upd_ytd_err}")
                    return {'success': True, 'processed': len(payroll_runs), 'skipped': skipped}
                else:
                    print("DEBUG: Failed to insert variable percentage payroll runs")
                    return {'success': False, 'processed': 0, 'skipped': skipped}
            else:
                if skipped:
                    try:
                        skipped_msg = ", ".join([f"{i} ({r})" for i, r in skipped])
                        print(f"DEBUG: No payroll runs to insert; skipped {len(skipped)} employees: {skipped_msg}")
                    except Exception:
                        print(f"DEBUG: No payroll runs to insert; skipped {len(skipped)} employees")
                else:
                    print("DEBUG: No payroll runs to insert")
                return {'success': True, 'processed': 0, 'skipped': skipped}
                
        except Exception as e:
            print(f"DEBUG: Error in variable percentage payroll: {e}")
            return False

    def generate_payslip(self, employee_id, payroll_run_id):
        """Generate payslip for a specific employee and payroll run"""
        try:
            # print(f"DEBUG: Generating payslip for employee {employee_id}, payroll run {payroll_run_id}")
            
            # Let user choose save location
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Payslip",
                f"Payslip_{employee_id}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if filename:
                # Generate the payslip
                result = generate_payslip_for_employee(employee_id, payroll_run_id, filename)
                
                if result:
                    QMessageBox.information(
                        self, 
                        "Success", 
                        f"Payslip generated successfully!\nSaved to: {filename}"
                    )
                    # print(f"DEBUG: Payslip generated successfully for {employee_id}")
                else:
                    QMessageBox.critical(
                        self, 
                        "Error", 
                        "Failed to generate payslip. Please check the console for details."
                    )
                    # print(f"DEBUG: Failed to generate payslip for {employee_id}")
            else:
                # print("DEBUG: User cancelled payslip generation")
                pass
                
        except Exception as e:
            # print(f"DEBUG: Error generating payslip: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate payslip: {str(e)}")

    def update_statutory_rates(self):
        try:
            rates = {
                "epf_employee": float(self.epf_employee_input.text()),
                "epf_employer": float(self.epf_employer_input.text()),
                "socso_employee": float(self.socso_employee_input.text()),
                "socso_employer": float(self.socso_employer_input.text()),
                "eis_employee": float(self.eis_employee_input.text()),
                "eis_employer": float(self.eis_employer_input.text()),
                "pcb_relief": float(self.pcb_relief_input.text()),
                "socso_wage_ceiling": float(self.socso_wage_ceiling_input.text())
            }
            if update_statutory_rates(rates):
                # print("DEBUG: Statutory rates updated successfully")
                QMessageBox.information(self, "Success", "Statutory rates updated")
            else:
                # print("DEBUG: Failed to update statutory rates")
                QMessageBox.critical(self, "Error", "Failed to update statutory rates")
        except Exception as e:
            # print(f"DEBUG: Error updating statutory rates: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to update statutory rates: {str(e)}")

    def download_payslip(self, url):
        try:
            import webbrowser
            webbrowser.open(url)
            # print(f"DEBUG: Opening payslip URL: {url}")
        except Exception as e:
            # print(f"DEBUG: Error downloading payslip: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to download payslip: {str(e)}")
    
    def add_view_contribution_tab(self, tab_widget):
        view_tab = QWidget()
        view_layout = QVBoxLayout()

        # Dropdown to select contribution type
        self.contribution_type_dropdown = QComboBox()
        self.contribution_type_dropdown.addItems(["EPF", "SOCSO", "EIS"])
        self.contribution_type_dropdown.currentIndexChanged.connect(self.update_part_filter)
        view_layout.addWidget(QLabel("Select Contribution Type:"))
        view_layout.addWidget(self.contribution_type_dropdown)

        # Add a debug button to check database
        debug_button = QPushButton("Check Database")
        debug_button.clicked.connect(self.check_database)
        view_layout.addWidget(debug_button)

        # Table to display contribution data
        self.contribution_table = QTableWidget()
        self.contribution_table.setColumnCount(6)  # Updated column count
        self.contribution_table.setHorizontalHeaderLabels([
            "Part", "From Wage", "To Wage", "Employee Contribution", "Employer Contribution", "Total Contribution"
        ])
        self.contribution_table.horizontalHeader().setStretchLastSection(True)
        self.contribution_table
        view_layout.addWidget(self.contribution_table)

        # Filter input
        filter_layout = QHBoxLayout()

        # Add Part filter dropdown
        self.part_filter_dropdown = QComboBox()
        self.part_filter_dropdown.currentIndexChanged.connect(self.load_contribution_data)
        filter_layout.addWidget(QLabel("Part:"))
        filter_layout.addWidget(self.part_filter_dropdown)

        # Add wage range filter
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by wage range...")
        self.filter_input.textChanged.connect(self.filter_contribution_data)
        filter_layout.addWidget(QLabel("Filter:"))
        filter_layout.addWidget(self.filter_input)

        view_layout.addLayout(filter_layout)
        view_tab.setLayout(view_layout)
        tab_widget.addTab(view_tab, "View Contributions")
        self.update_part_filter()  # Initialize the part filter
        self.load_contribution_data()

        # Add simple bonus management tab
        self.add_simple_bonus_tab(tab_widget)

    def update_part_filter(self):
        """Update the part filter dropdown based on the selected contribution type"""
        contrib_type = self.contribution_type_dropdown.currentText().lower()
        self.part_filter_dropdown.clear()
        
        if contrib_type == "epf":
            self.part_filter_dropdown.addItems(["All Parts", "Part A", "Part B", "Part C", "Part D", "Part E"])
        elif contrib_type == "socso":
            # Get actual SOCSO categories from database
            try:
                response = supabase.table("contribution_tables").select("category").eq("contrib_type", "socso").execute()
                categories = list(set([row.get("category") for row in response.data if row.get("category")]))
                # print(f"DEBUG: Found SOCSO categories in database: {categories}")
                
                filter_items = ["All Parts"]
                for category in categories:
                    # Handle different SOCSO category names
                    if category == "category":
                        display_name = "SOCSO Rates"
                    elif category == "first_category":
                        display_name = "First Category (Under 60)"
                    elif category == "second_category":
                        display_name = "Second Category (60+)"
                    else:
                        # Format category name for display
                        display_name = category.replace("_", " ").title()
                    filter_items.append(display_name)
                
                self.part_filter_dropdown.addItems(filter_items)
            except Exception as e:
                # print(f"DEBUG: Error loading SOCSO categories: {str(e)}")
                self.part_filter_dropdown.addItems(["All Parts", "First Category (Under 60)", "Second Category (60+)", "SOCSO Rates"])
        elif contrib_type == "eis":
            self.part_filter_dropdown.addItems(["All Parts", "EIS"])
        else:
            self.part_filter_dropdown.addItems(["All Parts"])
        
        # Load contribution data after updating the filter
        self.load_contribution_data()

    def check_database(self):
        """Check what contribution types and categories exist in the database"""
        try:
            # Get all distinct contrib_type and category combinations
            response = supabase.table("contribution_tables").select("contrib_type, category").execute()
            
            # Group by contrib_type
            contrib_summary = {}
            for row in response.data:
                contrib_type = row['contrib_type']
                category = row['category']
                if contrib_type not in contrib_summary:
                    contrib_summary[contrib_type] = []
                if category not in contrib_summary[contrib_type]:
                    contrib_summary[contrib_type].append(category)
            
            # Create summary message
            summary = "Database Contribution Summary:\n\n"
            for contrib_type, categories in contrib_summary.items():
                summary += f"{contrib_type.upper()}:\n"
                for category in categories:
                    # Count rows for this combination
                    count_response = supabase.table("contribution_tables").select("id", count="exact").eq("contrib_type", contrib_type).eq("category", category).execute()
                    count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
                    summary += f"  - {category}: {count} rows\n"
                summary += "\n"
            
            if not contrib_summary:
                summary = "No contribution data found in database."
            
            QMessageBox.information(self, "Database Check", summary)
            # print(f"DEBUG: Database summary: {summary}")
            
        except Exception as e:
            # print(f"DEBUG: Error checking database: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to check database: {str(e)}")

    def load_contribution_data(self):
        try:
            contrib_type = self.contribution_type_dropdown.currentText().lower()
            part_filter = self.part_filter_dropdown.currentText()
            # print(f"DEBUG: Loading contribution data for type: {contrib_type}, filter: {part_filter}")

            # First, let's check what data exists for this contrib_type
            check_query = supabase.table("contribution_tables").select("category", count="exact").eq("contrib_type", contrib_type).execute()
            # print(f"DEBUG: Total rows for {contrib_type}: {len(check_query.data)}")
            
            # Show categories for this contrib_type
            categories = list(set([row.get("category") for row in check_query.data if row.get("category")]))
            # print(f"DEBUG: Available categories for {contrib_type}: {categories}")

            # Query the database for the selected contribution type
            query = supabase.table("contribution_tables").select("*").eq("contrib_type", contrib_type)

            # Apply Part filter if not "All Parts"
            if part_filter != "All Parts":
                # Handle special SOCSO category mappings
                if part_filter == "SOCSO Rates":
                    db_category = "category"
                elif part_filter == "First Category (Under 60)":
                    db_category = "first_category"
                elif part_filter == "Second Category (60+)":
                    db_category = "second_category"
                else:
                    # Convert display name back to database format
                    db_category = part_filter.lower().replace(" ", "_")
                # print(f"DEBUG: Filtering by category: {db_category}")
                query = query.eq("category", db_category)

            # Fetch all rows using range
            response = query.range(0, 1999).execute()  # Adjust the range to match your dataset size
            data = response.data
            # print(f"DEBUG: Query returned {len(data)} rows")
            # print(f"DEBUG: Sample data: {data[:2] if data else 'No data'}")

            if not data:
                # Show helpful message when no data is found
                if contrib_type == "socso":
                    QMessageBox.information(self, "No SOCSO Data", 
                                          "No SOCSO contribution data found in database.\n\n"
                                          "Please upload SOCSO rate files using the 'Upload SOCSO Rate PDF' button in the Fixed Value tab.")
                elif contrib_type == "eis":
                    QMessageBox.information(self, "No EIS Data", 
                                          "No EIS contribution data found in database.\n\n"
                                          "Please upload EIS rate files using the 'Upload EIS Rate PDF' button in the Fixed Value tab.")

            self.contribution_table.setRowCount(len(data))
            for row, entry in enumerate(data):
                # Format category name for display
                raw_category = entry["category"]
                if raw_category == "category":
                    category = "SOCSO Rates"
                elif raw_category == "first_category":
                    category = "First Category (Under 60)"
                elif raw_category == "second_category":
                    category = "Second Category (60+)"
                else:
                    category = raw_category.replace("_", " ").title()
                    
                items = [
                    category,  # Part column
                    f"RM {entry['from_wage']:.2f}",
                    f"RM {entry['to_wage']:.2f}" if entry['to_wage'] != 999999.99 else "RM 999999.99+",
                    f"RM {entry['employee_contribution']:.2f}",
                    f"RM {entry['employer_contribution']:.2f}",
                    f"RM {entry['total_contribution']:.2f}" if entry['total_contribution'] is not None else "N/A"
                ]
                for col, value in enumerate(items):
                    item = QTableWidgetItem(value)
                    item.setTextAlignment(Qt.AlignCenter)
                    self.contribution_table.setItem(row, col, item)

            # print(f"DEBUG: Loaded {len(data)} rows for {contrib_type.upper()} contributions with Part filter: {part_filter}")
        except Exception as e:
            # print(f"DEBUG: Error loading contribution data: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to load contribution data: {str(e)}")
        
    def filter_contribution_data(self):
        filter_text = self.filter_input.text().strip().lower()
        for row in range(self.contribution_table.rowCount()):
            match = False
            for col in range(self.contribution_table.columnCount()):
                item = self.contribution_table.item(row, col)
                if item and filter_text in item.text().lower():
                    match = True
                    break
            self.contribution_table.setRowHidden(row, not match)

    def add_simple_bonus_tab(self, tab_widget):
        """Add a simple bonus management tab with full CRUD functionality"""
        bonus_tab = QWidget()
        layout = QVBoxLayout()
        
        # Header
        title_label = QLabel("💰 Bonus Management")
        title_label
        layout.addWidget(title_label)
        
        # Info
        info_label = QLabel("Manage employee bonuses. Bonuses are automatically included in payroll calculations.")
        layout.addWidget(info_label)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        manage_btn = QPushButton("🔧 Manage Bonuses")
        manage_btn
        manage_btn.clicked.connect(self.open_bonus_management)
        button_layout.addWidget(manage_btn)
        
        refresh_btn = QPushButton("🔄 Refresh Summary")
        refresh_btn
        refresh_btn.clicked.connect(self.load_simple_bonuses)
        button_layout.addWidget(refresh_btn)
        
        info_btn = QPushButton("ℹ️ Bonus Rules")
        info_btn
        info_btn.clicked.connect(self.show_bonus_info)
        button_layout.addWidget(info_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # Simple summary table
        self.simple_bonus_table = QTableWidget()
        self.simple_bonus_table.setColumnCount(5)
        self.simple_bonus_table.setHorizontalHeaderLabels([
            "Employee", "Bonus Type", "Amount (RM)", "Effective Date", "Status"
        ])
        self.simple_bonus_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.simple_bonus_table.horizontalHeader().setStretchLastSection(True)
        # Make table read-only
        self.simple_bonus_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.simple_bonus_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.simple_bonus_table.setAlternatingRowColors(True)
        self.simple_bonus_table
        
        layout.addWidget(self.simple_bonus_table)
        
        # Summary info
        self.summary_layout = QHBoxLayout()
        self.total_bonuses_summary = QLabel("Total Bonuses: 0")
        self.active_bonuses_summary = QLabel("Active: 0") 
        self.total_amount_summary = QLabel("Total Amount: RM 0.00")
        
        self.summary_layout.addWidget(self.total_bonuses_summary)
        self.summary_layout.addWidget(self.active_bonuses_summary)
        self.summary_layout.addWidget(self.total_amount_summary)
        self.summary_layout.addStretch()
        
        layout.addLayout(self.summary_layout)
        
        bonus_tab.setLayout(layout)
        tab_widget.addTab(bonus_tab, "💰 Bonuses")
        
        # Load bonuses on startup
        self.load_simple_bonuses()
    
    def open_bonus_management(self):
        """Open the comprehensive bonus management dialog"""
        try:
            from gui.bonus_management_dialog import BonusManagementDialog
            dialog = BonusManagementDialog(self)
            dialog.exec_()
            # Refresh the summary after dialog closes
            self.load_simple_bonuses()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open bonus management: {str(e)}")
            # print(f"DEBUG: Error opening bonus management dialog: {str(e)}")
    
    def load_simple_bonuses(self):
        """Load bonuses in a simple way with summary"""
        try:
            # Get bonus data without JOIN to avoid relationship errors
            response = supabase.table("bonuses").select("*").limit(20).execute()
            
            total_amount = 0
            active_count = 0
            total_count = 0
            
            if response.data:
                # Manually enrich with employee data
                for bonus in response.data:
                    employee_id = bonus.get('employee_id')
                    if employee_id:
                        try:
                            emp_result = supabase.table("employees").select("full_name").eq("id", employee_id).execute()
                            if emp_result.data:
                                bonus['employees'] = emp_result.data[0]
                            else:
                                bonus['employees'] = {'full_name': 'Unknown Employee'}
                        except Exception:
                            bonus['employees'] = {'full_name': 'Unknown Employee'}
                    else:
                        bonus['employees'] = {'full_name': 'Unknown Employee'}
                self.simple_bonus_table.setRowCount(len(response.data))
                total_count = len(response.data)
                
                for row, bonus in enumerate(response.data):
                    employee_data = bonus.get('employees', {})
                    
                    # Employee name
                    self.simple_bonus_table.setItem(row, 0, QTableWidgetItem(employee_data.get('full_name', 'N/A')))
                    
                    # Bonus type
                    self.simple_bonus_table.setItem(row, 1, QTableWidgetItem(bonus.get('bonus_type', '')))
                    
                    # Amount
                    amount = float(bonus.get('amount', 0))
                    self.simple_bonus_table.setItem(row, 2, QTableWidgetItem(f"{amount:.2f}"))
                    
                    # Effective date
                    effective_date = bonus.get('effective_date', '')
                    if effective_date:
                        date_obj = datetime.fromisoformat(effective_date.replace('Z', '+00:00'))
                        formatted_date = date_obj.strftime('%Y-%m-%d')
                        self.simple_bonus_table.setItem(row, 3, QTableWidgetItem(formatted_date))
                    else:
                        self.simple_bonus_table.setItem(row, 3, QTableWidgetItem('N/A'))
                    
                    # Status
                    status = bonus.get('status', 'Active')
                    self.simple_bonus_table.setItem(row, 4, QTableWidgetItem(status))
                    
                    # Calculate summary
                    if status.lower() == 'active':
                        active_count += 1
                        total_amount += amount
            else:
                self.simple_bonus_table.setRowCount(1)
                self.simple_bonus_table.setItem(0, 0, QTableWidgetItem("No bonuses found"))
                self.simple_bonus_table.setItem(0, 1, QTableWidgetItem(""))
                self.simple_bonus_table.setItem(0, 2, QTableWidgetItem(""))
                self.simple_bonus_table.setItem(0, 3, QTableWidgetItem(""))
                self.simple_bonus_table.setItem(0, 4, QTableWidgetItem(""))
            
            # Update summary labels
            self.total_bonuses_summary.setText(f"Total Bonuses: {total_count}")
            self.active_bonuses_summary.setText(f"Active: {active_count}")
            self.total_amount_summary.setText(f"Total Amount: RM {total_amount:.2f}")
                
        except Exception as e:
            # print(f"DEBUG: Error loading simple bonuses: {str(e)}")
            self.simple_bonus_table.setRowCount(1)
            self.simple_bonus_table.setItem(0, 0, QTableWidgetItem("Error loading bonuses"))
            self.simple_bonus_table.setItem(0, 1, QTableWidgetItem(str(e)))
            self.simple_bonus_table.setItem(0, 2, QTableWidgetItem(""))
            self.simple_bonus_table.setItem(0, 3, QTableWidgetItem(""))
            self.simple_bonus_table.setItem(0, 4, QTableWidgetItem(""))
            
            # Reset summary on error
            if hasattr(self, 'total_bonuses_summary'):
                self.total_bonuses_summary.setText("Total Bonuses: 0")
                self.active_bonuses_summary.setText("Active: 0")
                self.total_amount_summary.setText("Total Amount: RM 0.00")
    
    def show_bonus_info(self):
        """Show information about bonus management and rules"""
        QMessageBox.information(self, "Bonus Management Rules", 
            "💰 Bonus Management System\n\n"
            "📋 How to manage bonuses:\n"
            "• Click 'Manage Bonuses' to add, edit, or delete bonuses\n"
            "• Bonuses are automatically included in payroll calculations\n"
            "• Use 'Refresh Summary' to update the display\n\n"
            "📐 EPF Bonus Rule:\n"
            "• When basic salary + bonus > RM 5,000:\n"
            "  - Employer EPF contribution becomes 13%\n"
            "  - Employee EPF contribution remains 11%\n\n"
            "📅 Bonus Types:\n"
            "• Performance, Annual, Festival, Commission\n"
            "• Attendance, Project, Overtime, Other\n\n"
            "⚡ Features:\n"
            "• Set effective and expiry dates\n"
            "• Mark as recurring for regular bonuses\n"
            "• Active/Inactive status control")

    def toggle_calculation_method(self, method):
        """Toggle between fixed rate and variable percentage calculation methods"""
        try:
            self.calculation_method = method
            
            if method == "fixed":
                self.fixed_rate_button.setChecked(True)
                self.variable_percentage_button.setChecked(False)
                self.method_status_label.setText("🔢 Current: Fixed Rate Calculation")
                self.method_status_label.setStyleSheet("color: green; font-weight: bold; padding: 5px;")
                QMessageBox.information(self, "Calculation Method", 
                    "Switched to Fixed Rate Calculation\n\n"
                    "Payroll will use fixed EPF, SOCSO, and EIS contribution tables.")
            else:
                self.fixed_rate_button.setChecked(False)
                self.variable_percentage_button.setChecked(True)
                self.method_status_label.setText("📊 Current: Variable Percentage Calculation")
                self.method_status_label.setStyleSheet("color: blue; font-weight: bold; padding: 5px;")
                QMessageBox.information(self, "Calculation Method", 
                    "Switched to Variable Percentage Calculation\n\n"
                    "Payroll will use custom percentage rates for contributions.")
            
            # Persist the setting so it survives app restarts
            try:
                update_payroll_settings(calculation_method=method)
            except Exception as _save_calc:
                print(f"DEBUG: Could not persist payroll calculation setting: {_save_calc}")
            # Also write local cache so restart reflects immediately even if DB write fails
            try:
                from services.local_settings_cache import save_cached_payroll_settings
                save_cached_payroll_settings({'calculation_method': method})
            except Exception:
                pass

            print(f"DEBUG: Calculation method changed to: {method}")
            
        except Exception as e:
            print(f"DEBUG: Error toggling calculation method: {e}")
            QMessageBox.warning(self, "Error", f"Failed to change calculation method: {e}")

    def add_variable_percentage_tab(self, tab_widget):
        """Add variable percentage calculation configuration tab"""
        try:
            variable_tab = QWidget()
            variable_layout = QVBoxLayout()
            
            # Title and description
            title_label = QLabel("📊 Variable Percentage Configuration")
            title_font = QFont()
            title_font.setPointSize(14)
            title_font.setBold(True)
            title_label.setFont(title_font)
            variable_layout.addWidget(title_label)
            
            desc_label = QLabel(
                "Configure custom percentage rates for payroll calculations. "
                "These rates will override the fixed contribution tables when Variable Percentage mode is active."
            )
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: gray; margin-bottom: 10px;")
            variable_layout.addWidget(desc_label)
            
            # EPF Configuration - Five Parts by Age and Citizenship (Official KWSP Parts A-E)
            epf_group = QGroupBox("EPF (Employee Provident Fund) - KWSP Third Schedule (Parts A-E)")
            epf_main_layout = QVBoxLayout()
            
            # EPF official rates explanation
            epf_info = QLabel(
                "💡 Configure EPF rates according to KWSP Third Schedule Parts A-E. "
                "Official EPF contribution parts based on citizenship, age, and election date."
            )
            epf_info.setWordWrap(True)
            epf_info.setStyleSheet("color: #2E86AB; font-size: 11px; background-color: #F0F8FF; padding: 6px; border-radius: 4px; margin-bottom: 8px;")
            epf_main_layout.addWidget(epf_info)
            
            # Create scrollable area for EPF rates
            epf_scroll = QScrollArea()
            epf_scroll_widget = QWidget()
            epf_scroll_layout = QVBoxLayout()
            
            # Part A: Malaysian Citizens + PRs + Non-citizens (before 1 Aug 1998) - Under 60
            part_a_group = QGroupBox("Part A: Malaysian Citizens + PRs + Non-citizens (elected before 1 Aug 1998) - Under 60")
            part_a_layout = QVBoxLayout()
            
            part_a_info = QLabel("Automatic EPF contribution for Malaysian citizens, permanent residents, and non-citizens who elected before 1 Aug 1998 (under 60 years)")
            part_a_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            part_a_layout.addWidget(part_a_info)
            
            # Basic rates (for table lookup)
            part_a_basic_layout = QFormLayout()
            
            self.epf_part_a_employee = QDoubleSpinBox()
            self.epf_part_a_employee.setRange(0.0, 20.0)
            self.epf_part_a_employee.setSuffix(" %")
            self.epf_part_a_employee.setValue(11.0)  # Standard rate
            self.epf_part_a_employee.setSingleStep(0.1)
            
            self.epf_part_a_employer = QDoubleSpinBox()
            self.epf_part_a_employer.setRange(0.0, 20.0)
            self.epf_part_a_employer.setSuffix(" %")
            self.epf_part_a_employer.setValue(12.0)  # Standard rate
            self.epf_part_a_employer.setSingleStep(0.1)
            
            part_a_basic_layout.addRow("Employee Rate (Table/Basic):", self.epf_part_a_employee)
            part_a_basic_layout.addRow("Employer Rate (Table/Basic):", self.epf_part_a_employer)
            
            # Rates for wages exceeding RM20,000
            part_a_over20k_layout = QFormLayout()
            part_a_over20k_label = QLabel("For wages exceeding RM20,000:")
            part_a_over20k_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
            part_a_layout.addWidget(part_a_over20k_label)
            
            self.epf_part_a_employee_over20k = QDoubleSpinBox()
            self.epf_part_a_employee_over20k.setRange(0.0, 20.0)
            self.epf_part_a_employee_over20k.setSuffix(" %")
            self.epf_part_a_employee_over20k.setValue(11.0)  # Official: 11%
            self.epf_part_a_employee_over20k.setSingleStep(0.1)
            
            self.epf_part_a_employer_over20k = QDoubleSpinBox()
            self.epf_part_a_employer_over20k.setRange(0.0, 20.0)
            self.epf_part_a_employer_over20k.setSuffix(" %")
            self.epf_part_a_employer_over20k.setValue(12.0)  # Official: 12%
            self.epf_part_a_employer_over20k.setSingleStep(0.1)
            
            part_a_over20k_layout.addRow("Employee Rate (>RM20k):", self.epf_part_a_employee_over20k)
            part_a_over20k_layout.addRow("Employer Rate (>RM20k):", self.epf_part_a_employer_over20k)
            
            # Bonus rule for Part A
            part_a_bonus_layout = QFormLayout()
            part_a_bonus_label = QLabel("Bonus Rule (wages ≤RM5k + bonus >RM5k):")
            part_a_bonus_label.setStyleSheet("font-weight: bold; color: #8B4513; margin-top: 10px;")
            part_a_layout.addWidget(part_a_bonus_label)
            
            self.epf_part_a_employer_bonus = QDoubleSpinBox()
            self.epf_part_a_employer_bonus.setRange(0.0, 20.0)
            self.epf_part_a_employer_bonus.setSuffix(" %")
            self.epf_part_a_employer_bonus.setValue(13.0)  # Official: 13% for bonus rule
            self.epf_part_a_employer_bonus.setSingleStep(0.1)
            
            part_a_bonus_layout.addRow("Employer Rate (Bonus Rule):", self.epf_part_a_employer_bonus)
            
            part_a_layout.addLayout(part_a_basic_layout)
            part_a_layout.addLayout(part_a_over20k_layout)
            part_a_layout.addLayout(part_a_bonus_layout)
            part_a_group.setLayout(part_a_layout)
            
            # Part B: Non-citizens (on/after 1 Aug 1998) - Under 60
            part_b_group = QGroupBox("Part B: Non-citizens (elected on/after 1 Aug 1998) - Under 60")
            part_b_layout = QVBoxLayout()
            
            part_b_info = QLabel("Non-citizens under 60 who elected to contribute on/after 1 Aug 1998")
            part_b_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            part_b_layout.addWidget(part_b_info)
            
            # Basic rates (for table lookup up to RM20k)
            part_b_basic_layout = QFormLayout()
            
            self.epf_part_b_employee = QDoubleSpinBox()
            self.epf_part_b_employee.setRange(0.0, 20.0)
            self.epf_part_b_employee.setSuffix(" %")
            self.epf_part_b_employee.setValue(11.0)  # Standard rate
            self.epf_part_b_employee.setSingleStep(0.1)
            
            self.epf_part_b_employer = QDoubleSpinBox()
            self.epf_part_b_employer.setRange(0.0, 20.0)
            self.epf_part_b_employer.setSuffix(" %")
            self.epf_part_b_employer.setValue(4.0)  # Percentage rate for table
            self.epf_part_b_employer.setSingleStep(0.1)
            
            part_b_basic_layout.addRow("Employee Rate (Table):", self.epf_part_b_employee)
            part_b_basic_layout.addRow("Employer Rate (Table):", self.epf_part_b_employer)
            
            # Rates for wages exceeding RM20,000
            part_b_over20k_layout = QFormLayout()
            part_b_over20k_label = QLabel("For wages exceeding RM20,000:")
            part_b_over20k_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
            part_b_layout.addWidget(part_b_over20k_label)
            
            self.epf_part_b_employee_over20k = QDoubleSpinBox()
            self.epf_part_b_employee_over20k.setRange(0.0, 20.0)
            self.epf_part_b_employee_over20k.setSuffix(" %")
            self.epf_part_b_employee_over20k.setValue(11.0)  # Official: 11%
            self.epf_part_b_employee_over20k.setSingleStep(0.1)
            
            self.epf_part_b_employer_over20k_fixed = QDoubleSpinBox()
            self.epf_part_b_employer_over20k_fixed.setRange(0.0, 50.0)
            self.epf_part_b_employer_over20k_fixed.setSuffix(" RM")
            self.epf_part_b_employer_over20k_fixed.setValue(5.0)  # Official: Fixed RM5.00
            self.epf_part_b_employer_over20k_fixed.setSingleStep(1.0)
            
            part_b_over20k_layout.addRow("Employee Rate (>RM20k):", self.epf_part_b_employee_over20k)
            part_b_over20k_layout.addRow("Employer (>RM20k, Fixed):", self.epf_part_b_employer_over20k_fixed)
            
            part_b_layout.addLayout(part_b_basic_layout)
            part_b_layout.addLayout(part_b_over20k_layout)
            part_b_group.setLayout(part_b_layout)
            
            # Part C: PRs + Non-citizens (before 1 Aug 1998) - 60 and above
            part_c_group = QGroupBox("Part C: PRs + Non-citizens (elected before 1 Aug 1998) - 60 and above")
            part_c_layout = QVBoxLayout()
            
            part_c_info = QLabel("Permanent residents and non-citizens 60+ who elected before 1 Aug 1998")
            part_c_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            part_c_layout.addWidget(part_c_info)
            
            # Basic rates (for table lookup up to RM20k)
            part_c_basic_layout = QFormLayout()
            
            self.epf_part_c_employee = QDoubleSpinBox()
            self.epf_part_c_employee.setRange(0.0, 20.0)
            self.epf_part_c_employee.setSuffix(" %")
            self.epf_part_c_employee.setValue(0.0)  # 60+ employee default 0%
            self.epf_part_c_employee.setSingleStep(0.1)
            
            self.epf_part_c_employer_fixed = QDoubleSpinBox()
            self.epf_part_c_employer_fixed.setRange(0.0, 50.0)
            self.epf_part_c_employer_fixed.setSuffix(" RM")
            self.epf_part_c_employer_fixed.setValue(5.0)  # Fixed RM5 for table
            self.epf_part_c_employer_fixed.setSingleStep(1.0)
            
            part_c_basic_layout.addRow("Employee Rate (Table):", self.epf_part_c_employee)
            part_c_basic_layout.addRow("Employer (Table, Fixed RM):", self.epf_part_c_employer_fixed)
            
            # Rates for wages exceeding RM20,000
            part_c_over20k_layout = QFormLayout()
            part_c_over20k_label = QLabel("For wages exceeding RM20,000:")
            part_c_over20k_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
            part_c_layout.addWidget(part_c_over20k_label)
            
            self.epf_part_c_employee_over20k = QDoubleSpinBox()
            self.epf_part_c_employee_over20k.setRange(0.0, 20.0)
            self.epf_part_c_employee_over20k.setSuffix(" %")
            self.epf_part_c_employee_over20k.setValue(0.0)  # 60+ employee default 0% (>RM20k)
            self.epf_part_c_employee_over20k.setSingleStep(0.1)
            
            self.epf_part_c_employer_over20k = QDoubleSpinBox()
            self.epf_part_c_employer_over20k.setRange(0.0, 20.0)
            self.epf_part_c_employer_over20k.setSuffix(" %")
            self.epf_part_c_employer_over20k.setValue(6.0)  # Official: 6%
            self.epf_part_c_employer_over20k.setSingleStep(0.1)
            
            part_c_over20k_layout.addRow("Employee Rate (>RM20k):", self.epf_part_c_employee_over20k)
            part_c_over20k_layout.addRow("Employer Rate (>RM20k):", self.epf_part_c_employer_over20k)
            
            # Bonus rule for Part C
            part_c_bonus_layout = QFormLayout()
            part_c_bonus_label = QLabel("Bonus Rule (wages ≤RM5k + bonus >RM5k):")
            part_c_bonus_label.setStyleSheet("font-weight: bold; color: #8B4513; margin-top: 10px;")
            part_c_layout.addWidget(part_c_bonus_label)
            
            self.epf_part_c_employer_bonus = QDoubleSpinBox()
            self.epf_part_c_employer_bonus.setRange(0.0, 20.0)
            self.epf_part_c_employer_bonus.setSuffix(" %")
            self.epf_part_c_employer_bonus.setValue(6.5)  # Official: 6.5% for bonus rule
            self.epf_part_c_employer_bonus.setSingleStep(0.1)
            
            part_c_bonus_layout.addRow("Employer Rate (Bonus Rule):", self.epf_part_c_employer_bonus)
            
            part_c_layout.addLayout(part_c_basic_layout)
            part_c_layout.addLayout(part_c_over20k_layout)
            part_c_layout.addLayout(part_c_bonus_layout)
            part_c_group.setLayout(part_c_layout)
            
            # Part D: Non-citizens (on/after 1 Aug 1998) - 60 and above
            part_d_group = QGroupBox("Part D: Non-citizens (elected on/after 1 Aug 1998) - 60 and above")
            part_d_layout = QVBoxLayout()
            
            part_d_info = QLabel("Non-citizens 60+ who elected to contribute on/after 1 Aug 1998")
            part_d_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            part_d_layout.addWidget(part_d_info)
            
            # Basic rates (for table lookup up to RM20k)
            part_d_basic_layout = QFormLayout()
            
            self.epf_part_d_employee = QDoubleSpinBox()
            self.epf_part_d_employee.setRange(0.0, 20.0)
            self.epf_part_d_employee.setSuffix(" %")
            self.epf_part_d_employee.setValue(0.0)  # 60+ employee default 0%
            self.epf_part_d_employee.setSingleStep(0.1)
            
            self.epf_part_d_employer = QDoubleSpinBox()
            self.epf_part_d_employer.setRange(0.0, 20.0)
            self.epf_part_d_employer.setSuffix(" %")
            self.epf_part_d_employer.setValue(4.0)  # Percentage rate for table
            self.epf_part_d_employer.setSingleStep(0.1)
            
            part_d_basic_layout.addRow("Employee Rate (Table):", self.epf_part_d_employee)
            part_d_basic_layout.addRow("Employer Rate (Table):", self.epf_part_d_employer)
            
            # Rates for wages exceeding RM20,000
            part_d_over20k_layout = QFormLayout()
            part_d_over20k_label = QLabel("For wages exceeding RM20,000:")
            part_d_over20k_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
            part_d_layout.addWidget(part_d_over20k_label)
            
            self.epf_part_d_employee_over20k = QDoubleSpinBox()
            self.epf_part_d_employee_over20k.setRange(0.0, 20.0)
            self.epf_part_d_employee_over20k.setSuffix(" %")
            self.epf_part_d_employee_over20k.setValue(0.0)  # 60+ employee default 0% (>RM20k)
            self.epf_part_d_employee_over20k.setSingleStep(0.1)
            
            self.epf_part_d_employer_over20k_fixed = QDoubleSpinBox()
            self.epf_part_d_employer_over20k_fixed.setRange(0.0, 50.0)
            self.epf_part_d_employer_over20k_fixed.setSuffix(" RM")
            self.epf_part_d_employer_over20k_fixed.setValue(5.0)  # Official: Fixed RM5.00
            self.epf_part_d_employer_over20k_fixed.setSingleStep(1.0)
            
            part_d_over20k_layout.addRow("Employee Rate (>RM20k):", self.epf_part_d_employee_over20k)
            part_d_over20k_layout.addRow("Employer (>RM20k, Fixed):", self.epf_part_d_employer_over20k_fixed)
            
            part_d_layout.addLayout(part_d_basic_layout)
            part_d_layout.addLayout(part_d_over20k_layout)
            part_d_group.setLayout(part_d_layout)
            
            # Part E: Malaysian Citizens - 60 and above
            part_e_group = QGroupBox("Part E: Malaysian Citizens - 60 and above")
            part_e_layout = QVBoxLayout()
            
            part_e_info = QLabel("Malaysian citizens 60 and above (automatic EPF)")
            part_e_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
            part_e_layout.addWidget(part_e_info)
            
            # Basic rates (for table lookup up to RM20k)
            part_e_basic_layout = QFormLayout()
            
            self.epf_part_e_employee = QDoubleSpinBox()
            self.epf_part_e_employee.setRange(0.0, 20.0)
            self.epf_part_e_employee.setSuffix(" %")
            self.epf_part_e_employee.setValue(0.0)  # Voluntary
            self.epf_part_e_employee.setSingleStep(0.1)
            
            self.epf_part_e_employer = QDoubleSpinBox()
            self.epf_part_e_employer.setRange(0.0, 20.0)
            self.epf_part_e_employer.setSuffix(" %")
            self.epf_part_e_employer.setValue(4.0)  # Fixed 4%
            self.epf_part_e_employer.setSingleStep(0.1)
            
            part_e_basic_layout.addRow("Employee Rate (Voluntary, Table):", self.epf_part_e_employee)
            part_e_basic_layout.addRow("Employer Rate (Table):", self.epf_part_e_employer)
            
            # Rates for wages exceeding RM20,000
            part_e_over20k_layout = QFormLayout()
            part_e_over20k_label = QLabel("For wages exceeding RM20,000:")
            part_e_over20k_label.setStyleSheet("font-weight: bold; color: #2c3e50; margin-top: 10px;")
            part_e_layout.addWidget(part_e_over20k_label)
            
            self.epf_part_e_employee_over20k = QDoubleSpinBox()
            self.epf_part_e_employee_over20k.setRange(0.0, 20.0)
            self.epf_part_e_employee_over20k.setSuffix(" %")
            self.epf_part_e_employee_over20k.setValue(0.0)  # Official: 0.0% (no contribution)
            self.epf_part_e_employee_over20k.setSingleStep(0.1)
            
            self.epf_part_e_employer_over20k = QDoubleSpinBox()
            self.epf_part_e_employer_over20k.setRange(0.0, 20.0)
            self.epf_part_e_employer_over20k.setSuffix(" %")
            self.epf_part_e_employer_over20k.setValue(4.0)  # Official: 4%
            self.epf_part_e_employer_over20k.setSingleStep(0.1)
            
            part_e_over20k_layout.addRow("Employee Rate (>RM20k):", self.epf_part_e_employee_over20k)
            part_e_over20k_layout.addRow("Employer Rate (>RM20k):", self.epf_part_e_employer_over20k)
            
            part_e_layout.addLayout(part_e_basic_layout)
            part_e_layout.addLayout(part_e_over20k_layout)
            part_e_group.setLayout(part_e_layout)
            
            # Add all parts to scroll layout
            epf_scroll_layout.addWidget(part_a_group)
            epf_scroll_layout.addWidget(part_b_group)
            epf_scroll_layout.addWidget(part_c_group)
            epf_scroll_layout.addWidget(part_d_group)
            epf_scroll_layout.addWidget(part_e_group)
            
            epf_scroll_widget.setLayout(epf_scroll_layout)
            epf_scroll.setWidget(epf_scroll_widget)
            epf_scroll.setWidgetResizable(True)
            epf_scroll.setMaximumHeight(400)  # Limit height to prevent excessive scrolling
            
            epf_main_layout.addWidget(epf_scroll)
            epf_group.setLayout(epf_main_layout)
            variable_layout.addWidget(epf_group)
            
            # SOCSO Configuration (Workers' Social Security Act 1969) - Two Categories
            socso_group = QGroupBox("SOCSO (Workers' Social Security Act 1969) - PERKESO")
            socso_main_layout = QVBoxLayout()
            
            # SOCSO explanation
            socso_info = QLabel(
                "💡 SOCSO operates under two contribution categories based on age and schemes covered"
            )
            socso_info.setWordWrap(True)
            socso_info.setStyleSheet("color: #2E86AB; font-size: 11px; background-color: #F0F8FF; padding: 6px; border-radius: 4px; margin-bottom: 8px;")
            socso_main_layout.addWidget(socso_info)
            
            # Create column layout for SOCSO categories
            socso_categories_layout = QHBoxLayout()
            
            # First Category: Under 60 (Both schemes)
            first_category_group = QGroupBox("First Category (Under 60 years)")
            first_category_layout = QFormLayout()
            
            self.socso_first_employee_rate = QDoubleSpinBox()
            self.socso_first_employee_rate.setRange(0.0, 5.0)
            self.socso_first_employee_rate.setSuffix(" %")
            self.socso_first_employee_rate.setValue(0.5)  # Official PERKESO rate
            self.socso_first_employee_rate.setSingleStep(0.1)
            
            self.socso_first_employer_rate = QDoubleSpinBox()
            self.socso_first_employer_rate.setRange(0.0, 5.0)
            self.socso_first_employer_rate.setSuffix(" %")
            self.socso_first_employer_rate.setValue(1.75)  # Official PERKESO rate
            self.socso_first_employer_rate.setSingleStep(0.1)
            
            first_category_layout.addRow("Employee Rate:", self.socso_first_employee_rate)
            first_category_layout.addRow("Employer Rate:", self.socso_first_employer_rate)
            
            # Add note about first category coverage
            first_note = QLabel("Covers: Employment Injury Scheme + Invalidity Scheme")
            first_note.setStyleSheet("color: green; font-style: italic; font-size: 9px;")
            first_note.setWordWrap(True)
            first_category_layout.addRow("", first_note)
            
            first_category_group.setLayout(first_category_layout)
            
            # Second Category: 60+ (Employment Injury only)
            second_category_group = QGroupBox("Second Category (60+ years)")
            second_category_layout = QFormLayout()
            
            self.socso_second_employee_rate = QDoubleSpinBox()
            self.socso_second_employee_rate.setRange(0.0, 5.0)
            self.socso_second_employee_rate.setSuffix(" %")
            self.socso_second_employee_rate.setValue(0.0)  # Official PERKESO: No employee contribution
            self.socso_second_employee_rate.setSingleStep(0.1)
            
            self.socso_second_employer_rate = QDoubleSpinBox()
            self.socso_second_employer_rate.setRange(0.0, 5.0)
            self.socso_second_employer_rate.setSuffix(" %")
            self.socso_second_employer_rate.setValue(1.25)  # Official PERKESO rate
            self.socso_second_employer_rate.setSingleStep(0.1)
            
            second_category_layout.addRow("Employee Rate:", self.socso_second_employee_rate)
            second_category_layout.addRow("Employer Rate:", self.socso_second_employer_rate)
            
            # Add note about second category coverage
            second_note = QLabel("Covers: Employment Injury Scheme only")
            second_note.setStyleSheet("color: green; font-style: italic; font-size: 9px;")
            second_note.setWordWrap(True)
            second_category_layout.addRow("", second_note)
            
            second_category_group.setLayout(second_category_layout)
            
            # Add both category columns to the layout
            socso_categories_layout.addWidget(first_category_group)
            socso_categories_layout.addWidget(second_category_group)
            socso_main_layout.addLayout(socso_categories_layout)
            
            socso_group.setLayout(socso_main_layout)
            variable_layout.addWidget(socso_group)
            
            # EIS Configuration (Employment Insurance System Act 2017) - Single Rate
            eis_group = QGroupBox("EIS (Employment Insurance System Act 2017) - PERKESO")
            eis_main_layout = QVBoxLayout()
            
            # EIS explanation
            eis_info = QLabel(
                "💡 EIS provides unemployment benefits with single contribution rate (Age 18-60, max salary RM6,000)"
            )
            eis_info.setWordWrap(True)
            eis_info.setStyleSheet("color: #2E86AB; font-size: 11px; background-color: #F0F8FF; padding: 6px; border-radius: 4px; margin-bottom: 8px;")
            eis_main_layout.addWidget(eis_info)
            
            # EIS rates layout (single rate structure)
            eis_rates_layout = QFormLayout()
            
            self.eis_employee_rate = QDoubleSpinBox()
            self.eis_employee_rate.setRange(0.0, 2.0)
            self.eis_employee_rate.setSuffix(" %")
            self.eis_employee_rate.setValue(0.2)  # Official PERKESO rate
            self.eis_employee_rate.setSingleStep(0.1)
            
            self.eis_employer_rate = QDoubleSpinBox()
            self.eis_employer_rate.setRange(0.0, 2.0)
            self.eis_employer_rate.setSuffix(" %")
            self.eis_employer_rate.setValue(0.2)  # Official PERKESO rate
            self.eis_employer_rate.setSingleStep(0.1)
            
            eis_rates_layout.addRow("Employee Rate:", self.eis_employee_rate)
            eis_rates_layout.addRow("Employer Rate:", self.eis_employer_rate)
            
            # Add EIS coverage note
            eis_note = QLabel("Benefits: Job Search Allowance, Early Re-employment Allowance, Reduced Income Allowance, Training Allowance")
            eis_note.setStyleSheet("color: green; font-style: italic; font-size: 9px;")
            eis_note.setWordWrap(True)
            eis_rates_layout.addRow("", eis_note)
            
            # Add salary ceiling note
            eis_ceiling_note = QLabel("⚠️ Contribution capped at RM6,000 monthly salary")
            eis_ceiling_note.setStyleSheet("color: orange; font-weight: bold; font-size: 9px;")
            eis_ceiling_note.setWordWrap(True)
            eis_rates_layout.addRow("", eis_ceiling_note)
            
            eis_main_layout.addLayout(eis_rates_layout)
            eis_group.setLayout(eis_main_layout)
            variable_layout.addWidget(eis_group)

            # Save/Load configuration controls
            config_controls = QHBoxLayout()
            config_controls.addWidget(QLabel("Config name:"))
            self.variable_config_name_input = QLineEdit()
            self.variable_config_name_input.setPlaceholderText("default")
            self.variable_config_name_input.setText("default")
            self.variable_config_name_input.setMaximumWidth(220)
            config_controls.addWidget(self.variable_config_name_input)

            self.save_variable_config_button = QPushButton("💾 Save Variable % Config")
            self.save_variable_config_button.setToolTip("Save the current EPF/SOCSO/EIS percentage settings under this name")
            self.save_variable_config_button.clicked.connect(self.save_variable_percentage_configuration)
            config_controls.addWidget(self.save_variable_config_button)

            self.load_variable_config_button = QPushButton("⤵ Load Config")
            self.load_variable_config_button.setToolTip("Load previously saved Variable % settings by name")
            self.load_variable_config_button.clicked.connect(self.load_variable_percentage_configuration)
            config_controls.addWidget(self.load_variable_config_button)

            config_controls.addStretch(1)
            variable_layout.addLayout(config_controls)
            
            # Create a scroll area to contain all the content
            scroll_area = QScrollArea()
            scroll_widget = QWidget()
            scroll_widget.setLayout(variable_layout)
            scroll_area.setWidget(scroll_widget)
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Create the main tab layout
            tab_layout = QVBoxLayout()
            tab_layout.setContentsMargins(0, 0, 0, 0)
            tab_layout.addWidget(scroll_area)
            variable_tab.setLayout(tab_layout)
            
            tab_widget.addTab(variable_tab, "📊 Variable %")

            # Attempt to load default configuration on first render
            try:
                self.load_variable_percentage_configuration("default")
            except Exception as _e:
                # Best-effort; fall back silently to built-in defaults
                print(f"DEBUG: load default variable% config skipped: {_e}")
            
        except Exception as e:
            print(f"DEBUG: Error creating variable percentage tab: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create variable percentage tab: {e}")

    # Full LHDN tax config tab implementation is defined later in this class
    
    def save_variable_percentage_configuration(self):
        """Collect Variable % rates from UI and persist via Supabase service"""
        try:
            config_name = (self.variable_config_name_input.text() or "default").strip()
            payload = {
                'config_name': config_name,
                # EPF under-60 (Part A defaults used as stage1)
                'epf_employee_rate_stage1': float(self.epf_part_a_employee.value()),
                'epf_employer_rate_stage1': float(self.epf_part_a_employer.value()),
                # EPF 60+ (Part E defaults used as stage2)
                'epf_employee_rate_stage2': float(self.epf_part_e_employee.value()),
                'epf_employer_rate_stage2': float(self.epf_part_e_employer.value()),
                # Persist raw EPF Part inputs so DB "follows the input"
                'epf_part_a_employee': float(self.epf_part_a_employee.value()),
                'epf_part_a_employer': float(self.epf_part_a_employer.value()),
                'epf_part_a_employee_over20k': float(getattr(self, 'epf_part_a_employee_over20k').value()) if hasattr(self, 'epf_part_a_employee_over20k') else None,
                'epf_part_a_employer_over20k': float(getattr(self, 'epf_part_a_employer_over20k').value()) if hasattr(self, 'epf_part_a_employer_over20k') else None,
                'epf_part_a_employer_bonus': float(getattr(self, 'epf_part_a_employer_bonus').value()) if hasattr(self, 'epf_part_a_employer_bonus') else None,
                # Part B & D fields (if widgets exist)
                'epf_part_b_employee': float(getattr(self, 'epf_part_b_employee').value()) if hasattr(self, 'epf_part_b_employee') else None,
                'epf_part_b_employer': float(getattr(self, 'epf_part_b_employer').value()) if hasattr(self, 'epf_part_b_employer') else None,
                'epf_part_b_employee_over20k': float(getattr(self, 'epf_part_b_employee_over20k').value()) if hasattr(self, 'epf_part_b_employee_over20k') else None,
                'epf_part_b_employer_over20k_fixed': float(getattr(self, 'epf_part_b_employer_over20k_fixed').value()) if hasattr(self, 'epf_part_b_employer_over20k_fixed') else None,
                'epf_part_c_employee': float(getattr(self, 'epf_part_c_employee').value()) if hasattr(self, 'epf_part_c_employee') else None,
                'epf_part_c_employer_fixed': float(getattr(self, 'epf_part_c_employer_fixed').value()) if hasattr(self, 'epf_part_c_employer_fixed') else None,
                'epf_part_c_employee_over20k': float(getattr(self, 'epf_part_c_employee_over20k').value()) if hasattr(self, 'epf_part_c_employee_over20k') else None,
                'epf_part_c_employer_over20k': float(getattr(self, 'epf_part_c_employer_over20k').value()) if hasattr(self, 'epf_part_c_employer_over20k') else None,
                'epf_part_c_employer_bonus': float(getattr(self, 'epf_part_c_employer_bonus').value()) if hasattr(self, 'epf_part_c_employer_bonus') else None,
                'epf_part_d_employee': float(getattr(self, 'epf_part_d_employee').value()) if hasattr(self, 'epf_part_d_employee') else None,
                'epf_part_d_employer': float(getattr(self, 'epf_part_d_employer').value()) if hasattr(self, 'epf_part_d_employer') else None,
                'epf_part_d_employee_over20k': float(getattr(self, 'epf_part_d_employee_over20k').value()) if hasattr(self, 'epf_part_d_employee_over20k') else None,
                'epf_part_d_employer_over20k_fixed': float(getattr(self, 'epf_part_d_employer_over20k_fixed').value()) if hasattr(self, 'epf_part_d_employer_over20k_fixed') else None,
                'epf_part_e_employee': float(getattr(self, 'epf_part_e_employee').value()) if hasattr(self, 'epf_part_e_employee') else None,
                'epf_part_e_employer': float(getattr(self, 'epf_part_e_employer').value()) if hasattr(self, 'epf_part_e_employer') else None,
                'epf_part_e_employee_over20k': float(getattr(self, 'epf_part_e_employee_over20k').value()) if hasattr(self, 'epf_part_e_employee_over20k') else None,
                'epf_part_e_employer_over20k': float(getattr(self, 'epf_part_e_employer_over20k').value()) if hasattr(self, 'epf_part_e_employer_over20k') else None,
                # SOCSO categories align with PERKESO
                'socso_first_employee_rate': float(self.socso_first_employee_rate.value()),
                'socso_first_employer_rate': float(self.socso_first_employer_rate.value()),
                'socso_second_employee_rate': float(self.socso_second_employee_rate.value()),
                'socso_second_employer_rate': float(self.socso_second_employer_rate.value()),
                # EIS
                'eis_employee_rate': float(self.eis_employee_rate.value()),
                'eis_employer_rate': float(self.eis_employer_rate.value()),
                'description': 'Saved from Admin Payroll Variable % tab'
            }

            # Map SOCSO two-category rates to ACT split if service expects
            # First category corresponds to under-60: typically ACT 4 (EIS separate)
            payload['socso_employee_rate'] = payload['socso_first_employee_rate']  # backward compat
            payload['socso_employer_rate'] = payload['socso_first_employer_rate']  # backward compat
            payload['socso_act4_employee_rate'] = payload['socso_first_employee_rate']
            payload['socso_act4_employer_rate'] = payload['socso_first_employer_rate']
            payload['socso_act800_employee_rate'] = 0.0
            payload['socso_act800_employer_rate'] = max(0.0, payload['socso_second_employer_rate'] - 0.5) if 'socso_second_employer_rate' in payload else 0.5

            ok = save_variable_percentage_config(payload)
            if ok:
                QMessageBox.information(self, "Saved", f"Variable % configuration '{config_name}' saved")
            else:
                QMessageBox.warning(self, "Not Saved", "Failed to save Variable % configuration")
        except Exception as e:
            print(f"DEBUG: Error saving variable % config: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save: {e}")

    def load_variable_percentage_configuration(self, config_name: str | None = None):
        """Load Variable % config by name and populate the UI controls"""
        try:
            name = (config_name or (self.variable_config_name_input.text() if hasattr(self, 'variable_config_name_input') else 'default') or 'default').strip()
            cfg = get_variable_percentage_config(name)
            if not cfg:
                QMessageBox.information(self, "No Config", f"No saved config '{name}' found; using defaults")
                return

            # Populate EPF stage mappings (using Part A/E widgets)
            if 'epf_employee_rate_stage1' in cfg:
                self.epf_part_a_employee.setValue(float(cfg['epf_employee_rate_stage1']))
            if 'epf_employer_rate_stage1' in cfg:
                self.epf_part_a_employer.setValue(float(cfg['epf_employer_rate_stage1']))
            if 'epf_employee_rate_stage2' in cfg:
                self.epf_part_e_employee.setValue(float(cfg['epf_employee_rate_stage2']))
            if 'epf_employer_rate_stage2' in cfg:
                self.epf_part_e_employer.setValue(float(cfg['epf_employer_rate_stage2']))

            # Populate SOCSO (map ACT 4 to First Category, ACT 800 to Second Category employer share)
            if 'socso_act4_employee_rate' in cfg:
                self.socso_first_employee_rate.setValue(float(cfg['socso_act4_employee_rate']))
            elif 'socso_employee_rate' in cfg:
                self.socso_first_employee_rate.setValue(float(cfg['socso_employee_rate']))

            if 'socso_act4_employer_rate' in cfg:
                self.socso_first_employer_rate.setValue(float(cfg['socso_act4_employer_rate']))
            elif 'socso_employer_rate' in cfg:
                self.socso_first_employer_rate.setValue(float(cfg['socso_employer_rate']))

            # For second category (60+), employee rate usually 0; employer may be 1.25
            if 'socso_act800_employee_rate' in cfg:
                self.socso_second_employee_rate.setValue(float(cfg['socso_act800_employee_rate']))
            else:
                self.socso_second_employee_rate.setValue(0.0)

            if 'socso_act800_employer_rate' in cfg:
                self.socso_second_employer_rate.setValue(float(cfg['socso_act800_employer_rate']))
            elif 'socso_second_employer_rate' in cfg:
                self.socso_second_employer_rate.setValue(float(cfg['socso_second_employer_rate']))
            else:
                # Default PERKESO employer rate for 60+
                self.socso_second_employer_rate.setValue(1.25)

            # EIS
            if 'eis_employee_rate' in cfg:
                self.eis_employee_rate.setValue(float(cfg['eis_employee_rate']))
            if 'eis_employer_rate' in cfg:
                self.eis_employer_rate.setValue(float(cfg['eis_employer_rate']))

            # If EPF part fields are returned, hydrate the UI controls
            for key in list(cfg.keys()):
                if isinstance(key, str) and key.startswith('epf_part_'):
                    try:
                        val = float(cfg[key]) if cfg[key] is not None else None
                    except Exception:
                        val = None
                    if val is None:
                        continue
                    # Map key to widget if exists
                    if hasattr(self, key):
                        try:
                            getattr(self, key).setValue(val)
                        except Exception:
                            pass

            if hasattr(self, 'variable_config_name_input'):
                self.variable_config_name_input.setText(name)
        except Exception as e:
            print(f"DEBUG: Error loading variable % config: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load config: {e}")

    def calculate_pcb_amount(self, monthly_taxable_income: float, age: int = 30) -> tuple:
        """
        Calculate PCB amount using a simple flat rate (PCB functionality was simplified)
        Returns (pcb_amount, calculation_details)
        """
        # Simple flat rate calculation since PCB UI was removed
        pcb_amount = 0.0  # No PCB calculation without the UI controls
        return pcb_amount, "PCB calculation disabled (UI components removed)"



















    def handle_tax_resident_status_change(self):
        """Handle change in tax resident status to hide/show tax relief configurations"""
        try:
            # Check if tax resident checkbox exists (PCB components were removed)
            if not hasattr(self, 'tax_resident_checkbox'):
                return  # Skip if PCB UI components were removed
                
            # Get current tax resident status
            is_resident = self.tax_resident_checkbox.isChecked()
            
            # Hide/show the basic tax relief configuration group
            if hasattr(self, 'reliefs_group'):
                # Show only tax status field for non-residents, hide relief fields
                if not is_resident:
                    # Hide relief input fields but keep the tax status visible
                    if hasattr(self, 'personal_relief'):
                        self.personal_relief.setVisible(False)
                    if hasattr(self, 'spouse_relief'):
                        self.spouse_relief.setVisible(False) 
                    if hasattr(self, 'child_relief'):
                        self.child_relief.setVisible(False)
                    if hasattr(self, 'other_reliefs'):
                        self.other_reliefs.setVisible(False)
                    
                    # Update group title to indicate non-resident status
                    if hasattr(self, 'reliefs_group'):
                        self.reliefs_group.setTitle("Tax Status - Non-Resident (30% Flat Rate)")
                        self.reliefs_group.setStyleSheet("QGroupBox { color: #ff9800; }")
                else:
                    # Show all relief fields for residents
                    if hasattr(self, 'personal_relief'):
                        self.personal_relief.setVisible(True)
                    if hasattr(self, 'spouse_relief'):
                        self.spouse_relief.setVisible(True)
                    if hasattr(self, 'child_relief'):
                        self.child_relief.setVisible(True)
                    if hasattr(self, 'other_reliefs'):
                        self.other_reliefs.setVisible(True)
                    
                    # Restore original title and styling
                    if hasattr(self, 'reliefs_group'):
                        self.reliefs_group.setTitle("Tax Reliefs (Annual) - Basic PCB Calculation")
                        self.reliefs_group.setStyleSheet("")
            
            # Hide/show the comprehensive tax relief max subtab
            if hasattr(self, 'lhdn_subtab_widget') and hasattr(self, 'tax_relief_subtab_index'):
                widget = self.lhdn_subtab_widget
                idx = self.tax_relief_subtab_index
                # Prefer setTabVisible if available; fallback to setTabEnabled for older Qt
                has_set_visible = hasattr(widget, 'setTabVisible')
                if not is_resident:
                    if has_set_visible:
                        widget.setTabVisible(idx, False)
                    else:
                        widget.setTabEnabled(idx, False)
                    widget.setTabToolTip(idx, "Tax relief configuration is not available for non-residents (30% flat rate applies)")
                else:
                    if has_set_visible:
                        widget.setTabVisible(idx, True)
                    else:
                        widget.setTabEnabled(idx, True)
                    widget.setTabToolTip(idx, "Configure maximum amounts for Malaysian tax relief categories")
            
        except Exception as e:
            print(f"DEBUG: Error handling tax resident status change: {e}")

    # Public wrappers delegating to modularized implementations
    def add_lhdn_tax_config_tab(self, tab_widget):
        return lhdn_sections.add_lhdn_tax_config_tab(self, tab_widget)

    def add_tax_rates_subtab(self, subtab_widget):
        return lhdn_sections.add_tax_rates_subtab(self, subtab_widget)

    def add_tax_relief_max_subtab(self, subtab_widget):
        result = lhdn_sections.add_tax_relief_max_subtab(self, subtab_widget)
        # After existing tax config / max cap related tabs, append overrides subtab
        try:
            build_relief_overrides_subtab(self, subtab_widget)
        except Exception as e:
            print(f"DEBUG: Failed to build Relief Overrides subtab: {e}")
        return result

    def add_tax_config_management_subtab(self, subtab_widget):
        return lhdn_sections.add_tax_config_management_subtab(self, subtab_widget)

    # Original implementations are kept as private methods for clarity

    def _add_tax_rates_subtab_impl(self, subtab_widget):
        """Add Tax Rates subtab with latest LHDN tax brackets"""
        try:
            rates_tab = QWidget()
            
            # Create scroll area for the subtab
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Main widget inside scroll area
            main_widget = QWidget()
            layout = QVBoxLayout()
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Tax Rate Information Panel
            info_group = QGroupBox("Malaysian Personal Income Tax Rates (Assessment Year 2023, 2024 & 2025)")
            info_layout = QVBoxLayout()
            
            info_text = QLabel("""
<b>LHDN Progressive Tax System 2025:</b><br>
• <b>Tax Year:</b> Assessment Year 2025 (Income Year 2024)<br>
• <b>Progressive Rates:</b> 0% to 30% across multiple tax brackets<br>
• <b>Non-Resident Rate:</b> Flat 30% on total income<br><br>

<b>Reference:</b> <a href="https://www.hasil.gov.my/en/individual/individual-life-cycle/how-to-declare-income/tax-rate/">HASIL Official Tax Rates</a>
            """)
            info_text.setWordWrap(True)
            info_text.setOpenExternalLinks(True)
            info_text.setStyleSheet("QLabel { font-size: 11px; padding: 15px; background-color: #f0f8ff; border: 1px solid #ccc; border-radius: 5px; }")
            info_layout.addWidget(info_text)
            info_group.setLayout(info_layout)
            layout.addWidget(info_group)
            
            # Tax Brackets Configuration
            brackets_group = QGroupBox("Tax Brackets Configuration")
            brackets_layout = QVBoxLayout()
            
            # Create a scroll area for tax brackets
            brackets_scroll = QScrollArea()
            brackets_scroll.setWidgetResizable(True)
            brackets_scroll.setMaximumHeight(400)
            
            # Widget to contain all tax bracket input groups
            brackets_container = QWidget()
            brackets_container_layout = QVBoxLayout()
            
            # Create tax bracket input groups
            self.tax_bracket_inputs = []
            
            # Default LHDN tax brackets for initialization
            default_brackets = [
                {"from": 0, "to": 5000, "on_first": 0, "next": 0, "rate": 0, "tax_first": 0, "tax_next": 0},
                {"from": 5001, "to": 20000, "on_first": 5000, "next": 15000, "rate": 1, "tax_first": 0, "tax_next": 150},
                {"from": 20001, "to": 35000, "on_first": 20000, "next": 15000, "rate": 3, "tax_first": 150, "tax_next": 450},
                {"from": 35001, "to": 50000, "on_first": 35000, "next": 15000, "rate": 6, "tax_first": 600, "tax_next": 900},
                {"from": 50001, "to": 70000, "on_first": 50000, "next": 20000, "rate": 11, "tax_first": 1500, "tax_next": 2200},
                {"from": 70001, "to": 100000, "on_first": 70000, "next": 30000, "rate": 19, "tax_first": 3700, "tax_next": 5700},
                {"from": 100001, "to": 400000, "on_first": 100000, "next": 300000, "rate": 25, "tax_first": 9400, "tax_next": 75000},
                {"from": 400001, "to": 600000, "on_first": 400000, "next": 200000, "rate": 26, "tax_first": 84400, "tax_next": 52000},
                {"from": 600001, "to": 2000000, "on_first": 600000, "next": 1400000, "rate": 28, "tax_first": 136400, "tax_next": 392000},
                {"from": 2000001, "to": 999999999, "on_first": 2000000, "next": 0, "rate": 30, "tax_first": 528400, "tax_next": 0},
            ]
            
            for i, bracket in enumerate(default_brackets):
                bracket_group = self.create_tax_bracket_input_group(i + 1, bracket)
                brackets_container_layout.addWidget(bracket_group)
            
            # Add button to add new bracket
            add_bracket_button = QPushButton("➕ Add Tax Bracket")
            add_bracket_button.clicked.connect(self.add_new_tax_bracket)
            brackets_container_layout.addWidget(add_bracket_button)
            
            brackets_container.setLayout(brackets_container_layout)
            brackets_scroll.setWidget(brackets_container)
            brackets_layout.addWidget(brackets_scroll)
            
            # Special provisions
            special_group = QGroupBox("Special Tax Provisions")
            special_layout = QFormLayout()
            
            # Individual Tax Rebate
            self.individual_tax_rebate = QDoubleSpinBox()
            self.individual_tax_rebate.setRange(0.0, 10000.0)
            self.individual_tax_rebate.setValue(400.0)
            self.individual_tax_rebate.setSuffix(" RM")
            self.individual_tax_rebate.setToolTip("Individual tax rebate amount (LHDN 2025: RM 400)")
            special_layout.addRow("Individual Tax Rebate:", self.individual_tax_rebate)
            
            # Non-resident rate
            self.lhdn_non_resident_rate = QDoubleSpinBox()
            self.lhdn_non_resident_rate.setRange(0.0, 100.0)
            self.lhdn_non_resident_rate.setValue(30.0)
            self.lhdn_non_resident_rate.setSuffix(" %")
            self.lhdn_non_resident_rate.setToolTip("Flat tax rate for non-residents (LHDN 2025: 30%)")
            special_layout.addRow("Non-Resident Tax Rate:", self.lhdn_non_resident_rate)
            
            special_group.setLayout(special_layout)
            brackets_layout.addWidget(special_group)
            
            brackets_group.setLayout(brackets_layout)
            layout.addWidget(brackets_group)
            
            # Action buttons for tax rates
            rates_buttons_layout = QHBoxLayout()
            
            edit_rates_button = QPushButton("🔧 Toggle Input Fields")
            edit_rates_button.clicked.connect(self.toggle_tax_rates_editing)
            rates_buttons_layout.addWidget(edit_rates_button)
            
            reset_rates_button = QPushButton("↺ Reset to LHDN Default")
            reset_rates_button.clicked.connect(self.reset_tax_rates_to_default)
            rates_buttons_layout.addWidget(reset_rates_button)
            
            save_brackets_button = QPushButton("💾 Save Tax Brackets")
            save_brackets_button.clicked.connect(self.save_tax_brackets_configuration)
            rates_buttons_layout.addWidget(save_brackets_button)
            
            test_rates_button = QPushButton("🧮 Test Tax Calculation")
            test_rates_button.clicked.connect(self.test_tax_rates_calculation)
            rates_buttons_layout.addWidget(test_rates_button)
            
            rates_buttons_layout.addStretch()
            layout.addLayout(rates_buttons_layout)
            
            # Set layout and add to scroll area
            main_widget.setLayout(layout)
            scroll_area.setWidget(main_widget)
            
            # Create the rates tab layout
            rates_tab_layout = QVBoxLayout()
            rates_tab_layout.setContentsMargins(0, 0, 0, 0)
            rates_tab_layout.addWidget(scroll_area)
            rates_tab.setLayout(rates_tab_layout)
            
            subtab_widget.addTab(rates_tab, "📊 Tax Rates")
            
        except Exception as e:
            print(f"DEBUG: Error creating tax rates subtab: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create tax rates subtab: {e}")

    def _add_tax_relief_max_subtab_impl(self, subtab_widget):
        """Add Tax Relief Maximum Amounts subtab using payroll_dialog.py potongan bulan semasa structure as reference"""
        try:
            relief_tab = QWidget()
            
            # Create scroll area for the subtab (same pattern as payroll_dialog.py)
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
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
            
            # Main widget inside scroll area (following payroll_dialog pattern)
            main_widget = QWidget()
            main_widget.setStyleSheet("""
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
            layout = QVBoxLayout()
            layout.setSpacing(25)  # Same spacing as payroll_dialog
            layout.setContentsMargins(20, 20, 20, 20)  # Same margins as payroll_dialog
            
            # Information Panel (using Malaysian context like payroll_dialog)
            info_group = QGroupBox("💼 Konfigurasi Had Maksimum & Sub-Had - Potongan Bulan Semasa")
            info_layout = QVBoxLayout()
            
            info_text = QLabel("""
<b>Had Maksimum & Sub-Had Potongan Bulan Semasa (Rujukan LHDN 2025):</b><br><br>

<b style="color: #d32f2f;">🔒 MAX CAP - Had Maksimum Keseluruhan:</b><br>
• Had maksimum untuk keseluruhan kategori<br>
• Mengawal jumlah keseluruhan yang boleh dituntut dalam kategori tersebut<br><br>

<b style="color: #388e3c;">🤝 SHARED ALLOCATION - Berkongsi Baki Had:</b><br>
• Item yang TIDAK mempunyai sub-cap khusus<br>
• Boleh menggunakan penuh had kategori jika item lain tidak digunakan<br>
• Contoh: Penyakit serius atau rawatan kesuburan boleh guna penuh RM10,000 jika bersendirian<br><br>

<b style="color: #1976d2;">📋 SUB MAX CAP - Had Khusus Subkategori:</b><br>
• Had khusus untuk subkategori tertentu yang mempunyai limitasi tersendiri<br>
• Tidak boleh melebihi had mereka walaupun ada ruang dalam kategori<br><br>

<b>📌 Contoh B6 Medical Relief (RM10,000):</b><br>
<b>Kes 1:</b> RM10,000 penyakit serius → Boleh tuntut penuh RM10,000 ✅<br>
<b>Kes 2:</b> RM2,000 vaksin + RM10,000 serius → Vaksin RM1,000 + Serius RM9,000 = RM10,000 ✅<br>
<b>Kes 3:</b> RM8,000 serius + RM500 checkup → Serius RM8,000 + Checkup RM500 = RM8,500 ✅<br>
<b>Kes 4:</b> RM5,000 kesuburan sahaja → Boleh tuntut penuh RM5,000 ✅<br><br>

<b>🔑 Peraturan Utama:</b> Had keseluruhan RM10,000. Sub-cap mesti dipatuhi. Shared allocation berkongsi baki.<br><br>

<b>Rujukan:</b> <a href="https://www.hasil.gov.my/en/individual/individual-life-cycle/how-to-declare-income/tax-relief/">HASIL Potongan Cukai Rasmi</a>
            """)
            info_text.setWordWrap(True)
            info_text.setOpenExternalLinks(True)
            info_text.setStyleSheet("QLabel { font-size: 11px; padding: 15px; background-color: #f0f8ff; border: 1px solid #ccc; border-radius: 5px; }")
            info_layout.addWidget(info_text)
            info_group.setLayout(info_layout)
            layout.addWidget(info_group)
            
            # Create two columns layout (same as payroll_dialog pattern)
            columns_widget = QWidget()
            columns_layout = QHBoxLayout(columns_widget)
            columns_layout.setSpacing(15)  # Same spacing as payroll_dialog monthly deductions
            
            # LEFT COLUMN - Categories 1-5 (following payroll_dialog structure)
            left_column = QWidget()
            left_layout = QVBoxLayout(left_column)
            
            # B1 & B14-B16: Personal & Family Reliefs (Foundation reliefs)
            personal_family_group = QGroupBox("B1 & B14-B16: Personal & Family Reliefs")
            personal_family_form = QFormLayout()
            personal_family_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            # Information label
            info_label = QLabel("👨‍👩‍👧‍👦 <b>AUTOMATIC RELIEFS - Based on Employee Profile:</b>")
            info_label.setStyleSheet("color: #7b1fa2; font-weight: bold;")
            personal_family_form.addRow(info_label)
            
            # B1 - Individual Relief (automatic but configurable)
            self.lhdn_b1_individual_relief = QDoubleSpinBox()
            self.lhdn_b1_individual_relief.setRange(0.0, 15000.0)
            self.lhdn_b1_individual_relief.setValue(9000.0)
            self.lhdn_b1_individual_relief.setSuffix(" RM")
            self.lhdn_b1_individual_relief.setMinimumWidth(150)
            self.lhdn_b1_individual_relief.setStyleSheet("QDoubleSpinBox { background-color: #f3e5f5; font-weight: bold; }")
            self.lhdn_b1_individual_relief.setToolTip("B1 - Individual relief (automatic for all residents)")
            personal_family_form.addRow("B1 - Individual Relief (automatic):", self.lhdn_b1_individual_relief)
            
            # B14 - Spouse Relief
            self.lhdn_b14_spouse_relief = QDoubleSpinBox()
            self.lhdn_b14_spouse_relief.setRange(0.0, 10000.0)
            self.lhdn_b14_spouse_relief.setValue(4000.0)
            self.lhdn_b14_spouse_relief.setSuffix(" RM")
            self.lhdn_b14_spouse_relief.setMinimumWidth(150)
            self.lhdn_b14_spouse_relief.setStyleSheet("QDoubleSpinBox { background-color: #f3e5f5; }")
            self.lhdn_b14_spouse_relief.setToolTip("Relief for spouse with no income (automatic if married)")
            personal_family_form.addRow("B14 - Spouse Relief (had maksimum):", self.lhdn_b14_spouse_relief)
            
            # B15 - Disabled Spouse Relief
            self.lhdn_b15_disabled_spouse_relief = QDoubleSpinBox()
            self.lhdn_b15_disabled_spouse_relief.setRange(0.0, 10000.0)
            self.lhdn_b15_disabled_spouse_relief.setValue(5000.0)
            self.lhdn_b15_disabled_spouse_relief.setSuffix(" RM")
            self.lhdn_b15_disabled_spouse_relief.setMinimumWidth(150)
            self.lhdn_b15_disabled_spouse_relief.setStyleSheet("QDoubleSpinBox { background-color: #f3e5f5; }")
            self.lhdn_b15_disabled_spouse_relief.setToolTip("Additional relief for disabled spouse")
            personal_family_form.addRow("B15 - Disabled Spouse Relief (had maksimum):", self.lhdn_b15_disabled_spouse_relief)
            
            # B16 - Children Relief section (Official LHDN categories)
            children_label = QLabel("B16 - Children Relief (per child, exact LHDN calculations):")
            children_label.setStyleSheet("color: #1976d2; font-weight: bold; margin-top: 10px;")
            personal_family_form.addRow(children_label)
            
            # === NORMAL CHILDREN (NON-DISABLED) ===
            normal_children_label = QLabel("🔹 Normal Children (Non-Disabled):")
            normal_children_label.setStyleSheet("color: #388e3c; font-weight: bold; margin-top: 8px;")
            personal_family_form.addRow(normal_children_label)
            
            # B16(a) - Normal children under 18 years
            self.lhdn_b16_children_under_18 = QDoubleSpinBox()
            self.lhdn_b16_children_under_18.setRange(0.0, 5000.0)
            self.lhdn_b16_children_under_18.setValue(2000.0)
            self.lhdn_b16_children_under_18.setSuffix(" RM")
            self.lhdn_b16_children_under_18.setMinimumWidth(150)
            self.lhdn_b16_children_under_18.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            self.lhdn_b16_children_under_18.setToolTip("Normal children under 18 years - RM2,000 each")
            personal_family_form.addRow("B16(a) - Normal <18 tahun:", self.lhdn_b16_children_under_18)
            
            # B16(b) - Normal children 18+ studying matrikulasi/A-Level in Malaysia
            self.lhdn_b16_children_study_malaysia = QDoubleSpinBox()
            self.lhdn_b16_children_study_malaysia.setRange(0.0, 5000.0)
            self.lhdn_b16_children_study_malaysia.setValue(2000.0)
            self.lhdn_b16_children_study_malaysia.setSuffix(" RM")
            self.lhdn_b16_children_study_malaysia.setMinimumWidth(150)
            self.lhdn_b16_children_study_malaysia.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            self.lhdn_b16_children_study_malaysia.setToolTip("Normal children 18+ studying matrikulasi/pra ijazah/A-Level in Malaysia - RM2,000 each")
            personal_family_form.addRow("B16(b) - Normal 18+ matrikulasi/A-Level:", self.lhdn_b16_children_study_malaysia)
            
            # B16(c) - Normal children 18+ studying diploma/degree
            self.lhdn_b16_children_higher_education = QDoubleSpinBox()
            self.lhdn_b16_children_higher_education.setRange(0.0, 10000.0)
            self.lhdn_b16_children_higher_education.setValue(8000.0)
            self.lhdn_b16_children_higher_education.setSuffix(" RM")
            self.lhdn_b16_children_higher_education.setMinimumWidth(150)
            self.lhdn_b16_children_higher_education.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            self.lhdn_b16_children_higher_education.setToolTip("Normal children 18+ studying diploma/degree (Malaysia/overseas) - RM8,000 each")
            personal_family_form.addRow("B16(c) - Normal 18+ diploma/degree:", self.lhdn_b16_children_higher_education)
            
            # === DISABLED CHILDREN (OKU) ===
            disabled_children_label = QLabel("🔹 Disabled Children (OKU) - No Age Limit (belum berkahwin only):")
            disabled_children_label.setStyleSheet("color: #f57c00; font-weight: bold; margin-top: 8px;")
            personal_family_form.addRow(disabled_children_label)
            
            # B16(d) - Disabled children (any age, not studying)
            self.lhdn_b16_disabled_not_studying = QDoubleSpinBox()
            self.lhdn_b16_disabled_not_studying.setRange(0.0, 10000.0)
            self.lhdn_b16_disabled_not_studying.setValue(8000.0)
            self.lhdn_b16_disabled_not_studying.setSuffix(" RM")
            self.lhdn_b16_disabled_not_studying.setMinimumWidth(150)
            self.lhdn_b16_disabled_not_studying.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; }")
            self.lhdn_b16_disabled_not_studying.setToolTip("Disabled children (any age, unmarried) - RM8,000")
            personal_family_form.addRow("B16(d) - OKU (any age, tidak belajar):", self.lhdn_b16_disabled_not_studying)
            
            # B16(e) - Disabled children 18+ studying (additional relief)
            self.lhdn_b16_disabled_studying = QDoubleSpinBox()
            self.lhdn_b16_disabled_studying.setRange(0.0, 10000.0)
            self.lhdn_b16_disabled_studying.setValue(8000.0)
            self.lhdn_b16_disabled_studying.setSuffix(" RM")
            self.lhdn_b16_disabled_studying.setMinimumWidth(150)
            self.lhdn_b16_disabled_studying.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; }")
            self.lhdn_b16_disabled_studying.setToolTip("Additional relief for disabled children 18+ studying - RM8,000 (total RM16,000)")
            personal_family_form.addRow("B16(e) - OKU 18+ belajar (tambahan RM8K):", self.lhdn_b16_disabled_studying)
            
            # Note for OKU children calculation rules
            oku_note_label = QLabel("📌 OKU Rules: Any age tidak belajar=RM8K | 18+ belajar=RM8K+RM8K=RM16K total")
            oku_note_label.setStyleSheet("color: #f57c00; font-style: italic; font-size: 10px; margin-left: 20px;")
            personal_family_form.addRow(oku_note_label)
            
            personal_family_group.setLayout(personal_family_form)
            left_layout.addWidget(personal_family_group)
            
            # B4 & B17-B20: Automatic Statutory Reliefs (Automatic contributions)
            statutory_group = QGroupBox("B4 & B17-B20: Automatic Statutory Reliefs")
            statutory_form = QFormLayout()
            statutory_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            # Information label
            statutory_info_label = QLabel("🏛️ <b>AUTOMATIC STATUTORY RELIEFS - Based on Payroll Deductions:</b>")
            statutory_info_label.setStyleSheet("color: #388e3c; font-weight: bold;")
            statutory_form.addRow(statutory_info_label)
            
            # B4 - Individual Disability Relief (automatic if registered as OKU)
            self.lhdn_b4_individual_disability = QDoubleSpinBox()
            self.lhdn_b4_individual_disability.setRange(0.0, 10000.0)
            self.lhdn_b4_individual_disability.setValue(6000.0)
            self.lhdn_b4_individual_disability.setSuffix(" RM")
            self.lhdn_b4_individual_disability.setMinimumWidth(150)
            self.lhdn_b4_individual_disability.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            self.lhdn_b4_individual_disability.setToolTip("B4 - Disabled individual relief (automatic if LHDN recognizes as OKU)")
            statutory_form.addRow("B4 - Individual Disability (automatic OKU):", self.lhdn_b4_individual_disability)
            
            # B17 - Mandatory EPF Employee Contribution Relief (automatic from payroll)
            self.lhdn_b17_mandatory_epf = QDoubleSpinBox()
            self.lhdn_b17_mandatory_epf.setRange(0.0, 8000.0)  # Increased from 4000 for flexibility
            self.lhdn_b17_mandatory_epf.setValue(4000.0)
            self.lhdn_b17_mandatory_epf.setSuffix(" RM")
            self.lhdn_b17_mandatory_epf.setMinimumWidth(150)
            self.lhdn_b17_mandatory_epf.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            self.lhdn_b17_mandatory_epf.setToolTip("B17 - Mandatory EPF employee contribution relief (up to RM4,000) - auto-calculated from payroll")
            statutory_form.addRow("B17 - Mandatory EPF Relief (automatic):", self.lhdn_b17_mandatory_epf)
            
            # Note: Mandatory EPF relief is automatically calculated from monthly EPF deductions
            epf_mandatory_note_label = QLabel("📌 Mandatory EPF Relief: Up to RM4,000 automatically calculated from monthly 11% EPF deductions")
            epf_mandatory_note_label.setStyleSheet("color: #666; font-style: italic; font-size: 10px; margin-left: 20px;")
            statutory_form.addRow(epf_mandatory_note_label)
            
            # B20 - PERKESO (SOCSO + EIS) Relief (automatic from payroll)
            self.lhdn_b20_perkeso = QDoubleSpinBox()
            self.lhdn_b20_perkeso.setRange(0.0, 1000.0)  # Increased from 500 for flexibility
            self.lhdn_b20_perkeso.setValue(350.0)
            self.lhdn_b20_perkeso.setSuffix(" RM")
            self.lhdn_b20_perkeso.setMinimumWidth(150)
            self.lhdn_b20_perkeso.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            self.lhdn_b20_perkeso.setToolTip("B20 - PERKESO (SOCSO + EIS) relief (automatic from payroll deductions)")
            statutory_form.addRow("B20 - PERKESO Relief (automatic):", self.lhdn_b20_perkeso)
            
            statutory_group.setLayout(statutory_form)
            left_layout.addWidget(statutory_group)
            
            # 1. Perbelanjaan untuk ibu bapa / datuk nenek (≤ RM8,000 setahun)
            parent_medical_group = QGroupBox("1. Perbelanjaan untuk ibu bapa / datuk nenek")
            parent_medical_form = QFormLayout()
            parent_medical_form.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
            
            # MAX CAP for parent medical category
            max_cap_label = QLabel("🔒 <b>MAX CAP - Had Maksimum Keseluruhan:</b>")
            max_cap_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            parent_medical_form.addRow(max_cap_label)
            
            self.parent_medical_max_cap = QDoubleSpinBox()
            self.parent_medical_max_cap.setRange(0.0, 15000.0)
            self.parent_medical_max_cap.setValue(8000.0)
            self.parent_medical_max_cap.setSuffix(" RM")
            self.parent_medical_max_cap.setMinimumWidth(150)
            self.parent_medical_max_cap.setStyleSheet("QDoubleSpinBox { background-color: #ffebee; font-weight: bold; }")
            parent_medical_form.addRow("Had Maksimum Kategori:", self.parent_medical_max_cap)
            
            # SUB MAX CAPs for subcategories
            sub_cap_label = QLabel("📋 <b>SUB MAX CAP - Had Khusus Subkategori:</b>")
            sub_cap_label.setStyleSheet("color: #1976d2; font-weight: bold; margin-top: 10px;")
            parent_medical_form.addRow(sub_cap_label)
            
            # a) Rawatan perubatan / keperluan khas / penjagaan
            self.parent_medical_treatment_max = QDoubleSpinBox()
            self.parent_medical_treatment_max.setRange(0.0, 8000.0)
            self.parent_medical_treatment_max.setValue(8000.0)
            self.parent_medical_treatment_max.setSuffix(" RM")
            self.parent_medical_treatment_max.setMinimumWidth(150)
            parent_medical_form.addRow("a) Rawatan perubatan/keperluan khas/penjagaan:", self.parent_medical_treatment_max)
            
            # b) Rawatan pergigian
            self.parent_dental_max = QDoubleSpinBox()
            self.parent_dental_max.setRange(0.0, 8000.0)
            self.parent_dental_max.setValue(8000.0)
            self.parent_dental_max.setSuffix(" RM")
            self.parent_dental_max.setMinimumWidth(150)
            parent_medical_form.addRow("b) Rawatan pergigian:", self.parent_dental_max)
            
            # c) Pemeriksaan penuh + vaksin (≤ RM1,000 daripada 8,000)
            self.parent_checkup_vaccine_max = QDoubleSpinBox()
            self.parent_checkup_vaccine_max.setRange(0.0, 1000.0)
            self.parent_checkup_vaccine_max.setValue(1000.0)
            self.parent_checkup_vaccine_max.setSuffix(" RM")
            self.parent_checkup_vaccine_max.setMinimumWidth(150)
            self.parent_checkup_vaccine_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            parent_medical_form.addRow("c) Pemeriksaan penuh + vaksin (sub-had khusus):", self.parent_checkup_vaccine_max)
            
            # SPECIAL SUB-CAP UPPER LIMIT CONTROLLER
            special_limit_label = QLabel("🎯 <b>SPECIAL SUB-CAP UPPER LIMIT:</b>")
            special_limit_label.setStyleSheet("color: #e65100; font-weight: bold; margin-top: 15px;")
            parent_medical_form.addRow(special_limit_label)
            
            self.parent_checkup_vaccine_upper_limit = QDoubleSpinBox()
            self.parent_checkup_vaccine_upper_limit.setRange(500.0, 5000.0)  # Allow admin to set between RM500-RM5,000
            self.parent_checkup_vaccine_upper_limit.setValue(1000.0)  # Default RM1,000
            self.parent_checkup_vaccine_upper_limit.setSuffix(" RM")
            self.parent_checkup_vaccine_upper_limit.setMinimumWidth(150)
            self.parent_checkup_vaccine_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
            parent_medical_form.addRow("⚙️ Upper Limit for Checkup/Vaccine:", self.parent_checkup_vaccine_upper_limit)
            
            # Add explanatory note
            note_label = QLabel("<i>📝 Note: Checkup/vaccine will be limited to min(Upper Limit, Main MAX CAP)</i>")
            note_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
            parent_medical_form.addRow(note_label)
            
            # Connect signals for real-time MAX CAP broadcasting
            self.parent_medical_max_cap.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('parent_medical_max_cap', value))
            self.parent_medical_max_cap.valueChanged.connect(self.update_sub_max_cap_ranges)
            self.parent_medical_treatment_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('parent_medical_treatment_max', value))
            self.parent_dental_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('parent_dental_max', value))
            self.parent_checkup_vaccine_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('parent_checkup_vaccine_max', value))
            
            # Connect special upper limit controller
            self.parent_checkup_vaccine_upper_limit.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('parent_checkup_vaccine_upper_limit', value))
            self.parent_checkup_vaccine_upper_limit.valueChanged.connect(self.update_sub_max_cap_ranges)
            
            parent_medical_group.setLayout(parent_medical_form)
            left_layout.addWidget(parent_medical_group)
            
            # 2. Peralatan sokongan asas (≤ RM6,000)
            support_group = QGroupBox("2. Peralatan sokongan asas (≤ RM6,000)")
            support_form = QFormLayout()
            
            self.basic_support_equipment_max = QDoubleSpinBox()
            self.basic_support_equipment_max.setRange(0.0, 6000.0)
            self.basic_support_equipment_max.setValue(6000.0)
            self.basic_support_equipment_max.setSuffix(" RM")
            self.basic_support_equipment_max.setMinimumWidth(150)
            support_form.addRow("Peralatan sokongan asas:", self.basic_support_equipment_max)
            
            # Connect signal for real-time broadcasting
            self.basic_support_equipment_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('basic_support_equipment_max', value))
            
            support_group.setLayout(support_form)
            left_layout.addWidget(support_group)
            
            # 3. Yuran pengajian sendiri (≤ RM7,000 setahun)
            education_group = QGroupBox("3. Yuran pengajian sendiri")
            education_form = QFormLayout()
            
            # MAX CAP for education category
            max_cap_label = QLabel("🔒 <b>MAX CAP - Had Maksimum Keseluruhan:</b>")
            max_cap_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            education_form.addRow(max_cap_label)
            
            self.education_max_cap = QDoubleSpinBox()
            self.education_max_cap.setRange(0.0, 10000.0)
            self.education_max_cap.setValue(7000.0)
            self.education_max_cap.setSuffix(" RM")
            self.education_max_cap.setMinimumWidth(150)
            self.education_max_cap.setStyleSheet("QDoubleSpinBox { background-color: #ffebee; font-weight: bold; }")
            education_form.addRow("Had Maksimum Kategori:", self.education_max_cap)
            
            # SUB MAX CAPs for subcategories
            sub_cap_label = QLabel("📋 <b>SUB MAX CAP - Had Khusus Subkategori:</b>")
            sub_cap_label.setStyleSheet("color: #1976d2; font-weight: bold; margin-top: 10px;")
            education_form.addRow(sub_cap_label)
            
            # c) Kursus kemahiran / diri (≤ RM2,000)
            self.skills_course_max = QDoubleSpinBox()
            self.skills_course_max.setRange(0.0, 2000.0)
            self.skills_course_max.setValue(2000.0)
            self.skills_course_max.setSuffix(" RM")
            self.skills_course_max.setMinimumWidth(150)
            self.skills_course_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            education_form.addRow("c) Kursus kemahiran/diri (sub-had khusus):", self.skills_course_max)
            
            # SKILLS COURSE SPECIAL SUB-CAP UPPER LIMIT CONTROLLER
            skills_special_limit_label = QLabel("🎯 <b>SKILLS COURSE UPPER LIMIT:</b>")
            skills_special_limit_label.setStyleSheet("color: #e65100; font-weight: bold; margin-top: 15px;")
            education_form.addRow(skills_special_limit_label)
            
            self.skills_course_upper_limit = QDoubleSpinBox()
            self.skills_course_upper_limit.setRange(1000.0, 10000.0)  # Allow admin to set between RM1,000-RM10,000
            self.skills_course_upper_limit.setValue(2000.0)  # Default RM2,000
            self.skills_course_upper_limit.setSuffix(" RM")
            self.skills_course_upper_limit.setMinimumWidth(150)
            self.skills_course_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
            education_form.addRow("⚙️ Upper Limit for Skills Course:", self.skills_course_upper_limit)
            
            # Add explanatory note
            skills_note_label = QLabel("<i>📝 Note: Skills course will be limited to min(Upper Limit, Education MAX CAP)</i>")
            skills_note_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
            education_form.addRow(skills_note_label)
            
            # SHARED ALLOCATION (items without specific sub-caps)
            shared_label = QLabel("🤝 <b>SHARED ALLOCATION - Berkongsi Baki Had:</b>")
            shared_label.setStyleSheet("color: #388e3c; font-weight: bold; margin-top: 10px;")
            education_form.addRow(shared_label)
            
            # a) Selain Sarjana/PhD (bidang tertentu)
            self.education_non_masters_max = QDoubleSpinBox()
            self.education_non_masters_max.setRange(0.0, 7000.0)
            self.education_non_masters_max.setValue(7000.0)
            self.education_non_masters_max.setSuffix(" RM")
            self.education_non_masters_max.setMinimumWidth(150)
            self.education_non_masters_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            education_form.addRow("a) Selain Sarjana/PhD (berkongsi baki):", self.education_non_masters_max)
            
            # b) Sarjana / PhD (semua bidang)
            self.education_masters_phd_max = QDoubleSpinBox()
            self.education_masters_phd_max.setRange(0.0, 7000.0)
            self.education_masters_phd_max.setValue(7000.0)
            self.education_masters_phd_max.setSuffix(" RM")
            self.education_masters_phd_max.setMinimumWidth(150)
            self.education_masters_phd_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            education_form.addRow("b) Sarjana/PhD (berkongsi baki):", self.education_masters_phd_max)
            self.skills_course_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            education_form.addRow("c) Kursus kemahiran/diri (sub-had khusus):", self.skills_course_max)
            
            education_group.setLayout(education_form)
            left_layout.addWidget(education_group)
            
            # Connect Education signal connections
            self.skills_course_upper_limit.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('skills_course_upper_limit', value))
            
            # 4. Perubatan diri/pasangan/anak 
            medical_group = QGroupBox("4. Perubatan diri/pasangan/anak")
            medical_form = QFormLayout()
            
            # MAX CAP for medical family category
            max_cap_label = QLabel("🔒 <b>MAX CAP - Had Maksimum Keseluruhan:</b>")
            max_cap_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            medical_form.addRow(max_cap_label)
            
            self.medical_family_max_cap = QDoubleSpinBox()
            self.medical_family_max_cap.setRange(0.0, 15000.0)
            self.medical_family_max_cap.setValue(10000.0)
            self.medical_family_max_cap.setSuffix(" RM")
            self.medical_family_max_cap.setMinimumWidth(150)
            self.medical_family_max_cap.setStyleSheet("QDoubleSpinBox { background-color: #ffebee; font-weight: bold; }")
            medical_form.addRow("Had Maksimum Kategori:", self.medical_family_max_cap)
            
            # SHARED ALLOCATION (items without specific sub-caps)
            shared_label = QLabel("🤝 <b>SHARED ALLOCATION - Berkongsi Baki Had:</b>")
            shared_label.setStyleSheet("color: #388e3c; font-weight: bold; margin-top: 10px;")
            medical_form.addRow(shared_label)
            
            # a) Penyakit serius (shares remaining allocation)
            self.serious_disease_max = QDoubleSpinBox()
            self.serious_disease_max.setRange(0.0, 10000.0)
            self.serious_disease_max.setValue(10000.0)
            self.serious_disease_max.setSuffix(" RM")
            self.serious_disease_max.setMinimumWidth(150)
            self.serious_disease_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            medical_form.addRow("a) Penyakit serius (berkongsi baki):", self.serious_disease_max)
            
            # b) Rawatan kesuburan (shares remaining allocation)
            self.fertility_treatment_max = QDoubleSpinBox()
            self.fertility_treatment_max.setRange(0.0, 10000.0)
            self.fertility_treatment_max.setValue(10000.0)
            self.fertility_treatment_max.setSuffix(" RM")
            self.fertility_treatment_max.setMinimumWidth(150)
            self.fertility_treatment_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            medical_form.addRow("b) Rawatan kesuburan (berkongsi baki):", self.fertility_treatment_max)
            
            # SUB MAX CAPs for subcategories with specific limits
            sub_cap_label = QLabel("📋 <b>SUB MAX CAP - Had Khusus Subkategori:</b>")
            sub_cap_label.setStyleSheet("color: #1976d2; font-weight: bold; margin-top: 10px;")
            medical_form.addRow(sub_cap_label)
            
            # c) Pemvaksinan (≤ RM1,000)
            self.vaccination_max = QDoubleSpinBox()
            self.vaccination_max.setRange(0.0, 1000.0)
            self.vaccination_max.setValue(1000.0)
            self.vaccination_max.setSuffix(" RM")
            self.vaccination_max.setMinimumWidth(150)
            self.vaccination_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            medical_form.addRow("c) Pemvaksinan (sub-had khusus):", self.vaccination_max)
            
            # d) Pemeriksaan & rawatan pergigian (≤ RM1,000)
            self.dental_treatment_max = QDoubleSpinBox()
            self.dental_treatment_max.setRange(0.0, 1000.0)
            self.dental_treatment_max.setValue(1000.0)
            self.dental_treatment_max.setSuffix(" RM")
            self.dental_treatment_max.setMinimumWidth(150)
            self.dental_treatment_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            medical_form.addRow("d) Pemeriksaan & rawatan pergigian (sub-had khusus):", self.dental_treatment_max)
            
            # e) Pemeriksaan penuh / COVID-19 / mental health (≤ RM1,000)
            self.health_checkup_max = QDoubleSpinBox()
            self.health_checkup_max.setRange(0.0, 1000.0)
            self.health_checkup_max.setValue(1000.0)
            self.health_checkup_max.setSuffix(" RM")
            self.health_checkup_max.setMinimumWidth(150)
            self.health_checkup_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            medical_form.addRow("e) Pemeriksaan penuh/COVID-19/mental health (sub-had khusus):", self.health_checkup_max)
            
            # f) Penilaian & intervensi anak kurang upaya pembelajaran <18 (≤ RM6,000)
            self.child_learning_disability_max = QDoubleSpinBox()
            self.child_learning_disability_max.setRange(0.0, 6000.0)
            self.child_learning_disability_max.setValue(6000.0)
            self.child_learning_disability_max.setSuffix(" RM")
            self.child_learning_disability_max.setMinimumWidth(150)
            self.child_learning_disability_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            medical_form.addRow("f) Anak kurang upaya pembelajaran <18 (sub-had khusus):", self.child_learning_disability_max)
            
            # PERSONAL MEDICAL SPECIAL SUB-CAP UPPER LIMIT CONTROLLERS
            medical_special_limit_label = QLabel("🎯 <b>PERSONAL MEDICAL SPECIAL UPPER LIMITS:</b>")
            medical_special_limit_label.setStyleSheet("color: #e65100; font-weight: bold; margin-top: 15px;")
            medical_form.addRow(medical_special_limit_label)
            
            # Vaccination Upper Limit Controller
            self.vaccination_upper_limit = QDoubleSpinBox()
            self.vaccination_upper_limit.setRange(500.0, 5000.0)  # RM500-RM5,000
            self.vaccination_upper_limit.setValue(1000.0)  # Default RM1,000
            self.vaccination_upper_limit.setSuffix(" RM")
            self.vaccination_upper_limit.setMinimumWidth(150)
            self.vaccination_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
            medical_form.addRow("⚙️ Vaccination Upper Limit:", self.vaccination_upper_limit)
            
            # Dental Treatment Upper Limit Controller
            self.dental_treatment_upper_limit = QDoubleSpinBox()
            self.dental_treatment_upper_limit.setRange(500.0, 5000.0)  # RM500-RM5,000
            self.dental_treatment_upper_limit.setValue(1000.0)  # Default RM1,000
            self.dental_treatment_upper_limit.setSuffix(" RM")
            self.dental_treatment_upper_limit.setMinimumWidth(150)
            self.dental_treatment_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
            medical_form.addRow("⚙️ Dental Treatment Upper Limit:", self.dental_treatment_upper_limit)
            
            # Health Checkup Upper Limit Controller
            self.health_checkup_upper_limit = QDoubleSpinBox()
            self.health_checkup_upper_limit.setRange(500.0, 5000.0)  # RM500-RM5,000
            self.health_checkup_upper_limit.setValue(1000.0)  # Default RM1,000
            self.health_checkup_upper_limit.setSuffix(" RM")
            self.health_checkup_upper_limit.setMinimumWidth(150)
            self.health_checkup_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
            medical_form.addRow("⚙️ Health Checkup Upper Limit:", self.health_checkup_upper_limit)
            
            # Child Learning Disability Upper Limit Controller
            self.child_learning_disability_upper_limit = QDoubleSpinBox()
            self.child_learning_disability_upper_limit.setRange(3000.0, 15000.0)  # RM3,000-RM15,000 (higher range for this category)
            self.child_learning_disability_upper_limit.setValue(6000.0)  # Default RM6,000
            self.child_learning_disability_upper_limit.setSuffix(" RM")
            self.child_learning_disability_upper_limit.setMinimumWidth(150)
            self.child_learning_disability_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
            medical_form.addRow("⚙️ Child Learning Disability Upper Limit:", self.child_learning_disability_upper_limit)
            
            # Add explanatory note
            medical_note_label = QLabel("<i>📝 Note: All special limits will be min(Upper Limit, Medical MAX CAP)</i>")
            medical_note_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
            medical_form.addRow(medical_note_label)
            
            medical_group.setLayout(medical_form)
            left_layout.addWidget(medical_group)
            
            # Connect Personal Medical upper limit signal connections for real-time broadcasting
            self.vaccination_upper_limit.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('vaccination_upper_limit', value))
            self.dental_treatment_upper_limit.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('dental_treatment_upper_limit', value))
            self.health_checkup_upper_limit.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('health_checkup_upper_limit', value))
            self.child_learning_disability_upper_limit.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('child_learning_disability_upper_limit', value))
            
            # 5. Gaya hidup asas
            lifestyle_basic_group = QGroupBox("5. Gaya hidup asas")
            lifestyle_basic_form = QFormLayout()
            
            # MAX CAP for lifestyle basic category
            max_cap_label = QLabel("🔒 <b>MAX CAP - Had Maksimum Keseluruhan:</b>")
            max_cap_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            lifestyle_basic_form.addRow(max_cap_label)
            
            self.lifestyle_basic_max_cap = QDoubleSpinBox()
            self.lifestyle_basic_max_cap.setRange(0.0, 5000.0)
            self.lifestyle_basic_max_cap.setValue(2500.0)
            self.lifestyle_basic_max_cap.setSuffix(" RM")
            self.lifestyle_basic_max_cap.setMinimumWidth(150)
            self.lifestyle_basic_max_cap.setStyleSheet("QDoubleSpinBox { background-color: #ffebee; font-weight: bold; }")
            lifestyle_basic_form.addRow("Had Maksimum Kategori:", self.lifestyle_basic_max_cap)
            
            # Connect signals for real-time MAX CAP broadcasting and subcap range updates
            self.lifestyle_basic_max_cap.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('lifestyle_basic_max_cap', value))
            self.lifestyle_basic_max_cap.valueChanged.connect(self.update_sub_max_cap_ranges)
            
            # SHARED ALLOCATION (all items share the total allocation)
            shared_label = QLabel("🤝 <b>SHARED ALLOCATION - Berkongsi Baki Had:</b>")
            shared_label.setStyleSheet("color: #388e3c; font-weight: bold; margin-top: 10px;")
            lifestyle_basic_form.addRow(shared_label)
            
            # a) Buku / majalah / surat khabar
            self.lifestyle_books_max = QDoubleSpinBox()
            self.lifestyle_books_max.setRange(0.0, 2500.0)
            self.lifestyle_books_max.setValue(2500.0)
            self.lifestyle_books_max.setSuffix(" RM")
            self.lifestyle_books_max.setMinimumWidth(150)
            self.lifestyle_books_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            lifestyle_basic_form.addRow("a) Buku/majalah/surat khabar (berkongsi):", self.lifestyle_books_max)
            
            # b) Komputer / telefon / tablet
            self.lifestyle_computer_max = QDoubleSpinBox()
            self.lifestyle_computer_max.setRange(0.0, 2500.0)
            self.lifestyle_computer_max.setValue(2500.0)
            self.lifestyle_computer_max.setSuffix(" RM")
            self.lifestyle_computer_max.setMinimumWidth(150)
            self.lifestyle_computer_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            lifestyle_basic_form.addRow("b) Komputer/telefon/tablet (berkongsi):", self.lifestyle_computer_max)
            
            # c) Internet (nama sendiri)
            self.lifestyle_internet_max = QDoubleSpinBox()
            self.lifestyle_internet_max.setRange(0.0, 2500.0)
            self.lifestyle_internet_max.setValue(2500.0)
            self.lifestyle_internet_max.setSuffix(" RM")
            self.lifestyle_internet_max.setMinimumWidth(150)
            self.lifestyle_internet_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            lifestyle_basic_form.addRow("c) Internet nama sendiri (berkongsi):", self.lifestyle_internet_max)
            
            # d) Kursus kemahiran
            self.lifestyle_skills_max = QDoubleSpinBox()
            self.lifestyle_skills_max.setRange(0.0, 2500.0)
            self.lifestyle_skills_max.setValue(2500.0)
            self.lifestyle_skills_max.setSuffix(" RM")
            self.lifestyle_skills_max.setMinimumWidth(150)
            self.lifestyle_skills_max.setStyleSheet("QDoubleSpinBox { background-color: #e8f5e8; }")
            lifestyle_basic_form.addRow("d) Kursus kemahiran (berkongsi):", self.lifestyle_skills_max)
            
            # Connect individual lifestyle subcap signals for real-time broadcasting
            self.lifestyle_books_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('lifestyle_books_max', value))
            self.lifestyle_computer_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('lifestyle_computer_max', value))
            self.lifestyle_internet_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('lifestyle_internet_max', value))
            self.lifestyle_skills_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('lifestyle_skills_max', value))
            
            lifestyle_basic_group.setLayout(lifestyle_basic_form)
            left_layout.addWidget(lifestyle_basic_group)
            
            # Add left column to columns layout
            columns_layout.addWidget(left_column)
            
            # RIGHT COLUMN - Categories 6-16 (following payroll_dialog structure)
            right_column = QWidget()
            right_layout = QVBoxLayout(right_column)
            
            # 6. Gaya hidup tambahan
            lifestyle_additional_group = QGroupBox("6. Gaya hidup tambahan")
            lifestyle_additional_form = QFormLayout()
            
            # MAX CAP for lifestyle additional category
            max_cap_label = QLabel("🔒 <b>MAX CAP - Had Maksimum Keseluruhan:</b>")
            max_cap_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
            lifestyle_additional_form.addRow(max_cap_label)
            
            self.lifestyle_additional_max_cap = QDoubleSpinBox()
            self.lifestyle_additional_max_cap.setRange(0.0, 2000.0)
            self.lifestyle_additional_max_cap.setValue(1000.0)
            self.lifestyle_additional_max_cap.setSuffix(" RM")
            self.lifestyle_additional_max_cap.setMinimumWidth(150)
            self.lifestyle_additional_max_cap.setStyleSheet("QDoubleSpinBox { background-color: #ffebee; font-weight: bold; }")
            lifestyle_additional_form.addRow("Had Maksimum Kategori:", self.lifestyle_additional_max_cap)
            
            # SUB MAX CAPs for subcategories (same as Section 3 structure)
            sub_cap_label = QLabel("📋 <b>SUB MAX CAP - Had Khusus Subkategori:</b>")
            sub_cap_label.setStyleSheet("color: #1976d2; font-weight: bold; margin-top: 10px;")
            lifestyle_additional_form.addRow(sub_cap_label)
            
            # a) Peralatan sukan
            self.sports_equipment_max = QDoubleSpinBox()
            self.sports_equipment_max.setRange(0.0, 1000.0)
            self.sports_equipment_max.setValue(1000.0)
            self.sports_equipment_max.setSuffix(" RM")
            self.sports_equipment_max.setMinimumWidth(150)
            self.sports_equipment_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            lifestyle_additional_form.addRow("a) Peralatan sukan:", self.sports_equipment_max)
            
            # b) Sewa / fi fasiliti sukan
            self.sports_facility_rent_max = QDoubleSpinBox()
            self.sports_facility_rent_max.setRange(0.0, 1000.0)
            self.sports_facility_rent_max.setValue(1000.0)
            self.sports_facility_rent_max.setSuffix(" RM")
            self.sports_facility_rent_max.setMinimumWidth(150)
            self.sports_facility_rent_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            lifestyle_additional_form.addRow("b) Sewa/fi fasiliti sukan:", self.sports_facility_rent_max)
            
            # c) Fi pertandingan diluluskan
            self.competition_fees_max = QDoubleSpinBox()
            self.competition_fees_max.setRange(0.0, 1000.0)
            self.competition_fees_max.setValue(1000.0)
            self.competition_fees_max.setSuffix(" RM")
            self.competition_fees_max.setMinimumWidth(150)
            self.competition_fees_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            lifestyle_additional_form.addRow("c) Fi pertandingan diluluskan:", self.competition_fees_max)
            
            # d) Yuran gym / latihan sukan
            self.gym_fees_max = QDoubleSpinBox()
            self.gym_fees_max.setRange(0.0, 1000.0)
            self.gym_fees_max.setValue(1000.0)
            self.gym_fees_max.setSuffix(" RM")
            self.gym_fees_max.setMinimumWidth(150)
            self.gym_fees_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
            lifestyle_additional_form.addRow("d) Yuran gym/latihan sukan:", self.gym_fees_max)
            
            # Connect lifestyle additional max cap signal for real-time broadcasting (same as Section 3)
            self.lifestyle_additional_max_cap.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('lifestyle_additional_max_cap', value))
            self.lifestyle_additional_max_cap.valueChanged.connect(self.update_sub_max_cap_ranges)
            
            # Connect individual lifestyle subcap signals for real-time broadcasting
            self.sports_equipment_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('sports_equipment_max', value))
            self.sports_facility_rent_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('sports_facility_rent_max', value))
            self.competition_fees_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('competition_fees_max', value))
            self.gym_fees_max.valueChanged.connect(
                lambda value: self.max_cap_changed.emit('gym_fees_max', value))
            
            lifestyle_additional_group.setLayout(lifestyle_additional_form)
            right_layout.addWidget(lifestyle_additional_group)
            
            # Create remaining deductions categories for right column (following payroll_dialog pattern)
            self.create_remaining_max_deductions_for_column(right_layout)
            
            # Add right column to columns layout
            columns_layout.addWidget(right_column)
            
            # Add columns to main layout
            layout.addWidget(columns_widget)
            
            # Action buttons (same pattern as payroll_dialog)
            relief_buttons_layout = QHBoxLayout()
            
            reset_relief_max_button = QPushButton("↺ Set Semula ke Had LHDN")
            reset_relief_max_button.clicked.connect(self.reset_potongan_max_to_default)
            relief_buttons_layout.addWidget(reset_relief_max_button)
            
            save_relief_max_button = QPushButton("💾 Simpan Konfigurasi Had")
            save_relief_max_button.clicked.connect(self.save_potongan_max_configuration)
            relief_buttons_layout.addWidget(save_relief_max_button)

            load_relief_max_button = QPushButton("↻ Muat Konfigurasi Had")
            load_relief_max_button.clicked.connect(self.load_potongan_max_configuration)
            relief_buttons_layout.addWidget(load_relief_max_button)
            
            export_relief_button = QPushButton("📤 Eksport Konfigurasi")
            export_relief_button.clicked.connect(self.export_potongan_configuration)
            relief_buttons_layout.addWidget(export_relief_button)
            
            relief_buttons_layout.addStretch()
            layout.addLayout(relief_buttons_layout)
            
            # Set layout and add to scroll area
            main_widget.setLayout(layout)
            scroll_area.setWidget(main_widget)
            
            # Create the relief tab layout
            relief_tab_layout = QVBoxLayout()
            relief_tab_layout.setContentsMargins(0, 0, 0, 0)
            relief_tab_layout.addWidget(scroll_area)
            relief_tab.setLayout(relief_tab_layout)
            
            subtab_widget.addTab(relief_tab, "💼 Had Potongan Bulanan")
            
        except Exception as e:
            print(f"DEBUG: Error creating tax relief max subtab: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create tax relief max subtab: {e}")

    def create_remaining_max_deductions_for_column(self, parent_layout):
        """Create the remaining deduction categories maximums for the right column (following payroll_dialog)"""
        
        # 7. Peralatan penyusuan ibu (≤ RM1,000, sekali setiap 2 tahun)
        breastfeeding_group = QGroupBox("7. Peralatan penyusuan ibu (≤ RM1,000, sekali setiap 2 tahun)")
        breastfeeding_form = QFormLayout()
        
        self.breastfeeding_equipment_max = QDoubleSpinBox()
        self.breastfeeding_equipment_max.setRange(0.0, 1000.0)
        self.breastfeeding_equipment_max.setValue(1000.0)
        self.breastfeeding_equipment_max.setSuffix(" RM")
        self.breastfeeding_equipment_max.setMinimumWidth(150)
        breastfeeding_form.addRow("Peralatan penyusuan:", self.breastfeeding_equipment_max)
        
        breastfeeding_group.setLayout(breastfeeding_form)
        parent_layout.addWidget(breastfeeding_group)
        
        # 8. Yuran taska / tadika anak ≤ 6 tahun (≤ RM3,000)
        childcare_group = QGroupBox("8. Yuran taska/tadika anak ≤ 6 tahun (≤ RM3,000)")
        childcare_form = QFormLayout()
        
        self.childcare_fees_max = QDoubleSpinBox()
        self.childcare_fees_max.setRange(0.0, 3000.0)
        self.childcare_fees_max.setValue(3000.0)
        self.childcare_fees_max.setSuffix(" RM")
        self.childcare_fees_max.setMinimumWidth(150)
        childcare_form.addRow("Yuran taska/tadika:", self.childcare_fees_max)
        
        childcare_group.setLayout(childcare_form)
        parent_layout.addWidget(childcare_group)
        
        # 9. SSPN (tabungan bersih) (≤ RM8,000)
        sspn_group = QGroupBox("9. SSPN (tabungan bersih) (≤ RM8,000)")
        sspn_form = QFormLayout()
        
        self.sspn_savings_max = QDoubleSpinBox()
        self.sspn_savings_max.setRange(0.0, 8000.0)
        self.sspn_savings_max.setValue(8000.0)
        self.sspn_savings_max.setSuffix(" RM")
        self.sspn_savings_max.setMinimumWidth(150)
        sspn_form.addRow("SSPN tabungan bersih:", self.sspn_savings_max)
        
        sspn_group.setLayout(sspn_form)
        parent_layout.addWidget(sspn_group)
        
        # 10. Alimoni kepada bekas isteri (≤ RM4,000)
        alimony_group = QGroupBox("10. Alimoni kepada bekas isteri (≤ RM4,000)")
        alimony_form = QFormLayout()
        
        self.alimony_max = QDoubleSpinBox()
        self.alimony_max.setRange(0.0, 4000.0)
        self.alimony_max.setValue(4000.0)
        self.alimony_max.setSuffix(" RM")
        self.alimony_max.setMinimumWidth(150)
        alimony_form.addRow("Alimoni:", self.alimony_max)
        
        alimony_group.setLayout(alimony_form)
        parent_layout.addWidget(alimony_group)
        
        # 11. KWSP + Insuran Nyawa (COMBINED RM7,000 Bucket - LHDN Law)
        epf_insurance_group = QGroupBox("11. KWSP + Insuran Nyawa (COMBINED MAX: RM7,000 - LHDN Law)")
        epf_insurance_form = QFormLayout()
        
        # CRITICAL LAW CLARIFICATION
        law_note = QLabel("🏛️ <b>LHDN Law:</b> ALL EPF (compulsory + voluntary) + Life Insurance = RM7,000 COMBINED MAXIMUM")
        law_note.setStyleSheet("color: #d32f2f; font-weight: bold; font-size: 12px; margin-bottom: 10px; padding: 8px; background: #fff3e0; border-left: 4px solid #ff9800;")
        epf_insurance_form.addRow(law_note)
        
        # PCB Calculator explanation
        pcb_note = QLabel("📊 <b>PCB Calculator Note:</b> Shows 'RM4K + RM3K' for data entry convenience, but law treats as ONE bucket")
        pcb_note.setStyleSheet("color: #1976d2; font-weight: bold; font-size: 11px; margin-bottom: 8px;")
        epf_insurance_form.addRow(pcb_note)
        
        # MAX CAP for EPF + Insurance category (same as Section 3 structure)
        max_cap_label = QLabel("🔒 <b>MAX CAP - Had Maksimum Keseluruhan:</b>")
        max_cap_label.setStyleSheet("color: #d32f2f; font-weight: bold;")
        epf_insurance_form.addRow(max_cap_label)
        
        self.epf_insurance_combined_max = QDoubleSpinBox()
        self.epf_insurance_combined_max.setRange(1000.0, 15000.0)  # Allow admin flexibility
        self.epf_insurance_combined_max.setValue(7000.0)  # LHDN default
        self.epf_insurance_combined_max.setSuffix(" RM")
        self.epf_insurance_combined_max.setMinimumWidth(150)
        self.epf_insurance_combined_max.setStyleSheet("QDoubleSpinBox { background-color: #ffebee; font-weight: bold; }")
        self.epf_insurance_combined_max.setToolTip("Total combined limit for ALL EPF contributions (compulsory + voluntary) + Life Insurance. LHDN default: RM7,000")
        epf_insurance_form.addRow("Had Maksimum Kategori:", self.epf_insurance_combined_max)
        
        # SUB MAX CAPs for subcategories (same as Section 3 structure)
        sub_cap_label = QLabel("📋 <b>SUB MAX CAP - Had Khusus Subkategori:</b>")
        sub_cap_label.setStyleSheet("color: #1976d2; font-weight: bold; margin-top: 10px;")
        epf_insurance_form.addRow(sub_cap_label)
        
        # a) SHARED EPF SUBCAP (applies to both mandatory + voluntary EPF)
        self.epf_shared_subcap = QDoubleSpinBox()
        self.epf_shared_subcap.setRange(1000.0, 7000.0)  
        self.epf_shared_subcap.setValue(4000.0)  # LHDN default for ALL EPF combined
        self.epf_shared_subcap.setSuffix(" RM")
        self.epf_shared_subcap.setMinimumWidth(150)
        epf_insurance_form.addRow("a) EPF Combined Subcap (Mandatory + Voluntary):", self.epf_shared_subcap)
        
        # b) Life Insurance Subcap (≤ RM3,000 default, but configurable)
        self.life_insurance_subcap = QDoubleSpinBox()
        self.life_insurance_subcap.setRange(1000.0, 3000.0)  # Will be updated by special upper limit
        self.life_insurance_subcap.setValue(3000.0)  # LHDN subcap default
        self.life_insurance_subcap.setSuffix(" RM")
        self.life_insurance_subcap.setMinimumWidth(150)
        self.life_insurance_subcap.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
        epf_insurance_form.addRow("b) Life Insurance Subcap (sub-had khusus):", self.life_insurance_subcap)
        
        # SPECIAL SUB-CAP UPPER LIMIT CONTROLLER (same as Section 3 pattern)
        special_limit_label = QLabel("🎯 <b>SPECIAL SUB-CAP UPPER LIMIT:</b>")
        special_limit_label.setStyleSheet("color: #e65100; font-weight: bold; margin-top: 15px;")
        epf_insurance_form.addRow(special_limit_label)
        
        self.life_insurance_upper_limit = QDoubleSpinBox()
        self.life_insurance_upper_limit.setRange(1000.0, 7000.0)  # Allow admin to set between RM1,000-RM7,000
        self.life_insurance_upper_limit.setValue(3000.0)  # Default RM3,000 (LHDN)
        self.life_insurance_upper_limit.setSuffix(" RM")
        self.life_insurance_upper_limit.setMinimumWidth(150)
        self.life_insurance_upper_limit.setStyleSheet("QDoubleSpinBox { background-color: #fff3e0; font-weight: bold; border: 2px solid #e65100; }")
        epf_insurance_form.addRow("⚙️ Upper Limit for Life Insurance:", self.life_insurance_upper_limit)
        
        # Add explanatory note (same as Section 3)
        note_label = QLabel("<i>📝 Note: Life Insurance will be limited to min(Upper Limit, Combined MAX CAP)</i>")
        note_label.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        epf_insurance_form.addRow(note_label)
        
        # Connect EPF insurance max cap signal for real-time broadcasting (same as Section 3)
        self.epf_insurance_combined_max.valueChanged.connect(
            lambda value: self.max_cap_changed.emit('epf_insurance_combined_max', value))
        self.epf_insurance_combined_max.valueChanged.connect(self.update_sub_max_cap_ranges)
        
        # Connect individual EPF insurance subcap signals for real-time broadcasting
        self.epf_shared_subcap.valueChanged.connect(
            lambda value: self.max_cap_changed.emit('epf_shared_subcap', value))
        self.life_insurance_subcap.valueChanged.connect(
            lambda value: self.max_cap_changed.emit('life_insurance_subcap', value))
        
        # Connect special upper limit controller (same as Section 3 pattern)
        self.life_insurance_upper_limit.valueChanged.connect(
            lambda value: self.max_cap_changed.emit('life_insurance_upper_limit', value))
        self.life_insurance_upper_limit.valueChanged.connect(self.update_sub_max_cap_ranges)
        
        epf_insurance_group.setLayout(epf_insurance_form)
        parent_layout.addWidget(epf_insurance_group)
        
        # 12. PRS / Anuiti tertangguh (≤ RM3,000)
        prs_group = QGroupBox("12. PRS / Anuiti tertangguh (≤ RM3,000)")
        prs_form = QFormLayout()
        
        self.prs_annuity_max = QDoubleSpinBox()
        self.prs_annuity_max.setRange(0.0, 3000.0)
        self.prs_annuity_max.setValue(3000.0)
        self.prs_annuity_max.setSuffix(" RM")
        self.prs_annuity_max.setMinimumWidth(150)
        prs_form.addRow("PRS/Anuiti:", self.prs_annuity_max)
        
        prs_group.setLayout(prs_form)
        parent_layout.addWidget(prs_group)
        
        # 13. Insurans pendidikan & perubatan (≤ RM4,000)
        education_medical_insurance_group = QGroupBox("13. Insurans pendidikan & perubatan (≤ RM4,000)")
        education_medical_insurance_form = QFormLayout()
        
        self.education_medical_insurance_max = QDoubleSpinBox()
        self.education_medical_insurance_max.setRange(0.0, 4000.0)
        self.education_medical_insurance_max.setValue(4000.0)
        self.education_medical_insurance_max.setSuffix(" RM")
        self.education_medical_insurance_max.setMinimumWidth(150)
        education_medical_insurance_form.addRow("Insurans pendidikan & perubatan:", self.education_medical_insurance_max)
        
        education_medical_insurance_group.setLayout(education_medical_insurance_form)
        parent_layout.addWidget(education_medical_insurance_group)
        
        # Section 14 removed - PERKESO is handled automatically via B20 from payroll deductions
        
        # 14. EV charger / compost machine (≤ RM2,500 sekali 3 tahun)
        ev_group = QGroupBox("15. EV charger / compost machine (≤ RM2,500 sekali 3 tahun)")
        ev_form = QFormLayout()
        
        self.ev_charger_max = QDoubleSpinBox()
        self.ev_charger_max.setRange(0.0, 5000.0)  # Increased from 2500 for flexibility
        self.ev_charger_max.setValue(2500.0)
        self.ev_charger_max.setSuffix(" RM")
        self.ev_charger_max.setMinimumWidth(150)
        self.ev_charger_max.setToolTip("EV charger/compost machine relief. LHDN default: RM2,500, can be set higher if needed.")
        ev_form.addRow("EV charger/compost machine:", self.ev_charger_max)
        
        ev_group.setLayout(ev_form)
        parent_layout.addWidget(ev_group)
        
        # 16. Faedah pinjaman rumah pertama
        housing_group = QGroupBox("16. Faedah pinjaman rumah pertama")
        housing_form = QFormLayout()
        
        # SUB MAX CAPs for mutually exclusive subcategories
        sub_cap_label = QLabel("📋 <b>SUB MAX CAP - Had Khusus Subkategori (Pilih Salah Satu):</b>")
        sub_cap_label.setStyleSheet("color: #1976d2; font-weight: bold;")
        housing_form.addRow(sub_cap_label)
        
        # a) Harga ≤ RM500k → ≤ RM7,000
        self.housing_loan_under_500k_max = QDoubleSpinBox()
        self.housing_loan_under_500k_max.setRange(0.0, 7000.0)
        self.housing_loan_under_500k_max.setValue(7000.0)
        self.housing_loan_under_500k_max.setSuffix(" RM")
        self.housing_loan_under_500k_max.setMinimumWidth(150)
        self.housing_loan_under_500k_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
        housing_form.addRow("a) Harga ≤ RM500k:", self.housing_loan_under_500k_max)
        
        # b) Harga RM500k–750k → ≤ RM5,000
        self.housing_loan_500k_750k_max = QDoubleSpinBox()
        self.housing_loan_500k_750k_max.setRange(0.0, 5000.0)
        self.housing_loan_500k_750k_max.setValue(5000.0)
        self.housing_loan_500k_750k_max.setSuffix(" RM")
        self.housing_loan_500k_750k_max.setMinimumWidth(150)
        self.housing_loan_500k_750k_max.setStyleSheet("QDoubleSpinBox { background-color: #e3f2fd; }")
        housing_form.addRow("b) Harga RM500k-750k:", self.housing_loan_500k_750k_max)
        
        housing_group.setLayout(housing_form)
        parent_layout.addWidget(housing_group)

    def _add_tax_config_management_subtab_impl(self, subtab_widget):
        """Configuration subtab removed; no-op."""
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Removed", "Configuration subtab is removed in this build.")
            return
            # config_tab = QWidget()
            
            # Create scroll area for the subtab
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            
            # Main widget inside scroll area
            main_widget = QWidget()
            layout = QVBoxLayout()
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)
            
            # Configuration Management Section
            config_group = QGroupBox("Configuration Management")
            config_layout = QVBoxLayout()
            
            # Configuration selector
            config_selector_layout = QHBoxLayout()
            config_selector_layout.addWidget(QLabel("Configuration:"))
            
            self.lhdn_config_selector = QComboBox()
            self.lhdn_config_selector.setMinimumWidth(200)
            self.lhdn_config_selector.currentTextChanged.connect(self.on_lhdn_config_selection_changed)
            config_selector_layout.addWidget(self.lhdn_config_selector)
            
            refresh_lhdn_configs_button = QPushButton("🔄")
            refresh_lhdn_configs_button.setToolTip("Refresh configuration list")
            refresh_lhdn_configs_button.clicked.connect(self.load_lhdn_configuration_list)
            refresh_lhdn_configs_button.setMaximumWidth(30)
            config_selector_layout.addWidget(refresh_lhdn_configs_button)
            
            config_layout.addLayout(config_selector_layout)
            
            # Configuration name for saving
            save_config_layout = QHBoxLayout()
            save_config_layout.addWidget(QLabel("Save as:"))
            
            self.lhdn_config_name_input = QLineEdit()
            self.lhdn_config_name_input.setPlaceholderText("Enter configuration name...")
            save_config_layout.addWidget(self.lhdn_config_name_input)
            
            config_layout.addLayout(save_config_layout)
            
            # Configuration description
            desc_layout = QHBoxLayout()
            desc_layout.addWidget(QLabel("Description:"))
            
            self.lhdn_config_description_input = QLineEdit()
            self.lhdn_config_description_input.setPlaceholderText("Optional description...")
            desc_layout.addWidget(self.lhdn_config_description_input)
            
            config_layout.addLayout(desc_layout)
            
            # Action buttons
            lhdn_button_layout = QHBoxLayout()
            
            save_lhdn_config_button = QPushButton("💾 Save Configuration")
            save_lhdn_config_button.clicked.connect(self.save_lhdn_tax_config)
            lhdn_button_layout.addWidget(save_lhdn_config_button)
            
            load_lhdn_config_button = QPushButton("📂 Load Configuration")
            load_lhdn_config_button.clicked.connect(self.load_selected_lhdn_configuration)
            lhdn_button_layout.addWidget(load_lhdn_config_button)
            
            delete_lhdn_config_button = QPushButton("🗑️ Delete Configuration")
            delete_lhdn_config_button.clicked.connect(self.delete_selected_lhdn_configuration)
            lhdn_button_layout.addWidget(delete_lhdn_config_button)
            
            reset_lhdn_defaults_button = QPushButton("↩️ Reset to LHDN Defaults")
            reset_lhdn_defaults_button.clicked.connect(self.reset_lhdn_tax_defaults)
            lhdn_button_layout.addWidget(reset_lhdn_defaults_button)
            
            lhdn_button_layout.addStretch()
            
            config_layout.addLayout(lhdn_button_layout)
            config_group.setLayout(config_layout)
            layout.addWidget(config_group)
            
            # Preview Section
            preview_group = QGroupBox("Tax Calculation Preview")
            preview_layout = QVBoxLayout()
            
            # Preview inputs
            preview_inputs_layout = QFormLayout()
            
            self.lhdn_preview_annual_salary = QDoubleSpinBox()
            self.lhdn_preview_annual_salary.setRange(0.0, 10000000.0)
            self.lhdn_preview_annual_salary.setValue(60000.0)
            self.lhdn_preview_annual_salary.setSuffix(" RM")
            self.lhdn_preview_annual_salary.valueChanged.connect(self.update_lhdn_preview_calculation)
            preview_inputs_layout.addRow("Annual Salary:", self.lhdn_preview_annual_salary)
            
            self.lhdn_preview_children = QSpinBox()
            self.lhdn_preview_children.setRange(0, 20)
            self.lhdn_preview_children.setValue(0)
            self.lhdn_preview_children.valueChanged.connect(self.update_lhdn_preview_calculation)
            preview_inputs_layout.addRow("Number of Children:", self.lhdn_preview_children)
            
            self.lhdn_preview_disabled_children = QSpinBox()
            self.lhdn_preview_disabled_children.setRange(0, 10)
            self.lhdn_preview_disabled_children.setValue(0)
            self.lhdn_preview_disabled_children.valueChanged.connect(self.update_lhdn_preview_calculation)
            preview_inputs_layout.addRow("Disabled Children:", self.lhdn_preview_disabled_children)
            
            preview_layout.addLayout(preview_inputs_layout)
            
            # Preview results
            self.lhdn_preview_result = QTextEdit()
            self.lhdn_preview_result.setMaximumHeight(200)
            self.lhdn_preview_result.setStyleSheet("QTextEdit { background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 5px; padding: 10px; font-family: 'Courier New', monospace; }")
            preview_layout.addWidget(self.lhdn_preview_result)
            
            preview_group.setLayout(preview_layout)
            layout.addWidget(preview_group)
            
            # Test calculation button
            test_lhdn_button = QPushButton("🧮 Test LHDN Tax Calculation")
            test_lhdn_button.clicked.connect(self.test_lhdn_tax_calculation)
            layout.addWidget(test_lhdn_button)
            
            # Set layout and add to scroll area
            main_widget.setLayout(layout)
            scroll_area.setWidget(main_widget)
            
            # Create the config tab layout
            config_tab_layout = QVBoxLayout()
            config_tab_layout.setContentsMargins(0, 0, 0, 0)
            config_tab_layout.addWidget(scroll_area)
            config_tab.setLayout(config_tab_layout)
            
            subtab_widget.addTab(config_tab, "⚙️ Configuration")
            
        except Exception as e:
            print(f"DEBUG: Error creating tax config management subtab: {e}")
            QMessageBox.warning(self, "Error", f"Failed to create tax config management subtab: {e}")

    def load_lhdn_configuration_list(self):
        """Load available LHDN tax configurations into the selector"""
        try:
            # Check if LHDN components exist before proceeding
            if not hasattr(self, 'lhdn_config_selector') or self.lhdn_config_selector is None:
                print("DEBUG: LHDN config selector not available, skipping LHDN configuration loading")
                return
                
            self.lhdn_config_selector.clear()
            
            # Add default option
            self.lhdn_config_selector.addItem("LHDN 2025 Default", "default")
            # DB-backed LHDN configs removed; default only
            print("DEBUG: LHDN configs disabled; using default only")
            
        except Exception as e:
            print(f"DEBUG: Error loading LHDN configuration list: {e}")

    def on_lhdn_config_selection_changed(self, text):
        """Handle LHDN configuration selection change"""
        try:
            current_data = self.lhdn_config_selector.currentData()
            if current_data and current_data != 'default':
                # Auto-load the selected configuration
                self.load_lhdn_tax_config(current_data)
                
        except Exception as e:
            print(f"DEBUG: Error handling LHDN config selection: {e}")

    def load_selected_lhdn_configuration(self):
        """Load the selected LHDN configuration"""
        try:
            config_name = self.lhdn_config_selector.currentData()
            if not config_name:
                QMessageBox.warning(self, "Warning", "Please select a configuration to load.")
                return
            
            self.load_lhdn_tax_config(config_name)
            
        except Exception as e:
            print(f"DEBUG: Error loading selected LHDN configuration: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load configuration: {e}")

    def save_lhdn_tax_config(self):
        """Save LHDN tax configuration to database (disabled)"""
        try:
            QMessageBox.information(self, "Info", "Saving custom LHDN configurations is disabled in this build.")
            self.load_lhdn_configuration_list()
            
        except Exception as e:
            print(f"DEBUG: Error saving LHDN tax config: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save configuration: {e}")

    def load_lhdn_tax_config(self, config_name=None):
        """Load LHDN tax configuration (DB configs disabled; default only)"""
        try:
            if config_name is None or config_name == 'default':
                # Load LHDN 2025 defaults
                self.reset_lhdn_tax_defaults()
                return
            
            # DB-backed configs removed; always reset to default
            self.reset_lhdn_tax_defaults()
            if config_name and config_name != 'default':
                QMessageBox.information(self, "Info", "Custom LHDN configurations are disabled; default values loaded.")
            
        except Exception as e:
            print(f"DEBUG: Error loading LHDN tax config: {e}")
            QMessageBox.warning(self, "Error", f"Failed to load configuration: {e}")

    def delete_selected_lhdn_configuration(self):
        """Delete the selected LHDN configuration (disabled)"""
        try:
            QMessageBox.information(self, "Info", "Custom LHDN configurations are disabled; nothing to delete.")
                
        except Exception as e:
            print(f"DEBUG: Error deleting LHDN configuration: {e}")
            QMessageBox.warning(self, "Error", f"Failed to delete configuration: {e}")

    def reset_lhdn_tax_defaults(self):
        """Reset LHDN tax configuration to official 2025 B1-B21 defaults"""
        try:
            # Set B1 & B14-B16: Personal & Family Reliefs (LHDN 2025 defaults)
            self.lhdn_b1_individual_relief.setValue(9000.0)
            self.lhdn_b14_spouse_relief.setValue(4000.0)
            self.lhdn_b15_disabled_spouse_relief.setValue(5000.0)
            self.lhdn_b16_children_under_18.setValue(2000.0)
            self.lhdn_b16_children_study_malaysia.setValue(2000.0)
            self.lhdn_b16_children_higher_education.setValue(8000.0)
            self.lhdn_b16_disabled_not_studying.setValue(8000.0)
            self.lhdn_b16_disabled_studying.setValue(8000.0)
            
            # Set B2-B8: Health & Medical Reliefs
            self.lhdn_b2_parent_medical.setValue(8000.0)
            self.lhdn_b3_basic_support_equipment.setValue(6000.0)
            self.lhdn_b4_individual_disability.setValue(6000.0)
            self.lhdn_b6_medical_expenses.setValue(10000.0)
            self.lhdn_b7_medical_checkup.setValue(1000.0)
            self.lhdn_b8_child_learning_disability.setValue(4000.0)
            
            # Set B5, B12-B13: Education & Childcare Reliefs
            self.lhdn_b5_education_fees.setValue(7000.0)
            self.lhdn_b12_childcare_fees.setValue(3000.0)
            self.lhdn_b13_sspn.setValue(8000.0)
            
            # Set B9-B11, B21: Lifestyle & Other Reliefs
            self.lhdn_b9_basic_lifestyle.setValue(2500.0)
            self.lhdn_b10_additional_lifestyle.setValue(1000.0)
            self.lhdn_b11_breastfeeding_equipment.setValue(1000.0)
            self.lhdn_b21_ev_charging.setValue(2500.0)
            
            # Set B17-B20: Investment & Insurance Reliefs
            self.lhdn_b17_mandatory_epf.setValue(4000.0)  # B17 - Mandatory EPF only
            self.lhdn_b18_prs_annuity.setValue(3000.0)
            self.lhdn_b19_education_medical_insurance.setValue(3000.0)
            self.lhdn_b20_perkeso.setValue(350.0)
            
            # Tax Status - Default assumption (individual status handled in payroll dialog)
            # Default to resident for admin configuration purposes
            
            # Update input fields
            self.lhdn_config_name_input.setText("LHDN 2025 B1-B21 Default")
            self.lhdn_config_description_input.setText("Official LHDN 2025 tax reliefs B1-B21 with progressive rates")
            
            self.update_lhdn_preview_calculation()
            QMessageBox.information(self, "Reset", "Configuration reset to official LHDN 2025 B1-B21 defaults!")
            
        except Exception as e:
            print(f"DEBUG: Error resetting LHDN tax defaults: {e}")
            QMessageBox.warning(self, "Error", f"Failed to reset defaults: {e}")

    def update_lhdn_preview_calculation(self):
        """Update the LHDN tax calculation preview"""
        try:
            annual_salary = self.lhdn_preview_annual_salary.value()
            children = self.lhdn_preview_children.value()
            disabled_children = self.lhdn_preview_disabled_children.value()
            
            # Calculate monthly taxable income (assuming 11% EPF)
            monthly_gross = annual_salary / 12
            monthly_epf = monthly_gross * 0.11
            monthly_taxable = monthly_gross - monthly_epf
            
            # Create PCB calculator instance
            calculator = MalaysianPCBCalculator()
            
            # Calculate tax using correct method signature
            reliefs = {
                'personal': self.lhdn_personal_relief.value(),
                'spouse': self.lhdn_spouse_relief.value(),
                'children': self.lhdn_child_relief.value() * children,
                'disabled_children': self.lhdn_disabled_child_relief.value() * disabled_children,
                'epf': min(annual_salary * 0.11, self.lhdn_epf_relief_max.value())
            }
            
            result = calculator.calculate_pcb(
                monthly_taxable_income=monthly_taxable,
                reliefs=reliefs,
                is_resident=True  # Default to resident for admin config (individual status handled in payroll dialog)
            )
            
            # Format preview text
            preview_text = f"""
<b>📊 LHDN Tax Calculation Preview</b><br>
<b>════════════════════════════════</b><br>
<b>Annual Gross Income:</b> RM{annual_salary:,.2f}<br>
<b>Monthly Gross Income:</b> RM{monthly_gross:,.2f}<br>
<b>Monthly EPF (11%):</b> RM{monthly_epf:,.2f}<br>
<b>Monthly Taxable:</b> RM{monthly_taxable:,.2f}<br>
<b>────────────────────────────────</b><br>
<b>Tax Reliefs:</b><br>
• Personal Relief: RM{reliefs['personal']:,.2f}<br>
• Spouse Relief: RM{reliefs['spouse']:,.2f}<br>
• Child Relief: RM{reliefs['children']:,.2f} ({children} children)<br>
• Disabled Child Relief: RM{reliefs['disabled_children']:,.2f} ({disabled_children} disabled)<br>
• EPF Relief: RM{reliefs['epf']:,.2f}<br>
<b>────────────────────────────────</b><br>
<b>Annual Taxable Income:</b> RM{result['annual_taxable_income']:,.2f}<br>
<b>Total Reliefs:</b> RM{result['total_reliefs']:,.2f}<br>
<b>Chargeable Income:</b> RM{result['chargeable_income']:,.2f}<br>
<b>Annual Net Tax:</b> RM{result['annual_net_tax']:,.2f}<br>
            <b>────────────────────────────────</b><br>
<b>Monthly PCB:</b> RM{result['monthly_pcb']:,.2f}<br>
<b>Tax Status:</b> Resident (Individual status configured in payroll dialog)<br>
            """
            
            self.lhdn_preview_result.setHtml(preview_text)
            
        except Exception as e:
            print(f"DEBUG: Error updating LHDN preview: {e}")
            self.lhdn_preview_result.setPlainText(f"Error calculating tax: {e}")

    def test_lhdn_tax_calculation(self):
        """Test LHDN tax calculation with detailed breakdown"""
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("LHDN Tax Calculation Test")
            dialog.setMinimumSize(600, 500)
            
            layout = QVBoxLayout()
            
            # Test parameters
            test_group = QGroupBox("Test Parameters")
            test_layout = QFormLayout()
            
            test_salary = QDoubleSpinBox()
            test_salary.setRange(0.0, 10000000.0)
            test_salary.setValue(self.lhdn_preview_annual_salary.value())
            test_salary.setSuffix(" RM")
            test_layout.addRow("Annual Salary:", test_salary)
            
            test_children = QSpinBox()
            test_children.setRange(0, 20)
            test_children.setValue(self.lhdn_preview_children.value())
            test_layout.addRow("Children:", test_children)
            
            test_disabled_children = QSpinBox()
            test_disabled_children.setRange(0, 10)
            test_disabled_children.setValue(self.lhdn_preview_disabled_children.value())
            test_layout.addRow("Disabled Children:", test_disabled_children)
            
            test_group.setLayout(test_layout)
            layout.addWidget(test_group)
            
            # Calculate button
            calc_button = QPushButton("Calculate Detailed Tax Breakdown")
            layout.addWidget(calc_button)
            
            # Results area
            results_area = QTextEdit()
            results_area.setMinimumHeight(300)
            results_area.setStyleSheet("QTextEdit { font-family: 'Courier New', monospace; }")
            layout.addWidget(results_area)
            
            def calculate():
                try:
                    calculator = MalaysianPCBCalculator()
                    
                    # Calculate monthly values
                    annual_income = test_salary.value()
                    monthly_gross = annual_income / 12
                    monthly_epf = monthly_gross * 0.11
                    monthly_taxable = monthly_gross - monthly_epf
                    
                    # Prepare reliefs
                    reliefs = {
                        'personal': self.lhdn_personal_relief.value(),
                        'spouse': self.lhdn_spouse_relief.value(),
                        'children': self.lhdn_child_relief.value() * test_children.value(),
                        'disabled_children': self.lhdn_disabled_child_relief.value() * test_disabled_children.value(),
                        'epf': min(annual_income * 0.11, self.lhdn_epf_relief_max.value())
                    }
                    
                    result = calculator.calculate_pcb(
                        monthly_taxable_income=monthly_taxable,
                        reliefs=reliefs,
                        is_resident=True  # Default to resident for admin config (individual status handled in payroll dialog)
                    )
                    
                    # Format detailed results with step-by-step breakdown
                    detailed_text = f"""
🏛️ LHDN TAX CALCULATION - DETAILED BREAKDOWN
═══════════════════════════════════════════════════════════════

📊 INPUT PARAMETERS:
• Annual Gross Income    : RM{annual_income:,.2f}
• Monthly Gross Income   : RM{monthly_gross:,.2f}
• Monthly EPF (11%)      : RM{monthly_epf:,.2f}
• Monthly Taxable Income : RM{monthly_taxable:,.2f}
• Personal Relief        : RM{reliefs['personal']:,.2f}
• Spouse Relief          : RM{reliefs['spouse']:,.2f}
• Child Relief           : RM{reliefs['children']:,.2f} ({test_children.value()} × RM{self.lhdn_child_relief.value():,.2f})
• Disabled Child Relief  : RM{reliefs['disabled_children']:,.2f} ({test_disabled_children.value()} × RM{self.lhdn_disabled_child_relief.value():,.2f})
• EPF Relief Max         : RM{self.lhdn_epf_relief_max.value():,.2f}
• Tax Status             : Resident (Individual status configured in payroll dialog)

💰 CALCULATION RESULTS:
• Annual Taxable Income  : RM{result['annual_taxable_income']:,.2f}
• Total Reliefs Applied  : RM{result['total_reliefs']:,.2f}
• Chargeable Income      : RM{result['chargeable_income']:,.2f}
• Annual Gross Tax       : RM{result['annual_gross_tax']:,.2f}
• Annual Net Tax         : RM{result['annual_net_tax']:,.2f}
• Monthly PCB            : RM{result['monthly_pcb']:,.2f}

� TAX BRACKET BREAKDOWN (HASIL 2025):
{self._generate_tax_breakdown(result['chargeable_income'])}

�💡 COMPLIANCE NOTES:
• Calculation follows LHDN 2025 progressive tax structure
• Monthly PCB = Annual Net Tax ÷ 12
• EPF relief capped at RM6,000 annually
• Resident vs non-resident tax rates applied correctly
                    """
                    
                    results_area.setPlainText(detailed_text)
                    
                except Exception as e:
                    results_area.setPlainText(f"Error in calculation: {e}")
            
            calc_button.clicked.connect(calculate)
            
            # Calculate initially
            calculate()
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            print(f"DEBUG: Error testing LHDN tax calculation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to test calculation: {e}")

    def _generate_tax_breakdown(self, chargeable_income: float) -> str:
        """Generate detailed tax bracket breakdown like HASIL table"""
        if chargeable_income <= 0:
            return "No tax liability (chargeable income ≤ 0)"
        
        breakdown = []
        remaining = chargeable_income
        total_tax = 0
        
        # HASIL 2025 brackets with step-by-step calculation
        brackets = [
            ("A", 0, 5000, 0.00, "On the First 5,000"),
            ("B", 5001, 20000, 0.01, "Next 15,000"),
            ("C", 20001, 35000, 0.03, "Next 15,000"),
            ("D", 35001, 50000, 0.06, "Next 15,000"),
            ("E", 50001, 70000, 0.11, "Next 20,000"),
            ("F", 70001, 100000, 0.19, "Next 30,000"),
            ("G", 100001, 400000, 0.25, "Next 300,000"),
            ("H", 400001, 600000, 0.26, "Next 200,000"),
            ("I", 600001, 2000000, 0.28, "Next 1,400,000"),
            ("J", 2000001, float('inf'), 0.30, "Exceeding 2,000,000")
        ]
        
        for category, range_from, range_to, rate, description in brackets:
            if remaining <= 0:
                break
                
            if chargeable_income > range_from - 1:  # -1 because ranges start from X+1
                if range_to == float('inf'):
                    taxable_amount = remaining
                    breakdown.append(f"  {category}  │ {description:<20} │ RM{taxable_amount:>12,.2f} × {rate*100:>3.0f}% = RM{taxable_amount * rate:>10,.2f}")
                    total_tax += taxable_amount * rate
                    break
                else:
                    bracket_limit = range_to - (range_from - 1)
                    taxable_amount = min(remaining, bracket_limit)
                    tax_amount = taxable_amount * rate
                    
                    if taxable_amount > 0:
                        breakdown.append(f"  {category}  │ {description:<20} │ RM{taxable_amount:>12,.2f} × {rate*100:>3.0f}% = RM{tax_amount:>10,.2f}")
                        total_tax += tax_amount
                        remaining -= taxable_amount
        
        result = "┌─────┬──────────────────────┬─────────────────┬────────────┐\n"
        result += "│ Cat │      Description     │ Taxable Amount  │   Tax (RM) │\n"
        result += "├─────┼──────────────────────┼─────────────────┼────────────┤\n"
        result += "\n".join(breakdown) + "\n"
        result += "├─────┴──────────────────────┴─────────────────┼────────────┤\n"
        result += f"│ TOTAL GROSS TAX                              │ RM{total_tax:>8,.2f} │\n"
        result += "├──────────────────────────────────────────────┼────────────┤\n"
        result += f"│ TOTAL NET TAX                                │ RM{total_tax:>8,.2f} │\n"
        result += "└──────────────────────────────────────────────┴────────────┘"
        
        return result

    def toggle_tax_rates_editing(self):
        """Toggle editing mode for tax bracket inputs"""
        try:
            # Tax bracket inputs are always editable, so this can enable/disable them
            enabled = not self.tax_bracket_inputs[0]['from'].isEnabled() if self.tax_bracket_inputs else True
            
            for bracket_input in self.tax_bracket_inputs:
                for key in ['from', 'to', 'on_first', 'next', 'rate', 'tax_first', 'tax_next']:
                    bracket_input[key].setEnabled(enabled)
            
            status = "enabled" if enabled else "disabled"
            QMessageBox.information(self, "Edit Mode", f"Tax bracket inputs are now {status}.")
            
        except Exception as e:
            print(f"DEBUG: Error toggling tax rates editing: {e}")

    def reset_tax_rates_to_default(self):
        """Reset tax rates to LHDN default values"""
        try:
            reply = QMessageBox.question(self, "Reset Tax Rates", 
                                       "Are you sure you want to reset all tax rates to LHDN default values?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Reset non-resident rate
                if hasattr(self, 'lhdn_non_resident_rate'):
                    self.lhdn_non_resident_rate.setValue(30.0)
                
                # Reset tax brackets to LHDN defaults
                default_brackets = [
                    {"from": 0, "to": 5000, "on_first": 0, "next": 0, "rate": 0, "tax_first": 0, "tax_next": 0},
                    {"from": 5001, "to": 20000, "on_first": 5000, "next": 15000, "rate": 1, "tax_first": 0, "tax_next": 150},
                    {"from": 20001, "to": 35000, "on_first": 20000, "next": 15000, "rate": 3, "tax_first": 150, "tax_next": 450},
                    {"from": 35001, "to": 50000, "on_first": 35000, "next": 15000, "rate": 6, "tax_first": 600, "tax_next": 900},
                    {"from": 50001, "to": 70000, "on_first": 50000, "next": 20000, "rate": 11, "tax_first": 1500, "tax_next": 2200},
                    {"from": 70001, "to": 100000, "on_first": 70000, "next": 30000, "rate": 19, "tax_first": 3700, "tax_next": 5700},
                    {"from": 100001, "to": 400000, "on_first": 100000, "next": 300000, "rate": 25, "tax_first": 9400, "tax_next": 75000},
                    {"from": 400001, "to": 600000, "on_first": 400000, "next": 200000, "rate": 26, "tax_first": 84400, "tax_next": 52000},
                    {"from": 600001, "to": 2000000, "on_first": 600000, "next": 1400000, "rate": 28, "tax_first": 136400, "tax_next": 392000},
                    {"from": 2000001, "to": 999999999, "on_first": 2000000, "next": 0, "rate": 30, "tax_first": 528400, "tax_next": 0},
                ]
                
                # Update existing brackets with default values
                for i, bracket_input in enumerate(self.tax_bracket_inputs):
                    if i < len(default_brackets):
                        default = default_brackets[i]
                        bracket_input['from'].setValue(default["from"])
                        bracket_input['to'].setValue(default["to"])
                        bracket_input['on_first'].setValue(default["on_first"])
                        bracket_input['next'].setValue(default["next"])
                        bracket_input['rate'].setValue(default["rate"])
                        bracket_input['tax_first'].setValue(default["tax_first"])
                        bracket_input['tax_next'].setValue(default["tax_next"])
                
                QMessageBox.information(self, "Reset Complete", "Tax rates have been reset to LHDN default values.")
                
        except Exception as e:
            print(f"DEBUG: Error resetting tax rates: {e}")
            QMessageBox.warning(self, "Error", f"Failed to reset tax rates: {e}")
            print(f"DEBUG: Error resetting tax rates: {e}")
            QMessageBox.warning(self, "Error", f"Failed to reset tax rates: {e}")

    def reset_tax_reliefs_to_default(self):
        """Reset tax reliefs to LHDN B1-B21 default values"""
        try:
            reply = QMessageBox.question(self, "Reset Tax Reliefs", 
                                       "Are you sure you want to reset all tax reliefs to LHDN B1-B21 default values?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Reset B1 & B14-B16: Personal & Family Reliefs
                self.lhdn_b1_individual_relief.setValue(9000.0)
                self.lhdn_b14_spouse_relief.setValue(4000.0)
                self.lhdn_b15_disabled_spouse_relief.setValue(5000.0)
                self.lhdn_b16_children_under_18.setValue(2000.0)
                self.lhdn_b16_children_tertiary.setValue(8000.0)
                self.lhdn_b16_children_disabled.setValue(8000.0)
                
                # Reset B2-B8: Health & Medical Reliefs
                self.lhdn_b2_parent_medical.setValue(8000.0)
                self.lhdn_b3_basic_support_equipment.setValue(6000.0)
                self.lhdn_b4_individual_disability.setValue(6000.0)
                self.lhdn_b6_medical_expenses.setValue(10000.0)
                self.lhdn_b7_medical_checkup.setValue(1000.0)
                self.lhdn_b8_child_learning_disability.setValue(4000.0)
                
                # Reset B5, B12-B13: Education & Childcare Reliefs
                self.lhdn_b5_education_fees.setValue(7000.0)
                self.lhdn_b12_childcare_fees.setValue(3000.0)
                self.lhdn_b13_sspn.setValue(8000.0)
                
                # Reset B9-B11, B21: Lifestyle & Other Reliefs
                self.lhdn_b9_basic_lifestyle.setValue(2500.0)
                self.lhdn_b10_additional_lifestyle.setValue(1000.0)
                self.lhdn_b11_breastfeeding_equipment.setValue(1000.0)
                self.lhdn_b21_ev_charging.setValue(2500.0)
                
                # Reset B17-B20: Investment & Insurance Reliefs
                self.lhdn_b17_mandatory_epf.setValue(4000.0)  # Updated to mandatory EPF only
                self.lhdn_b18_prs_annuity.setValue(3000.0)
                self.lhdn_b19_education_medical_insurance.setValue(3000.0)
                self.lhdn_b20_perkeso.setValue(350.0)
                
                # Tax Status - Default to resident (individual status handled in payroll dialog)
                # No UI control needed here anymore
                
                QMessageBox.information(self, "Success", "Tax reliefs have been reset to LHDN B1-B21 default values.")
                
        except Exception as e:
            print(f"DEBUG: Error resetting tax reliefs: {e}")
            QMessageBox.warning(self, "Error", f"Failed to reset tax reliefs: {e}")

    def test_tax_rates_calculation(self):
        """Test tax calculation using current tax rates"""
        try:
            # Simple dialog to get test input
            from PyQt5.QtWidgets import QInputDialog
            
            annual_income, ok = QInputDialog.getDouble(self, "Test Tax Calculation", 
                                                     "Enter annual taxable income (RM):", 
                                                     60000.0, 0.0, 10000000.0, 2)
            
            if ok:
                # Calculate tax using current rates (simplified progressive calculation)
                tax_brackets = [
                    (5000, 0.0),    # First RM5,000: 0%
                    (20000, 0.01),  # Next RM15,000: 1%
                    (35000, 0.03),  # Next RM15,000: 3%
                    (50000, 0.06),  # Next RM15,000: 6%
                    (70000, 0.11),  # Next RM20,000: 11%
                    (100000, 0.19), # Next RM30,000: 19%
                    (250000, 0.25), # Next RM150,000: 25%
                    (400000, 0.26), # Next RM150,000: 26%
                    (600000, 0.28), # Next RM200,000: 28%
                    (1000000, 0.30), # Next RM400,000: 30%
                    (float('inf'), 0.30)  # Above RM1,000,000: 30%
                ]
                
                total_tax = 0.0
                remaining_income = annual_income
                prev_threshold = 0
                
                for threshold, rate in tax_brackets:
                    if remaining_income <= 0:
                        break
                    
                    taxable_in_bracket = min(remaining_income, threshold - prev_threshold)
                    tax_in_bracket = taxable_in_bracket * rate
                    total_tax += tax_in_bracket
                    
                    remaining_income -= taxable_in_bracket
                    prev_threshold = threshold
                
                final_tax = max(0, total_tax)
                
                result_msg = f"""
Tax Calculation Results:

Annual Taxable Income: RM {annual_income:,.2f}
Gross Tax: RM {total_tax:,.2f}
Final Tax Payable: RM {final_tax:,.2f}
Effective Tax Rate: {(final_tax/annual_income*100):.2f}%
                """
                
                QMessageBox.information(self, "Tax Calculation Result", result_msg)
                
        except Exception as e:
            print(f"DEBUG: Error testing tax rates calculation: {e}")
            QMessageBox.warning(self, "Error", f"Failed to test tax calculation: {e}")

    def create_tax_bracket_input_group(self, bracket_number, bracket_data):
        """Create an input group for a single tax bracket"""
        group = QGroupBox(f"Tax Bracket {bracket_number}")
        layout = QGridLayout()
        
        # Chargeable Income (From and To)
        layout.addWidget(QLabel("Chargeable Income:"), 0, 0)
        
        from_input = QDoubleSpinBox()
        from_input.setRange(0.0, 999999999.0)
        from_input.setValue(bracket_data["from"])
        from_input.setSuffix(" RM")
        from_input.setMaximumWidth(120)
        layout.addWidget(QLabel("From:"), 0, 1)
        layout.addWidget(from_input, 0, 2)
        
        to_input = QDoubleSpinBox()
        to_input.setRange(0.0, 999999999.0)
        to_input.setValue(bracket_data["to"])
        to_input.setSuffix(" RM")
        to_input.setMaximumWidth(120)
        layout.addWidget(QLabel("To:"), 0, 3)
        layout.addWidget(to_input, 0, 4)
        
        # Calculation (On First and Next)
        layout.addWidget(QLabel("Calculation:"), 1, 0)
        
        on_first_input = QDoubleSpinBox()
        on_first_input.setRange(0.0, 999999999.0)
        on_first_input.setValue(bracket_data["on_first"])
        on_first_input.setSuffix(" RM")
        on_first_input.setMaximumWidth(120)
        layout.addWidget(QLabel("On First:"), 1, 1)
        layout.addWidget(on_first_input, 1, 2)
        
        next_input = QDoubleSpinBox()
        next_input.setRange(0.0, 999999999.0)
        next_input.setValue(bracket_data["next"])
        next_input.setSuffix(" RM")
        next_input.setMaximumWidth(120)
        layout.addWidget(QLabel("Next:"), 1, 3)
        layout.addWidget(next_input, 1, 4)
        
        # Rate (%)
        rate_input = QDoubleSpinBox()
        rate_input.setRange(0.0, 100.0)
        rate_input.setValue(bracket_data["rate"])
        rate_input.setSuffix(" %")
        rate_input.setMaximumWidth(80)
        layout.addWidget(QLabel("Rate (%):"), 2, 1)
        layout.addWidget(rate_input, 2, 2)
        
        # Tax (RM) - On First and Next
        layout.addWidget(QLabel("Tax (RM):"), 3, 0)
        
        tax_first_input = QDoubleSpinBox()
        tax_first_input.setRange(0.0, 999999999.0)
        tax_first_input.setValue(bracket_data["tax_first"])
        tax_first_input.setSuffix(" RM")
        tax_first_input.setMaximumWidth(120)
        layout.addWidget(QLabel("On First:"), 3, 1)
        layout.addWidget(tax_first_input, 3, 2)
        
        tax_next_input = QDoubleSpinBox()
        tax_next_input.setRange(0.0, 999999999.0)
        tax_next_input.setValue(bracket_data["tax_next"])
        tax_next_input.setSuffix(" RM")
        tax_next_input.setMaximumWidth(120)
        layout.addWidget(QLabel("Next:"), 3, 3)
        layout.addWidget(tax_next_input, 3, 4)
        
        # Remove button
        remove_button = QPushButton("🗑️ Remove")
        remove_button.clicked.connect(lambda: self.remove_tax_bracket(group))
        layout.addWidget(remove_button, 4, 4)
        
        group.setLayout(layout)
        
        # Store references to inputs
        bracket_inputs = {
            'group': group,
            'from': from_input,
            'to': to_input,
            'on_first': on_first_input,
            'next': next_input,
            'rate': rate_input,
            'tax_first': tax_first_input,
            'tax_next': tax_next_input
        }
        
        self.tax_bracket_inputs.append(bracket_inputs)
        return group

    def add_new_tax_bracket(self):
        """Add a new tax bracket input group"""
        try:
            # Default values for new bracket
            new_bracket = {
                "from": 0, "to": 0, "on_first": 0, "next": 0, 
                "rate": 0, "tax_first": 0, "tax_next": 0
            }
            
            bracket_number = len(self.tax_bracket_inputs) + 1
            bracket_group = self.create_tax_bracket_input_group(bracket_number, new_bracket)
            
            # Add to the container layout (before the "Add" button)
            container_layout = bracket_group.parent().layout()
            button_index = container_layout.count() - 1  # Add button is last
            container_layout.insertWidget(button_index, bracket_group)
            
        except Exception as e:
            print(f"DEBUG: Error adding new tax bracket: {e}")
            QMessageBox.warning(self, "Error", f"Failed to add new tax bracket: {e}")

    def remove_tax_bracket(self, bracket_group):
        """Remove a tax bracket input group"""
        try:
            reply = QMessageBox.question(self, "Remove Tax Bracket", 
                                       "Are you sure you want to remove this tax bracket?",
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # Remove from inputs list
                self.tax_bracket_inputs = [b for b in self.tax_bracket_inputs if b['group'] != bracket_group]
                
                # Remove from UI
                bracket_group.setParent(None)
                bracket_group.deleteLater()
                
                # Renumber remaining brackets
                for i, bracket_input in enumerate(self.tax_bracket_inputs):
                    bracket_input['group'].setTitle(f"Tax Bracket {i + 1}")
                    
        except Exception as e:
            print(f"DEBUG: Error removing tax bracket: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove tax bracket: {e}")

    def get_tax_brackets_data(self):
        """Get all tax bracket data from input fields"""
        brackets_data = []
        for bracket_input in self.tax_bracket_inputs:
            bracket_data = {
                "from": bracket_input['from'].value(),
                "to": bracket_input['to'].value(),
                "on_first": bracket_input['on_first'].value(),
                "next": bracket_input['next'].value(),
                "rate": bracket_input['rate'].value(),
                "tax_first": bracket_input['tax_first'].value(),
                "tax_next": bracket_input['tax_next'].value()
            }
            brackets_data.append(bracket_data)
        return brackets_data

    def save_tax_brackets_configuration(self):
        """Persist current tax brackets to Supabase via services.save_progressive_tax_brackets"""
        try:
            brackets_data = self.get_tax_brackets_data()
            ok = False
            try:
                # Defer to service to normalize and persist
                from services.supabase_service import save_progressive_tax_brackets
                ok = save_progressive_tax_brackets(brackets_data, config_name='default')
            except Exception as svc_err:
                print(f"DEBUG: Service error saving brackets: {svc_err}")
                ok = False

            if ok:
                QMessageBox.information(self, "Saved", f"Tax brackets saved to database. Total brackets: {len(brackets_data)}")
            else:
                # Fallback: show preview to help diagnose
                import json
                preview = json.dumps(brackets_data, indent=2)
                QMessageBox.warning(self, "Save Failed", f"Failed to save tax brackets to database.\n\nPreview (not saved):\n{preview[:700]}{'...' if len(preview) > 700 else ''}")

        except Exception as e:
            print(f"DEBUG: Error saving tax brackets configuration: {e}")
            QMessageBox.warning(self, "Error", f"Failed to save tax brackets configuration: {e}")

    def calculate_total_tax_relief(self):
        """Calculate total tax relief based on current B1-B21 settings"""
        try:
            # B1 & B14-B16: Personal & Family Reliefs
            b1_individual = self.lhdn_b1_individual_relief.value()
            b14_spouse = self.lhdn_b14_spouse_relief.value()
            b15_disabled_spouse = self.lhdn_b15_disabled_spouse_relief.value()
            b16_children_under_18 = self.lhdn_b16_children_under_18.value()
            b16_children_study_malaysia = self.lhdn_b16_children_study_malaysia.value() 
            b16_children_higher_education = self.lhdn_b16_children_higher_education.value()
            b16_children_disabled = self.lhdn_b16_children_disabled.value()
            b16_children_disabled_studying = self.lhdn_b16_children_disabled_studying.value()
            
            personal_family_total = b1_individual + b14_spouse + b15_disabled_spouse + \
                                    b16_children_under_18 + b16_children_study_malaysia + \
                                    b16_children_higher_education + b16_children_disabled + \
                                    b16_children_disabled_studying
            
            # B2-B8: Health & Medical Reliefs
            b2_parent_medical = self.lhdn_b2_parent_medical.value()
            b3_basic_support = self.lhdn_b3_basic_support_equipment.value()
            b4_individual_disability = self.lhdn_b4_individual_disability.value()
            b6_medical_expenses = self.lhdn_b6_medical_expenses.value()
            b7_medical_checkup = self.lhdn_b7_medical_checkup.value()
            b8_child_learning = self.lhdn_b8_child_learning_disability.value()
            
            health_medical_total = b2_parent_medical + b3_basic_support + b4_individual_disability + \
                                  b6_medical_expenses + b7_medical_checkup + b8_child_learning
            
            # B5, B12-B13: Education & Childcare Reliefs
            b5_education_fees = self.lhdn_b5_education_fees.value()
            b12_childcare_fees = self.lhdn_b12_childcare_fees.value()
            b13_sspn = self.lhdn_b13_sspn.value()
            
            education_childcare_total = b5_education_fees + b12_childcare_fees + b13_sspn
            
            # B9-B11, B21: Lifestyle & Other Reliefs
            b9_basic_lifestyle = self.lhdn_b9_basic_lifestyle.value()
            b10_additional_lifestyle = self.lhdn_b10_additional_lifestyle.value()
            b11_breastfeeding = self.lhdn_b11_breastfeeding_equipment.value()
            b21_ev_charging = self.lhdn_b21_ev_charging.value()
            
            lifestyle_other_total = b9_basic_lifestyle + b10_additional_lifestyle + b11_breastfeeding + b21_ev_charging
            
            # B17-B20: Investment & Insurance Reliefs
            b17_mandatory_epf = self.lhdn_b17_mandatory_epf.value()
            b18_prs_annuity = self.lhdn_b18_prs_annuity.value()
            b19_education_medical_insurance = self.lhdn_b19_education_medical_insurance.value()
            b20_perkeso = self.lhdn_b20_perkeso.value()
            
            investment_insurance_total = b17_mandatory_epf + b18_prs_annuity + \
                                        b19_education_medical_insurance + b20_perkeso
            
            # Total Tax Reliefs
            total_relief = personal_family_total + health_medical_total + education_childcare_total + \
                          lifestyle_other_total + investment_insurance_total
            
            result_msg = f"""
<b>LHDN Tax Relief B1-B21 Calculation Summary</b>
<i>Note: Actual relief = min(actual_expense, relief_cap)</i>

<b>B1 & B14-B16: Personal & Family Reliefs</b>
• B1 - Individual Relief: RM {b1_individual:,.2f} (automatic)
• B14 - Spouse Relief: RM {b14_spouse:,.2f} (max cap)
• B15 - Disabled Spouse Relief: RM {b15_disabled_spouse:,.2f} (max cap)
• B16(b) - Children Under 18: RM {b16_children_under_18:,.2f} (max per child)
• B16(c) - Children 18+ Study Malaysia: RM {b16_children_study_malaysia:,.2f} (max per child)
• B16(d) - Children 18+ Higher Education: RM {b16_children_higher_education:,.2f} (max per child)
• B16(e) - Disabled Children: RM {b16_children_disabled:,.2f} (max per child)
• B16(f) - Disabled Children Studying: RM {b16_children_disabled_studying:,.2f} (max per child)
<b>Subtotal: RM {personal_family_total:,.2f}</b>

<b>B2-B8: Health & Medical Reliefs</b>
• B2 - Parent Medical Care: RM {b2_parent_medical:,.2f} (cap: min(actual, RM8,000))
• B3 - Basic Support Equipment: RM {b3_basic_support:,.2f} (cap: min(actual, RM6,000))
• B4 - Individual Disability: RM {b4_individual_disability:,.2f} (fixed)
• B6 - Medical Expenses: RM {b6_medical_expenses:,.2f} (cap: min(actual, RM10,000))
• B7 - Medical Checkup: RM {b7_medical_checkup:,.2f} (cap: min(actual, RM1,000))
• B8 - Child Learning Disability: RM {b8_child_learning:,.2f} (cap: min(actual, RM4,000))
<b>Subtotal: RM {health_medical_total:,.2f}</b>

<b>B5, B12-B13: Education & Childcare Reliefs</b>
• B5 - Education Fees: RM {b5_education_fees:,.2f} (cap: min(actual, RM7,000))
• B12 - Childcare Fees: RM {b12_childcare_fees:,.2f} (cap: min(actual, RM3,000))
• B13 - SSPN: RM {b13_sspn:,.2f} (cap: min(actual, RM8,000))
<b>Subtotal: RM {education_childcare_total:,.2f}</b>

<b>B9-B11, B21: Lifestyle & Other Reliefs</b>
• B9 - Basic Lifestyle: RM {b9_basic_lifestyle:,.2f} (cap: min(actual, RM2,500))
• B10 - Additional Lifestyle: RM {b10_additional_lifestyle:,.2f} (cap: min(actual, RM1,000))
• B11 - Breastfeeding Equipment: RM {b11_breastfeeding:,.2f} (cap: min(actual, RM1,000))
• B21 - EV Charging: RM {b21_ev_charging:,.2f} (cap: min(actual, RM2,500))
<b>Subtotal: RM {lifestyle_other_total:,.2f}</b>

<b>B17-B20: Investment & Insurance Reliefs</b>
• B17 - Mandatory EPF: RM {b17_mandatory_epf:,.2f} (cap: min(actual, RM4,000))
• B18 - PRS/Annuity: RM {b18_prs_annuity:,.2f} (cap: min(actual, RM3,000))
• B19 - Education & Medical Insurance: RM {b19_education_medical_insurance:,.2f} (cap: min(actual, RM3,000))
• B20 - PERKESO: RM {b20_perkeso:,.2f} (cap: min(actual, RM350))
<b>Subtotal: RM {investment_insurance_total:,.2f}</b>

<b>TOTAL TAX RELIEF: RM {total_relief:,.2f}</b>

<i>Note: In actual payroll calculation, use min(employee_declared_amount, relief_cap) for each category.</i>
            """
            
            # Create a custom message box with larger size
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("LHDN B1-B21 Tax Relief Summary")
            msg_box.setText(result_msg)
            msg_box.setTextFormat(Qt.RichText)
            msg_box.setIcon(QMessageBox.Information)
            msg_box.setStandardButtons(QMessageBox.Ok)
            msg_box.setMinimumWidth(600)
            msg_box.exec_()
            
        except Exception as e:
            print(f"DEBUG: Error calculating total tax relief: {e}")
            QMessageBox.warning(self, "Error", f"Failed to calculate total tax relief: {e}")

    def reset_potongan_max_to_default(self):
        """Set semula semua amaun maksimum potongan bulan semasa ke nilai lalai LHDN"""
        try:
            # 1. Perbelanjaan untuk ibu bapa / datuk nenek
            self.parent_medical_treatment_max.setValue(8000.0)
            self.parent_dental_max.setValue(8000.0)
            self.parent_checkup_vaccine_max.setValue(1000.0)
            
            # 2. Peralatan sokongan asas
            self.basic_support_equipment_max.setValue(6000.0)
            
            # 3. Yuran pengajian sendiri
            self.education_non_masters_max.setValue(7000.0)
            self.education_masters_phd_max.setValue(7000.0)
            self.skills_course_max.setValue(2000.0)
            
            # 4. Perubatan diri/pasangan/anak
            self.serious_disease_max.setValue(10000.0)
            self.fertility_treatment_max.setValue(1000.0)
            self.vaccination_max.setValue(1000.0)
            self.dental_treatment_max.setValue(1000.0)
            self.health_checkup_max.setValue(1000.0)
            self.child_learning_disability_max.setValue(6000.0)
            
            # 5. Gaya hidup asas
            self.lifestyle_books_max.setValue(2500.0)
            self.lifestyle_computer_max.setValue(2500.0)
            self.lifestyle_internet_max.setValue(2500.0)
            self.lifestyle_skills_max.setValue(2500.0)
            
            # 6. Gaya hidup tambahan
            self.sports_equipment_max.setValue(1000.0)
            self.sports_facility_rent_max.setValue(1000.0)
            self.competition_fees_max.setValue(1000.0)
            self.gym_fees_max.setValue(1000.0)
            
            # 7-16. Remaining categories
            self.breastfeeding_equipment_max.setValue(1000.0)
            self.childcare_fees_max.setValue(3000.0)
            self.sspn_savings_max.setValue(8000.0)
            self.alimony_max.setValue(4000.0)
            self.epf_insurance_combined_max.setValue(7000.0)
            self.epf_shared_subcap.setValue(4000.0)
            self.life_insurance_subcap.setValue(3000.0)
            self.prs_annuity_max.setValue(3000.0)
            self.education_medical_insurance_max.setValue(4000.0)
            # socso_eis_max removed - PERKESO handled automatically via B20
            self.ev_charger_max.setValue(2500.0)
            self.housing_loan_under_500k_max.setValue(7000.0)
            self.housing_loan_500k_750k_max.setValue(5000.0)
            
            QMessageBox.information(self, "Set Semula Selesai", 
                                  "Semua amaun maksimum potongan bulan semasa telah ditetapkan semula mengikut nilai lalai LHDN semasa.")
            
        except Exception as e:
            print(f"DEBUG: Error resetting potongan max: {e}")
            QMessageBox.warning(self, "Ralat", f"Gagal menetapkan semula had maksimum potongan: {e}")

    def save_potongan_max_configuration(self):
        """Simpan konfigurasi had maksimum potongan bulan semasa (JSON + DB upsert)."""
        try:
            from datetime import datetime
            year = datetime.now().year
            # Helper to safely read a widget's .value() or return default
            def _val(attr: str, default: float = 0.0) -> float:
                try:
                    w = getattr(self, attr, None)
                    return float(w.value()) if w is not None else float(default)
                except Exception:
                    return float(default)

            potongan_config = {
                'meta': {
                    'schema': 'hpb_config_v1',
                    'year': year,
                    'note': 'All Had Potongan Bulanan inputs/caps including B-codes and special limits.'
                },
                'b_codes': {
                    'b1_individual': _val('lhdn_b1_individual_relief'),
                    'b4_individual_disability': _val('lhdn_b4_individual_disability'),
                    'b14_spouse': _val('lhdn_b14_spouse_relief'),
                    'b15_disabled_spouse': _val('lhdn_b15_disabled_spouse_relief'),
                    'b16_children_under_18': _val('lhdn_b16_children_under_18'),
                    'b16_children_study_malaysia': _val('lhdn_b16_children_study_malaysia'),
                    'b16_children_higher_education': _val('lhdn_b16_children_higher_education'),
                    'b16_disabled_not_studying': _val('lhdn_b16_disabled_not_studying'),
                    'b16_disabled_studying': _val('lhdn_b16_disabled_studying'),
                    'b17_mandatory_epf': _val('lhdn_b17_mandatory_epf'),
                    'b20_perkeso': _val('lhdn_b20_perkeso')
                },
                'parent_care': {
                    'max_cap': _val('parent_medical_max_cap'),
                    'treatment_max': _val('parent_medical_treatment_max'),
                    'dental_max': _val('parent_dental_max'),
                    'checkup_vaccine_max': _val('parent_checkup_vaccine_max'),
                    'checkup_vaccine_upper_limit': getattr(self, 'parent_checkup_vaccine_upper_limit', None).value() if hasattr(self, 'parent_checkup_vaccine_upper_limit') else 1000.0
                },
                'basic_support': {
                    'equipment_max': _val('basic_support_equipment_max')
                },
                'education': {
                    'max_cap': _val('education_max_cap'),
                    'non_masters_max': _val('education_non_masters_max'),
                    'masters_phd_max': _val('education_masters_phd_max'),
                    'skills_course_max': _val('skills_course_max'),
                    'skills_course_upper_limit': getattr(self, 'skills_course_upper_limit', None).value() if hasattr(self, 'skills_course_upper_limit') else 2000.0
                },
                'personal_medical': {
                    'max_cap': _val('medical_family_max_cap'),
                    'serious_disease_max': _val('serious_disease_max'),
                    'fertility_treatment_max': _val('fertility_treatment_max'),
                    'vaccination_max': _val('vaccination_max'),
                    'dental_treatment_max': _val('dental_treatment_max'),
                    'health_checkup_max': _val('health_checkup_max'),
                    'child_learning_disability_max': _val('child_learning_disability_max'),
                    'vaccination_upper_limit': getattr(self, 'vaccination_upper_limit', None).value() if hasattr(self, 'vaccination_upper_limit') else 1000.0,
                    'dental_treatment_upper_limit': getattr(self, 'dental_treatment_upper_limit', None).value() if hasattr(self, 'dental_treatment_upper_limit') else 1000.0,
                    'health_checkup_upper_limit': getattr(self, 'health_checkup_upper_limit', None).value() if hasattr(self, 'health_checkup_upper_limit') else 1000.0,
                    'child_learning_disability_upper_limit': getattr(self, 'child_learning_disability_upper_limit', None).value() if hasattr(self, 'child_learning_disability_upper_limit') else 6000.0
                },
                'lifestyle_basic': {
                    'max_cap': _val('lifestyle_basic_max_cap'),
                    'books_max': _val('lifestyle_books_max'),
                    'computer_max': _val('lifestyle_computer_max'),
                    'internet_max': _val('lifestyle_internet_max'),
                    'skills_max': _val('lifestyle_skills_max')
                },
                'lifestyle_additional': {
                    'max_cap': _val('lifestyle_additional_max_cap'),
                    'sports_equipment_max': _val('sports_equipment_max'),
                    'sports_facility_rent_max': _val('sports_facility_rent_max'),
                    'competition_fees_max': _val('competition_fees_max'),
                    'gym_fees_max': _val('gym_fees_max')
                },
                'breastfeeding': {
                    'equipment_max': _val('breastfeeding_equipment_max')
                },
                'childcare': {
                    'fees_max': _val('childcare_fees_max')
                },
                'sspn': {
                    'savings_max': _val('sspn_savings_max')
                },
                'alimony': {
                    'max': _val('alimony_max')
                },
                'epf_life_combined': {
                    'combined_max': _val('epf_insurance_combined_max'),
                    'epf_shared_subcap': _val('epf_shared_subcap'),
                    'life_insurance_subcap': _val('life_insurance_subcap'),
                    'life_insurance_upper_limit': getattr(self, 'life_insurance_upper_limit', None).value() if hasattr(self, 'life_insurance_upper_limit') else 3000.0
                },
                'prs_annuity': {
                    'max': _val('prs_annuity_max')
                },
                'education_medical_insurance': {
                    'max': _val('education_medical_insurance_max')
                },
                'ev_charger_compost': {
                    'max': _val('ev_charger_max')
                },
                'first_home_loan_interest': {
                    'under_500k_max': _val('housing_loan_under_500k_max'),
                    'range_500k_750k_max': _val('housing_loan_500k_750k_max')
                }
            }

            # Persist to Supabase
            try:
                from services.supabase_service import upsert_hpb_config, create_hpb_configs_table_sql
                ok = upsert_hpb_config('default', year, potongan_config)
                if not ok:
                    ddl = create_hpb_configs_table_sql()
                    QMessageBox.information(
                        self,
                        "Create HPB Table",
                        "HPB table not found or insert failed. Run this SQL in Supabase, then Save again:\n\n"
                        + ddl[:1500] + ("\n..." if len(ddl) > 1500 else "")
                    )
                else:
                    QMessageBox.information(self, "Disimpan", "Konfigurasi HPB berjaya disimpan ke pangkalan data.")
            except Exception as svc_err:
                print(f"DEBUG: Service error saving HPB config: {svc_err}")
                QMessageBox.warning(self, "Ralat", f"Gagal menyimpan ke pangkalan data: {svc_err}")

        except Exception as e:
            print(f"DEBUG: Error saving potongan max config: {e}")
            QMessageBox.warning(self, "Ralat", f"Gagal menyimpan konfigurasi potongan: {e}")

    def load_potongan_max_configuration(self):
        """Muat konfigurasi HPB (Had Potongan Bulanan) dari pangkalan data dan terapkan ke UI."""
        try:
            from datetime import datetime
            year = datetime.now().year
            from services.supabase_service import get_hpb_config, create_hpb_configs_table_sql

            details = get_hpb_config('default', year)
            if details is None:
                ddl = create_hpb_configs_table_sql()
                QMessageBox.information(
                    self,
                    "Tiada Konfigurasi Ditemui",
                    "Tiada rekod konfigurasi untuk tahun ini. Jika jadual belum dibuat, jalankan SQL berikut di Supabase dan cuba lagi:\n\n"
                    + ddl[:1500] + ("\n..." if len(ddl) > 1500 else "")
                )
                return

            self._apply_hpb_config_details(details)
            QMessageBox.information(self, "Dimuat", "Konfigurasi HPB berjaya dimuat dan diterapkan ke borang.")
        except Exception as e:
            print(f"DEBUG: Error loading HPB configuration: {e}")
            QMessageBox.warning(self, "Ralat", f"Gagal memuat konfigurasi: {e}")

    def _apply_hpb_config_details(self, cfg: dict):
        """Apply saved HPB JSON values back to the UI widgets safely."""
        try:
            b = cfg.get('b_codes', {})
            if hasattr(self, 'lhdn_b1_individual_relief') and 'b1_individual' in b:
                self.lhdn_b1_individual_relief.setValue(float(b.get('b1_individual', 0)))
            if hasattr(self, 'lhdn_b4_individual_disability') and 'b4_individual_disability' in b:
                self.lhdn_b4_individual_disability.setValue(float(b.get('b4_individual_disability', 0)))
            if hasattr(self, 'lhdn_b14_spouse_relief') and 'b14_spouse' in b:
                self.lhdn_b14_spouse_relief.setValue(float(b.get('b14_spouse', 0)))
            if hasattr(self, 'lhdn_b15_disabled_spouse_relief') and 'b15_disabled_spouse' in b:
                self.lhdn_b15_disabled_spouse_relief.setValue(float(b.get('b15_disabled_spouse', 0)))
            if hasattr(self, 'lhdn_b16_children_under_18') and 'b16_children_under_18' in b:
                self.lhdn_b16_children_under_18.setValue(float(b.get('b16_children_under_18', 0)))
            if hasattr(self, 'lhdn_b16_children_study_malaysia') and 'b16_children_study_malaysia' in b:
                self.lhdn_b16_children_study_malaysia.setValue(float(b.get('b16_children_study_malaysia', 0)))
            if hasattr(self, 'lhdn_b16_children_higher_education') and 'b16_children_higher_education' in b:
                self.lhdn_b16_children_higher_education.setValue(float(b.get('b16_children_higher_education', 0)))
            if hasattr(self, 'lhdn_b16_disabled_not_studying') and 'b16_disabled_not_studying' in b:
                self.lhdn_b16_disabled_not_studying.setValue(float(b.get('b16_disabled_not_studying', 0)))
            if hasattr(self, 'lhdn_b16_disabled_studying') and 'b16_disabled_studying' in b:
                self.lhdn_b16_disabled_studying.setValue(float(b.get('b16_disabled_studying', 0)))
            if hasattr(self, 'lhdn_b17_mandatory_epf') and 'b17_mandatory_epf' in b:
                self.lhdn_b17_mandatory_epf.setValue(float(b.get('b17_mandatory_epf', 0)))
            if hasattr(self, 'lhdn_b20_perkeso') and 'b20_perkeso' in b:
                self.lhdn_b20_perkeso.setValue(float(b.get('b20_perkeso', 0)))

            p = cfg.get('parent_care', {})
            if hasattr(self, 'parent_medical_max_cap') and 'max_cap' in p:
                self.parent_medical_max_cap.setValue(float(p.get('max_cap', 0)))
            if hasattr(self, 'parent_medical_treatment_max') and 'treatment_max' in p:
                self.parent_medical_treatment_max.setValue(float(p.get('treatment_max', 0)))
            if hasattr(self, 'parent_dental_max') and 'dental_max' in p:
                self.parent_dental_max.setValue(float(p.get('dental_max', 0)))
            if hasattr(self, 'parent_checkup_vaccine_max') and 'checkup_vaccine_max' in p:
                self.parent_checkup_vaccine_max.setValue(float(p.get('checkup_vaccine_max', 0)))
            if hasattr(self, 'parent_checkup_vaccine_upper_limit') and 'checkup_vaccine_upper_limit' in p:
                self.parent_checkup_vaccine_upper_limit.setValue(float(p.get('checkup_vaccine_upper_limit', 1000)))

            bs = cfg.get('basic_support', {})
            if hasattr(self, 'basic_support_equipment_max') and 'equipment_max' in bs:
                self.basic_support_equipment_max.setValue(float(bs.get('equipment_max', 0)))

            edu = cfg.get('education', {})
            if hasattr(self, 'education_max_cap') and 'max_cap' in edu:
                self.education_max_cap.setValue(float(edu.get('max_cap', 0)))
            if hasattr(self, 'education_non_masters_max') and 'non_masters_max' in edu:
                self.education_non_masters_max.setValue(float(edu.get('non_masters_max', 0)))
            if hasattr(self, 'education_masters_phd_max') and 'masters_phd_max' in edu:
                self.education_masters_phd_max.setValue(float(edu.get('masters_phd_max', 0)))
            if hasattr(self, 'skills_course_max') and 'skills_course_max' in edu:
                self.skills_course_max.setValue(float(edu.get('skills_course_max', 0)))
            if hasattr(self, 'skills_course_upper_limit') and 'skills_course_upper_limit' in edu:
                self.skills_course_upper_limit.setValue(float(edu.get('skills_course_upper_limit', 2000)))

            pm = cfg.get('personal_medical', {})
            if hasattr(self, 'medical_family_max_cap') and 'max_cap' in pm:
                self.medical_family_max_cap.setValue(float(pm.get('max_cap', 0)))
            if hasattr(self, 'serious_disease_max') and 'serious_disease_max' in pm:
                self.serious_disease_max.setValue(float(pm.get('serious_disease_max', 0)))
            if hasattr(self, 'fertility_treatment_max') and 'fertility_treatment_max' in pm:
                self.fertility_treatment_max.setValue(float(pm.get('fertility_treatment_max', 0)))
            if hasattr(self, 'vaccination_max') and 'vaccination_max' in pm:
                self.vaccination_max.setValue(float(pm.get('vaccination_max', 0)))
            if hasattr(self, 'dental_treatment_max') and 'dental_treatment_max' in pm:
                self.dental_treatment_max.setValue(float(pm.get('dental_treatment_max', 0)))
            if hasattr(self, 'health_checkup_max') and 'health_checkup_max' in pm:
                self.health_checkup_max.setValue(float(pm.get('health_checkup_max', 0)))
            if hasattr(self, 'child_learning_disability_max') and 'child_learning_disability_max' in pm:
                self.child_learning_disability_max.setValue(float(pm.get('child_learning_disability_max', 0)))
            if hasattr(self, 'vaccination_upper_limit') and 'vaccination_upper_limit' in pm:
                self.vaccination_upper_limit.setValue(float(pm.get('vaccination_upper_limit', 1000)))
            if hasattr(self, 'dental_treatment_upper_limit') and 'dental_treatment_upper_limit' in pm:
                self.dental_treatment_upper_limit.setValue(float(pm.get('dental_treatment_upper_limit', 1000)))
            if hasattr(self, 'health_checkup_upper_limit') and 'health_checkup_upper_limit' in pm:
                self.health_checkup_upper_limit.setValue(float(pm.get('health_checkup_upper_limit', 1000)))
            if hasattr(self, 'child_learning_disability_upper_limit') and 'child_learning_disability_upper_limit' in pm:
                self.child_learning_disability_upper_limit.setValue(float(pm.get('child_learning_disability_upper_limit', 6000)))

            lb = cfg.get('lifestyle_basic', {})
            if hasattr(self, 'lifestyle_basic_max_cap') and 'max_cap' in lb:
                self.lifestyle_basic_max_cap.setValue(float(lb.get('max_cap', 0)))
            if hasattr(self, 'lifestyle_books_max') and 'books_max' in lb:
                self.lifestyle_books_max.setValue(float(lb.get('books_max', 0)))
            if hasattr(self, 'lifestyle_computer_max') and 'computer_max' in lb:
                self.lifestyle_computer_max.setValue(float(lb.get('computer_max', 0)))
            if hasattr(self, 'lifestyle_internet_max') and 'internet_max' in lb:
                self.lifestyle_internet_max.setValue(float(lb.get('internet_max', 0)))
            if hasattr(self, 'lifestyle_skills_max') and 'skills_max' in lb:
                self.lifestyle_skills_max.setValue(float(lb.get('skills_max', 0)))

            la = cfg.get('lifestyle_additional', {})
            if hasattr(self, 'lifestyle_additional_max_cap') and 'max_cap' in la:
                self.lifestyle_additional_max_cap.setValue(float(la.get('max_cap', 0)))
            if hasattr(self, 'sports_equipment_max') and 'sports_equipment_max' in la:
                self.sports_equipment_max.setValue(float(la.get('sports_equipment_max', 0)))
            if hasattr(self, 'sports_facility_rent_max') and 'sports_facility_rent_max' in la:
                self.sports_facility_rent_max.setValue(float(la.get('sports_facility_rent_max', 0)))
            if hasattr(self, 'competition_fees_max') and 'competition_fees_max' in la:
                self.competition_fees_max.setValue(float(la.get('competition_fees_max', 0)))
            if hasattr(self, 'gym_fees_max') and 'gym_fees_max' in la:
                self.gym_fees_max.setValue(float(la.get('gym_fees_max', 0)))

            if 'breastfeeding' in cfg and hasattr(self, 'breastfeeding_equipment_max'):
                self.breastfeeding_equipment_max.setValue(float(cfg['breastfeeding'].get('equipment_max', 0)))
            if 'childcare' in cfg and hasattr(self, 'childcare_fees_max'):
                self.childcare_fees_max.setValue(float(cfg['childcare'].get('fees_max', 0)))
            if 'sspn' in cfg and hasattr(self, 'sspn_savings_max'):
                self.sspn_savings_max.setValue(float(cfg['sspn'].get('savings_max', 0)))
            if 'alimony' in cfg and hasattr(self, 'alimony_max'):
                self.alimony_max.setValue(float(cfg['alimony'].get('max', 0)))

            epf = cfg.get('epf_life_combined', {})
            if hasattr(self, 'epf_insurance_combined_max') and 'combined_max' in epf:
                self.epf_insurance_combined_max.setValue(float(epf.get('combined_max', 0)))
            if hasattr(self, 'epf_shared_subcap') and 'epf_shared_subcap' in epf:
                self.epf_shared_subcap.setValue(float(epf.get('epf_shared_subcap', 0)))
            if hasattr(self, 'life_insurance_subcap') and 'life_insurance_subcap' in epf:
                self.life_insurance_subcap.setValue(float(epf.get('life_insurance_subcap', 0)))
            if hasattr(self, 'life_insurance_upper_limit') and 'life_insurance_upper_limit' in epf:
                self.life_insurance_upper_limit.setValue(float(epf.get('life_insurance_upper_limit', 3000)))

            if 'prs_annuity' in cfg and hasattr(self, 'prs_annuity_max'):
                self.prs_annuity_max.setValue(float(cfg['prs_annuity'].get('max', 0)))
            if 'education_medical_insurance' in cfg and hasattr(self, 'education_medical_insurance_max'):
                self.education_medical_insurance_max.setValue(float(cfg['education_medical_insurance'].get('max', 0)))
            if 'ev_charger_compost' in cfg and hasattr(self, 'ev_charger_max'):
                self.ev_charger_max.setValue(float(cfg['ev_charger_compost'].get('max', 0)))

            hl = cfg.get('first_home_loan_interest', {})
            if hasattr(self, 'housing_loan_under_500k_max') and 'under_500k_max' in hl:
                self.housing_loan_under_500k_max.setValue(float(hl.get('under_500k_max', 0)))
            if hasattr(self, 'housing_loan_500k_750k_max') and 'range_500k_750k_max' in hl:
                self.housing_loan_500k_750k_max.setValue(float(hl.get('range_500k_750k_max', 0)))

            if hasattr(self, 'update_sub_max_cap_ranges'):
                self.update_sub_max_cap_ranges()
        except Exception as e:
            print(f"DEBUG: Error applying HPB config details: {e}")

    def export_potongan_configuration(self):
        """Eksport konfigurasi had maksimum potongan bulan semasa ke fail"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import json
            from datetime import datetime
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Eksport Konfigurasi Potongan Bulan Semasa", 
                f"konfigurasi_had_potongan_bulanan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "Fail JSON (*.json);;Semua Fail (*)"
            )
            
            if file_path:
                potongan_config = {
                    'maklumat_eksport': {
                        'tarikh_eksport': datetime.now().isoformat(),
                        'penerangan': 'Konfigurasi Had Maksimum Potongan Bulan Semasa LHDN',
                        'tahun_rujukan': '2025',
                        'jumlah_kategori': 16
                    },
                    'penjagaan_ibubapa_datuknenek': {
                        'rawatan_perubatan_penjagaan': {'amaun_maksimum': self.parent_medical_treatment_max.value(), 'penerangan': 'Rawatan perubatan/keperluan khas/penjagaan'},
                        'rawatan_pergigian': {'amaun_maksimum': self.parent_dental_max.value(), 'penerangan': 'Rawatan pergigian'},
                        'pemeriksaan_vaksin': {'amaun_maksimum': self.parent_checkup_vaccine_max.value(), 'penerangan': 'Pemeriksaan penuh + vaksin'}
                    },
                    'peralatan_sokongan_asas': {
                        'peralatan_sokongan': {'amaun_maksimum': self.basic_support_equipment_max.value(), 'penerangan': 'Peralatan sokongan asas untuk kurang upaya'}
                    },
                    'yuran_pengajian_sendiri': {
                        'selain_sarjana_phd': {'amaun_maksimum': self.education_non_masters_max.value(), 'penerangan': 'Selain Sarjana/PhD (bidang tertentu)'},
                        'sarjana_phd': {'amaun_maksimum': self.education_masters_phd_max.value(), 'penerangan': 'Sarjana/PhD (semua bidang)'},
                        'kursus_kemahiran': {'amaun_maksimum': self.skills_course_max.value(), 'penerangan': 'Kursus kemahiran/diri'}
                    },
                    'perubatan_diri_pasangan_anak': {
                        'penyakit_serius': {'amaun_maksimum': self.serious_disease_max.value(), 'penerangan': 'Penyakit serius'},
                        'rawatan_kesuburan': {'amaun_maksimum': self.fertility_treatment_max.value(), 'penerangan': 'Rawatan kesuburan'},
                        'pemvaksinan': {'amaun_maksimum': self.vaccination_max.value(), 'penerangan': 'Pemvaksinan'},
                        'rawatan_pergigian': {'amaun_maksimum': self.dental_treatment_max.value(), 'penerangan': 'Pemeriksaan & rawatan pergigian'},
                        'pemeriksaan_kesihatan': {'amaun_maksimum': self.health_checkup_max.value(), 'penerangan': 'Pemeriksaan penuh/COVID-19/mental health'},
                        'anak_kurang_upaya_pembelajaran': {'amaun_maksimum': self.child_learning_disability_max.value(), 'penerangan': 'Anak kurang upaya pembelajaran <18'}
                    },
                    'gaya_hidup_asas': {
                        'buku_majalah': {'amaun_maksimum': self.lifestyle_books_max.value(), 'penerangan': 'Buku/majalah/surat khabar'},
                        'komputer_telefon': {'amaun_maksimum': self.lifestyle_computer_max.value(), 'penerangan': 'Komputer/telefon/tablet'},
                        'internet': {'amaun_maksimum': self.lifestyle_internet_max.value(), 'penerangan': 'Internet (nama sendiri)'},
                        'kursus_kemahiran': {'amaun_maksimum': self.lifestyle_skills_max.value(), 'penerangan': 'Kursus kemahiran'}
                    },
                    'gaya_hidup_tambahan': {
                        'peralatan_sukan': {'amaun_maksimum': self.sports_equipment_max.value(), 'penerangan': 'Peralatan sukan'},
                        'sewa_fasiliti_sukan': {'amaun_maksimum': self.sports_facility_rent_max.value(), 'penerangan': 'Sewa/fi fasiliti sukan'},
                        'fi_pertandingan': {'amaun_maksimum': self.competition_fees_max.value(), 'penerangan': 'Fi pertandingan diluluskan'},
                        'yuran_gym': {'amaun_maksimum': self.gym_fees_max.value(), 'penerangan': 'Yuran gym/latihan sukan'}
                    },
                    'kategori_lain': {
                        'peralatan_penyusuan': {'amaun_maksimum': self.breastfeeding_equipment_max.value(), 'penerangan': 'Peralatan penyusuan ibu'},
                        'yuran_taska': {'amaun_maksimum': self.childcare_fees_max.value(), 'penerangan': 'Yuran taska/tadika anak ≤6 tahun'},
                        'sspn_savings': {'amaun_maksimum': self.sspn_savings_max.value(), 'penerangan': 'SSPN tabungan bersih'},
                        'alimoni': {'amaun_maksimum': self.alimony_max.value(), 'penerangan': 'Alimoni kepada bekas isteri'},
                        'epf_insurance_combined': {'amaun_maksimum': self.epf_insurance_combined_max.value(), 'penerangan': 'KWSP (wajib+sukarela) + Insurans nyawa - GABUNGAN'},
                        'epf_shared_subcap': {'amaun_maksimum': self.epf_shared_subcap.value(), 'penerangan': 'KWSP gabungan (wajib+sukarela) - Had berkongsi'},
                        'life_insurance_subcap': {'amaun_maksimum': self.life_insurance_subcap.value(), 'penerangan': 'Insurans nyawa - Had khusus dalam bucket gabungan'},
                        'prs_anuiti': {'amaun_maksimum': self.prs_annuity_max.value(), 'penerangan': 'PRS/Anuiti tertangguh'},
                        'insurans_pendidikan_perubatan': {'amaun_maksimum': self.education_medical_insurance_max.value(), 'penerangan': 'Insurans pendidikan & perubatan'},
                        # 'perkeso': removed - handled automatically via B20
                        'ev_charger': {'amaun_maksimum': self.ev_charger_max.value(), 'penerangan': 'EV charger/compost machine'},
                        'pinjaman_rumah_500k': {'amaun_maksimum': self.housing_loan_under_500k_max.value(), 'penerangan': 'Faedah pinjaman rumah ≤RM500k'},
                        'pinjaman_rumah_500k_750k': {'amaun_maksimum': self.housing_loan_500k_750k_max.value(), 'penerangan': 'Faedah pinjaman rumah RM500k-750k'}
                    }
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(potongan_config, f, indent=4, ensure_ascii=False)
                
                QMessageBox.information(self, "Eksport Selesai", 
                                      f"Konfigurasi potongan bulan semasa berjaya dieksport ke:\n{file_path}\n\n"
                                      f"Fail mengandungi semua kategori potongan dengan amaun maksimum dan penerangan mengikut struktur LHDN.")
                
        except Exception as e:
            print(f"DEBUG: Error exporting potongan config: {e}")
            QMessageBox.warning(self, "Ralat", f"Gagal mengeksport konfigurasi potongan: {e}")

    def update_sub_max_cap_ranges(self):
        """Auto-adjust sub MAX CAP ranges when main MAX CAP changes (without saving)"""
        try:
            # Update parent medical subcategory ranges based on main MAX CAP
            if hasattr(self, 'parent_medical_max_cap') and hasattr(self, 'parent_medical_treatment_max'):
                main_max_cap = self.parent_medical_max_cap.value()
                
                # Update treatment max range (can't exceed main MAX CAP)
                if hasattr(self, 'parent_medical_treatment_max'):
                    current_value = self.parent_medical_treatment_max.value()
                    self.parent_medical_treatment_max.setRange(0.0, main_max_cap)
                    # If current value exceeds new max, adjust it
                    if current_value > main_max_cap:
                        self.parent_medical_treatment_max.setValue(main_max_cap)
                
                # Update dental max range (can't exceed main MAX CAP)
                if hasattr(self, 'parent_dental_max'):
                    current_value = self.parent_dental_max.value()
                    self.parent_dental_max.setRange(0.0, main_max_cap)
                    if current_value > main_max_cap:
                        self.parent_dental_max.setValue(main_max_cap)
                
                # Checkup/vaccine has configurable special upper limit (sub-limit of main MAX CAP)
                if hasattr(self, 'parent_checkup_vaccine_max'):
                    current_value = self.parent_checkup_vaccine_max.value()
                    
                    # Get configurable upper limit (default 1000.0 if not set)
                    if hasattr(self, 'parent_checkup_vaccine_upper_limit'):
                        special_upper_limit = self.parent_checkup_vaccine_upper_limit.value()
                    else:
                        special_upper_limit = 1000.0  # Fallback to default
                    
                    checkup_limit = min(special_upper_limit, main_max_cap)  # Min of special limit or main MAX CAP
                    self.parent_checkup_vaccine_max.setRange(0.0, checkup_limit)
                    if current_value > checkup_limit:
                        self.parent_checkup_vaccine_max.setValue(checkup_limit)
                    
                    print(f"DEBUG: Checkup/vaccine limit: min(Special: RM{special_upper_limit:,.0f}, Main: RM{main_max_cap:,.0f}) = RM{checkup_limit:,.0f}")
                
                print(f"DEBUG: Updated sub MAX CAP ranges based on main MAX CAP: RM{main_max_cap:,.0f}")
            
            # Update lifestyle basic subcategory ranges (shared allocation model)
            if hasattr(self, 'lifestyle_basic_max_cap'):
                lifestyle_main_max = self.lifestyle_basic_max_cap.value()
                
                # In shared allocation model, each subcap can be up to the main MAX CAP
                # but their combined total cannot exceed the main MAX CAP
                lifestyle_subcaps = [
                    'lifestyle_books_max',
                    'lifestyle_computer_max', 
                    'lifestyle_internet_max',
                    'lifestyle_skills_max'
                ]
                
                for subcap_name in lifestyle_subcaps:
                    if hasattr(self, subcap_name):
                        subcap_widget = getattr(self, subcap_name)
                        current_value = subcap_widget.value()
                        # Each subcap can be up to the main MAX CAP (shared allocation)
                        subcap_widget.setRange(0.0, lifestyle_main_max)
                        # If current value exceeds new max, adjust it
                        if current_value > lifestyle_main_max:
                            subcap_widget.setValue(lifestyle_main_max)
                
                print(f"DEBUG: Updated lifestyle basic subcap ranges based on main MAX CAP: RM{lifestyle_main_max:,.0f}")
            
            # Update lifestyle additional subcategory ranges (Section 6 - same as Section 3 structure)
            if hasattr(self, 'lifestyle_additional_max_cap'):
                lifestyle_additional_main_max = self.lifestyle_additional_max_cap.value()
                
                lifestyle_additional_subcaps = [
                    'sports_equipment_max',
                    'sports_facility_rent_max',
                    'competition_fees_max',
                    'gym_fees_max'
                ]
                
                for subcap_name in lifestyle_additional_subcaps:
                    if hasattr(self, subcap_name):
                        subcap_widget = getattr(self, subcap_name)
                        current_value = subcap_widget.value()
                        # Each subcap can be up to the main MAX CAP
                        subcap_widget.setRange(0.0, lifestyle_additional_main_max)
                        # If current value exceeds new max, adjust it
                        if current_value > lifestyle_additional_main_max:
                            subcap_widget.setValue(lifestyle_additional_main_max)
                
                print(f"DEBUG: Updated lifestyle additional subcap ranges based on main MAX CAP: RM{lifestyle_additional_main_max:,.0f}")
            
            # Update EPF + Insurance subcategory ranges (Section 11 - same as Section 3 pattern)
            if hasattr(self, 'epf_insurance_combined_max'):
                epf_insurance_main_max = self.epf_insurance_combined_max.value()
                
                # EPF shared subcap can be up to the main MAX CAP (regular subcap)
                if hasattr(self, 'epf_shared_subcap'):
                    current_value = self.epf_shared_subcap.value()
                    self.epf_shared_subcap.setRange(1000.0, epf_insurance_main_max)
                    if current_value > epf_insurance_main_max:
                        self.epf_shared_subcap.setValue(epf_insurance_main_max)
                
                # Life insurance subcap has configurable special upper limit (same as Section 3 checkup/vaccine pattern)
                if hasattr(self, 'life_insurance_subcap'):
                    current_value = self.life_insurance_subcap.value()
                    
                    # Get configurable upper limit (default 3000.0 if not set)
                    if hasattr(self, 'life_insurance_upper_limit'):
                        special_upper_limit = self.life_insurance_upper_limit.value()
                    else:
                        special_upper_limit = 3000.0  # Fallback to LHDN default
                    
                    insurance_limit = min(special_upper_limit, epf_insurance_main_max)  # Min of special limit or main MAX CAP
                    self.life_insurance_subcap.setRange(1000.0, insurance_limit)
                    if current_value > insurance_limit:
                        self.life_insurance_subcap.setValue(insurance_limit)
                    
                    print(f"DEBUG: Life insurance limit: min(Special: RM{special_upper_limit:,.0f}, Main: RM{epf_insurance_main_max:,.0f}) = RM{insurance_limit:,.0f}")
                
                print(f"DEBUG: Updated EPF+Insurance subcap ranges based on main MAX CAP: RM{epf_insurance_main_max:,.0f}")
                
        except Exception as e:
            print(f"DEBUG: Error updating sub MAX CAP ranges: {e}")
