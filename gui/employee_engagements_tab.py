from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QListWidget, QListWidgetItem,
    QPushButton, QComboBox, QLineEdit, QFormLayout, QTextEdit, QDateEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt, QDate
from services.supabase_engagements import insert_engagement, fetch_engagements, update_engagement, delete_engagement
from services.supabase_service import supabase, upload_document_to_bucket

class EmployeeEngagementsTab(QWidget):
    def __init__(self, user_email: str):
        super().__init__()
        self.user_email = (user_email or '').lower()
        self.employee_uuid = self._resolve_employee_uuid_by_email(self.user_email)
        self._all_items_cache = []
        self._attachments = []
        self.init_ui()

    def _resolve_employee_uuid_by_email(self, email):
        try:
            r = supabase.table('employees').select('id').eq('email', email).limit(1).execute()
            if r and r.data:
                return r.data[0].get('id')
        except Exception:
            pass
        return None

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Submit tab
        s_tab = QWidget(); s_lay = QVBoxLayout()
        row = QHBoxLayout(); col1 = QFormLayout(); col2 = QFormLayout(); col3 = QFormLayout()

        self.type_select = QComboBox(); self.type_select.addItems(["Training", "Course", "Trip", "Work Assignment"])
        col1.addRow("Type:", self.type_select)

        self.title_input = QLineEdit(); col1.addRow("Title (for Training/Course):", self.title_input)

        self.country_input = QLineEdit(); col2.addRow("Country:", self.country_input)
        self.city_input = QLineEdit(); col2.addRow("City:", self.city_input)
        self.purpose_input = QComboBox(); self.purpose_input.addItems(["Meeting","Client Visit","Conference","Training","Project","Others"])
        col2.addRow("Purpose:", self.purpose_input)

        # Simplified: remove flight/accommodation specific fields from submit form

        self.start_date = QDateEdit(QDate.currentDate()); self.start_date.setCalendarPopup(True); self.start_date.setDisplayFormat('yyyy-MM-dd')
        self.end_date = QDateEdit(QDate.currentDate()); self.end_date.setCalendarPopup(True); self.end_date.setDisplayFormat('yyyy-MM-dd')
        self.duration_lbl = QLabel("0 days")
        def _upd_dur():
            try:
                days = max(self.start_date.date().daysTo(self.end_date.date()) + 1, 0)
            except Exception:
                days = 0
            self.duration_lbl.setText(f"{days} days")
        self.start_date.dateChanged.connect(lambda _: _upd_dur()); self.end_date.dateChanged.connect(lambda _: _upd_dur())
        col2.addRow("Start Date:", self.start_date)
        col2.addRow("End Date:", self.end_date)
        col2.addRow("Duration:", self.duration_lbl)

        self.desc_input = QTextEdit(); col3.addRow("Description:", self.desc_input)
        self.notes_input = QTextEdit(); col3.addRow("Notes:", self.notes_input)

        self.course_fees = QLineEdit(); self.course_fees.setPlaceholderText("0.00"); col1.addRow("Course Fees:", self.course_fees)
        self.travel_costs = QLineEdit(); self.travel_costs.setPlaceholderText("0.00"); col1.addRow("Travel Costs:", self.travel_costs)
        self.daily_allowance = QLineEdit(); self.daily_allowance.setPlaceholderText("0.00"); col1.addRow("Daily Allowance:", self.daily_allowance)
        self.total_lbl = QLabel("0.00"); col1.addRow("Total Cost:", self.total_lbl)
        def _to_num(t):
            try:
                s = str(t).replace(',', '').strip(); return float(s) if s else 0.0
            except Exception:
                return 0.0
        def _upd_total():
            tot = _to_num(self.course_fees.text()) + _to_num(self.travel_costs.text()) + _to_num(self.daily_allowance.text())
            self.total_lbl.setText(f"{tot:,.2f}")
        for w in (self.course_fees, self.travel_costs, self.daily_allowance):
            w.textChanged.connect(_upd_total)

        self.attach_btn = QPushButton("Choose Files")
        def _choose():
            files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
            self._attachments = files
            if files:
                self.attach_btn.setText(f"{len(files)} file(s) selected")
        self.attach_btn.clicked.connect(_choose)
        col3.addRow("Attachments:", self.attach_btn)

        row.addLayout(col1); row.addLayout(col2); row.addLayout(col3)
        s_lay.addLayout(row)
        submit_btn = QPushButton("Submit Engagement"); s_lay.addWidget(submit_btn)
        s_tab.setLayout(s_lay)

        # View tab
        v_tab = QWidget(); v_lay = QVBoxLayout()
        fb = QHBoxLayout(); fb.addWidget(QLabel("Keyword:")); self.keyword = QLineEdit(); fb.addWidget(self.keyword)
        refresh = QPushButton("Refresh"); fb.addWidget(refresh); fb.addStretch(); v_lay.addLayout(fb)
        self.list = QListWidget(); v_lay.addWidget(self.list)
        v_tab.setLayout(v_lay)

        self.tabs.addTab(s_tab, "📝 Submit Engagement")
        self.tabs.addTab(v_tab, "📚 My Engagements")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # wiring
        submit_btn.clicked.connect(self.submit_engagement)
        refresh.clicked.connect(self.load_my_engagements)
        self.keyword.textChanged.connect(self.apply_filter)

        self.load_my_engagements()

    def submit_engagement(self):
        if not self.employee_uuid:
            QMessageBox.warning(self, "Unavailable", "Your employee profile is not linked. Please contact HR.")
            return
        typ = self.type_select.currentText().strip().lower().replace(' ', '_')
        start_str = self.start_date.date().toString('yyyy-MM-dd') if self.start_date.date().isValid() else None
        end_str = self.end_date.date().toString('yyyy-MM-dd') if self.end_date.date().isValid() else None
        try:
            duration = max(self.start_date.date().daysTo(self.end_date.date()) + 1, 0)
        except Exception:
            duration = None
        def _to_num_opt(t):
            try:
                s = str(t).replace(',', '').strip(); return float(s) if s else None
            except Exception:
                return None
        cf = _to_num_opt(self.course_fees.text()); tc = _to_num_opt(self.travel_costs.text()); da = _to_num_opt(self.daily_allowance.text())
        total = None
        try:
            total = (cf or 0.0) + (tc or 0.0) + (da or 0.0)
        except Exception:
            total = None
        # attachments
        urls = []; failed = []
        for f in (self._attachments or []):
            try:
                url = upload_document_to_bucket(f, self.user_email)
                if url:
                    if isinstance(url, str) and url.endswith('?'): url = url.rstrip('?')
                    urls.append(url)
                else:
                    failed.append(f)
            except Exception:
                failed.append(f)
        payload = {
            'employee_id': self.employee_uuid,
            'type': typ,
            'title': self.title_input.text().strip() or None,
            'country': self.country_input.text().strip() or None,
            'city': self.city_input.text().strip() or None,
            'purpose': self.purpose_input.currentText(),
            'description': self.desc_input.toPlainText() or None,
            'start_date': start_str,
            'end_date': end_str,
            'duration': duration,
            'course_fees': cf,
            'travel_costs': tc,
            'daily_allowance': da,
            'total_cost': total,
            'attachment_url': ','.join(urls) if urls else None,
            'admin_notes': self.notes_input.toPlainText() or None,
        }
        try:
            resp = insert_engagement(payload)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to submit: {e}")
            return
        if (hasattr(resp, 'status_code') and getattr(resp, 'status_code') in (200,201)) or (hasattr(resp, 'data') and resp.data):
            msg = "Submitted." + (f" Note: {len(failed)} attachments failed." if failed else '')
            QMessageBox.information(self, "Success", msg)
            # reset minimal
            self.title_input.clear()
            self.country_input.clear(); self.city_input.clear()
            self.desc_input.clear(); self.notes_input.clear(); self.course_fees.clear(); self.travel_costs.clear(); self.daily_allowance.clear(); self.total_lbl.setText("0.00")
            today = QDate.currentDate(); self.start_date.setDate(today); self.end_date.setDate(today); self.duration_lbl.setText("0 days")
            self._attachments = []; self.attach_btn.setText("Choose Files")
            self.load_my_engagements()
        else:
            QMessageBox.warning(self, "Error", "Failed to submit engagement.")

    def load_my_engagements(self):
        self.list.clear(); self._all_items_cache = []
        if not self.employee_uuid:
            return
        try:
            recs = fetch_engagements(self.employee_uuid, {'employee_id': self.employee_uuid}) or []
        except Exception:
            recs = []
        def pdate(d):
            try:
                y,m,d0 = [int(x) for x in str(d or '').split('-')[:3]]; return (y,m,d0)
            except Exception:
                return (0,0,0)
        recs.sort(key=lambda r: pdate(r.get('start_date')), reverse=True)
        entries = []
        for r in recs:
            t = (r.get('type') or '').lower()
            if 'train' in t or 'course' in t:
                prefix = '🎓'; mid = r.get('title') or r.get('city') or ''
            else:
                prefix = '✈️'; mid = r.get('city') or r.get('country') or r.get('purpose') or ''
            date = r.get('start_date') or ''
            line = f"{prefix} {mid} ({date}) — {t.title()}"
            entries.append({'text': line, 'data': r})
        self._all_items_cache = entries
        for e in entries:
            it = QListWidgetItem(e['text']); it.setData(Qt.UserRole, e['data']); self.list.addItem(it)
        self.apply_filter()

    def apply_filter(self):
        kw = (self.keyword.text() or '').strip().lower()
        self.list.clear()
        for e in self._all_items_cache:
            if not kw or kw in e['text'].lower():
                it = QListWidgetItem(e['text']); it.setData(Qt.UserRole, e['data']); self.list.addItem(it)
