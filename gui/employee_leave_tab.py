# In gui/employee_leave_tab.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QComboBox, QDateEdit, QTextEdit, QHeaderView,
    QPushButton, QFileDialog, QTabWidget, QTableWidget, QTableWidgetItem, QHBoxLayout, QMessageBox,
    QScrollArea, QFrame, QFormLayout, QGroupBox, QLineEdit, QDialog, QSpinBox, QCheckBox, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDate
from datetime import datetime
import pytz
from services.supabase_service import submit_leave_request, fetch_user_leave_requests, upload_document_to_bucket, convert_utc_to_kl, get_individual_employee_leave_balance, get_individual_employee_sick_leave_balance, calculate_working_days
import os

KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')
DEBUG_UI = os.getenv('HRMS_DEBUG_UI', '0') == '1'

class EmployeeLeaveTab(QWidget):
    def __init__(self, user_email=None):
        super().__init__()
        self.user_email = user_email.lower() if user_email else None
        # print(f"DEBUG: Starting EmployeeLeaveTab.__init__ with user_email: {self.user_email}")
        self.document_url = None
        try:
            self.init_ui()
            # print("DEBUG: EmployeeLeaveTab.init_ui complete")
        except Exception as e:
            # print(f"DEBUG: Error in EmployeeLeaveTab.init_ui: {str(e)}")
            raise

    def init_ui(self):
        # print("DEBUG: Starting EmployeeLeaveTab.init_ui")
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        # Add dynamic tab styling for proper text fitting
        self.tabs

        self.form_tab = QWidget()
        self.records_tab = QWidget()

        self.tabs.addTab(self.form_tab, "Submit Leave Request")
        self.tabs.addTab(self.records_tab, "My Leave Requests")
        
        # Add dynamic tab width calculation

        self.init_form_tab()
        self.init_records_tab()

        layout.addWidget(self.tabs)
        self.setLayout(layout)

        self.load_leave_records()
        # Load leave balances when tab is initialized
        self.load_leave_balances()
        
        # Initialize dates based on default duration
        self.update_dates_from_duration(1)

    def init_form_tab(self):
        # Create main layout for the tab
        main_layout = QVBoxLayout()
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Create content widget
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # Dynamic leave types with refresh
        self.leave_type = QComboBox()
        self._populate_leave_types_dynamic()
        self.leave_type.currentTextChanged.connect(self.on_leave_type_changed)
        self.leave_types_refresh_btn = QPushButton("Refresh Types")
        self.leave_types_refresh_btn.setToolTip("Reload active leave types")
        self.leave_types_refresh_btn.clicked.connect(lambda: self._populate_leave_types_dynamic(force=True))

        # Half-day leave controls
        self.half_day_checkbox = QCheckBox("Half Day Leave (counts as 0.5 day)")
        self.half_day_checkbox.setToolTip("Check this to mark the request as a half-day. The system will count it as 0.5 day.")
        self.half_day_checkbox.toggled.connect(self.on_half_day_toggled)

        self.half_day_period = QComboBox()
        self.half_day_period.addItems(["Morning (8:00 AM - 1:00 PM)", "Afternoon (1:00 PM - 6:00 PM)"])
        # Make the period combobox visible/enabled by default to improve discoverability
        self.half_day_period.setEnabled(True)
        self.half_day_period.setToolTip("Select Morning or Afternoon for half-day requests.")

        self.leave_title = QLineEdit()
        self.leave_title.setPlaceholderText("Enter a brief title for your leave request...")

        # Date selection with number input option
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.start_date.dateChanged.connect(self.validate_start_date)

        # Add number input for leave duration (supports fractional when half-day)
        self.leave_duration_input = QDoubleSpinBox()
        self.leave_duration_input.setDecimals(1)
        self.leave_duration_input.setSingleStep(0.5)
        self.leave_duration_input.setMinimum(1.0)
        # Allow very large durations per user request
        self.leave_duration_input.setMaximum(10000.0)
        self.leave_duration_input.setValue(1.0)
        self.leave_duration_input.setSuffix(" working days")
        self.leave_duration_input.valueChanged.connect(self.update_dates_from_duration)

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())
        self.end_date.dateChanged.connect(self.validate_end_date)
        # When dates change, recalc duration
        self.start_date.dateChanged.connect(lambda d: self.on_dates_changed_update_duration())
        self.end_date.dateChanged.connect(lambda d: self.on_dates_changed_update_duration())
        
        self.upload_btn = QPushButton("Upload Document")
        self.upload_btn
        self.upload_btn.clicked.connect(self.upload_document)

        self.remove_doc_btn = QPushButton("Remove")
        self.remove_doc_btn
        self.remove_doc_btn.clicked.connect(self.remove_document)

        self.submit_btn = QPushButton("Submit Request")
        self.submit_btn
        self.submit_btn.clicked.connect(self.submit_request)

        # Create a grouped section for the leave request form
        from PyQt5.QtWidgets import QGroupBox, QFormLayout
        
        # Add leave balance display section
        balance_group = QGroupBox("📊 Your Leave Balance")
        balance_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                padding-top: 15px;
                margin-top: 10px;
                border: 2px solid #cccccc;
                border-radius: 8px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        balance_layout = QVBoxLayout()
        balance_layout.setContentsMargins(16, 16, 16, 16)
        
        # Labels for balance information
        self.annual_balance_label = QLabel("Annual Leave: Loading...")
        self.annual_balance_label.setStyleSheet("font-size: 14px; color: #2e7d32; margin: 5px 0;")
        
        self.sick_balance_label = QLabel("Sick Leave: Loading...")
        self.sick_balance_label.setStyleSheet("font-size: 14px; color: #d32f2f; margin: 5px 0;")
        
        self.refresh_balance_btn = QPushButton("🔄 Refresh Balance")
        self.refresh_balance_btn.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.refresh_balance_btn.clicked.connect(self.load_leave_balances)
        
        balance_layout.addWidget(self.annual_balance_label)
        balance_layout.addWidget(self.sick_balance_label)
        balance_layout.addWidget(self.refresh_balance_btn)
        balance_group.setLayout(balance_layout)
        layout.addWidget(balance_group)
        
        form_group = QGroupBox("📝 Leave Request Details")
        form_group
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(16, 16, 16, 16)
        
        # Leave type row with refresh button
        lt_row = QHBoxLayout()
        lt_row.addWidget(self.leave_type)
        lt_row.addWidget(self.leave_types_refresh_btn)
        lt_row.addStretch()
        lt_widget = QWidget(); lt_widget.setLayout(lt_row)
        form_layout.addRow(QLabel("Leave Type:"), lt_widget)
        # State selector for the leave request (for holiday/deduction rules)
        self.state_combo = QComboBox()
        self.state_combo.addItems([
            "All Malaysia", "JOHORE", "KEDAH", "KELANTAN", "MELAKA", "NEGERI SEMBILAN",
            "PAHANG", "PERAK", "PERLIS", "PULAU PINANG", "SELANGOR", "TERENGGANU",
            "KUALA LUMPUR", "PUTRAJAYA", "LABUAN", "SABAH", "SARAWAK"
        ])
        form_layout.addRow(QLabel("State (for holiday rules):"), self.state_combo)
        
        # Half-day controls
        half_day_layout = QHBoxLayout()
        half_day_layout.addWidget(self.half_day_checkbox)
        half_day_layout.addWidget(QLabel("Period:"))
        half_day_layout.addWidget(self.half_day_period)
        half_day_layout.addStretch()
        
        half_day_widget = QWidget()
        half_day_widget.setLayout(half_day_layout)
        form_layout.addRow(half_day_widget)
        
        form_layout.addRow(QLabel("Leave Title:"), self.leave_title)
        
        # Add sick leave information label
        self.sick_leave_info = QLabel()
        self.sick_leave_info.setWordWrap(True)
        self.sick_leave_info.hide()  # Initially hidden
        form_layout.addRow(self.sick_leave_info)
        
        # Create date layout
        # First row: Leave duration input
        duration_layout = QHBoxLayout()
        duration_layout.addWidget(QLabel("Leave duration:"))
        duration_layout.addWidget(self.leave_duration_input)
        duration_layout.addWidget(QLabel("(excludes weekends & holidays)"))
        duration_layout.addStretch()
        
        duration_widget = QWidget()
        duration_widget.setLayout(duration_layout)
        form_layout.addRow(duration_widget)
        
        # Second row: Date pickers
        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel("Or select dates:"))
        dates_layout.addWidget(QLabel("Start:"))
        dates_layout.addWidget(self.start_date)
        dates_layout.addWidget(QLabel("End:"))
        dates_layout.addWidget(self.end_date)
        dates_layout.addStretch()

        # Apply initial past-date rules depending on current leave type
        try:
            self._apply_past_date_rules()
        except Exception:
            pass
        
        dates_widget = QWidget()
        dates_widget.setLayout(dates_layout)
        form_layout.addRow(dates_widget)
        # Live display of working days between selected dates (placed below for visibility)
        self.date_days_label = QLabel("Working days: 1 (excludes weekends & holidays)")
        self.date_days_label.setObjectName("dateDaysLabel")
        self.date_days_label.setStyleSheet("color: #555; margin-left: 8px;")
        form_layout.addRow(self.date_days_label)
        
        # Update working-days label whenever state selection changes
        try:
            self.state_combo.currentTextChanged.connect(lambda _: self.on_dates_changed_update_duration())
        except Exception:
            pass

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # Create a grouped section for document upload
        doc_group = QGroupBox("📎 Supporting Documents")
        doc_group
        
        doc_layout = QHBoxLayout()
        doc_layout.setContentsMargins(16, 16, 16, 16)
        doc_layout.addWidget(self.upload_btn)
        doc_layout.addWidget(self.remove_doc_btn)
        doc_layout.addStretch()
        
        doc_group.setLayout(doc_layout)
        layout.addWidget(doc_group)

        # Add Employment Act 1955 info button
        info_group = QGroupBox("📋 Employment Law Information")
        info_group
        info_layout = QHBoxLayout()
        
        self.employment_act_btn = QPushButton("📖 Malaysian Employment Act 1955 - Leave Info")
        self.employment_act_btn
        self.employment_act_btn.clicked.connect(self.show_employment_act_leave_info)
        
        info_layout.addWidget(self.employment_act_btn)
        info_layout.addStretch()
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        layout.addWidget(self.submit_btn)
        
        # Set the content widget to the scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to main layout
        main_layout.addWidget(scroll_area)
        
        # Set the main layout to the form tab
        self.form_tab.setLayout(main_layout)

    def _populate_leave_types_dynamic(self, force=False):
        """Populate leave type combo from dynamic service.

        force=True will bypass cache so newly added types appear immediately.
        Falls back to legacy static list if service unavailable.
        """
        try:
            from services.supabase_leave_types import list_leave_types
            items = list_leave_types(active_only=True, force_refresh=force)
            if items:
                current_code = self.leave_type.currentData()
                self.leave_type.clear()
                for it in items:
                    code = it.get('code') or ''
                    name = it.get('name') or code.title()
                    self.leave_type.addItem(name, code)
                # Restore previous selection if still present
                if current_code:
                    idx = self.leave_type.findData(current_code)
                    if idx >= 0:
                        self.leave_type.setCurrentIndex(idx)
                # Trigger sick leave info if needed
                self.on_leave_type_changed(self.leave_type.currentText())
                return
        except Exception:
            pass
        # Fallback static list
        self.leave_type.clear()
        legacy = [
            ("Sick","sick"), ("Hospitalization","hospitalization"), ("Annual","annual"),
            ("Emergency","emergency"), ("Unpaid","unpaid"), ("Others","others")
        ]
        for label, code in legacy:
            self.leave_type.addItem(label, code)
        self.on_leave_type_changed(self.leave_type.currentText())

    def update_date_days_label(self):
        """Update the inline label showing working days for the current start/end selection."""
        try:
            start_qd = self.start_date.date()
            end_qd = self.end_date.date()
            # Guard invalid range
            if end_qd < start_qd:
                self.date_days_label.setText("Working days: -")
                return
            # Half-day override
            if hasattr(self, 'half_day_checkbox') and self.half_day_checkbox.isChecked():
                self.date_days_label.setText("Working days: 0.5 (half-day)")
                return

            # Determine state (None = nationwide)
            state = None
            try:
                state_text = getattr(self, 'state_combo', None) and self.state_combo.currentText()
                if state_text and state_text.strip().lower() != 'all malaysia':
                    state = state_text
            except Exception:
                state = None

            # Calculate with holiday-aware function
            start = start_qd.toPyDate().isoformat()
            end = end_qd.toPyDate().isoformat()
            days = calculate_working_days(start, end, state=state)
            self.date_days_label.setText(f"Working days: {int(round(days))} (excludes weekends & holidays)")
        except Exception:
            try:
                self.date_days_label.setText("")
            except Exception:
                pass

    def init_records_tab(self):
        layout = QVBoxLayout()
        
        # Add refresh button at the top
        button_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setObjectName("refreshButton")
        self.refresh_btn.clicked.connect(self.load_leave_records)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Leave Type", "Title", "Start Date", "End Date", "Status", "Submitted At", "Reviewed At", "Reviewer", "View Details"
        ])
        
        # Configure column widths for proper display
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents) # Leave Type
        header.setSectionResizeMode(1, QHeaderView.Stretch)          # Title
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents) # Start Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # End Date
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents) # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents) # Submitted At
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents) # Reviewed At
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents) # Reviewer
        header.setSectionResizeMode(8, QHeaderView.Fixed)            # View Details
        
        # Set fixed width for View Details column
        self.table.setColumnWidth(8, 120)
        
        # Set minimum row height for buttons
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.setObjectName("leaveRequestsTable")
        layout.addWidget(self.table)
        self.records_tab.setLayout(layout)

    def load_leave_balances(self, highlight_type=None):
        """Load and display leave balances for the current user"""
        if not self.user_email:
            self.annual_balance_label.setText("Annual Leave: User not logged in")
            self.sick_balance_label.setText("Sick Leave: User not logged in")
            return
        
        try:
            current_year = datetime.now().year
            
            # Get current leave type selection for highlighting
            if highlight_type is None and hasattr(self, 'leave_type'):
                highlight_type = self.leave_type.currentText()
            
            # Get annual leave balance
            annual_balance = get_individual_employee_leave_balance(self.user_email, current_year)
            if annual_balance:
                annual_entitlement = annual_balance.get('annual_entitlement', 0)
                annual_used = annual_balance.get('used_days', 0)
                annual_carried = annual_balance.get('carried_forward', 0)
                annual_remaining = annual_entitlement + annual_carried - annual_used
                
                annual_text = (
                    f"Annual Leave: {max(0, annual_remaining)} days remaining "
                    f"(Entitlement: {annual_entitlement}, Used: {annual_used}, Carried Forward: {annual_carried})"
                )
                
                # Highlight if this is the selected leave type
                if highlight_type == "Annual":
                    self.annual_balance_label.setText(f"🔸 {annual_text}")
                    self.annual_balance_label.setStyleSheet("font-size: 14px; color: #1976d2; margin: 5px 0; font-weight: bold;")
                else:
                    self.annual_balance_label.setText(annual_text)
                    self.annual_balance_label.setStyleSheet("font-size: 14px; color: #2e7d32; margin: 5px 0;")
            else:
                self.annual_balance_label.setText("Annual Leave: Data not available")
                self.annual_balance_label.setStyleSheet("font-size: 14px; color: #2e7d32; margin: 5px 0;")
            
            # Get sick leave balance
            sick_balance = get_individual_employee_sick_leave_balance(self.user_email, current_year)
            if sick_balance:
                sick_entitlement = sick_balance.get('sick_days_entitlement', 14)
                sick_used = sick_balance.get('used_sick_days', 0)
                sick_remaining = sick_entitlement - sick_used
                
                # Hospitalization days are tracked separately
                hosp_entitlement = sick_balance.get('hospitalization_days_entitlement', 60)
                hosp_used = sick_balance.get('used_hospitalization_days', 0)  # Separate tracking
                hosp_remaining = hosp_entitlement - hosp_used
                
                # Update sick leave and hospitalization summary labels
                try:
                    sick_text = (
                        f"Sick Leave: {max(0, sick_remaining)} days remaining "
                        f"(Entitlement: {sick_entitlement}, Used: {sick_used})"
                    )
                    hosp_text = (
                        f"Hospitalization: {max(0, hosp_remaining)} days remaining "
                        f"(Entitlement: {hosp_entitlement}, Used: {hosp_used})"
                    )
                    # Display both pieces in the sick balance label
                    self.sick_balance_label.setText(sick_text + " — " + hosp_text)
                    self.sick_balance_label.setStyleSheet("font-size: 14px; color: #d32f2f; margin: 5px 0;")
                except Exception:
                    # Fallback display
                    self.sick_balance_label.setText("Sick Leave: Data not available")
                    self.sick_balance_label.setStyleSheet("font-size: 14px; color: #d32f2f; margin: 5px 0;")
        except Exception as e:
            # If any error occurs while loading balances, show a safe fallback
            try:
                self.annual_balance_label.setText("Annual Leave: Data not available")
            except Exception:
                pass
            try:
                self.sick_balance_label.setText("Sick Leave: Data not available")
            except Exception:
                pass

    def on_half_day_toggled(self, checked):
        """Handle half-day checkbox toggle"""
        self.half_day_period.setEnabled(checked)
        
        if checked:
            # Allow fractional input for half-day and default to 0.5
            try:
                if DEBUG_UI:
                    print(f"DEBUG_UI: on_half_day_toggled -> set duration to 0.5 and keep enabled")
                self.leave_duration_input.blockSignals(True)
                self.leave_duration_input.setDecimals(1)
                self.leave_duration_input.setSingleStep(0.5)
                self.leave_duration_input.setMinimum(0.5)
                self.leave_duration_input.setValue(0.5)
            finally:
                try:
                    self.leave_duration_input.blockSignals(False)
                except Exception:
                    pass
            
            # Set end date to same as start date
            start_date = self.start_date.date()
            self.end_date.setDate(start_date)
            self.end_date.setEnabled(False)
            try:
                # Refresh inline label to show 0.5
                self.update_date_days_label()
            except Exception:
                pass
        else:
            # Re-enable end date and restore whole-day min/step for duration input
            self.end_date.setEnabled(True)
            try:
                if DEBUG_UI:
                    print(f"DEBUG_UI: on_half_day_toggled -> restore min=1.0 and step=1.0")
                self.leave_duration_input.blockSignals(True)
                self.leave_duration_input.setMinimum(1.0)
                self.leave_duration_input.setSingleStep(1.0)
                if self.leave_duration_input.value() < 1.0:
                    self.leave_duration_input.setValue(1.0)
            finally:
                try:
                    self.leave_duration_input.blockSignals(False)
                except Exception:
                    pass
        # Refresh inline working-days label on any toggle state change
        try:
            self.update_date_days_label()
        except Exception:
            pass
            try:
                # Refresh label after toggling off half-day
                self.update_date_days_label()
            except Exception:
                pass

    def on_leave_type_changed(self, leave_type):
        """Handle leave type selection changes from the combo box."""
        # Apply past-date rules: allow backdating only for 'Unrecorded'
        try:
            self._apply_past_date_rules()
        except Exception:
            pass
        # Show contextual guidance for sick leave
        try:
            if leave_type and leave_type.lower() == "sick":
                self.sick_leave_info.setText(
                    "ℹ️ Sick Leave Requirements:\n"
                    "• Upload Medical Certificate (MC) document\n"
                    "• MC required as per Malaysian Employment Act 1955\n"
                    "⚠️ Important: Sick leave requests without MC document will be deducted from Annual Leave balance instead"
                )
                self.sick_leave_info.show()
            else:
                self.sick_leave_info.hide()
        except Exception:
            # Safe fallback: hide the info on any error
            try:
                self.sick_leave_info.hide()
            except Exception:
                pass
        # Refresh displayed balances (no highlight)
        try:
            self.load_leave_balances(highlight_type=None)
        except Exception:
            pass

    def update_dates_from_duration(self, working_days):
        """Update start and end dates based on working days duration (holiday-aware)."""
        try:
            from services.supabase_service import calculate_working_days
        except Exception:
            calculate_working_days = None

        if DEBUG_UI:
            print(f"DEBUG_UI: update_dates_from_duration called with working_days={working_days}")
        # Prevent signal feedback loops while we programmatically change dates/spinbox
        try:
            self.leave_duration_input.blockSignals(True)
        except Exception:
            pass

    def _apply_past_date_rules(self):
        """Allow past dates only when leave type is 'Unrecorded'."""
        try:
            lt = (self.leave_type.currentText() or '').strip().lower()
        except Exception:
            lt = ''
        if lt == 'unrecorded':
            try:
                self.start_date.setMinimumDate(QDate(2000,1,1))
                self.end_date.setMinimumDate(QDate(2000,1,1))
            except Exception:
                pass
        else:
            today = QDate.currentDate()
            try:
                self.start_date.setMinimumDate(today)
                self.end_date.setMinimumDate(max(today, self.start_date.date()))
            except Exception:
                pass
        try:
            self.start_date.blockSignals(True)
            self.end_date.blockSignals(True)
        except Exception:
            pass

        # Use the currently selected start date if available, otherwise default to today
        start_date = self.start_date.date() if hasattr(self, 'start_date') else QDate.currentDate()

        # Respect selected state when fetching holidays; normalize UI label to canonical name
        state = None
        try:
            state_text = getattr(self, 'state_combo', None) and self.state_combo.currentText()
            from core.holidays_service import canonical_state_name
            state = canonical_state_name(state_text)
        except Exception:
            state = None

        # Fetch holidays for the relevant years (start year and next) using local python-holidays adapter
        holiday_dates = set()
        try:
            from core.holidays_service import get_holidays_for_year
            try:
                ys = {start_date.year(), start_date.year() + 1}
            except Exception:
                ys = {datetime.now().year}
            for y in ys:
                try:
                    hs, _ = get_holidays_for_year(int(y), state=state)
                    holiday_dates.update(hs)
                except Exception:
                    continue
        except Exception:
            holiday_dates = set()

        # Determine state-specific weekend days for Qt (Fri=5, Sat=6, Sun=7)
        try:
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            from core.holidays_service import canonical_state_name
            qt_state = canonical_state_name(self.state_combo.currentText()) if hasattr(self, 'state_combo') else None
            weekend_qt_days = {5, 6} if (qt_state in fri_sat_states) else {6, 7}
        except Exception:
            weekend_qt_days = {6, 7}

        # Ensure start_date is a working day (skip state-specific weekends and holidays)
        while start_date.dayOfWeek() in weekend_qt_days or getattr(start_date, 'toPyDate', lambda: None)() in holiday_dates:
            start_date = start_date.addDays(1)

        # Fast path: if external calculate_working_days is available, we can attempt
        # to find an end date via incremental expansion using local holiday set to avoid blocking.
        if working_days <= 1:
            self.start_date.setDate(start_date)
            self.end_date.setDate(start_date)
            try:
                self.load_leave_balances()
            finally:
                try:
                    self.start_date.blockSignals(False)
                    self.end_date.blockSignals(False)
                except Exception:
                    pass
                try:
                    self.leave_duration_input.blockSignals(False)
                except Exception:
                    pass
            return

        # Local holiday-aware expansion (keeps UI responsive)
        days_added = 1
        candidate = start_date
        while days_added < working_days:
            candidate = candidate.addDays(1)
            # skip state-specific weekends
            if candidate.dayOfWeek() in weekend_qt_days:
                continue
            # skip holidays (compare by python date)
            try:
                py = candidate.toPyDate()
                if py in holiday_dates:
                    continue
            except Exception:
                pass
            days_added += 1

        if DEBUG_UI:
            print(f"DEBUG_UI: update_dates_from_duration -> setting start={start_date.toString('yyyy-MM-dd')} end={candidate.toString('yyyy-MM-dd')}")

        self.start_date.setDate(start_date)
        self.end_date.setDate(candidate)
        try:
            self.load_leave_balances()
        finally:
            try:
                self.start_date.blockSignals(False)
                self.end_date.blockSignals(False)
            except Exception:
                pass
            try:
                self.leave_duration_input.blockSignals(False)
            except Exception:
                pass
        # Refresh working-days label after programmatic date changes
        try:
            self.update_date_days_label()
        except Exception:
            pass
        return

    def on_dates_changed_update_duration(self):
        try:
            from services.supabase_service import calculate_working_days
            start = self.start_date.date().toPyDate().isoformat()
            end = self.end_date.date().toPyDate().isoformat()
            # Respect state selection when available
            state = None
            try:
                state_text = getattr(self, 'state_combo', None) and self.state_combo.currentText()
                if state_text and state_text.strip().lower() != 'all malaysia':
                    state = state_text
            except Exception:
                state = None
            # If half-day is selected, don't overwrite the fractional user input; just update label
            if getattr(self, 'half_day_checkbox', None) and self.half_day_checkbox.isChecked():
                self.update_date_days_label()
                return
            computed = calculate_working_days(start, end, state=state)
            if DEBUG_UI:
                print(f"DEBUG_UI: on_dates_changed_update_duration computed={computed} for {start} to {end}")
            self.leave_duration_input.blockSignals(True)
            self.leave_duration_input.setValue(float(int(round(computed))))
            self.leave_duration_input.blockSignals(False)
            # Also refresh the inline days label
            self.update_date_days_label()
        except Exception:
            start = self.start_date.date().toPyDate()
            end = self.end_date.date().toPyDate()
            days = (end - start).days + 1
            self.leave_duration_input.blockSignals(True)
            self.leave_duration_input.setValue(float(days))
            self.leave_duration_input.blockSignals(False)
            # Best-effort label update
            try:
                self.date_days_label.setText(f"Working days: {days}")
            except Exception:
                pass

    def validate_start_date(self, date):
        """Validate start date: disallow past for non-'Unrecorded'; skip weekends."""
        try:
            lt = (self.leave_type.currentText() or '').strip().lower()
        except Exception:
            lt = ''
        today = QDate.currentDate()
        if lt != 'unrecorded' and date < today:
            date = today
        try:
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            from core.holidays_service import canonical_state_name
            qt_state = canonical_state_name(self.state_combo.currentText()) if hasattr(self, 'state_combo') else None
            weekend_qt_days = {5, 6} if (qt_state in fri_sat_states) else {6, 7}
        except Exception:
            weekend_qt_days = {6, 7}
        if date.dayOfWeek() in weekend_qt_days:  # Weekend
            # Find next working day
            while date.dayOfWeek() in weekend_qt_days:
                date = date.addDays(1)
            self.start_date.setDate(date)
        
        # Refresh balance display when dates change
        self.load_leave_balances()
            
    def validate_end_date(self, date):
        """Validate end date: disallow past for non-'Unrecorded'; keep >= start; skip weekends."""
        try:
            lt = (self.leave_type.currentText() or '').strip().lower()
        except Exception:
            lt = ''
        today = QDate.currentDate()
        if lt != 'unrecorded' and date < today:
            date = today
        try:
            if date < self.start_date.date():
                date = self.start_date.date()
        except Exception:
            pass
        try:
            fri_sat_states = {"Johor", "Kedah", "Kelantan", "Terengganu"}
            from core.holidays_service import canonical_state_name
            qt_state = canonical_state_name(self.state_combo.currentText()) if hasattr(self, 'state_combo') else None
            weekend_qt_days = {5, 6} if (qt_state in fri_sat_states) else {6, 7}
        except Exception:
            weekend_qt_days = {6, 7}
        if date.dayOfWeek() in weekend_qt_days:  # Weekend
            # Find previous working day
            while date.dayOfWeek() in weekend_qt_days:
                date = date.addDays(-1)
            self.end_date.setDate(date)
        
        # Refresh balance display when dates change  
        self.load_leave_balances()

    def load_leave_records(self):
        # print("DEBUG: Loading leave records in EmployeeLeaveTab")
        try:
            if not self.user_email:
                # print("DEBUG: No user_email set, skipping leave records fetch")
                self.table.setRowCount(0)
                return
            leave_requests = fetch_user_leave_requests(self.user_email)
            # print(f"DEBUG: Fetched {len(leave_requests)} leave requests")
            self.table.setRowCount(len(leave_requests))
            
            for row, request in enumerate(leave_requests):
                # Populate data columns (excluding View Details column)
                columns_data = [
                    ("leave_type", 0),
                    ("title", 1), 
                    ("start_date", 2),
                    ("end_date", 3),
                    ("status", 4),
                    ("submitted_at", 5),
                    ("reviewed_at", 6),
                    ("reviewed_by", 7)
                ]
                
                for key, col in columns_data:
                    value = request.get(key, "-")
                    
                    # Special handling for leave type to include half-day info
                    if key == "leave_type":
                        is_half_day = request.get("is_half_day", False)
                        half_day_period = request.get("half_day_period", "")
                        if is_half_day:
                            period = "Morning" if "Morning" in half_day_period else "Afternoon"
                            value = f"{value} (Half Day - {period})"
                    elif key in ["submitted_at", "reviewed_at"] and value not in ("-", None, ""):
                        value = convert_utc_to_kl(value)  # This now returns formatted string
                    elif key == "reviewed_by" and value in ("-", None, ""):
                        value = "-"
                    
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)
                
                # Add View Details button in the last column
                view_btn = QPushButton("👁️ View")
                view_btn.setObjectName("viewDetailsButton")
                view_btn.clicked.connect(lambda checked, r=request: self.view_leave_details(r))
                self.table.setCellWidget(row, 8, view_btn)
                
            # print("DEBUG: Leave records table populated")
        except Exception as e:
            # print(f"DEBUG: Error fetching leave requests: {str(e)}")
            self.table.setRowCount(0)
            QMessageBox.warning(self, "Error", f"Failed to load leave requests: {str(e)}")

    def view_leave_details(self, record):
        """View detailed information about a leave request"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 My Leave Request Details")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # Leave request information
        info_group = QGroupBox("📝 Leave Request Information")
        info_layout = QFormLayout()
        info_layout.addRow("Leave Type:", QLabel(record.get("leave_type", "-")))
        info_layout.addRow("Title:", QLabel(record.get("title", "-")))
        info_layout.addRow("Start Date:", QLabel(record.get("start_date", "-")))
        info_layout.addRow("End Date:", QLabel(record.get("end_date", "-")))
        
        # Calculate working days
        try:
            start_date = datetime.strptime(record.get("start_date", ""), "%Y-%m-%d")
            end_date = datetime.strptime(record.get("end_date", ""), "%Y-%m-%d")
            # Try to get state associated with this leave request
            try:
                from services.supabase_service import get_leave_request_states
                states = get_leave_request_states(record.get('id'))
                state = states[0] if states else None
            except Exception:
                state = None
            days = calculate_working_days(start_date, end_date, state=state)
            info_layout.addRow("Working Days:", QLabel(str(days)))
        except:
            info_layout.addRow("Total Days:", QLabel("-"))
            
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Status information
        status_group = QGroupBox("📊 Status Information")
        status_layout = QFormLayout()
        
        status_label = QLabel(record.get("status", "-").title())
        if record.get("status", "").lower() == "approved":
            status_label.setStyleSheet("color: green; font-weight: bold;")
        elif record.get("status", "").lower() == "rejected":
            status_label.setStyleSheet("color: red; font-weight: bold;")
        elif record.get("status", "").lower() == "pending":
            status_label.setStyleSheet("color: orange; font-weight: bold;")
        status_layout.addRow("Status:", status_label)
        
        # Format timestamps
        submitted_at = record.get("submitted_at", "-")
        if submitted_at != "-":
            try:
                submitted_at = convert_utc_to_kl(submitted_at)  # This now returns formatted string
            except:
                pass
        status_layout.addRow("Submitted At:", QLabel(submitted_at))
        
        reviewed_at = record.get("reviewed_at", "-")
        if reviewed_at != "-":
            try:
                reviewed_at = convert_utc_to_kl(reviewed_at)  # This now returns formatted string
            except:
                pass
        status_layout.addRow("Reviewed At:", QLabel(reviewed_at))
        
        status_layout.addRow("Reviewed By:", QLabel(record.get("reviewed_by", "-")))
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Title section - only show for Annual Leave (not for Sick Leave)
        leave_type = record.get("leave_type", "").lower()
        if leave_type == "annual":
            title_group = QGroupBox("📝 Leave Request Title")
            title_layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setText(record.get("title", "No title provided"))
            text_edit.setMinimumHeight(150)
            title_layout.addWidget(text_edit)
            title_group.setLayout(title_layout)
            layout.addWidget(title_group)
        # No title section for sick leave - completely removed
        
        # Document information
        if record.get("document_url"):
            doc_group = QGroupBox("📎 Supporting Document")
            doc_layout = QHBoxLayout()
            doc_btn = QPushButton("📄 Open Document")
            doc_btn.setObjectName("documentButton")
            doc_btn.clicked.connect(lambda: self.open_document(record.get("document_url")))
            doc_layout.addWidget(doc_btn)
            doc_layout.addStretch()
            doc_group.setLayout(doc_layout)
            layout.addWidget(doc_group)
        else:
            # Show no document message
            doc_group = QGroupBox("📎 Supporting Document")
            doc_layout = QVBoxLayout()
            no_doc_label = QLabel("No supporting document uploaded")
            no_doc_label.setStyleSheet("color: gray; font-style: italic;")
            doc_layout.addWidget(no_doc_label)
            doc_group.setLayout(doc_layout)
            layout.addWidget(doc_group)
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def open_document(self, document_url):
        """Open a document URL in the browser"""
        try:
            import webbrowser
            webbrowser.open(document_url)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open document: {str(e)}")

    def upload_document(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Document", "", "PDF Files (*.pdf);;All Files (*)")
        if file_path:
            try:
                if not self.user_email:
                    raise ValueError("User email is not set")
                document_url = upload_document_to_bucket(file_path, self.user_email, is_leave_request=True)
                if document_url:
                    self.document_url = document_url
                    self.upload_btn.setText(os.path.basename(file_path))
                    QMessageBox.information(self, "Success", "Document uploaded successfully.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to upload document. Please try again.")
            except Exception as e:
                # print(f"DEBUG: Error uploading document: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to upload document: {str(e)}")

    def remove_document(self):
        self.document_url = None
        self.upload_btn.setText("Upload Document")

    def submit_request(self):
        if not self.user_email:
            QMessageBox.critical(self, "Error", "User email is not set. Please log in again.")
            return

        # Prefer internal code (userData) but fallback to display text
        leave_type = self.leave_type.currentData() or self.leave_type.currentText()
        title = self.leave_title.text().strip()
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()

        if not title:
            QMessageBox.warning(self, "Missing", "Please provide a title for the leave request.")
            return
        if start > end:
            QMessageBox.warning(self, "Invalid", "Start date cannot be after end date.")
            return
        current_date = datetime.now(KL_TZ).date()
        if start < current_date:
            QMessageBox.warning(self, "Invalid", "Start date cannot be in the past.")
            return

        # Calculate requested days
        requested_days = (end - start).days + 1

        # Check leave balance for annual and sick leave
        try:
            current_year = datetime.now().year
            
            if str(leave_type).lower() == "annual":
                annual_balance = get_individual_employee_leave_balance(self.user_email, current_year)
                if annual_balance:
                    annual_entitlement = annual_balance.get('annual_entitlement', 0)
                    annual_used = annual_balance.get('used_days', 0)
                    annual_carried = annual_balance.get('carried_forward', 0)
                    annual_remaining = annual_entitlement + annual_carried - annual_used
                    
                    if requested_days > annual_remaining:
                        reply = QMessageBox.question(
                            self,
                            "Insufficient Annual Leave Balance",
                            f"You are requesting {requested_days} days but only have {max(0, annual_remaining)} days remaining.\n\n"
                            f"Details:\n"
                            f"• Entitlement: {annual_entitlement} days\n"
                            f"• Carried Forward: {annual_carried} days\n"
                            f"• Used: {annual_used} days\n"
                            f"• Remaining: {max(0, annual_remaining)} days\n\n"
                            f"Do you want to proceed anyway? (May result in unpaid leave)",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
            
            elif str(leave_type).lower() == "sick":
                sick_balance = get_individual_employee_sick_leave_balance(self.user_email, current_year)
                if sick_balance:
                    sick_entitlement = sick_balance.get('sick_days_entitlement', 14)
                    sick_used = sick_balance.get('used_sick_days', 0)
                    sick_remaining = sick_entitlement - sick_used
                    
                    if requested_days > sick_remaining:
                        reply = QMessageBox.question(
                            self,
                            "Insufficient Sick Leave Balance",
                            f"You are requesting {requested_days} days but only have {max(0, sick_remaining)} sick days remaining.\n\n"
                            f"Details:\n"
                            f"• Entitlement: {sick_entitlement} days\n"
                            f"• Used: {sick_used} days\n"
                            f"• Remaining: {max(0, sick_remaining)} days\n\n"
                            f"Note: You also have {sick_balance.get('hospitalization_days_entitlement', 60)} hospitalization days available.\n\n"
                            f"Do you want to proceed anyway?",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.No
                        )
                        if reply == QMessageBox.No:
                            return
        except Exception as e:
            print(f"Warning: Could not verify leave balance: {str(e)}")
            # Continue with submission even if balance check fails

        # For sick leave, require medical certificate upload
        if str(leave_type).lower() == "sick":
            if not self.document_url:
                reply = QMessageBox.question(
                    self, 
                    "Medical Certificate Required", 
                    "Sick leave requires Medical Certificate (MC) upload.\n\n"
                    "Malaysian Employment Act 1955 requires proper medical documentation for sick leave.\n\n"
                    "Please upload your MC document before submitting.\n"
                    "Click 'Yes' to proceed without MC (not recommended)\n"
                    "Click 'No' to upload MC first",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return

        try:
            # Get half-day information
            is_half_day = self.half_day_checkbox.isChecked()
            half_day_period = self.half_day_period.currentText() if is_half_day else None
            
            # Build states payload from selector (None means nationwide)
            selected_state = self.state_combo.currentText() if hasattr(self, 'state_combo') else None
            states_payload = None if selected_state in (None, "All Malaysia") else [selected_state]

            # Submit leave request with half-day information and optional states
            success = submit_leave_request(
                self.user_email, leave_type, start.isoformat(), end.isoformat(), 
                title or "", self.document_url, None, is_half_day, half_day_period,
                states=states_payload
            )
            if success:
                QMessageBox.information(self, "Success", "Leave request submitted successfully.")
                self.leave_title.clear()
                self.document_url = None
                self.upload_btn.setText("Upload Document")
                self.load_leave_records()
                # Refresh leave balances after successful submission
                self.load_leave_balances()
            else:
                QMessageBox.warning(self, "Error", "Failed to submit leave request.")
        except Exception as e:
            # print(f"DEBUG: Error submitting leave request: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to submit leave request: {str(e)}")

    def show_employment_act_leave_info(self):
        """Show Malaysian Employment Act 1955 leave information for employees"""
        from PyQt5.QtWidgets import QDialog, QTextEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Malaysian Employment Act 1955 - Leave Entitlements")
        dialog.resize(700, 600)
        
        layout = QVBoxLayout()
        
        info_text = """
<h2>🇲🇾 Malaysian Employment Act 1955</h2>
<h3>Your Leave Entitlements</h3>

<h4>📅 Annual Leave:</h4>
<ul>
<li><b>Less than 2 years service:</b> Minimum 8 days per year</li>
<li><b>2-5 years service:</b> Minimum 12 days per year</li>
<li><b>More than 5 years service:</b> Minimum 16 days per year</li>
<li><b>Notice:</b> Provide reasonable advance notice</li>
<li><b>Scheduling:</b> Subject to employer approval and business needs</li>
<li><b>Carry Forward:</b> Unused leave may carry forward (check company policy)</li>
</ul>

<h4>🏥 Sick Leave:</h4>
<ul>
<li><b>Less than 2 years service:</b> 14 days per year</li>
<li><b>2-5 years service:</b> 18 days per year</li>
<li><b>More than 5 years service:</b> 22 days per year</li>
<li><b>Medical Certificate:</b> Required for more than 1 consecutive day</li>
<li><b>Hospitalization:</b> Up to 60 days per year (separate entitlement)</li>
<li><b>No Carry Forward:</b> Unused sick leave does not carry to next year</li>
</ul>

<h4>👨‍👩‍👧‍👦 Other Leave Types:</h4>
<ul>
<li><b>Maternity Leave:</b> 98 days (for eligible employees)</li>
<li><b>Paternity Leave:</b> 7 days (for married male employees)</li>
<li><b>Public Holidays:</b> 11 gazetted holidays minimum per year</li>
<li><b>Emergency Leave:</b> May be granted at employer's discretion</li>
</ul>

<h4>📋 Important Requirements:</h4>
<ul>
<li><b>Application:</b> Submit leave requests in advance when possible</li>
<li><b>Documentation:</b> Provide medical certificates for sick leave</li>
<li><b>Approval:</b> All leave requires management approval</li>
<li><b>Records:</b> Keep copies of approved leave applications</li>
</ul>

<h4>⚖️ Your Rights:</h4>
<ul>
<li>Minimum leave entitlements as per Employment Act 1955</li>
<li>Pro-rated leave for partial year employment</li>
<li>Payment for unused annual leave upon termination</li>
<li>Right to take continuous leave (minimum 3 days if requested)</li>
</ul>

<h4>📞 Need Help?</h4>
<ul>
<li>Contact HR for company-specific leave policies</li>
<li>Ensure you understand your employment contract terms</li>
<li>Keep all medical certificates and documentation</li>
<li>Plan leave requests in advance for better approval chances</li>
</ul>

<p><i><b>Note:</b> Your company may provide more generous leave benefits than the statutory minimums. This information covers the minimum requirements under Malaysian Employment Act 1955.</i></p>
        """
        
        text_widget = QTextEdit()
        text_widget.setHtml(info_text)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)
        
        # Close button
        button_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()