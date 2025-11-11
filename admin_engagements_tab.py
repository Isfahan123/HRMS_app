from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLineEdit, QFormLayout, QTextEdit, QDateEdit, QFileDialog
)
from PyQt5.QtCore import Qt, QDate

from services.supabase_engagements import (
    insert_engagement, fetch_engagements, update_engagement, delete_engagement,
    fetch_engagement_with_employee
)
from services.supabase_service import upload_document_to_bucket, supabase

try:
    from services.supabase_employee import fetch_employee_list as _fetch_emps
except Exception:
    _fetch_emps = None

from gui.widgets.city_autocomplete import CityAutocompleteWidget
from gui.widgets.country_dropdown import CountryDropdown


class AdminEngagementsTab(QWidget):
    """
    Unified Engagements (Training/Course/Trip/Work Assignment)
    - Single submit form with Type selector
    - Combined view of all engagements in one list
    - Single backing table: engagements
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        # Submit tab
        submit_tab = QWidget()
        s_layout = QVBoxLayout()

        # Filters not needed on submit
        form_row = QHBoxLayout()
        col1 = QFormLayout()
        col2 = QFormLayout()
        col3 = QFormLayout()

        # Employee selector
        self.employee_select = QComboBox()
        self.employee_select.addItem("Select Employee")
        try:
            emps = _fetch_emps() if _fetch_emps else []
        except Exception:
            emps = []
        for rec in emps:
            # support both shapes: (uuid, code, name) or (code, name)
            if len(rec) == 3:
                emp_uuid, emp_code, name = rec
                display = f"{name} ({emp_code})"
                self.employee_select.addItem(display, emp_uuid or emp_code)
            elif len(rec) == 2:
                emp_code, name = rec
                display = f"{name} ({emp_code})"
                self.employee_select.addItem(display, emp_code)
        col1.addRow("Employee:", self.employee_select)

        # Type selector
        self.type_select = QComboBox()
        self.type_select.addItems(["Training", "Course", "Trip", "Work Assignment"])
        col1.addRow("Type:", self.type_select)

        # Training/Course specific (simplified)
        self.title_input = QLineEdit()
        col1.addRow("Title (for Training/Course):", self.title_input)

        # Trip/Work specific
        self.country_input = CountryDropdown()
        self.city_widget = CityAutocompleteWidget(country_restriction=None)
        def _upd_city_country():
            self.city_widget.country_restriction = self.country_input.text().strip()
        self.country_input.countrySelected.connect(_upd_city_country)
        self.purpose_input = QComboBox(); self.purpose_input.addItems(["Meeting","Client Visit","Conference","Training","Project","Others"])
        col2.addRow("Country:", self.country_input)
        col2.addRow("City:", self.city_widget)
        col2.addRow("Purpose:", self.purpose_input)
        # Removed flight and accommodation details from submit form

        # Dates and duration
        self.start_date_input = QDateEdit(QDate.currentDate()); self.start_date_input.setCalendarPopup(True); self.start_date_input.setDisplayFormat('yyyy-MM-dd')
        self.end_date_input = QDateEdit(QDate.currentDate()); self.end_date_input.setCalendarPopup(True); self.end_date_input.setDisplayFormat('yyyy-MM-dd')
        self.duration_display = QLabel("0 days")
        def _upd_dur():
            try:
                days = max(self.start_date_input.date().daysTo(self.end_date_input.date()) + 1, 0)
            except Exception:
                days = 0
            self.duration_display.setText(f"{days} days")
        self.start_date_input.dateChanged.connect(lambda _: _upd_dur())
        self.end_date_input.dateChanged.connect(lambda _: _upd_dur())
        col2.addRow("Start Date:", self.start_date_input)
        col2.addRow("End Date:", self.end_date_input)
        col2.addRow("Duration:", self.duration_display)

        # Description / Notes
        self.description_input = QTextEdit()
        self.notes_input = QTextEdit()
        col3.addRow("Description:", self.description_input)
        col3.addRow("Notes:", self.notes_input)

        # Costs
        self.course_fees_input = QLineEdit(); self.course_fees_input.setPlaceholderText("0.00")
        self.travel_costs_input = QLineEdit(); self.travel_costs_input.setPlaceholderText("0.00")
        self.daily_allowance_input = QLineEdit(); self.daily_allowance_input.setPlaceholderText("0.00")
        self.total_cost_display = QLabel("0.00")
        def _to_num(txt):
            try:
                s = str(txt).replace(',', '').strip();
                return float(s) if s else 0.0
            except Exception:
                return 0.0
        def _upd_total():
            total = _to_num(self.course_fees_input.text()) + _to_num(self.travel_costs_input.text()) + _to_num(self.daily_allowance_input.text())
            self.total_cost_display.setText(f"{total:,.2f}")
        for w in (self.course_fees_input, self.travel_costs_input, self.daily_allowance_input):
            w.textChanged.connect(_upd_total)
        col1.addRow("Course Fees:", self.course_fees_input)
        col1.addRow("Travel Costs:", self.travel_costs_input)
        col1.addRow("Daily Allowance:", self.daily_allowance_input)
        col1.addRow("Total Cost:", self.total_cost_display)

        # Approval
        self.approved_by_input = QLineEdit()
        self.approval_date_input = QDateEdit(QDate.currentDate()); self.approval_date_input.setCalendarPopup(True); self.approval_date_input.setDisplayFormat('yyyy-MM-dd')
        col2.addRow("Approved By:", self.approved_by_input)
        col2.addRow("Approval Date:", self.approval_date_input)

        # Attachments
        self.attachment_inputs = []
        self.attachment_btn = QPushButton("Choose Files")
        def _choose_files():
            files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
            self.attachment_inputs = files
            if files:
                self.attachment_btn.setText(f"{len(files)} file(s) selected")
        self.attachment_btn.clicked.connect(_choose_files)
        col3.addRow("Attachments:", self.attachment_btn)

        form_row.addLayout(col1)
        form_row.addLayout(col2)
        form_row.addLayout(col3)
        s_layout.addLayout(form_row)

        submit_btn = QPushButton("Submit Engagement")
        s_layout.addWidget(submit_btn)
        submit_tab.setLayout(s_layout)

        # View tab
        view_tab = QWidget()
        v_layout = QVBoxLayout()
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("Employee:"))
        self.emp_filter = QComboBox(); self.emp_filter.addItem("All Employees", None)
        # load employees again for filter
        for rec in emps:
            if len(rec) == 3:
                emp_uuid, emp_code, name = rec
                display = f"{name} ({emp_code})"
                self.emp_filter.addItem(display, emp_uuid or emp_code)
            elif len(rec) == 2:
                emp_code, name = rec
                display = f"{name} ({emp_code})"
                self.emp_filter.addItem(display, emp_code)
        filter_bar.addWidget(self.emp_filter)
        filter_bar.addWidget(QLabel("Keyword:"))
        self.keyword = QLineEdit(); filter_bar.addWidget(self.keyword)
        refresh_btn = QPushButton("Refresh"); filter_bar.addWidget(refresh_btn)
        filter_bar.addStretch()
        v_layout.addLayout(filter_bar)

        self.list = QListWidget(); v_layout.addWidget(self.list)
        view_tab.setLayout(v_layout)

        self.tabs.addTab(submit_tab, "📝 Submit Engagement")
        self.tabs.addTab(view_tab, "📚 View Engagements")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # Local state
        self._all_items_cache = []  # list of {text, data}

        # Wiring
        submit_btn.clicked.connect(self.submit_record)
        refresh_btn.clicked.connect(self.load_list)
        self.emp_filter.currentIndexChanged.connect(self.load_list)
        self.keyword.textChanged.connect(self.apply_keyword_filter)

        self.load_list()

    def _resolve_employee_uuid(self, token):
        """Token may be a UUID or employee_id code; return UUID string or None."""
        import uuid as _uuid
        if not token:
            return None
        try:
            _uuid.UUID(str(token));
            return str(token)
        except Exception:
            pass
        try:
            resp = supabase.table('employees').select('id').eq('employee_id', token).limit(1).execute()
            if resp and resp.data:
                return resp.data[0].get('id')
        except Exception:
            return None
        return None

    def submit_record(self):
        emp_idx = self.employee_select.currentIndex()
        emp_token = self.employee_select.itemData(emp_idx)
        emp_uuid = self._resolve_employee_uuid(emp_token)
        if not emp_uuid:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Missing", "Please select a valid employee.")
            return
        typ = self.type_select.currentText().strip().lower().replace(' ', '_')  # training/course/trip/work_assignment
        # Dates
        start_str = self.start_date_input.date().toString('yyyy-MM-dd') if self.start_date_input.date().isValid() else None
        end_str = self.end_date_input.date().toString('yyyy-MM-dd') if self.end_date_input.date().isValid() else None
        try:
            duration_days = max(self.start_date_input.date().daysTo(self.end_date_input.date()) + 1, 0)
        except Exception:
            duration_days = None
        # Costs
        def _to_num(txt):
            try:
                s = str(txt).replace(',', '').strip();
                return float(s) if s else None
            except Exception:
                return None
        course_fees = _to_num(self.course_fees_input.text())
        travel_costs = _to_num(self.travel_costs_input.text())
        daily_allowance = _to_num(self.daily_allowance_input.text())
        try:
            total_cost = (course_fees or 0.0) + (travel_costs or 0.0) + (daily_allowance or 0.0)
        except Exception:
            total_cost = None
        # Attachments
        attachment_urls = []
        failed = []
        # Resolve employee email for upload
        emp_email = None
        try:
            er = supabase.table('employees').select('email').eq('id', emp_uuid).limit(1).execute()
            if er and er.data:
                emp_email = er.data[0].get('email')
        except Exception:
            emp_email = None
        for fp in (self.attachment_inputs or []):
            try:
                url = upload_document_to_bucket(fp, emp_email or "")
                if url:
                    if isinstance(url, str) and url.endswith('?'):
                        url = url.rstrip('?')
                    attachment_urls.append(url)
                else:
                    failed.append(fp)
            except Exception:
                failed.append(fp)
        # Build payload (union of fields)
        data = {
            'employee_id': emp_uuid,
            'type': typ,
            'title': self.title_input.text().strip() or None,
            'country': self.country_input.text().strip() or None,
            'city': self.city_widget.text().strip() or None,
            'purpose': self.purpose_input.currentText(),
            'description': self.description_input.toPlainText() or None,
            'start_date': start_str,
            'end_date': end_str,
            'duration': duration_days,
            'course_fees': course_fees,
            'travel_costs': travel_costs,
            'daily_allowance': daily_allowance,
            'total_cost': total_cost,
            'approved_by': self.approved_by_input.text().strip() or None,
            'approval_date': self.approval_date_input.date().toString('yyyy-MM-dd') if self.approval_date_input.date().isValid() else None,
            'attachment_url': ",".join(attachment_urls) if attachment_urls else None,
            'admin_notes': self.notes_input.toPlainText() or None,
        }
        try:
            resp = insert_engagement(data)
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Error", f"Failed to submit engagement: {e}")
            return
        from PyQt5.QtWidgets import QMessageBox
        if (hasattr(resp, 'status_code') and getattr(resp, 'status_code') in (200,201)) or (hasattr(resp, 'data') and resp.data):
            msg = "Engagement submitted successfully."
            if failed:
                msg += f"\nWarning: {len(failed)} attachment(s) failed."
            QMessageBox.information(self, "Success", msg)
            # reset minimal fields
            self.title_input.clear(); self.description_input.clear(); self.notes_input.clear()
            self.course_fees_input.clear(); self.travel_costs_input.clear(); self.daily_allowance_input.clear(); self.total_cost_display.setText("0.00")
            today = QDate.currentDate(); self.start_date_input.setDate(today); self.end_date_input.setDate(today); self.duration_display.setText("0 days")
            self.attachment_inputs = []; self.attachment_btn.setText("Choose Files")
            self.load_list()
        else:
            QMessageBox.warning(self, "Error", "Failed to submit engagement.")

    def load_list(self):
        self.list.clear(); self._all_items_cache = []
        emp_idx = self.emp_filter.currentIndex(); emp_token = self.emp_filter.itemData(emp_idx)
        filters = {}
        if emp_idx > 0 and emp_token:
            filters['employee_id'] = emp_token
        try:
            records = fetch_engagements(None, filters) or []
        except Exception:
            records = []
        # Sort by start_date desc
        def pdate(d):
            try:
                y,m,dd = [int(x) for x in str(d or '').split('-')[:3]]; return (y,m,dd)
            except Exception:
                return (0,0,0)
        records.sort(key=lambda r: pdate(r.get('start_date')), reverse=True)
        entries = []
        for rec in records:
            typ = (rec.get('type') or '').lower()
            if 'train' in typ or 'course' in typ:
                prefix = '🎓'
                mid = rec.get('title') or rec.get('city') or ''
            else:
                prefix = '✈️'
                mid = rec.get('city') or rec.get('country') or rec.get('purpose') or ''
            date = rec.get('start_date') or ''
            emp = rec.get('employee_id')
            line = f"{prefix} {mid} ({date}) — {typ.title()} | {emp}"
            entries.append({'text': line, 'data': {'type': typ, 'record': rec}})
        self._all_items_cache = entries
        for e in entries:
            it = QListWidgetItem(e['text']); it.setData(Qt.UserRole, e['data']); self.list.addItem(it)
        self.apply_keyword_filter()

    def apply_keyword_filter(self):
        kw = (self.keyword.text() or '').strip().lower()
        if not self._all_items_cache:
            return
        self.list.clear()
        for e in self._all_items_cache:
            if not kw or kw in e['text'].lower():
                it = QListWidgetItem(e['text']); it.setData(Qt.UserRole, e['data']); self.list.addItem(it)
