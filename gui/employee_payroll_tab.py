from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox, QFileDialog, QGroupBox, QLabel, QHeaderView, QComboBox, QTabWidget
from PyQt5.QtCore import Qt
from services.supabase_service import get_payroll_runs
from services.payslip_generator import generate_payslip_for_employee

class EmployeePayrollTab(QWidget):
    def __init__(self, user_email=None):
        super().__init__()
        self.user_email = user_email.lower() if user_email else None
        self.setObjectName("EmployeePayrollTab")
        # print(f"DEBUG: Starting EmployeePayrollTab.__init__ with user_email: {self.user_email}")
        try:
            self.init_ui()
            # print("DEBUG: EmployeePayrollTab.init_ui complete")
        except Exception as e:
            # print(f"DEBUG: Error in EmployeePayrollTab.init_ui: {str(e)}")
            raise

    def init_ui(self):
        # print("DEBUG: Starting EmployeePayrollTab.init_ui")
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header Section
        header_group = QGroupBox("💰 Payroll History")
        header_group
        
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(16, 16, 16, 16)
        
        header_info = QLabel("View your payroll history and download payslips. Includes statutory deductions (EPF, SOCSO, EIS, PCB) and optional contributions (SIP, PRS, Insurance). All amounts are displayed in Malaysian Ringgit (RM).")
        header_info
        header_info.setWordWrap(True)
        header_layout.addWidget(header_info)
        header_group.setLayout(header_layout)
        main_layout.addWidget(header_group)

        # Payroll Records Section with Year + Month subtabs
        table_group = QGroupBox("📊 Payroll Records")
        group_layout = QVBoxLayout(); group_layout.setContentsMargins(16, 16, 16, 16); group_layout.setSpacing(8)

        # Top filter row: Year selector + Refresh
        filt_row = QHBoxLayout(); filt_row.setSpacing(8)
        filt_row.addWidget(QLabel("Year:"))
        self.year_combo = QComboBox(); filt_row.addWidget(self.year_combo)
        filt_row.addStretch()
        refresh_button = QPushButton("🔄 Refresh Data"); filt_row.addWidget(refresh_button)
        group_layout.addLayout(filt_row)

        # Month tabs: All + Jan–Dec
        self.payroll_month_tabs = QTabWidget()
        self.month_tables = {}
        # All tab initially
        all_tab = QWidget(); all_layout = QVBoxLayout(); all_layout.setContentsMargins(0,0,0,0)
        self.payroll_table = self._new_payroll_table()
        all_layout.addWidget(self.payroll_table)
        all_tab.setLayout(all_layout)
        self.payroll_month_tabs.addTab(all_tab, "All")
        group_layout.addWidget(self.payroll_month_tabs)

        table_group.setLayout(group_layout)
        main_layout.addWidget(table_group)

        # Wiring
        refresh_button.clicked.connect(self.load_payroll_history)
        self.year_combo.currentIndexChanged.connect(self._on_year_changed)
        self.payroll_month_tabs.currentChanged.connect(lambda _: self._populate_current_tab())

        self.setLayout(main_layout)
        if self.user_email:
            self.load_payroll_history()

    def set_user_email(self, email):
        # print(f"DEBUG: Setting user_email to {email} in EmployeePayrollTab")
        self.user_email = email.lower()
        self.load_payroll_history()

    def load_payroll_history(self):
        # print(f"DEBUG: Loading payroll history for {self.user_email}")
        try:
            self._all_runs = get_payroll_runs(self.user_email) or []
            # Build year options from data
            years = []
            for r in self._all_runs:
                try:
                    y = int(str(r.get('payroll_date', '')).split('-')[0])
                    if y not in years:
                        years.append(y)
                except Exception:
                    continue
            years.sort(reverse=True)
            # Populate year combo once or when changed
            current = self.year_combo.currentText()
            self.year_combo.blockSignals(True)
            self.year_combo.clear()
            for y in years:
                self.year_combo.addItem(str(y))
            self.year_combo.blockSignals(False)
            # Select most recent year by default
            if years:
                if current and current in [str(y) for y in years]:
                    self.year_combo.setCurrentText(current)
                else:
                    self.year_combo.setCurrentIndex(0)
            # Ensure month tabs for selected year
            self._ensure_month_tabs_for_year(self._selected_year())
            # Populate tables
            self._populate_all_tab()
            self._populate_month_tabs()
        except Exception as e:
            # print(f"DEBUG: Error loading payroll history: {str(e)}")
            try:
                self.payroll_table.setRowCount(0)
            except Exception:
                pass
            QMessageBox.warning(self, "Error", f"Failed to load payroll history: {str(e)}")

    def _selected_year(self):
        try:
            return int(self.year_combo.currentText())
        except Exception:
            return None

    def _on_year_changed(self, _idx):
        y = self._selected_year()
        if y:
            self._ensure_month_tabs_for_year(y)
            self._populate_all_tab()
            self._populate_month_tabs()

    def _ensure_month_tabs_for_year(self, year: int):
        # Keep only the first tab (All), rebuild month tabs for Jan–Dec
        try:
            while self.payroll_month_tabs.count() > 1:
                self.payroll_month_tabs.removeTab(1)
        except Exception:
            pass
        self.month_tables = {}
        for m in range(1, 13):
            tab = QWidget(); lay = QVBoxLayout(); lay.setContentsMargins(0,0,0,0)
            tbl = self._new_payroll_table(); lay.addWidget(tbl); tab.setLayout(lay)
            self.payroll_month_tabs.addTab(tab, self._month_short_name(m))
            self.month_tables[(year, m)] = tbl

    def _populate_all_tab(self):
        y = self._selected_year()
        runs = [r for r in (self._all_runs or []) if str(r.get('payroll_date','')).startswith(f"{y}-")] if y else (self._all_runs or [])
        self._populate_table(self.payroll_table, runs)

    def _populate_month_tabs(self):
        y = self._selected_year()
        for m in range(1, 13):
            tbl = self.month_tables.get((y, m))
            if not tbl:
                continue
            runs = []
            for r in (self._all_runs or []):
                d = str(r.get('payroll_date', ''))
                if len(d) >= 7:
                    try:
                        yy = int(d[:4]); mm = int(d[5:7])
                        if yy == y and mm == m:
                            runs.append(r)
                    except Exception:
                        pass
            self._populate_table(tbl, runs)

    def _new_payroll_table(self):
        tbl = QTableWidget()
        tbl.setColumnCount(19)
        tbl.setHorizontalHeaderLabels([
            "Payroll Date",
            "Gross Salary", "Allowances",
            "Unpaid Days", "Unpaid Deduction",
            "EPF Employee", "EPF Employer", "SOCSO Employee", "SOCSO Employer",
            "EIS Employee", "EIS Employer",
            "PCB",
            "SIP", "Additional EPF", "PRS", "Insurance", "Other Deductions",
            "Net Salary", "Payslip"
        ])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        tbl.horizontalHeader().setStretchLastSection(True)
        tbl.setSortingEnabled(True)
        return tbl

    def _month_short_name(self, m: int) -> str:
        names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        try:
            mi = int(m)
            if 1 <= mi <= 12:
                return names[mi-1]
        except Exception:
            pass
        return str(m)

    def _populate_current_tab(self):
        # No-op placeholder; sorting happens per-table; we repopulate on year change/refresh
        pass

    def _populate_table(self, table: QTableWidget, payroll_runs):
        table.setRowCount(len(payroll_runs))
        for row, payroll in enumerate(payroll_runs):
            allowances = payroll.get("allowances", {})
            if allowances:
                if isinstance(allowances, dict):
                    allowance_items = []
                    for k, v in allowances.items():
                        if v is not None:
                            try:
                                amount = float(v)
                                allowance_items.append(f"{k.replace('_', ' ').title()}: RM {amount:.2f}")
                            except (ValueError, TypeError):
                                continue
                    allowances_text = ", ".join(allowance_items) if allowance_items else "None"
                else:
                    allowances_text = str(allowances)
            else:
                allowances_text = "None"

            employee_name = "Employee"
            if "employee" in payroll and payroll["employee"]:
                employee_name = payroll["employee"].get("full_name", "Employee")

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
                    days = float(value)
                    return str(int(days)) if days == int(days) else f"{days:.1f}"
                except (ValueError, TypeError):
                    return "0"

            items = [
                payroll.get("payroll_date"),
                safe_format_currency(payroll.get('gross_salary')),
                allowances_text,
                safe_format_days(payroll.get('unpaid_leave_days')),
                safe_format_currency(payroll.get('unpaid_leave_deduction')),
                safe_format_currency(payroll.get('epf_employee')),
                safe_format_currency(payroll.get('epf_employer')),
                safe_format_currency(payroll.get('socso_employee')),
                safe_format_currency(payroll.get('socso_employer')),
                safe_format_currency(payroll.get('eis_employee')),
                safe_format_currency(payroll.get('eis_employer')),
                safe_format_currency(payroll.get('pcb', payroll.get('pcb_tax', payroll.get('pcb_amount')))),
                safe_format_currency(payroll.get('sip_deduction')),
                safe_format_currency(payroll.get('additional_epf_deduction')),
                safe_format_currency(payroll.get('prs_deduction')),
                safe_format_currency(payroll.get('insurance_premium')),
                safe_format_currency(payroll.get('other_deductions')),
                safe_format_currency(payroll.get('net_salary'))
            ]
            for col, value in enumerate(items):
                it = QTableWidgetItem(str(value)); it.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, it)
            download_button = QPushButton("📄 Generate")
            download_button.setToolTip("Generate and download payslip PDF")
            employee_id = payroll.get("employee_id")
            payroll_run_id = payroll.get("id")
            download_button.clicked.connect(lambda _, emp_id=employee_id, run_id=payroll_run_id, emp_name=employee_name: self.generate_payslip(emp_id, run_id, emp_name))
            table.setCellWidget(row, 18, download_button)

    def generate_payslip(self, employee_id, payroll_run_id, employee_name="Employee"):
        """Generate payslip for the employee's payroll run"""
        try:
            # print(f"DEBUG: Generating payslip for employee {employee_id}, payroll run {payroll_run_id}")
            
            if not employee_id or not payroll_run_id:
                QMessageBox.warning(self, "Error", "Missing employee or payroll information.")
                return
            
            # Let user choose save location
            default_filename = f"Payslip_{employee_name.replace(' ', '_')}_{payroll_run_id}.pdf"
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Save Payslip",
                default_filename,
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
                        "Failed to generate payslip. Please check the data and try again."
                    )
                    # print(f"DEBUG: Failed to generate payslip for {employee_id}")
            else:
                # print("DEBUG: User cancelled payslip generation")
                pass
                
        except Exception as e:
            # print(f"DEBUG: Error generating payslip: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate payslip: {str(e)}")
