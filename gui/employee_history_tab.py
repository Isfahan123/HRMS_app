from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QFormLayout, QMessageBox, QDateEdit, QFileDialog, QTabWidget, QComboBox, QShortcut
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QKeySequence
import json
import os
from uuid import uuid4
from services.supabase_employee_history import (
    insert_employee_history_record,
    fetch_employee_history_records,
    update_employee_history_record,
    delete_employee_history_record,
)
from services.supabase_service import supabase
from gui.employee_selector_dialog import EmployeeSelectorDialog
from gui.employee_profile_dialog import EmployeeProfileDialog
from core.job_title_mapping_loader import load_job_title_mapping
from services.org_structure_service import list_departments, get_department_units, list_job_title_groups, get_titles_for_group

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'employee_history.json')
STATUS_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'employee_status.json')

# canonical default when no employee is selected
DEFAULT_NO_EMP_TEXT = 'No employee selected'

def _ensure_db_path():
    d = os.path.dirname(DB_PATH)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump([], f)

def _load_all():
    _ensure_db_path()
    with open(DB_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []

def _save_all(rows):
    _ensure_db_path()
    with open(DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

def _ensure_status_path():
    d = os.path.dirname(STATUS_DB_PATH)
    if not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    if not os.path.exists(STATUS_DB_PATH):
        with open(STATUS_DB_PATH, 'w', encoding='utf-8') as f:
            json.dump({}, f)

def _load_status():
    _ensure_status_path()
    with open(STATUS_DB_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _save_status(obj):
    _ensure_status_path()
    with open(STATUS_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)

class EmployeeHistoryTab(QWidget):
    # Signal emitted when history records change for an employee (payload: employee_id)
    history_changed = pyqtSignal(str)
    """Simple employment / re-employment history tab.

    This is a lightweight placeholder implementation that stores records locally in
    `data/employee_history.json`. It provides a Submit form and a View table
    with edit/delete support. When integrated with your backend, replace the
    persistence functions with API/database calls.
    """

    def __init__(self, parent=None, employee_id=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.employee = None
        self.records = []
        # Preferred position to select after repopulating positions
        self._desired_position = None
        # Use a tab widget for History vs Employment Status
        main = QVBoxLayout()
        self.tabs = QTabWidget(self)
        DEBUG_WIDGET_INIT = True

        # --- History Tab (existing submit + view) ---
        history_widget = QWidget(self)
        history_layout = QHBoxLayout()

        # Submit form (left)
        form_layout = QFormLayout()
        # Use Date Joined as the start date field by default
        self.start_date_input = QDateEdit(self)
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDisplayFormat('yyyy-MM-dd')
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input = QDateEdit(self)
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDisplayFormat('yyyy-MM-dd')
        # allow end date to be empty by default (invalid QDate)
        try:
            self.end_date_input.setSpecialValueText('')
        except Exception:
            pass
        try:
            self.end_date_input.setDate(QDate())
        except Exception:
            pass
        # Replace free-text company/position with dropdowns to match profile dialog
        # populate job titles from centralized mapping where available, else org structure
        mapping = load_job_title_mapping()
        if mapping:
            jt_defaults = sorted(list(mapping.keys()))
        else:
            try:
                groups = list_job_title_groups()
                titles = []
                for g in groups:
                    titles.extend(get_titles_for_group(g) or [])
                jt_defaults = sorted(list(dict.fromkeys([t for t in titles if t]))) or ["Other"]
            except Exception:
                jt_defaults = ["Software Engineer", "Product Manager", "Accountant", "Other"]
        self.job_title_combo = QComboBox(self)
        self.job_title_combo.setEditable(True)
        self.job_title_combo.addItems(jt_defaults)
        if DEBUG_WIDGET_INIT:
            print('DBG: created job_title_combo', repr(self.job_title_combo))
        # auto-fill position/department when job title changes
        try:
            self.job_title_combo.currentTextChanged.connect(self.autofill_job_title)
        except Exception:
            pass

        # create remaining form widgets: position, department, employment type, attachments
        # position defaults — use common ranks; DB merge will still occur later
        self.position_combo = QComboBox(self)
        self.position_combo.setEditable(True)
        self.position_combo.addItems([
            "Junior", "Mid-level", "Senior", "Lead", "Manager", "Senior Manager",
            "Director", "Senior Director", "VP", "Senior VP", "C-Level", "Intern",
            "Contractor", "Consultant", "Other"
        ])

        self.department_combo = QComboBox(self)
        self.department_combo.setEditable(True)
        if DEBUG_WIDGET_INIT:
            print('DBG: created position/department combos', repr(self.position_combo), repr(self.department_combo))
        # derive department defaults from mapping if available
        try:
            dept_defaults = list_departments() or []
            if not dept_defaults:
                raise Exception('no dept list')
        except Exception:
            if mapping:
                dept_defaults = sorted(list({v.get('department') for v in mapping.values() if v.get('department')}))
            else:
                dept_defaults = [
                    "Engineering", "Product", "Design", "Research", "Data", "IT", "Security",
                    "Human Resources", "HR", "Finance", "Accounting", "Legal", "Compliance",
                    "Sales", "Business Development", "Marketing", "Customer Success", "Support",
                    "Operations", "Supply Chain", "Procurement", "Facilities", "Quality", "Admin",
                    "Executive", "Strategy", "Growth", "Other"
                ]
        self.department_combo.addItems(dept_defaults)

        # Functional Group combo (populated based on Department selection using template)
        self.func_group_combo = QComboBox(self)
        self.func_group_combo.setEditable(True)
        # Employment Status for history records (canonical employment state only)
        self.history_status_combo = QComboBox(self)
        self.history_status_combo.setEditable(True)
        # Keep employment status distinct from short-term work status
        self.history_status_combo.clear()
        self.history_status_combo.addItems(['Active', 'Inactive', 'Resigned', 'Terminated'])

        # load dept -> functional group template
        def _load_dept_template():
            try:
                import json
                p = os.path.join(os.path.dirname(__file__), 'department_functional_group_template.json')
                if os.path.exists(p):
                    with open(p, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception:
                pass
            return {}

        self._dept_template = _load_dept_template()

        def _populate_functional_groups(dept_text):
            cur = ''
            try:
                cur = self.func_group_combo.currentText() or ''
            except Exception:
                cur = ''
            self.func_group_combo.blockSignals(True)
            self.func_group_combo.clear()
            groups = []
            try:
                if self._dept_template and dept_text in self._dept_template:
                    groups = sorted(list(self._dept_template.get(dept_text, {}).keys()))
                else:
                    # try org structure service department units first
                    try:
                        groups = get_department_units(dept_text) or []
                    except Exception:
                        groups = []
                    # fallback: infer groups from mapping by using position values
                    if not groups:
                        groups = []
                        for jt, meta in mapping.items():
                            if meta.get('department') == dept_text and meta.get('position'):
                                groups.append(meta.get('position'))
                        groups = sorted(list(dict.fromkeys([g for g in groups if g])))
            except Exception:
                groups = []
            if groups:
                self.func_group_combo.addItems(groups)
            else:
                self.func_group_combo.addItem('')
            if cur:
                try:
                    idx = self.func_group_combo.findText(cur)
                    if idx >= 0:
                        self.func_group_combo.setCurrentIndex(idx)
                    else:
                        self.func_group_combo.setEditText(cur)
                except Exception:
                    pass
            self.func_group_combo.blockSignals(False)

        def _filter_job_titles_by_dept_and_group(dept_text, group_text=None, position_text=None):
            """Filter Job Title options by Department, Functional Group, and optionally Position.

            Mirrors the Employee Profile dialog behavior so users see consistent choices.
            """
            candidates = []
            try:
                if self._dept_template and dept_text in self._dept_template:
                    if group_text and group_text in self._dept_template.get(dept_text, {}):
                        candidates = self._dept_template[dept_text][group_text].get('job_titles', [])
                    else:
                        for g, info in self._dept_template.get(dept_text, {}).items():
                            candidates.extend(info.get('job_titles', []) or [])
                else:
                    # fallback to centralized mapping filtered by department (with simple aliasing)
                    def _norm(s):
                        try:
                            return (s or '').strip().lower()
                        except Exception:
                            return ''
                    def _norm_dept(s):
                        d = _norm(s)
                        aliases = {
                            'hr': 'human resources',
                            'people': 'human resources',
                            'it': 'information technology',
                            'customer service': 'customer success',
                        }
                        return aliases.get(d, d)
                    dept_norm = _norm_dept(dept_text)
                    for jt, meta in mapping.items():
                        meta_dept = _norm_dept(meta.get('department') or '')
                        if meta_dept and (dept_norm in meta_dept or meta_dept in dept_norm):
                            candidates.append(jt)
                candidates = sorted(list(dict.fromkeys([c for c in candidates if c])))

                # If a position filter is provided, narrow further using heuristics similar to profile dialog
                if position_text:
                    pos_norm = (position_text or '').strip().lower()
                    filtered = []
                    # 1) Prefer explicit mapping meta.position strict match
                    for jt in list(candidates):
                        try:
                            meta = mapping.get(jt, {}) or {}
                            if (meta.get('position') or '').strip().lower() == pos_norm:
                                filtered.append(jt)
                        except Exception:
                            continue
                    # 2) Token heuristics on job title string
                    if not filtered and candidates:
                        tokens_by_pos = {
                            'c-level': ['chief ', ' officer', 'CEO', 'CFO', 'COO', 'CTO', 'CIO', 'CMO', 'CHRO', 'CPO', 'CRO'],
                            'director': ['director'],
                            'senior director': ['senior director'],
                            'manager': ['manager'],
                            'senior manager': ['senior manager'],
                            'senior': ['senior'],
                            'lead': ['lead'],
                            'principal': ['principal'],
                            'vp': ['vp', 'vice president'],
                            'junior': ['junior', 'associate'],
                            'associate': ['associate'],
                            'assistant': ['assistant'],
                            'executive': ['executive'],
                            'specialist': ['specialist'],
                            'analyst': ['analyst'],
                            'officer': ['officer'],
                            'intern': ['intern']
                        }
                        import re as _re
                        for jt in list(candidates):
                            t = jt.strip()
                            toks = None
                            for key, arr in tokens_by_pos.items():
                                if key in pos_norm:
                                    toks = arr
                                    break
                            if not toks:
                                continue
                            t_low = t.lower()
                            matched = any(_re.search(r"\b" + _re.escape(tok.lower()) + r"\b", t_low, flags=_re.IGNORECASE) for tok in toks if tok)
                            # Guard against bleed (Manager vs Senior Manager, Director vs Senior Director, etc.)
                            if matched:
                                if 'senior manager' == pos_norm and 'senior manager' not in t_low:
                                    matched = False
                                if 'manager' == pos_norm and 'senior manager' in t_low:
                                    matched = False
                                if 'director' == pos_norm and 'senior director' in t_low:
                                    matched = False
                                if 'senior' == pos_norm and ('senior manager' in t_low or 'senior director' in t_low):
                                    matched = False
                            if matched:
                                filtered.append(jt)
                    # 3) Special-case C-level per department
                    if not filtered and 'c-level' in pos_norm:
                        def _c_titles_for_dept(dept: str):
                            d = (dept or '').strip().lower()
                            mapping_c = {
                                'human resources': ['Chief Human Resources Officer', 'Chief People Officer', 'CHRO', 'CPO'],
                                'hr': ['Chief Human Resources Officer', 'Chief People Officer', 'CHRO', 'CPO'],
                                'finance': ['Chief Financial Officer', 'CFO'],
                                'accounting': ['Chief Financial Officer', 'CFO'],
                                'engineering': ['Chief Technology Officer', 'CTO'],
                                'it': ['Chief Information Officer', 'CIO'],
                                'information technology': ['Chief Information Officer', 'CIO'],
                                'operations': ['Chief Operating Officer', 'COO'],
                                'marketing': ['Chief Marketing Officer', 'CMO'],
                                'sales': ['Chief Revenue Officer', 'CRO'],
                                'product': ['Chief Product Officer', 'CPO'],
                                'executive': ['Chief Executive Officer', 'CEO']
                            }
                            for k, vals in mapping_c.items():
                                if k in d:
                                    return vals
                            return ['Chief Executive Officer', 'CEO']
                        cands = _c_titles_for_dept(dept_text)
                        inter = [jt for jt in candidates if jt in cands]
                        filtered = inter if inter else cands

                    if filtered:
                        candidates = sorted(list(dict.fromkeys([c for c in filtered if c])))
            except Exception:
                candidates = []

            try:
                cur_txt = self.job_title_combo.currentText() or ''
            except Exception:
                cur_txt = ''
            self.job_title_combo.blockSignals(True)
            self.job_title_combo.clear()
            if candidates:
                self.job_title_combo.addItems(candidates)
            else:
                # No candidates; fall back to base defaults
                self.job_title_combo.addItems(jt_defaults)
            if cur_txt:
                idx = self.job_title_combo.findText(cur_txt)
                if idx >= 0:
                    self.job_title_combo.setCurrentIndex(idx)
                else:
                    try:
                        self.job_title_combo.setEditText(cur_txt)
                    except Exception:
                        pass
            self.job_title_combo.blockSignals(False)

        def _populate_positions(dept_text: str):
            """Populate positions dropdown based on selected department.

            Uses department template, then job_title mapping, then DB fallback, mirroring the profile dialog.
            """
            try:
                cur = self.position_combo.currentText() or ''
            except Exception:
                cur = ''
            existing = [self.position_combo.itemText(i) for i in range(self.position_combo.count())]
            self.position_combo.blockSignals(True)
            self.position_combo.clear()
            positions = []
            try:
                if self._dept_template and dept_text in self._dept_template:
                    for g, info in self._dept_template.get(dept_text, {}).items():
                        pos_list = info.get('positions') or info.get('roles') or []
                        if pos_list:
                            positions.extend(pos_list)
                if not positions:
                    for jt, meta in mapping.items():
                        try:
                            if meta.get('department') == dept_text and meta.get('position'):
                                positions.append(meta.get('position'))
                        except Exception:
                            continue
                if not positions:
                    try:
                        resp = supabase.table('employees').select('position').eq('department', dept_text).execute()
                        if resp and getattr(resp, 'data', None):
                            for r in resp.data:
                                p = (r.get('position') or '').strip()
                                if p:
                                    positions.append(p)
                    except Exception:
                        pass
                positions = sorted(list(dict.fromkeys([p for p in positions if p])))
            except Exception:
                positions = []
            # Always add a blank placeholder first so the combo doesn't default to an arbitrary first item
            try:
                self.position_combo.addItem('')
            except Exception:
                pass
            if positions:
                self.position_combo.addItems(positions)
            else:
                if existing:
                    # Preserve previously available choices if we had any
                    self.position_combo.addItems([it for it in existing if it])
                else:
                    # Fallback curated defaults
                    self.position_combo.addItems([
                        "Junior", "Mid-level", "Senior", "Lead", "Manager", "Senior Manager",
                        "Director", "Senior Director", "VP", "Senior VP", "C-Level", "Intern",
                        "Contractor", "Consultant", "Other"
                    ])
            try:
                self.position_combo.setEnabled(True)
            except Exception:
                pass
            # Restore previous or desired selection if available; otherwise leave blank (placeholder)
            if cur:
                try:
                    idx = self.position_combo.findText(cur)
                    if idx >= 0:
                        self.position_combo.setCurrentIndex(idx)
                    else:
                        self.position_combo.setEditText(cur)
                except Exception:
                    pass
            # If a desired position is set (e.g., from selected employee or editing a record), prefer it
            try:
                if getattr(self, '_desired_position', None):
                    dp = self._desired_position
                    self._desired_position = None
                    if dp:
                        idx = self.position_combo.findText(dp)
                        if idx >= 0:
                            self.position_combo.setCurrentIndex(idx)
                        else:
                            # allow free text if it's not in the list
                            try:
                                self.position_combo.setEditText(dp)
                            except Exception:
                                pass
            except Exception:
                pass
            self.position_combo.blockSignals(False)

        try:
            def _on_department_changed(txt):
                _populate_functional_groups(txt)
                _populate_positions(txt)
                _filter_job_titles_by_dept_and_group(txt, self.func_group_combo.currentText(), self.position_combo.currentText())
            self.department_combo.currentTextChanged.connect(_on_department_changed)
        except Exception:
            pass

        try:
            def _on_func_group_changed(txt):
                dept = self.department_combo.currentText() or ''
                _filter_job_titles_by_dept_and_group(dept, txt, self.position_combo.currentText())
            self.func_group_combo.currentTextChanged.connect(_on_func_group_changed)
        except Exception:
            pass

        # Wire position change to further filter job titles (e.g., C-Level + Department)
        try:
            def _on_position_changed(txt):
                dept = self.department_combo.currentText() or ''
                _filter_job_titles_by_dept_and_group(dept, self.func_group_combo.currentText(), txt)
            self.position_combo.currentTextChanged.connect(_on_position_changed)
        except Exception:
            pass

        self.employment_type_combo = QComboBox(self)
        self.employment_type_combo.addItems(["Full-time", "Part-time", "Contract", "Temporary"])
        # Work Status (short-term availability) and Payroll Status for history records
        self.work_status_combo = QComboBox(self)
        self.work_status_combo.setEditable(True)
        self.work_status_combo.addItems(['On Duty', 'On Leave', 'On Sick Leave', 'On Unpaid Leave', 'On Suspension', 'On Business Trip'])
        self.payroll_status_combo = QComboBox(self)
        self.payroll_status_combo.setEditable(True)
        self.payroll_status_combo.addItems(['Active Payroll', 'Inactive Payroll'])
        self.notes_input = QTextEdit(self)
        self.attach_btn = QPushButton('Choose Attachments', self)
        try:
            self.attach_btn.clicked.connect(self.choose_attachments)
        except Exception:
            pass
        self.attachment_inputs = []
        # Track uploaded public URLs for attachments (mirrors overseas tab behavior)
        self.uploaded_attachment_urls = []
        # header will be created later (single canonical header block below)

        # Populate the submit form rows (left) and the view table (right).
        try:
            form_layout.addRow('Job Title:', self.job_title_combo)
            if DEBUG_WIDGET_INIT:
                print('DBG: added job_title_combo to form_layout')
            form_layout.addRow('Position:', self.position_combo)
            form_layout.addRow('Department:', self.department_combo)
            form_layout.addRow('Functional Group:', self.func_group_combo)
            form_layout.addRow('Status:', self.history_status_combo)
            form_layout.addRow('Employment Type:', self.employment_type_combo)
            form_layout.addRow('Work Status:', self.work_status_combo)
            form_layout.addRow('Payroll Status:', self.payroll_status_combo)
            form_layout.addRow('Date Joined:', self.start_date_input)
            # End date with a small Clear button to allow empty value
            end_row_widget = QWidget(self)
            end_row_layout = QHBoxLayout()
            end_row_layout.setContentsMargins(0, 0, 0, 0)
            end_row_layout.addWidget(self.end_date_input)
            self.clear_end_date_btn = QPushButton('Clear', self)
            try:
                self.clear_end_date_btn.setToolTip('Clear end date (leave empty)')
            except Exception:
                pass
            try:
                self.clear_end_date_btn.clicked.connect(lambda: self.end_date_input.setDate(QDate()))
            except Exception:
                pass
            end_row_layout.addWidget(self.clear_end_date_btn)
            end_row_widget.setLayout(end_row_layout)
            form_layout.addRow('End Date (optional):', end_row_widget)
            form_layout.addRow('Notes:', self.notes_input)
            form_layout.addRow('Attachments:', self.attach_btn)
            self.submit_btn = QPushButton('Submit History', self)
            self.submit_btn.setObjectName('submit_history_btn')
            self.submit_btn.clicked.connect(self.submit_record)
            form_layout.addRow(self.submit_btn)
            # keep reference to the history form layout for later (used by edit_record to add Save button)
            self.history_form_layout = form_layout

            # Populate job/department/employment type choices from employees table
            try:
                self.load_employee_choices()
            except Exception:
                # Non-fatal: leave default combo items
                pass

            # Table view (right)
            view_layout = QVBoxLayout()
            view_layout.addWidget(QLabel('Employment / Re-employment History', self))
            if DEBUG_WIDGET_INIT:
                print('DBG: created view_layout')
            # --- Filter & Sort row ---
            filt_row = QHBoxLayout()
            self.search_input = QLineEdit(self)
            self.search_input.setPlaceholderText('Search job title, notes, or employee...')
            filt_row.addWidget(self.search_input, 2)
            self.filter_status_combo = QComboBox(self)
            self.filter_status_combo.addItem('All Statuses')
            filt_row.addWidget(self.filter_status_combo, 1)
            self.filter_dept_combo = QComboBox(self)
            self.filter_dept_combo.addItem('All Departments')
            filt_row.addWidget(self.filter_dept_combo, 1)
            self.sort_combo = QComboBox(self)
            self.sort_combo.addItems(['Sort: Start Date', 'Sort: End Date', 'Sort: Job Title', 'Sort: Department'])
            filt_row.addWidget(self.sort_combo, 1)
            self.sort_order_btn = QPushButton('↑', self)
            self.sort_order_btn.setToolTip('Toggle sort order (ascending/descending)')
            filt_row.addWidget(self.sort_order_btn)

            view_layout.addLayout(filt_row)

            self.record_table = QTableWidget(self)
            if DEBUG_WIDGET_INIT:
                print('DBG: created record_table', repr(self.record_table))
            # Columns: Employee Name, Job Title, Position, Department, Status, Functional Group, Employment Type,
            # Work Status, Payroll Status, Start Date, End Date, Service (yrs), Notes, Attachment URL, Last Updated (KL)
            self.record_table.setColumnCount(15)
            self.record_table.setHorizontalHeaderLabels(['Employee Name', 'Job Title', 'Position', 'Department', 'Status', 'Functional Group', 'Employment Type', 'Work Status', 'Payroll Status', 'Start Date', 'End Date', 'Service (yrs)', 'Notes', 'Attachment URL', 'Last Updated'])
            self.record_table.horizontalHeader().setStretchLastSection(True)
            try:
                self.record_table.itemDoubleClicked.connect(self.handle_edit_delete)
            except Exception:
                pass
            view_layout.addWidget(self.record_table)
            refresh_btn = QPushButton('Refresh', self)
            refresh_btn.clicked.connect(self.load_records)
            view_layout.addWidget(refresh_btn)
            # Validate and Auto-Fix buttons for invalid intervals
            validate_btn = QPushButton('Validate', self)
            validate_btn.setToolTip('Validate date intervals and highlight invalid rows')
            validate_btn.clicked.connect(lambda: self.load_records(validate_only=True))
            view_layout.addWidget(validate_btn)
            autofix_btn = QPushButton('Auto-Fix', self)
            autofix_btn.setToolTip('Attempt to auto-fix invalid intervals by swapping dates (asks before each change)')
            autofix_btn.clicked.connect(self.auto_fix_invalid_rows)
            view_layout.addWidget(autofix_btn)
            # connect filter signals to refresh table
            try:
                self.search_input.textChanged.connect(lambda _: self.load_records())
                self.filter_status_combo.currentIndexChanged.connect(lambda _: self.load_records())
                self.filter_dept_combo.currentIndexChanged.connect(lambda _: self.load_records())
                self.sort_combo.currentIndexChanged.connect(lambda _: self.load_records())
                self.sort_order_btn.clicked.connect(self.toggle_sort_order)
            except Exception:
                pass

            history_layout.addLayout(form_layout, 1)
            history_layout.addLayout(view_layout, 2)
            history_widget.setLayout(history_layout)
            if DEBUG_WIDGET_INIT:
                print('DBG: history_widget layout set; history_layout children count=', history_layout.count())
        except Exception:
            pass

        # Add tabs (History only; Employment Status subtab removed as redundant)
        if DEBUG_WIDGET_INIT:
            print('DBG: about to add tabs')
        self.tabs.addTab(history_widget, 'History')
        if DEBUG_WIDGET_INIT:
            print('DBG: tabs added; tabs.count=', self.tabs.count())

        # Header to show selected employee with avatar, name and actions
        header_row = QHBoxLayout()
        # Avatar
        self.avatar_label = QLabel(self)
        self.avatar_label.resize(60, 60)
        self.avatar_label.setStyleSheet('border-radius: 30px; background-color: #eee;')
        header_row.addWidget(self.avatar_label)

        # Name + subtitle stack
        name_col = QVBoxLayout()
        self.name_label = QLabel(DEFAULT_NO_EMP_TEXT, self)
        self.name_label.setProperty('class', 'subheading')
        # keep older attribute name for compatibility with tests/other modules
        # Ensure header_label is always initialized here so later code and tests can rely on it
        if not hasattr(self, 'header_label'):
            self.header_label = self.name_label
        self.subtitle_label = QLabel('', self)
        self.subtitle_label.setProperty('class', 'muted')
        name_col.addWidget(self.name_label)
        name_col.addWidget(self.subtitle_label)
        header_row.addLayout(name_col)

        header_row.addStretch()
        # Choose button (opens inline selector)
        self.choose_emp_btn = QPushButton('Choose employee', self)
        self.choose_emp_btn.setToolTip('Open a search dialog to select an employee')
        header_row.addWidget(self.choose_emp_btn)
        # View profile button (opens full profile dialog)
        self.view_profile_btn = QPushButton('View profile', self)
        self.view_profile_btn.setToolTip('Open the full employee profile dialog')
        self.view_profile_btn.setEnabled(False)
        header_row.addWidget(self.view_profile_btn)
        main.addLayout(header_row)
        # small instruction to clarify how to choose
        self.instruction_label = QLabel("Click 'Choose employee' or press Ctrl+E, then pick from the dialog.", self)
        self.instruction_label.setProperty('class', 'muted')
        main.addWidget(self.instruction_label)
        # Connect choose and view buttons
        self.choose_emp_btn.clicked.connect(self.request_choose_employee)
        self.view_profile_btn.clicked.connect(self.open_view_profile)
        # Shortcut to request choose employee
        try:
            self.choose_shortcut = QShortcut(QKeySequence('Ctrl+E'), self)
            self.choose_shortcut.activated.connect(self.request_choose_employee)
        except Exception:
            pass
        main.addWidget(self.tabs)
        if DEBUG_WIDGET_INIT:
            print('DBG: added tabs to main layout')
        # safety: ensure header_label exists (some runtime paths may have missed assignment)
        if not hasattr(self, 'header_label'):
            try:
                self.header_label = getattr(self, 'name_label')
            except Exception:
                self.header_label = QLabel(DEFAULT_NO_EMP_TEXT, self)
        if DEBUG_WIDGET_INIT:
            print('DBG: about to call setLayout(main)')
        self.setLayout(main)
        if DEBUG_WIDGET_INIT:
            print('DBG: setLayout done; widget layout count=', main.count())

        # disable form controls until an employee is selected
        self.set_form_enabled(False)
        # load initial data
        self.load_records()

    def autofill_job_title(self, text: str):
        """Auto-fill Position and Department from centralized mapping when job title changes.

        Conservative: does not overwrite non-empty fields.
        """
        try:
            from gui.job_title_mapping_loader import load_job_title_mapping
            mapping = load_job_title_mapping()
            if not mapping:
                return
            meta = mapping.get(text)
            if not meta:
                return
            if hasattr(self.position_combo, 'setCurrentText'):
                try:
                    cur = self.position_combo.currentText() if self.position_combo.currentText() else ''
                except Exception:
                    cur = ''
                if not cur:
                    self.position_combo.setCurrentText(meta.get('position') or '')
            if hasattr(self.department_combo, 'setCurrentText'):
                try:
                    curd = self.department_combo.currentText() if self.department_combo.currentText() else ''
                except Exception:
                    curd = ''
                if not curd:
                    self.department_combo.setCurrentText(meta.get('department') or '')
        except Exception:
            pass
        # autofill_job_title should only set values; widget creation and layout
        # population are handled in __init__ to ensure the UI is visible.

    def set_employee(self, employee):
        """Set the current employee (dict or id). Accepts employee dict with keys 'id' and 'full_name', or a uuid string."""
        if not employee:
            self.employee = None
            self.employee_id = None
            self.header_label.setText(DEFAULT_NO_EMP_TEXT)
            return
        if isinstance(employee, str):
            self.employee_id = employee
            self.employee = None
            self.header_label.setText(f'Employee: {employee}')
        else:
            # assume dict-like
            self.employee = employee
            self.employee_id = employee.get('id') or employee.get('employee_id')
            name = employee.get('full_name') or employee.get('employee_name') or str(self.employee_id)
            self.header_label.setText(f'Employee: {name}')
        # reload records for the new employee
        self.load_records()
        # refresh choice lists from employees table in case new values were added
        try:
            self.load_employee_choices()
        except Exception:
            pass
        # enable form controls now that we have an employee
        if self.employee_id:
            self.set_form_enabled(True)
            # update header avatar and subtitle
            try:
                # show a small avatar if available, else placeholder
                photo_url = None
                if isinstance(employee, dict):
                    photo_url = employee.get('photo_url') or employee.get('avatar')
                pm = None
                if photo_url:
                    try:
                        from urllib.request import urlopen
                        data = urlopen(photo_url).read()
                        pm = QPixmap()
                        pm.loadFromData(data)
                    except Exception:
                        pm = None
                # if no pixmap loaded, try default avatar file
                if pm is None:
                    default_path = os.path.join('assets', 'default_avatar.png')
                    if os.path.exists(default_path):
                        try:
                            pm = QPixmap(default_path)
                        except Exception:
                            pm = None
                # final fallback: create a placeholder pixmap
                if pm is None or pm.isNull():
                    pm = self._create_placeholder_pixmap(60)
                # Circular crop & scale to 60x60
                try:
                    cropped = QPixmap(60, 60)
                    cropped.fill(Qt.transparent)
                    from PyQt5.QtGui import QPainter, QPainterPath
                    painter = QPainter(cropped)
                    path = QPainterPath()
                    path.addEllipse(0, 0, 60, 60)
                    painter.setRenderHint(QPainter.Antialiasing)
                    painter.setClipPath(path)
                    painter.drawPixmap(0, 0, pm.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
                    painter.end()
                    self.avatar_label.setPixmap(cropped)
                except Exception:
                    # fallback to un-cropped pixmap
                    self.avatar_label.setPixmap(pm.scaled(60, 60))

                # subtitle: email / job title
                if isinstance(employee, dict):
                    email = employee.get('email') or ''
                    job = employee.get('job_title') or employee.get('position') or ''
                    self.subtitle_label.setText(f"{email} {('• ' + job) if job else ''}")
                    self.view_profile_btn.setEnabled(True)
            except Exception:
                pass
        else:
            self.set_form_enabled(False)

        # After setting the employee and loading choices, prefill the input widgets
        # with the employee's current employment values (so profile edits are reflected).
        try:
            if isinstance(employee, dict):
                jt = employee.get('job_title') or employee.get('position') or ''
                pos = employee.get('position') or ''
                dep = employee.get('department') or ''
                fg = employee.get('functional_group') or ''
                et = employee.get('employment_type') or ''
                # Set desired position so when department repopulates positions we keep the employee's actual value
                try:
                    if pos:
                        self._desired_position = pos
                except Exception:
                    pass
                try:
                    if jt:
                        # prefer exact match; fall back to edit text
                        idx = self.job_title_combo.findText(jt)
                        if idx >= 0:
                            self.job_title_combo.setCurrentIndex(idx)
                        else:
                            self.job_title_combo.setEditText(jt)
                except Exception:
                    pass
                try:
                    if pos:
                        idx = self.position_combo.findText(pos)
                        if idx >= 0:
                            self.position_combo.setCurrentIndex(idx)
                        else:
                            self.position_combo.setEditText(pos)
                except Exception:
                    pass
                try:
                    if dep:
                        idx = self.department_combo.findText(dep)
                        if idx >= 0:
                            self.department_combo.setCurrentIndex(idx)
                        else:
                            self.department_combo.setEditText(dep)
                except Exception:
                    pass
                try:
                    if fg:
                        idx = self.func_group_combo.findText(fg)
                        if idx >= 0:
                            self.func_group_combo.setCurrentIndex(idx)
                        else:
                            self.func_group_combo.setEditText(fg)
                except Exception:
                    pass
                try:
                    if et:
                        idx = self.employment_type_combo.findText(et)
                        if idx >= 0:
                            self.employment_type_combo.setCurrentIndex(idx)
                        else:
                            self.employment_type_combo.setEditText(et)
                except Exception:
                    pass
                # Prefill start_date_input from employee['date_joined'] when available
                try:
                    dj = employee.get('date_joined') if isinstance(employee, dict) else None
                    if dj:
                        d = QDate.fromString(dj, 'yyyy-MM-dd')
                        if d.isValid():
                            self.start_date_input.setDate(d)
                except Exception:
                    pass
        except Exception:
            pass

    def open_view_profile(self):
        if not self.employee:
            return
        try:
            dlg = EmployeeProfileDialog(employee_data=self.employee, parent=self, is_admin=True)
            # when profile dialog saves, refresh this history tab's records and choice lists
            try:
                dlg.employee_saved.connect(lambda emp_id: (self.load_records(), self.load_employee_choices()))
            except Exception:
                pass
            dlg.exec_()
        except Exception:
            pass

    def _create_placeholder_pixmap(self, size=60):
        from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont
        pm = QPixmap(size, size)
        pm.fill(Qt.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor('#888888'))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(0, 0, size, size)
        painter.setPen(QColor('#ffffff'))
        f = QFont('Arial', max(10, size // 2))
        painter.setFont(f)
        painter.drawText(pm.rect(), Qt.AlignCenter, '👤')
        painter.end()
        return pm

    def set_form_enabled(self, enabled: bool):
        """Enable/disable history and status form controls based on whether an employee is selected."""
        # History form
        try:
            self.job_title_combo.setEnabled(enabled)
        except Exception:
            pass
        try:
            self.position_combo.setEnabled(enabled)
        except Exception:
            pass
        try:
            self.department_combo.setEnabled(enabled)
        except Exception:
            pass
        try:
            self.func_group_combo.setEnabled(enabled)
        except Exception:
            pass
        try:
            self.employment_type_combo.setEnabled(enabled)
        except Exception:
            pass
        self.start_date_input.setEnabled(enabled)
        self.end_date_input.setEnabled(enabled)
        try:
            self.clear_end_date_btn.setEnabled(enabled)
        except Exception:
            pass
        self.notes_input.setEnabled(enabled)
        self.attach_btn.setEnabled(enabled)
        # find submit button (it's the last widget in the form layout)
        try:
            # find by object name which is set in __init__
            submit_btn = self.findChild(QPushButton, 'submit_history_btn')
            if submit_btn:
                submit_btn.setEnabled(enabled)
        except Exception:
            pass

    def request_choose_employee(self):
        """Slot to be connected by parent window to switch to Profiles tab when user clicks the Choose employee button."""
        # Open an inline modal dialog allowing search/selection so user doesn't need to switch tabs
        try:
            # prefill search with current employee name if available
            pre = ''
            try:
                if self.employee and isinstance(self.employee, dict):
                    pre = self.employee.get('full_name') or self.employee.get('employee_name') or ''
                elif hasattr(self, 'name_label') and self.name_label:
                    txt = self.name_label.text() or ''
                    if txt and 'No employee' not in txt:
                        pre = txt
            except Exception:
                pre = ''
            dlg = EmployeeSelectorDialog(self, prefilter=pre)
            if dlg.exec_():
                sel = dlg.selected
                if sel:
                    # apply selection immediately
                    self.set_employee(sel)
        except Exception:
            # fallback: try to call parent handler if dialog fails
            try:
                parent = self.parent()
                if parent and hasattr(parent, 'request_show_profiles_tab'):
                    parent.request_show_profiles_tab()
            except Exception:
                pass

    def load_employee_choices(self):
        """Load distinct job titles, departments, and employment types from the employees table
        and populate the corresponding combo boxes. Non-fatal on errors.
        """
        try:
            # include functional_group column (recently added) when querying employees
            resp = supabase.table('employees').select('job_title, department, employment_type, position, functional_group, work_status, payroll_status').execute()
            if not resp or not getattr(resp, 'data', None):
                return
            rows = resp.data
            job_titles = []
            positions = []
            departments = []
            emp_types = []
            func_groups = []
            work_statuses = []
            payroll_statuses = []
            for r in rows:
                jt = (r.get('job_title') or '').strip()
                pos = (r.get('position') or '').strip()
                dep = (r.get('department') or '').strip()
                et = (r.get('employment_type') or '').strip()
                fg = (r.get('functional_group') or '').strip()
                ws = (r.get('work_status') or '').strip()
                ps = (r.get('payroll_status') or '').strip()
                if jt:
                    job_titles.append(jt)
                if pos:
                    positions.append(pos)
                if dep:
                    departments.append(dep)
                if et:
                    emp_types.append(et)
                if fg:
                    func_groups.append(fg)
                if ws:
                    work_statuses.append(ws)
                if ps:
                    payroll_statuses.append(ps)

            # dedupe and sort
            def _uniq_sort(seq):
                return sorted(list(dict.fromkeys([s for s in seq if s])))

            job_titles = _uniq_sort(job_titles)
            positions = _uniq_sort(positions)
            departments = _uniq_sort(departments)
            emp_types = _uniq_sort(emp_types)
            func_groups = _uniq_sort(func_groups)
            work_statuses = _uniq_sort(work_statuses)
            payroll_statuses = _uniq_sort(payroll_statuses)

            # update combos while preserving any user-entered text
            def _merge_into_combo(combo, default_items, fetched_items, preserve_text=True):
                """Merge fetched_items into combo's existing default_items while preserving current text.

                - default_items: the curated defaults currently present in the widget (list)
                - fetched_items: list of items fetched from DB (already deduped/sorted)
                """
                # compute merged list: defaults first, then any fetched items not already present
                merged = list(dict.fromkeys((default_items or []) + (fetched_items or [])))
                cur_txt = ''
                if preserve_text:
                    try:
                        cur_txt = combo.currentText() or ''
                    except Exception:
                        cur_txt = ''
                combo.blockSignals(True)
                combo.clear()
                if merged:
                    combo.addItems(merged)
                else:
                    combo.addItems(default_items or ["Other"])
                if cur_txt:
                    idx = combo.findText(cur_txt)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                    else:
                        try:
                            combo.setEditText(cur_txt)
                        except Exception:
                            pass
                combo.blockSignals(False)

            # determine the current curated defaults from the widget (so we don't lose them)
            try:
                defaults_jt = [self.job_title_combo.itemText(i) for i in range(self.job_title_combo.count())]
            except Exception:
                defaults_jt = []
            try:
                defaults_pos = [self.position_combo.itemText(i) for i in range(self.position_combo.count())]
            except Exception:
                defaults_pos = []
            try:
                defaults_dep = [self.department_combo.itemText(i) for i in range(self.department_combo.count())]
            except Exception:
                defaults_dep = []
            try:
                defaults_et = [self.employment_type_combo.itemText(i) for i in range(self.employment_type_combo.count())]
            except Exception:
                defaults_et = []

            _merge_into_combo(self.job_title_combo, defaults_jt, job_titles)
            _merge_into_combo(self.position_combo, defaults_pos, positions)
            _merge_into_combo(self.department_combo, defaults_dep, departments)
            _merge_into_combo(self.func_group_combo, [self.func_group_combo.itemText(i) for i in range(self.func_group_combo.count())], func_groups)
            _merge_into_combo(self.employment_type_combo, defaults_et, emp_types or ["Full-time", "Part-time", "Contract", "Temporary"]) 
            try:
                if work_statuses:
                    # Merge work_status values only into the dedicated work_status combo (and keep status_combo canonical)
                    _merge_into_combo(self.work_status_combo, [self.work_status_combo.itemText(i) for i in range(self.work_status_combo.count())], work_statuses)
                if payroll_statuses:
                    _merge_into_combo(self.payroll_status_combo, [self.payroll_status_combo.itemText(i) for i in range(self.payroll_status_combo.count())], payroll_statuses)
            except Exception:
                pass
            # If an employee is currently selected, set the form inputs to their current values
            try:
                if getattr(self, 'employee', None) and isinstance(self.employee, dict):
                    emp = self.employee
                    try:
                        jt = emp.get('job_title') or emp.get('position') or ''
                        if jt:
                            idx = self.job_title_combo.findText(jt)
                            if idx >= 0:
                                self.job_title_combo.setCurrentIndex(idx)
                            else:
                                self.job_title_combo.setEditText(jt)
                    except Exception:
                        pass
                    try:
                        pos = emp.get('position') or ''
                        if pos:
                            idx = self.position_combo.findText(pos)
                            if idx >= 0:
                                self.position_combo.setCurrentIndex(idx)
                            else:
                                self.position_combo.setEditText(pos)
                    except Exception:
                        pass
                    # If the employee row has a date_joined, prefill the start_date_input so history form reflects profile
                    try:
                        dj = emp.get('date_joined') or emp.get('start_date')
                        if dj:
                            d = QDate.fromString(dj, 'yyyy-MM-dd')
                            if d.isValid():
                                self.start_date_input.setDate(d)
                    except Exception:
                        pass
                    try:
                        dep = emp.get('department') or ''
                        if dep:
                            idx = self.department_combo.findText(dep)
                            if idx >= 0:
                                self.department_combo.setCurrentIndex(idx)
                            else:
                                self.department_combo.setEditText(dep)
                    except Exception:
                        pass
                    try:
                        fg = emp.get('functional_group') or ''
                        if fg:
                            idx = self.func_group_combo.findText(fg)
                            if idx >= 0:
                                self.func_group_combo.setCurrentIndex(idx)
                            else:
                                self.func_group_combo.setEditText(fg)
                    except Exception:
                        pass
                    try:
                        et = emp.get('employment_type') or ''
                        if et:
                            idx = self.employment_type_combo.findText(et)
                            if idx >= 0:
                                self.employment_type_combo.setCurrentIndex(idx)
                            else:
                                self.employment_type_combo.setEditText(et)
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception as e:
            # non-fatal: preserve existing combo contents
            print(f"DEBUG: Failed loading employee choices: {e}")

        # Populate filter combos from the same fetched data where possible
        try:
            # job status list -> filter_status_combo
            status_items = ['All Statuses'] + (work_statuses or [])
            # but use canonical history statuses too
            hist_statuses = [self.history_status_combo.itemText(i) for i in range(self.history_status_combo.count())]
            status_items = ['All Statuses'] + sorted(list(dict.fromkeys(hist_statuses + (work_statuses or []))))
            self.filter_status_combo.blockSignals(True)
            self.filter_status_combo.clear()
            self.filter_status_combo.addItems(status_items)
            self.filter_status_combo.blockSignals(False)
        except Exception:
            pass
        try:
            dept_items = ['All Departments'] + (departments or [])
            # dedupe
            dept_items = ['All Departments'] + sorted(list(dict.fromkeys([d for d in (departments or []) if d])))
            self.filter_dept_combo.blockSignals(True)
            self.filter_dept_combo.clear()
            self.filter_dept_combo.addItems(dept_items)
            self.filter_dept_combo.blockSignals(False)
        except Exception:
            pass

    def choose_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(self, 'Select attachments')
        self.attachment_inputs = files
        if not files:
            self.attach_btn.setText('Choose Attachments')
            return

        # reflect selection immediately
        self.attach_btn.setText(f"{len(files)} file(s) selected")

        attachment_urls = []
        failed_uploads = []
        try:
            from services.supabase_service import upload_document_to_bucket
            identifier = None
            try:
                if isinstance(self.employee, dict):
                    identifier = self.employee.get('email') or self.employee.get('employee_id') or self.employee.get('id')
            except Exception:
                identifier = None
            if not identifier:
                identifier = str(self.employee_id) if self.employee_id else ''

            for file_path in (files or []):
                try:
                    url = upload_document_to_bucket(file_path, identifier)
                except Exception:
                    url = None
                if url:
                    if isinstance(url, str) and url.endswith('?'):
                        url = url.rstrip('?')
                    attachment_urls.append(url)
                else:
                    failed_uploads.append(os.path.basename(file_path))

            # store uploaded public URLs and update the button text
            self.uploaded_attachment_urls = attachment_urls
            if self.uploaded_attachment_urls:
                self.attach_btn.setText(f"{len(self.uploaded_attachment_urls)} uploaded")
            if failed_uploads:
                try:
                    QMessageBox.information(self, 'Partial Upload', f"Failed to upload: {', '.join(failed_uploads)}")
                except Exception:
                    print(f"DEBUG: Failed to notify about failed uploads: {failed_uploads}")
        except Exception as e:
            print(f"DEBUG: Attachment upload attempt failed: {e}")

    def submit_record(self):
        """Collect form fields, build a history record and insert it into the DB."""
        job_title = self.job_title_combo.currentText().strip()
        position = self.position_combo.currentText().strip()
        department = self.department_combo.currentText().strip()
        employment_type = self.employment_type_combo.currentText().strip()
        start_qd = self.start_date_input.date()
        end_qd = self.end_date_input.date()
        start_str = start_qd.toString('yyyy-MM-dd') if start_qd.isValid() else None
        # treat empty/invalid end date as None
        try:
            if end_qd.isValid() and end_qd != QDate():
                end_str = end_qd.toString('yyyy-MM-dd')
            else:
                end_str = None
        except Exception:
            end_str = None
        if not job_title or not department or not start_str:
            QMessageBox.warning(self, 'Input Error', 'Job Title, Department and Date Joined are required')
            return

        rec = {
            'id': str(uuid4()),
            'employee_id': self.employee_id,
            'job_title': job_title,
            'position': position,
            'department': department,
            'status': self.history_status_combo.currentText().strip() or None,
            'functional_group': self.func_group_combo.currentText().strip(),
            'work_status': self.work_status_combo.currentText().strip() or None,
            'payroll_status': self.payroll_status_combo.currentText().strip() or None,
            'employment_type': employment_type,
            'start_date': start_str,
            'end_date': end_str,
            'notes': self.notes_input.toPlainText() or None,
            'attachments': self.attachment_inputs or [],
            'attachment_url': (','.join(self.uploaded_attachment_urls) if self.uploaded_attachment_urls else None)
        }
        try:
            resp = insert_employee_history_record(rec)
            QMessageBox.information(self, 'Saved', 'History record saved')
            try:
                if self.employee_id:
                    self.history_changed.emit(str(self.employee_id))
            except Exception:
                pass
            # If this record represents the current/ongoing snapshot (no end date),
            # sync its fields back to the employee profile and employee_status.
            try:
                self._maybe_sync_profile_from_history(rec)
            except Exception as _sync_e:
                print(f"DEBUG: history->profile sync skipped: {_sync_e}")
        except Exception as e:
            QMessageBox.warning(self, 'Error', f'Failed to save history: {e}')
            return

        # Clear form
        try:
            self.job_title_combo.setCurrentText('')
        except Exception:
            pass
        try:
            self.position_combo.setCurrentText('')
        except Exception:
            pass
        try:
            self.func_group_combo.setCurrentText('')
        except Exception:
            pass
        try:
            self.department_combo.setCurrentText('')
        except Exception:
            pass
        try:
            self.employment_type_combo.setCurrentIndex(0)
        except Exception:
            pass
        self.start_date_input.setDate(QDate.currentDate())
        # leave end date empty by default after clearing
        try:
            self.end_date_input.setDate(QDate())
        except Exception:
            pass
        self.notes_input.clear()
        self.attachment_inputs = []
        self.attach_btn.setText('Choose Attachments')
        try:
            self.uploaded_attachment_urls = []
        except Exception:
            pass
        self.load_records()

    def load_records(self, validate_only: bool = False):
        # Fetch from supabase
        try:
            rows = fetch_employee_history_records(self.employee_id, None)
        except Exception:
            rows = []
        # apply filter & sort before populating the table
        try:
            rows = self.apply_filters_and_sort(rows)
        except Exception:
            pass
        self.record_table.clearContents()
        self.record_table.setRowCount(0)
        # If rows include employee IDs, fetch their names in one batch to avoid per-row queries
        emp_ids = sorted(list({r.get('employee_id') for r in (rows or []) if r.get('employee_id')}))
        emp_map = {}
        try:
            if emp_ids:
                resp = supabase.table('employees').select('id, full_name').in_('id', emp_ids).execute()
                if resp and getattr(resp, 'data', None):
                    for er in resp.data:
                        emp_map[er.get('id')] = er.get('full_name')
        except Exception:
            emp_map = {}

        for i, r in enumerate(rows):
            self.record_table.insertRow(i)
            # Employee name (prefer record field if present, else lookup by employee_id)
            name = r.get('full_name') or r.get('employee_name') or emp_map.get(r.get('employee_id')) or ''
            item_name = QTableWidgetItem(str(name))
            item_name.setData(Qt.UserRole, r)
            self.record_table.setItem(i, 0, item_name)

            # Job title and the rest (shifted by +1 because of the new Employee Name column)
            cols = [
                str(r.get('job_title') or ''),
                str(r.get('position') or ''),
                str(r.get('department') or ''),
                str(r.get('status') or ''),
                str(r.get('functional_group') or ''),
                str(r.get('employment_type') or ''),
                str(r.get('work_status') or ''),
                str(r.get('payroll_status') or ''),
                str(r.get('start_date') or ''),
                str(r.get('end_date') or ''),
            ]
            for col_idx, val in enumerate(cols, start=1):
                it = QTableWidgetItem(val)
                it.setData(Qt.UserRole, r)
                self.record_table.setItem(i, col_idx, it)

            # validate date intervals for this row and mark invalid intervals
            try:
                s_raw = r.get('start_date')
                e_raw = r.get('end_date')
                s_q = QDate.fromString(s_raw, 'yyyy-MM-dd') if s_raw else None
                e_q = QDate.fromString(e_raw, 'yyyy-MM-dd') if e_raw else None
                if s_q and s_q.isValid() and e_q and e_q.isValid():
                    if e_q < s_q:
                        # mark the whole row in light red and add a tooltip explaining the issue
                        for c in range(self.record_table.columnCount()):
                            item = self.record_table.item(i, c)
                            if item is None:
                                item = QTableWidgetItem('')
                                self.record_table.setItem(i, c, item)
                            try:
                                item.setBackground(QColor(255, 230, 230))
                                item.setToolTip('Invalid interval: End Date is earlier than Start Date')
                            except Exception:
                                pass
                        # annotate end date cell text to make it obvious
                        try:
                            end_item = self.record_table.item(i, 10) or self.record_table.item(i, 11)
                            if end_item:
                                end_item.setText(str(e_raw) + ' (invalid)')
                        except Exception:
                            pass
                        # set an auxiliary data flag so editors can detect invalid state
                        try:
                            first = self.record_table.item(i, 0)
                            if first:
                                first.setData(Qt.UserRole + 1, {'invalid_dates': True})
                        except Exception:
                            pass
            except Exception:
                pass

            notes = r.get('notes') or ''
            atts = ','.join([os.path.basename(p) for p in (r.get('attachments') or [])])

            # Service (years) for the record: per-row period only
            try:
                from core.employee_service import format_years
                s_date = r.get('start_date')
                e_date = r.get('end_date')
                serv_text = ''
                if s_date:
                    s = QDate.fromString(s_date, 'yyyy-MM-dd')
                    if s.isValid():
                        if e_date:
                            e = QDate.fromString(e_date, 'yyyy-MM-dd')
                            if e.isValid():
                                days = (e.toPyDate() - s.toPyDate()).days
                                serv_text = format_years(days / 365.25)
                            else:
                                serv_text = ''
                        else:
                            days = (QDate.currentDate().toPyDate() - s.toPyDate()).days
                            serv_text = format_years(days / 365.25)
            except Exception:
                serv_text = ''

            serv_item = QTableWidgetItem(serv_text)
            serv_item.setData(Qt.UserRole, r)
            self.record_table.setItem(i, 11, serv_item)

            note_item = QTableWidgetItem(notes)
            note_item.setData(Qt.UserRole, r)
            self.record_table.setItem(i, 12, note_item)
            att_item = QTableWidgetItem(str(r.get('attachment_url') or (atts or '')))
            att_item.setData(Qt.UserRole, r)
            self.record_table.setItem(i, 13, att_item)
            # Last updated (convert UTC/timestamptz to KL time for display)
            try:
                from services.supabase_service import convert_utc_to_kl
                upd = r.get('updated_at') or r.get('updated') or r.get('modified_at')
                if upd:
                    upd_text = convert_utc_to_kl(upd)
                else:
                    upd_text = ''
            except Exception:
                upd_text = str(r.get('updated_at') or '')
            upd_item = QTableWidgetItem(upd_text)
            upd_item.setData(Qt.UserRole, r)
            self.record_table.setItem(i, 14, upd_item)


    def handle_edit_delete(self, item):
        rec = item.data(Qt.UserRole)
        msg = QMessageBox()
        msg.setText('Edit or Delete this history record?')
        edit_btn = msg.addButton('Edit', QMessageBox.ActionRole)
        delete_btn = msg.addButton('Delete', QMessageBox.ActionRole)
        cancel_btn = msg.addButton(QMessageBox.Cancel)
        msg.exec_()
        if msg.clickedButton() == edit_btn:
            self.edit_record(rec)
        elif msg.clickedButton() == delete_btn:
            self.delete_record(rec)

    def edit_record(self, rec):
        # populate form with record data for inline edit
        # populate job/department/employment type
        # remember previous employee context so Cancel can restore it
        prev_employee = getattr(self, 'employee', None)
        prev_employee_id = getattr(self, 'employee_id', None)

        # If the record belongs to a different employee than currently selected,
        # fetch that employee and set as current so the header and form reflect
        # the record being edited. This makes inline editing act on the proper
        # employee without requiring the user to manually choose them first.
        try:
            rec_eid = rec.get('employee_id')
            if rec_eid and rec_eid != prev_employee_id:
                try:
                    resp = supabase.table('employees').select('*').eq('id', rec_eid).execute()
                    if resp and getattr(resp, 'data', None):
                        emp = resp.data[0]
                    else:
                        emp = {'id': rec_eid}
                    # call set_employee with the fetched employee dict (or fallback id)
                    self.set_employee(emp)
                except Exception:
                    # if fetching fails, still continue editing the record fields
                    pass
        except Exception:
            pass
        try:
            if rec.get('job_title') is not None:
                idx = self.job_title_combo.findText(rec.get('job_title'))
                if idx >= 0:
                    self.job_title_combo.setCurrentIndex(idx)
                else:
                    self.job_title_combo.setCurrentText(rec.get('job_title'))
        except Exception:
            pass
        # ensure autofill runs after job title is set
        try:
            self.autofill_job_title(self.job_title_combo.currentText())
        except Exception:
            pass
        try:
            if rec.get('position') is not None:
                # Ensure department-driven population selects this after refresh
                try:
                    self._desired_position = rec.get('position')
                except Exception:
                    pass
                idx = self.position_combo.findText(rec.get('position'))
                if idx >= 0:
                    self.position_combo.setCurrentIndex(idx)
                else:
                    self.position_combo.setCurrentText(rec.get('position'))
        except Exception:
            pass
        try:
            if rec.get('department') is not None:
                idx = self.department_combo.findText(rec.get('department'))
                if idx >= 0:
                    self.department_combo.setCurrentIndex(idx)
                else:
                    self.department_combo.setCurrentText(rec.get('department'))
        except Exception:
            pass
        # populate functional_group (after department so template-derived groups are available)
        try:
            if rec.get('functional_group') is not None:
                idx = self.func_group_combo.findText(rec.get('functional_group'))
                if idx >= 0:
                    self.func_group_combo.setCurrentIndex(idx)
                else:
                    self.func_group_combo.setCurrentText(rec.get('functional_group'))
        except Exception:
            pass
        try:
            if rec.get('employment_type') is not None:
                idx = self.employment_type_combo.findText(rec.get('employment_type'))
                if idx >= 0:
                    self.employment_type_combo.setCurrentIndex(idx)
        except Exception:
            pass
        try:
            if rec.get('status') is not None:
                idx = self.history_status_combo.findText(rec.get('status'))
                if idx >= 0:
                    self.history_status_combo.setCurrentIndex(idx)
                else:
                    self.history_status_combo.setCurrentText(rec.get('status'))
        except Exception:
            pass
        try:
            if rec.get('start_date'):
                d = QDate.fromString(rec.get('start_date'), 'yyyy-MM-dd')
                if d.isValid():
                    self.start_date_input.setDate(d)
        except Exception:
            pass
        try:
            if rec.get('end_date'):
                d = QDate.fromString(rec.get('end_date'), 'yyyy-MM-dd')
                if d.isValid():
                    self.end_date_input.setDate(d)
        except Exception:
            pass
        self.notes_input.setText(rec.get('notes',''))
        # ensure form controls are enabled for editing even if no employee selected
        try:
            self.set_form_enabled(True)
        except Exception:
            pass

        # Explicitly make widgets editable/enabled to cover cases where they
        # were created read-only or disabled elsewhere.
        try:
            try:
                self.job_title_combo.setEnabled(True)
            except Exception:
                pass
            try:
                self.job_title_combo.setEditable(True)
            except Exception:
                pass
            try:
                self.position_combo.setEnabled(True)
                self.position_combo.setEditable(True)
            except Exception:
                pass
            try:
                self.department_combo.setEnabled(True)
                self.department_combo.setEditable(True)
            except Exception:
                pass
            try:
                self.func_group_combo.setEnabled(True)
                self.func_group_combo.setEditable(True)
            except Exception:
                pass
            try:
                # employment_type may have been non-editable by design; allow editing during inline edit
                self.employment_type_combo.setEnabled(True)
                self.employment_type_combo.setEditable(True)
            except Exception:
                pass
            try:
                self.history_status_combo.setEnabled(True)
                self.history_status_combo.setEditable(True)
            except Exception:
                pass
            try:
                self.work_status_combo.setEnabled(True)
            except Exception:
                pass
            try:
                self.payroll_status_combo.setEnabled(True)
            except Exception:
                pass
            try:
                self.start_date_input.setEnabled(True)
                self.end_date_input.setEnabled(True)
            except Exception:
                pass
            try:
                self.notes_input.setEnabled(True)
                self.notes_input.setReadOnly(False)
            except Exception:
                pass
            try:
                self.attach_btn.setEnabled(True)
            except Exception:
                pass
            try:
                submit_btn = self.findChild(QPushButton, 'submit_history_btn')
                if submit_btn:
                    submit_btn.setEnabled(True)
            except Exception:
                pass
        except Exception:
            pass

        # save handler
        def save_edit():
            data = {
                'job_title': self.job_title_combo.currentText().strip() or None,
                'position': self.position_combo.currentText().strip() or None,
                'department': self.department_combo.currentText().strip() or None,
                'status': self.history_status_combo.currentText().strip() or None,
                'functional_group': self.func_group_combo.currentText().strip() or None,
                'work_status': self.work_status_combo.currentText().strip() or None,
                'payroll_status': self.payroll_status_combo.currentText().strip() or None,
                'employment_type': self.employment_type_combo.currentText().strip() or None,
                'start_date': self.start_date_input.date().toString('yyyy-MM-dd') if self.start_date_input.date().isValid() else None,
                'end_date': self.end_date_input.date().toString('yyyy-MM-dd') if self.end_date_input.date().isValid() else None,
                'notes': self.notes_input.toPlainText() or None,
                'attachments': self.attachment_inputs or None,
                'attachment_url': (','.join(self.uploaded_attachment_urls) if self.uploaded_attachment_urls else None),
            }
            # validate dates before saving
            try:
                sd = data.get('start_date')
                ed = data.get('end_date')
                if sd and ed:
                    s_q = QDate.fromString(sd, 'yyyy-MM-dd')
                    e_q = QDate.fromString(ed, 'yyyy-MM-dd')
                    if s_q.isValid() and e_q.isValid() and e_q < s_q:
                        QMessageBox.warning(self, 'Invalid Dates', 'End Date is earlier than Start Date. Please correct the dates before saving.')
                        return
            except Exception:
                pass
            try:
                resp = update_employee_history_record(rec.get('id'), data)
                QMessageBox.information(self, 'Saved', 'History record updated')
                try:
                    if self.employee_id:
                        self.history_changed.emit(str(self.employee_id))
                except Exception:
                    pass
                # Merge the updated fields onto the original record to decide on sync
                try:
                    merged = dict(rec)
                    merged.update({k: v for k, v in data.items() if v is not None or k in ('end_date','start_date')})
                    self._maybe_sync_profile_from_history(merged)
                except Exception as _sync_e:
                    print(f"DEBUG: history->profile sync (edit) skipped: {_sync_e}")
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to update record: {e}')
            self.load_records()
            # remove the save button after saving to avoid duplicate buttons
            try:
                existing = self.findChild(QPushButton, 'save_edit_btn')
                if existing is not None:
                    # try to remove from the form layout if present
                    try:
                        if hasattr(self, 'history_form_layout') and self.history_form_layout is not None:
                            # iterate rows and remove any row containing the widget
                            for ridx in range(self.history_form_layout.rowCount()-1, -1, -1):
                                try:
                                    label_item = self.history_form_layout.itemAt(ridx, self.history_form_layout.LabelRole)
                                    field_item = self.history_form_layout.itemAt(ridx, self.history_form_layout.FieldRole)
                                except Exception:
                                    label_item = None
                                    field_item = None
                                try:
                                    if (label_item and label_item.widget() is existing) or (field_item and field_item.widget() is existing):
                                        try:
                                            self.history_form_layout.removeRow(ridx)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    try:
                        existing.setParent(None)
                        existing.deleteLater()
                    except Exception:
                        pass
            except Exception:
                pass
        save_btn = QPushButton('Save Edit')
        save_btn.setObjectName('save_edit_btn')
        save_btn.clicked.connect(save_edit)
        # Cancel button restores previous employee context and removes buttons
        cancel_btn = QPushButton('Cancel')
        cancel_btn.setObjectName('cancel_edit_btn')
        def cancel_edit():
            # restore previous employee context
            try:
                if prev_employee is not None:
                    self.set_employee(prev_employee)
                else:
                    self.set_employee(prev_employee_id)
            except Exception:
                pass
            # remove save and cancel buttons from layout
            try:
                for name in ('save_edit_btn', 'cancel_edit_btn'):
                    existing = self.findChild(QPushButton, name)
                    if existing is not None:
                        try:
                            if hasattr(self, 'history_form_layout') and self.history_form_layout is not None:
                                for ridx in range(self.history_form_layout.rowCount()-1, -1, -1):
                                    try:
                                        label_item = self.history_form_layout.itemAt(ridx, self.history_form_layout.LabelRole)
                                        field_item = self.history_form_layout.itemAt(ridx, self.history_form_layout.FieldRole)
                                    except Exception:
                                        label_item = None
                                        field_item = None
                                    try:
                                        if (label_item and label_item.widget() is existing) or (field_item and field_item.widget() is existing):
                                            try:
                                                self.history_form_layout.removeRow(ridx)
                                            except Exception:
                                                pass
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        try:
                            existing.setParent(None)
                            existing.deleteLater()
                        except Exception:
                            pass
            except Exception:
                pass
        cancel_btn.clicked.connect(cancel_edit)
        try:
            # Remove any existing save button first to avoid duplicates
            existing = self.findChild(QPushButton, 'save_edit_btn')
            if existing is not None:
                try:
                    if hasattr(self, 'history_form_layout') and self.history_form_layout is not None:
                        for ridx in range(self.history_form_layout.rowCount()-1, -1, -1):
                            try:
                                label_item = self.history_form_layout.itemAt(ridx, self.history_form_layout.LabelRole)
                                field_item = self.history_form_layout.itemAt(ridx, self.history_form_layout.FieldRole)
                            except Exception:
                                label_item = None
                                field_item = None
                            try:
                                if (label_item and label_item.widget() is existing) or (field_item and field_item.widget() is existing):
                                    try:
                                        self.history_form_layout.removeRow(ridx)
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                except Exception:
                    pass
                try:
                    existing.setParent(None)
                    existing.deleteLater()
                except Exception:
                    pass

            # Add the save button to the history form layout (kept in self.history_form_layout)
            if hasattr(self, 'history_form_layout') and self.history_form_layout is not None:
                # add Save and Cancel side-by-side
                h = QHBoxLayout()
                h.addWidget(save_btn)
                h.addWidget(cancel_btn)
                self.history_form_layout.addRow(h)
            else:
                # fallback: add to top-level tabs area if available
                try:
                    self.tabs.widget(0).layout().itemAt(0).layout().addWidget(save_btn)
                except Exception:
                    # last resort: add to main layout
                    try:
                        self.layout().addWidget(save_btn)
                    except Exception:
                        pass
        except Exception:
            pass

    def delete_record(self, rec):
        ok = QMessageBox.question(self, 'Confirm Delete', 'Delete this history record?', QMessageBox.Yes | QMessageBox.No)
        if ok == QMessageBox.Yes:
            try:
                resp = delete_employee_history_record(rec.get('id'))
                QMessageBox.information(self, 'Deleted', 'History record deleted')
                try:
                    if self.employee_id:
                        self.history_changed.emit(str(self.employee_id))
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.warning(self, 'Error', f'Failed to delete record: {e}')
            self.load_records()


    def toggle_sort_order(self):
        """Toggle sort order button text and reload records."""
        try:
            if getattr(self, '_sort_desc', False):
                self._sort_desc = False
                self.sort_order_btn.setText('↑')
            else:
                self._sort_desc = True
                self.sort_order_btn.setText('↓')
        except Exception:
            self._sort_desc = getattr(self, '_sort_desc', False)
        try:
            self.load_records()
        except Exception:
            pass

    def apply_filters_and_sort(self, rows):
        """Filter and sort the provided rows list according to the UI controls.

        Supports text search (job title, notes, employee name), status filter,
        department filter and sorting by chosen column.
        """
        if not rows:
            return rows
        out = list(rows)
        # text search
        try:
            q = (self.search_input.text() or '').strip().lower()
            if q:
                filtered = []
                for r in out:
                    hay = ' '.join([str(r.get(k) or '') for k in ('job_title', 'position', 'department', 'notes', 'employee_name', 'full_name')]).lower()
                    if q in hay:
                        filtered.append(r)
                out = filtered
        except Exception:
            pass

        # status filter
        try:
            status_txt = self.filter_status_combo.currentText() if self.filter_status_combo.currentIndex() >= 0 else 'All Statuses'
            if status_txt and status_txt != 'All Statuses':
                out = [r for r in out if (r.get('status') or r.get('work_status') or '').lower() == status_txt.lower()]
        except Exception:
            pass

        # department filter
        try:
            dept_txt = self.filter_dept_combo.currentText() if self.filter_dept_combo.currentIndex() >= 0 else 'All Departments'
            if dept_txt and dept_txt != 'All Departments':
                out = [r for r in out if (r.get('department') or '').lower() == dept_txt.lower()]
        except Exception:
            pass

        # sorting
        try:
            idx = self.sort_combo.currentIndex()
            key = None
            if idx == 0:
                key = 'start_date'
            elif idx == 1:
                key = 'end_date'
            elif idx == 2:
                key = 'job_title'
            elif idx == 3:
                key = 'department'
            if key:
                def sort_key(r):
                    v = r.get(key)
                    if v is None:
                        return ''
                    return v
                out.sort(key=sort_key, reverse=getattr(self, '_sort_desc', False))
        except Exception:
            pass

        return out

    def auto_fix_invalid_rows(self):
        """Scan employee_history rows for invalid intervals (end < start) and offer to auto-fix by swapping dates."""
        try:
            rows = fetch_employee_history_records(self.employee_id, None) or []
            for r in rows:
                try:
                    s = r.get('start_date')
                    e = r.get('end_date')
                    if s and e:
                        s_q = QDate.fromString(s, 'yyyy-MM-dd')
                        e_q = QDate.fromString(e, 'yyyy-MM-dd')
                        if s_q.isValid() and e_q.isValid() and e_q < s_q:
                            # Ask user to confirm swap
                            msg = QMessageBox()
                            msg.setWindowTitle('Auto-fix interval?')
                            msg.setText(f"Found invalid interval for record starting {s} ending {e}.\nSwap dates to {e} (start) / {s} (end)?")
                            swap_btn = msg.addButton('Swap Dates', QMessageBox.AcceptRole)
                            skip_btn = msg.addButton('Skip', QMessageBox.RejectRole)
                            cancel_btn = msg.addButton(QMessageBox.Cancel)
                            msg.exec_()
                            if msg.clickedButton() == swap_btn:
                                # perform swap
                                try:
                                    data = dict(r)
                                    data['start_date'] = e
                                    data['end_date'] = s
                                    # remove db-only keys
                                    for k in ('id', 'created_at', 'updated_at'):
                                        data.pop(k, None)
                                    update_employee_history_record(r.get('id'), data)
                                except Exception as ex:
                                    QMessageBox.warning(self, 'Auto-fix failed', f'Failed to auto-fix record {r.get("id")}: {ex}')
                            elif msg.clickedButton() == cancel_btn:
                                return
                            else:
                                # skip to next
                                continue
                except Exception:
                    pass
            QMessageBox.information(self, 'Auto-Fix complete', 'Auto-fix scan complete. Invalid rows were updated where you chose to swap dates.')
            try:
                self.load_records()
            except Exception:
                pass
        except Exception as e:
            QMessageBox.warning(self, 'Auto-Fix error', f'Error during auto-fix: {e}')

    # Employment Status subtab removed; status updates are handled via profile dialog save hooks and history snapshots.

    def _maybe_sync_profile_from_history(self, record: dict):
        """Best-effort: If a history record represents the current snapshot, sync key employment
        fields back to employees table and employee_status so the profile dialog reflects changes
        made here.

        Rules:
        - If end_date is None (ongoing record), treat as current and sync job_title, position,
          department, functional_group, employment_type, status, work_status, payroll_status.
        - If end_date is set but status is Resigned/Terminated, still sync status/work/payroll.
        - Avoid overwriting employees with empty strings; only send non-empty values.
        """
        try:
            if not self.employee_id:
                return
            end_date = record.get('end_date')
            status_txt = (record.get('status') or '').strip().lower()
            is_current = end_date in (None, '', 'None')
            # Unconditional sync requested: proceed regardless of end_date/status

            # Build payload of non-empty updates
            def _nz(v):
                if v is None:
                    return None
                if isinstance(v, str):
                    v2 = v.strip()
                    return v2 if v2 else None
                return v
            upd = {}
            for k_src, k_emp in (
                ('job_title', 'job_title'),
                ('position', 'position'),
                ('department', 'department'),
                ('functional_group', 'functional_group'),
                ('employment_type', 'employment_type'),
                ('status', 'status'),
                ('work_status', 'work_status'),
                ('payroll_status', 'payroll_status'),
            ):
                val = _nz(record.get(k_src))
                if val is not None:
                    upd[k_emp] = val
            # If this is the current snapshot, map start_date -> employees.date_joined when present
            if is_current:
                sd = _nz(record.get('start_date'))
                if sd is not None:
                    upd['date_joined'] = sd
            if not upd:
                return

            # Resolve canonical employees.id (UUID) before updating employees table
            emp_uuid = None
            try:
                # Prefer from current employee dict if available
                if isinstance(self.employee, dict):
                    emp_uuid = self.employee.get('id') or None
            except Exception:
                emp_uuid = None
            try:
                from services.supabase_service import supabase
                if not emp_uuid:
                    # If self.employee_id is a UUID-like id, try match by id; otherwise try by business employee_id
                    eid = self.employee_id
                    if eid:
                        # Try lookup by id first
                        try:
                            r = supabase.table('employees').select('id').eq('id', eid).limit(1).execute()
                            if r and getattr(r, 'data', None):
                                emp_uuid = r.data[0].get('id')
                        except Exception:
                            pass
                        if not emp_uuid:
                            # Try lookup by business employee_id
                            try:
                                r2 = supabase.table('employees').select('id').eq('employee_id', eid).limit(1).execute()
                                if r2 and getattr(r2, 'data', None):
                                    emp_uuid = r2.data[0].get('id')
                            except Exception:
                                pass
            except Exception:
                emp_uuid = emp_uuid or None

            # Update employees table using resolved UUID
            try:
                if emp_uuid:
                    from services.supabase_service import update_employee
                    update_employee(str(emp_uuid), upd)
                else:
                    print("DEBUG: Unable to resolve employee UUID for history->profile sync; skipping employees update")
            except Exception as _eu:
                print(f"DEBUG: employees update from history failed: {_eu}")

            # Upsert employee_status using business employee_id (not the UUID)
            try:
                from services.supabase_employee_history import upsert_employee_status
                # Resolve business employee_id code if not present in self.employee
                biz = None
                try:
                    if isinstance(self.employee, dict):
                        biz = self.employee.get('employee_id') or self.employee.get('employee_code')
                except Exception:
                    biz = None
                if not biz:
                    try:
                        resp = supabase.table('employees').select('employee_id').eq('id', self.employee_id).limit(1).execute()
                        if resp and getattr(resp, 'data', None):
                            biz = resp.data[0].get('employee_id')
                    except Exception:
                        biz = None
                if biz:
                    # Import datetime and KL_TZ locally to avoid top-level deps
                    from datetime import datetime as _dt
                    from services.supabase_service import KL_TZ as _KL
                    upsert_employee_status(biz, {
                        'department': upd.get('department'),
                        'status': upd.get('status'),
                        'work_status': upd.get('work_status'),
                        'payroll_status': upd.get('payroll_status'),
                        'position': upd.get('position'),
                        'job_title': upd.get('job_title'),
                        'functional_group': upd.get('functional_group'),
                        'employment_type': upd.get('employment_type'),
                        'last_changed_by': '',
                        'last_changed_at': _dt.now(_KL).isoformat(),
                    })
            except Exception as _se:
                print(f"DEBUG: employee_status upsert from history failed: {_se}")
        except Exception:
            pass
