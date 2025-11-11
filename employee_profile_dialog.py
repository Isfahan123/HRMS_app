import email
from PyQt5.QtWidgets import (
    QDialog, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout,
    QMessageBox, QComboBox, QDateEdit, QHBoxLayout, QGroupBox,
    QScrollArea, QGridLayout, QFileDialog, QTextEdit, QCheckBox, QDoubleSpinBox
)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtCore import QDate, Qt, QByteArray
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QTextDocument, QFont, QColor
from datetime import datetime, date
from services.supabase_service import add_employee_with_login, update_employee, upload_profile_picture, supabase, KL_TZ, convert_utc_to_kl
from gui.job_title_mapping_loader import load_job_title_mapping
from services.org_structure_service import (
    list_departments,
    list_position_hierarchy,
    list_job_title_groups,
    get_titles_for_group,
    get_department_units,
)
from gui.payroll_dialog import PayrollInformationDialog
import re
import os
import uuid
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
import pytz

class EmployeeProfileDialog(QDialog):
    # signal emitted when an employee is added or updated; payload is employee id (str)
    employee_saved = pyqtSignal(str)
    def __init__(self, employee_data=None, user_email=None, parent=None, is_admin=False):
        super().__init__(parent)
        self.employee_data = employee_data
        self.user_email = user_email or (employee_data.get("email") if employee_data else None)
        self.profile_pic_path = None
        self.resume_path = None
        self.is_admin = is_admin
        self.setWindowTitle("Edit Employee" if employee_data else "Add Employee")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        # Main vertical layout for the dialog
        main_layout = QVBoxLayout()

        # Scrollable content area so the dialog is usable on small screens
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)

        # Content widget inside the scroll area and its layout
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)

        # Build all sections into self.content_layout
        self.create_sections()
        self.create_buttons()

        # Wire up scroll area and main layout
        self.scroll_area.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll_area)
        self.setLayout(main_layout)

        # If editing an existing employee, populate form
        if self.employee_data:
            self.populate_form(self.employee_data)

    def create_sections(self):
        # fields dictionary holds references to widgets used across the dialog
        self.fields = {}

        # --- Picture Section ---
        picture_layout = QHBoxLayout()
        self.picture_label = QLabel()
        self.picture_label.resize(120, 120)
        self.picture_label.setStyleSheet("border: 2px solid #ddd; border-radius: 60px;")
        self.picture_label.setAlignment(Qt.AlignCenter)
        self.default_avatar_path = os.path.join(os.path.dirname(__file__), "..", "assets", "default_avatar.png")
        self.load_default_picture()

        picture_buttons_layout = QVBoxLayout()
        upload_pic_btn = QPushButton("Upload Picture")
        upload_pic_btn.clicked.connect(self.upload_picture)
        picture_buttons_layout.addWidget(upload_pic_btn)

        # Resume upload
        resume_group = QGroupBox("Resume")
        resume_layout = QVBoxLayout()
        self.resume_label = QLabel("No file selected")
        upload_resume_btn = QPushButton("Upload Resume")
        upload_resume_btn.clicked.connect(self.upload_resume)
        resume_layout.addWidget(self.resume_label)
        resume_layout.addWidget(upload_resume_btn)
        resume_group.setLayout(resume_layout)
        picture_buttons_layout.addWidget(resume_group)

        picture_layout.addWidget(self.picture_label)
        picture_layout.addLayout(picture_buttons_layout)
        self.content_layout.addLayout(picture_layout)

        # --- Main Content in Horizontal Layout ---
        main_content_layout = QHBoxLayout()

        # Left column layout
        left_layout = QVBoxLayout()

        # --- Personal Info Section ---
        personal_groupbox = QGroupBox("Personal Information")
        personal_form = QFormLayout()
        personal_groupbox.setLayout(personal_form)

        # Define personal fields and widgets
        personal_fields = [
            ("Full Name", QLineEdit(self)),
            ("Gender", self.combo(["Male", "Female", "Other"], parent=self)),
            ("Date of Birth", self.date_edit(parent=self)),
            ("Age", QLabel("Age: -", self)),
            ("NRIC", QLineEdit(self)),
            ("Nationality", QLineEdit(self)),
            ("Citizenship", self.combo(["Citizen", "Non-citizen", "Permanent Resident"], parent=self)),
            ("Race", QLineEdit(self)),
            ("Religion", QLineEdit(self)),
            ("Marital Status", self.combo(["Single", "Married", "Divorced", "Widowed"], parent=self)),
            ("Number of Children", self.combo([str(i) for i in range(0, 11)], parent=self)),  # 0-10 children
            ("Spouse Working", self.combo(["Yes", "No"], parent=self))
        ]

        for label, widget in personal_fields:
            personal_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget

        # Connect signals for EPF/SOCSO auto-calculation
        def update_epf_socso_status_wrapper():
            self.update_epf_socso_status()

        # Connect after the personal fields are created
        if "Nationality" in self.fields:
            try:
                self.fields["Nationality"].textChanged.connect(update_epf_socso_status_wrapper)
            except Exception:
                pass
        if "Citizenship" in self.fields:
            try:
                self.fields["Citizenship"].currentTextChanged.connect(update_epf_socso_status_wrapper)
            except Exception:
                pass
        if "Date of Birth" in self.fields:
            try:
                self.fields["Date of Birth"].dateChanged.connect(update_epf_socso_status_wrapper)
            except Exception:
                pass

        # Add EPF/SOCSO Status Section
        epf_socso_label = QLabel("EPF/SOCSO Information:")
        epf_socso_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        personal_form.addRow(epf_socso_label)

        # EPF Status Display (simplified)
        self.fields["EPF Status"] = QLineEdit(self)
        self.fields["EPF Status"].setReadOnly(True)
        self.fields["EPF Status"].setStyleSheet("background-color: #ecf0f1; color: #2c3e50;")
        personal_form.addRow("EPF Status:", self.fields["EPF Status"])

        # EPF Part Selection for Non-Citizens (simplified)
        self.epf_part_widget = QWidget(self)
        epf_part_layout = QVBoxLayout(self.epf_part_widget)
        epf_part_layout.setContentsMargins(0, 0, 0, 0)

        # Add explanation label
        epf_explanation = QLabel("For Non-Citizens: Select EPF Part", self.epf_part_widget)
        epf_explanation.setStyleSheet("font-style: italic; color: #7f8c8d; font-size: 11px;")
        epf_part_layout.addWidget(epf_explanation)

        # Create dropdown for EPF part selection (all 5 official parts)
        self.epf_part_combo = self.combo(["None", "Part A", "Part B", "Part C", "Part D", "Part E"], parent=self)
        self.fields["EPF Part"] = self.epf_part_combo
        epf_part_layout.addWidget(self.epf_part_combo)

        # Initially hide the EPF part selection (will show for non-citizens)
        self.epf_part_widget.hide()
        personal_form.addRow("EPF Election:", self.epf_part_widget)

        # Connect signal for EPF part changes
        try:
            self.epf_part_combo.currentTextChanged.connect(lambda text: self.update_epf_socso_status())
        except Exception:
            pass

        # SOCSO Status Display (simplified)
        self.fields["SOCSO Status"] = QLineEdit(self)
        self.fields["SOCSO Status"].setReadOnly(True)
        self.fields["SOCSO Status"].setStyleSheet("background-color: #ecf0f1; color: #2c3e50;")
        personal_form.addRow("SOCSO Status:", self.fields["SOCSO Status"])

        left_layout.addWidget(personal_groupbox)

        # --- Show/hide logic for citizenship ---
        def nationality_changed():
            try:
                nat = self.fields["Nationality"].text().strip().lower()
                citizenship_combo = self.fields["Citizenship"]
                if nat in ("malaysia", "malaysian"):
                    citizenship_combo.setCurrentText("Citizen")
                    citizenship_combo.setEnabled(False)
                else:
                    citizenship_combo.setEnabled(True)
            except Exception:
                pass

        # Connect signals
        try:
            self.fields["Nationality"].textChanged.connect(nationality_changed)
        except Exception:
            pass

        # --- Contact Info Section ---
        contact_groupbox = QGroupBox("Contact Information")
        contact_form = QFormLayout()
        contact_groupbox.setLayout(contact_form)

        contact_fields = [
            ("Email", QLineEdit(self)),
            ("Username", QLineEdit(self)),
            ("Phone", QLineEdit(self)),
            ("Address", QLineEdit(self)),
            ("City", QLineEdit(self)),
            ("State", QLineEdit(self)),
            ("Zipcode", QLineEdit(self))
        ]

        for label, widget in contact_fields:
            contact_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget

        left_layout.addWidget(contact_groupbox)

        # Right column layout
        right_layout = QVBoxLayout()

        # --- Employment Info Section ---
        employment_groupbox = QGroupBox("Employment Information")
        self.employment_groupbox = employment_groupbox
        employment_form = QFormLayout()
        employment_groupbox.setLayout(employment_form)

        # Use centralized mapping and org structure service to populate Job Title / Position / Department defaults
        mapping = load_job_title_mapping()
        # job title defaults: prefer job_title_mapping keys, else fall back to org structure job titles
        if mapping:
            job_title_defaults = sorted(list(mapping.keys()))
        else:
            # try to load from org structure groups
            try:
                groups = list_job_title_groups()
                titles = []
                for g in groups:
                    titles.extend(get_titles_for_group(g) or [])
                job_title_defaults = sorted(list(dict.fromkeys([t for t in titles if t]))) or ["Other"]
            except Exception:
                job_title_defaults = ["Software Engineer", "Senior Software Engineer", "Product Manager", "Accountant", "Other"]
        self.job_title_combo = self.combo(job_title_defaults, parent=employment_groupbox)
        self.job_title_combo.setEditable(True)

        # Position dropdown (seniority/level) to complement Job Title — prefer org position hierarchy if available
        try:
            pos_hierarchy = list_position_hierarchy()
            position_defaults = pos_hierarchy or [
                "Junior", "Mid-level", "Senior", "Lead", "Manager", "Senior Manager",
                "Director", "Senior Director", "VP", "Senior VP", "C-Level", "Intern",
                "Contractor", "Consultant", "Other"
            ]
        except Exception:
            position_defaults = [
                "Junior", "Mid-level", "Senior", "Lead", "Manager", "Senior Manager",
                "Director", "Senior Director", "VP", "Senior VP", "C-Level", "Intern",
                "Contractor", "Consultant", "Other"
            ]
        self.position_combo = self.combo(position_defaults, parent=employment_groupbox)
        self.position_combo.setEditable(True)

        # Try to populate position choices from employees table (non-fatal)
        try:
            resp = supabase.table('employees').select('position').execute()
            if resp and getattr(resp, 'data', None):
                rows = resp.data
                positions = []
                for r in rows:
                    p = (r.get('position') or '').strip()
                    if p:
                        positions.append(p)

                def _uniq_sort(seq):
                    return sorted(list(dict.fromkeys([s for s in seq if s])))

                positions = _uniq_sort(positions)
                # merge DB positions with existing defaults while preserving order
                existing = [self.position_combo.itemText(i) for i in range(self.position_combo.count())]
                merged = _uniq_sort(positions + existing)

                cur = ''
                try:
                    cur = self.position_combo.currentText() or ''
                except Exception:
                    cur = ''
                self.position_combo.blockSignals(True)
                self.position_combo.clear()
                self.position_combo.addItems(merged or (existing or ["Other"]))
                if cur:
                    idx = self.position_combo.findText(cur)
                    if idx >= 0:
                        self.position_combo.setCurrentIndex(idx)
                    else:
                        self.position_combo.setEditText(cur)
                self.position_combo.blockSignals(False)
        except Exception as e:
            print(f"DEBUG: Failed loading position choices in profile dialog: {e}")

        # Derive department defaults: prefer org_structure_service list, else mapping-derived, else fallback
        try:
            dept_list = list_departments()
            department_defaults = dept_list or ["Other"]
        except Exception:
            if mapping:
                dept_set = sorted(list({v.get('department') for v in mapping.values() if v.get('department')}))
                department_defaults = dept_set or ["Other"]
            else:
                department_defaults = [
                    "Engineering", "Product", "Design", "Research", "Data", "IT", "Security",
                    "Human Resources", "HR", "Finance", "Accounting", "Legal", "Compliance",
                    "Sales", "Business Development", "Marketing", "Customer Success", "Support",
                    "Operations", "Supply Chain", "Procurement", "Facilities", "Quality", "Admin",
                    "Executive", "Strategy", "Growth", "Other"
                ]
        self.department_combo = self.combo(department_defaults, parent=employment_groupbox)
        self.department_combo.setEditable(True)

        # Functional Group combo (populated based on Department selection using template)
        self.func_group_combo = self.combo([], parent=employment_groupbox)
        self.func_group_combo.setEditable(True)

        # helper to load department -> functional groups template
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

        dept_template = _load_dept_template()

        def _populate_functional_groups(dept_text):
            # preserve current text
            cur = ''
            try:
                cur = self.func_group_combo.currentText() or ''
            except Exception:
                cur = ''
            self.func_group_combo.blockSignals(True)
            self.func_group_combo.clear()
            groups = []
            try:
                if dept_template and dept_text in dept_template:
                    groups = sorted(list(dept_template.get(dept_text, {}).keys()))
                else:
                    # try org_structure_service department units
                    try:
                        groups = get_department_units(dept_text) or []
                    except Exception:
                        # fallback: infer groups from job_title_mapping by department field
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
            # Helpers for position heuristics
            def _normalize(s: str) -> str:
                try:
                    return (s or '').strip().lower()
                except Exception:
                    return ''

            def _normalize_dept(s: str) -> str:
                d = _normalize(s)
                # simple aliases to improve matching across data sources
                aliases = {
                    'hr': 'human resources',
                    'people': 'human resources',
                    'it': 'information technology',
                    'customer service': 'customer success',
                }
                return aliases.get(d, d)

            def _is_c_level_title(title: str) -> bool:
                t = _normalize(title)
                # Chief X Officer or acronym like CEO/CTO/CFO/COO/CHRO/CIO/CMO/CPO/CRO
                if 'chief ' in t and ' officer' in t:
                    return True
                import re
                return bool(re.search(r"\bC[A-Z]{2}O\b", (title or '')))

            def _c_level_titles_for_dept(dept: str) -> list:
                d = _normalize(dept)
                mapping = {
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
                # choose by best key match (simple contains)
                for k, vals in mapping.items():
                    if k in d:
                        return vals
                # default generic C-level titles
                return ['Chief Executive Officer', 'CEO']

            # build candidate job titles from template first, else mapping
            candidates = []
            try:
                if dept_template and dept_text in dept_template:
                    # if group specified, use that group's job_titles; else collect all in dept
                    if group_text and group_text in dept_template.get(dept_text, {}):
                        candidates = dept_template[dept_text][group_text].get('job_titles', [])
                    else:
                        # gather all job_titles across all groups
                        for g, info in dept_template.get(dept_text, {}).items():
                            candidates.extend(info.get('job_titles', []) or [])
                else:
                    # fallback to mapping keys that match department (case-insensitive, with aliases)
                    dept_norm = _normalize_dept(dept_text)
                    for jt, meta in mapping.items():
                        meta_dept_norm = _normalize_dept(meta.get('department') or '')
                        if meta_dept_norm and (dept_norm in meta_dept_norm or meta_dept_norm in dept_norm):
                            candidates.append(jt)
                # dedupe & sort
                candidates = sorted(list(dict.fromkeys([c for c in candidates if c])))
                base_candidates = list(candidates)  # keep unfiltered base for fallbacks

                # If a position filter is provided, narrow job titles
                if position_text:
                    pos_norm = _normalize(position_text)
                    filtered = []
                    # 1) Prefer explicit mapping match on meta.position
                    for jt in candidates:
                        try:
                            meta = mapping.get(jt, {}) or {}
                            pos_meta = _normalize(meta.get('position', '') or '')
                            if pos_meta:
                                # Strict matching for most positions to avoid bleed-over
                                if pos_meta == pos_norm:
                                    filtered.append(jt)
                        except Exception:
                            continue
                    # 2) Heuristic string match directly on job title text (e.g., contains Director/Manager/Lead/etc.)
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
                        for jt in candidates:
                            t = _normalize(jt)
                            tokens = None
                            # map pos_norm to known token set
                            for key, toks in tokens_by_pos.items():
                                if key in pos_norm:
                                    tokens = toks
                                    break
                            if not tokens:
                                continue
                            # Use word boundaries to avoid accidental matches
                            matched = any(_re.search(r"\\b" + _re.escape(tok.lower()) + r"\\b", t, flags=_re.IGNORECASE) for tok in tokens if tok)
                            # Negative checks to prevent cross-level bleed (e.g., Manager should not match Senior Manager)
                            if matched:
                                if 'senior manager' == pos_norm and not ('senior manager' in t):
                                    matched = False
                                if 'manager' == pos_norm and ('senior manager' in t):
                                    matched = False
                                if 'director' == pos_norm and ('senior director' in t):
                                    matched = False
                                if 'senior' == pos_norm and (('senior manager' in t) or ('senior director' in t)):
                                    matched = False
                            if matched:
                                filtered.append(jt)
                    # 3) Special handling for C-Level: restrict to department-specific C titles
                    if not filtered and 'c-level' in pos_norm:
                        c_titles = _c_level_titles_for_dept(dept_text)
                        # Use intersection if present in candidates, else offer the C-level list directly
                        inter = [jt for jt in candidates if jt in c_titles]
                        filtered = inter if inter else c_titles

                    # Finalize: if we have filtered, use it; otherwise fall back to base candidates
                    if filtered:
                        candidates = sorted(list(dict.fromkeys([c for c in filtered if c])))
                    else:
                        candidates = base_candidates
            except Exception:
                candidates = []

            # merge with existing job title defaults while preserving current text
            try:
                cur_txt = self.job_title_combo.currentText() or ''
            except Exception:
                cur_txt = ''
            self.job_title_combo.blockSignals(True)
            self.job_title_combo.clear()
            if candidates:
                self.job_title_combo.addItems(candidates)
            else:
                # No candidates at all; if a position is selected, fall back to base dept/group list to avoid unrelated titles
                if position_text and dept_text:
                    # Try to rebuild base candidates quickly (without position filtering)
                    base = []
                    try:
                        if dept_template and dept_text in dept_template:
                            for g, info in dept_template.get(dept_text, {}).items():
                                base.extend(info.get('job_titles', []) or [])
                        else:
                            dept_norm = _normalize_dept(dept_text)
                            for jt, meta in mapping.items():
                                meta_dept_norm = _normalize_dept(meta.get('department') or '')
                                if meta_dept_norm and (dept_norm in meta_dept_norm or meta_dept_norm in dept_norm):
                                    base.append(jt)
                        base = sorted(list(dict.fromkeys([b for b in base if b])))
                    except Exception:
                        base = []
                    if base:
                        self.job_title_combo.addItems(base)
                    else:
                        self.job_title_combo.addItems(job_title_defaults)
                else:
                    self.job_title_combo.addItems(job_title_defaults)

            # If current text is not in candidates, clear it to avoid feeling "stuck"
            try:
                cur_txt_after = self.job_title_combo.currentText() or ''
                items_now = [self.job_title_combo.itemText(i) for i in range(self.job_title_combo.count())]
                if cur_txt_after and cur_txt_after not in items_now:
                    # Clear to blank to encourage new selection
                    self.job_title_combo.setEditText('')
            except Exception:
                pass
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

        def _populate_positions(dept_text):
            """Populate positions dropdown based on selected department."""
            # preserve current text and existing items (don't lose defaults)
            try:
                cur = self.position_combo.currentText() or ''
            except Exception:
                cur = ''
            # capture existing items before clearing so we can restore if needed
            existing = [self.position_combo.itemText(i) for i in range(self.position_combo.count())]
            self.position_combo.blockSignals(True)
            self.position_combo.clear()
            positions = []
            try:
                # Try dept_template first: check for positions under each group if present
                if dept_template and dept_text in dept_template:
                    for g, info in dept_template.get(dept_text, {}).items():
                        # common key names might be 'positions' or fall back to 'job_titles'->infer
                        pos_list = info.get('positions') or info.get('roles') or []
                        if pos_list:
                            positions.extend(pos_list)
                # Fallback to mapping: collect 'position' metadata from job title mapping
                if not positions:
                    for jt, meta in mapping.items():
                        try:
                            if meta.get('department') == dept_text and meta.get('position'):
                                positions.append(meta.get('position'))
                        except Exception:
                            continue
                # Last resort: query DB for positions in this department
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

                # dedupe & sort
                positions = sorted(list(dict.fromkeys([p for p in positions if p])))
            except Exception:
                positions = []

            # Merge with existing defaults if no specific positions found
            if positions:
                self.position_combo.addItems(positions)
            else:
                # restore previously-captured existing items if present
                if existing:
                    self.position_combo.addItems(existing)
                else:
                    # fallback to initial position defaults defined earlier
                    try:
                        self.position_combo.addItems(position_defaults)
                    except Exception:
                        pass

            # Ensure the combo is enabled so selection works
            try:
                self.position_combo.setEnabled(True)
            except Exception:
                pass

            # restore previous selection if possible
            if cur:
                try:
                    idx = self.position_combo.findText(cur)
                    if idx >= 0:
                        self.position_combo.setCurrentIndex(idx)
                    else:
                        self.position_combo.setEditText(cur)
                except Exception:
                    pass
            self.position_combo.blockSignals(False)

        # wire department -> populate functional groups and filter job titles
        try:
            def _on_department_changed(txt):
                _populate_functional_groups(txt)
                _filter_job_titles_by_dept_and_group(txt, self.func_group_combo.currentText(), self.position_combo.currentText())
                # also populate position choices based on department
                try:
                    _populate_positions(txt)
                except Exception:
                    pass

            self.department_combo.currentTextChanged.connect(_on_department_changed)
        except Exception:
            pass

        # wire functional group -> filter job titles further
        try:
            def _on_func_group_changed(txt):
                dept = self.department_combo.currentText() or ''
                _filter_job_titles_by_dept_and_group(dept, txt, self.position_combo.currentText())
            self.func_group_combo.currentTextChanged.connect(_on_func_group_changed)
        except Exception:
            pass

        # Wire position change to further filter job titles (e.g., C-Level + Department -> CHRO)
        try:
            def _on_position_changed(txt):
                dept = self.department_combo.currentText() or ''
                _filter_job_titles_by_dept_and_group(dept, self.func_group_combo.currentText(), txt)
            self.position_combo.currentTextChanged.connect(_on_position_changed)
        except Exception:
            pass

        # Create persistent widgets as attributes to ensure Python keeps references
        self.employee_id_edit = QLineEdit(employment_groupbox)
        self.role_combo = self.combo(["employee", "admin"], parent=employment_groupbox)
        # job_title_combo, position_combo, department_combo, func_group_combo already set above
        self.status_combo = self.combo(["Active", "Inactive", "Terminated"], parent=employment_groupbox)
        # Work Status (short-term availability)
        self.work_status_combo = self.combo(["On Duty", "On Leave", "On Sick Leave", "On Unpaid Leave", "On Suspension", "On Business Trip"], parent=employment_groupbox)
        # Payroll Status (finance-related)
        self.payroll_status_combo = self.combo(["Active Payroll", "Inactive Payroll"], parent=employment_groupbox)
        self.employment_type_combo = self.combo(["Full-time", "Part-time", "Contract", "Temporary"], parent=employment_groupbox)
        self.date_joined_edit = self.date_edit(parent=employment_groupbox)

        employment_fields = [
            ("Employee ID", self.employee_id_edit),
            ("Role", self.role_combo),
            ("Job Title", self.job_title_combo),
            ("Position Level", self.position_combo),
            ("Department", self.department_combo),
            ("Functional Group", self.func_group_combo),
            ("Status", self.status_combo),
            ("Work Status", self.work_status_combo),
            ("Payroll Status", self.payroll_status_combo),
            ("Employment Type", self.employment_type_combo),
            ("Date Joined", self.date_joined_edit)
        ]

        for label, widget in employment_fields:
            employment_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget

        # Add a small warning label for job title vs position mismatch (hidden by default)
        try:
            from PyQt5.QtWidgets import QLabel as _QLabel
            self.position_hint_label = _QLabel("")
            self.position_hint_label.setStyleSheet("color:#c0392b; font-size:11px;")
            self.position_hint_label.setWordWrap(True)
            self.position_hint_label.hide()
            employment_form.addRow(_QLabel(""), self.position_hint_label)
        except Exception:
            self.position_hint_label = None

        # Auto-suggest Position Level from Job Title text and warn on mismatch
        def _suggest_position_from_title(title_text: str) -> str:
            try:
                t = (title_text or "").lower()
                # prioritize multi-word senior roles
                if "senior manager" in t:
                    return "Senior Manager"
                if "senior director" in t:
                    return "Senior Director"
                if "vice president" in t or "vp" in t:
                    return "VP"
                if any(k in t for k in ["chief ", " cto", " cfo", " ceo", " cmo", " cio", " cso", " cpo", " cco"]):
                    return "C-Level"
                if "intern" in t:
                    return "Intern"
                if "junior" in t:
                    return "Junior"
                if "mid" in t or "associate" in t:
                    return "Mid-level"
                if "senior" in t:
                    return "Senior"
                if "lead" in t:
                    return "Lead"
                if "manager" in t:
                    return "Manager"
                if "director" in t:
                    return "Director"
                return ""
            except Exception:
                return ""

        def _update_position_warning():
            try:
                jt = self.job_title_combo.currentText()
                pos = self.position_combo.currentText()
                sug = _suggest_position_from_title(jt)
                show = bool(sug and pos and (sug.lower() != (pos or "").strip().lower()))
                if self.position_hint_label:
                    if show:
                        self.position_hint_label.setText(f"Job Title suggests '{sug}' but Position Level is '{pos}'.")
                        self.position_hint_label.show()
                    else:
                        self.position_hint_label.hide()
            except Exception:
                pass

        def _on_job_title_changed(txt):
            try:
                sug = _suggest_position_from_title(txt)
                if sug:
                    cur = self.position_combo.currentText() or ""
                    # Set if empty or clearly different from suggestion
                    if not cur or cur.strip().lower() != sug.lower():
                        idx = self.position_combo.findText(sug)
                        if idx >= 0:
                            self.position_combo.setCurrentIndex(idx)
                        else:
                            try:
                                self.position_combo.setEditText(sug)
                            except Exception:
                                pass
                _update_position_warning()
            except Exception:
                pass

        try:
            self.job_title_combo.currentTextChanged.connect(_on_job_title_changed)
            self.position_combo.currentTextChanged.connect(lambda _t: _update_position_warning())
        except Exception:
            pass

        # Add employment groupbox to right column
        right_layout.addWidget(employment_groupbox)

        # --- Education Info Section ---
        education_groupbox = QGroupBox("Education Information")
        education_layout = QVBoxLayout()
        education_groupbox.setLayout(education_layout)

        # --- Primary Education ---
        primary_group = QGroupBox("Primary Education")
        primary_form = QFormLayout()
        primary_group.setLayout(primary_form)

        self.fields["Primary School Name"] = QLineEdit(self)
        self.fields["Primary Location"] = QLineEdit(self)
        self.fields["Primary Year Started"] = QLineEdit(self)
        self.fields["Primary Year Completed"] = QLineEdit(self)
        # Primary types expanded to include Religious
        self.fields["Primary Type"] = self.combo(["National", "Vernacular", "Religious", "Private", "International", "Other"], parent=primary_group)

        primary_form.addRow(QLabel("School Name:"), self.fields["Primary School Name"])
        primary_form.addRow(QLabel("Location:"), self.fields["Primary Location"])
        primary_form.addRow(QLabel("Year Started:"), self.fields["Primary Year Started"])
        primary_form.addRow(QLabel("Year Completed:"), self.fields["Primary Year Completed"])
        primary_form.addRow(QLabel("Type (e.g. National, Private):"), self.fields["Primary Type"])

        # --- Secondary Education ---
        secondary_group = QGroupBox("Secondary Education")
        secondary_form = QFormLayout()
        secondary_group.setLayout(secondary_form)

        self.fields["Secondary School Name"] = QLineEdit(self)
        self.fields["Secondary Location"] = QLineEdit(self)
        self.fields["Secondary Year Started"] = QLineEdit(self)
        self.fields["Secondary Year Completed"] = QLineEdit(self)
        self.fields["Secondary Qualification"] = QLineEdit(self)
        # Secondary school types per requested mapping
        self.fields["Secondary Type"] = self.combo([
            "National", "Vernacular", "Religious", "Elite/Boarding", "Technical/Vocational",
            "Specialized", "Private", "International", "Other"
        ], parent=secondary_group)
        self.fields["Secondary Stream"] = self.combo(["Science", "Arts", "Technical", "Vocational", "Other"], parent=secondary_group)
        self.fields["Secondary Grades"] = QLineEdit(self)

        secondary_form.addRow(QLabel("School Name:"), self.fields["Secondary School Name"])
        secondary_form.addRow(QLabel("Location:"), self.fields["Secondary Location"])
        secondary_form.addRow(QLabel("Year Started:"), self.fields["Secondary Year Started"])
        secondary_form.addRow(QLabel("Year Completed:"), self.fields["Secondary Year Completed"])
        secondary_form.addRow(QLabel("Qualification Obtained:"), self.fields["Secondary Qualification"])
        secondary_form.addRow(QLabel("Type (e.g. National, Private):"), self.fields["Secondary Type"])
        secondary_form.addRow(QLabel("Stream:"), self.fields["Secondary Stream"])
        secondary_form.addRow(QLabel("Grades / Results (optional):"), self.fields["Secondary Grades"])

        # --- Tertiary Education ---
        tertiary_group = QGroupBox("Tertiary Education")
        tertiary_form = QFormLayout()
        tertiary_group.setLayout(tertiary_form)

        self.fields["Tertiary Institution Name"] = QLineEdit(self)
        self.fields["Tertiary Location"] = QLineEdit(self)
        self.fields["Tertiary Level"] = self.combo(["Certificate", "Diploma", "Bachelor", "Master", "PhD", "Other"], parent=tertiary_group)
        # Tertiary institution types per requested mapping
        self.fields["Tertiary Institution Type"] = self.combo([
            "National (Public)", "Private", "Polytechnic", "Community College", "TVET", "International Branch", "Other"
        ], parent=tertiary_group)
        self.fields["Tertiary Field"] = QLineEdit(self)
        self.fields["Tertiary Major"] = QLineEdit(self)
        self.fields["Tertiary Year Started"] = QLineEdit(self)
        self.fields["Tertiary Year Completed"] = QLineEdit(self)
        self.fields["Tertiary Status"] = self.combo(["Completed", "Ongoing", "Dropped"], parent=tertiary_group)
        self.fields["Tertiary CGPA"] = QLineEdit(self)

        tertiary_form.addRow(QLabel("Institution Name:"), self.fields["Tertiary Institution Name"])
        tertiary_form.addRow(QLabel("Location:"), self.fields["Tertiary Location"])
        tertiary_form.addRow(QLabel("Level of Qualification:"), self.fields["Tertiary Level"])
        tertiary_form.addRow(QLabel("Institution Type:"), self.fields["Tertiary Institution Type"])
        tertiary_form.addRow(QLabel("Field of Study:"), self.fields["Tertiary Field"])
        tertiary_form.addRow(QLabel("Major / Minor:"), self.fields["Tertiary Major"])
        tertiary_form.addRow(QLabel("Year Started:"), self.fields["Tertiary Year Started"])
        tertiary_form.addRow(QLabel("Year Completed:"), self.fields["Tertiary Year Completed"])
        tertiary_form.addRow(QLabel("Status (Completed/Ongoing/Dropped):"), self.fields["Tertiary Status"])
        tertiary_form.addRow(QLabel("CGPA / Final Result (optional):"), self.fields["Tertiary CGPA"])

        # assemble
        education_layout.addWidget(primary_group)
        education_layout.addWidget(secondary_group)
        education_layout.addWidget(tertiary_group)

        right_layout.addWidget(education_groupbox)

        # --- Emergency Contact Section ---
        emergency_groupbox = QGroupBox("Emergency Contact")
        emergency_form = QFormLayout()
        emergency_groupbox.setLayout(emergency_form)

        emergency_fields = [
            ("Contact Name", QLineEdit(self)),
            ("Relation", QLineEdit(self)),
            ("Emergency Phone", QLineEdit(self))
        ]

        for label, widget in emergency_fields:
            emergency_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget

        right_layout.addWidget(emergency_groupbox)

        # --- Salary History Section (Admin Only) ---
        if self.is_admin and self.employee_data:
            salary_history_groupbox = QGroupBox("Recent Salary History")
            salary_history_layout = QVBoxLayout()
            salary_history_groupbox.setLayout(salary_history_layout)
            
            # Current salary display
            current_salary_layout = QHBoxLayout()
            current_salary_layout.addWidget(QLabel("Current Salary:"))
            self.current_salary_display = QLabel("Loading...", self)
            self.current_salary_display.setStyleSheet("font-weight: bold; color: #2e7d32; font-size: 14px;")
            current_salary_layout.addWidget(self.current_salary_display)
            current_salary_layout.addStretch()
            salary_history_layout.addLayout(current_salary_layout)
            
            # Recent changes label
            self.salary_changes_label = QLabel("Loading salary history...", self)
            self.salary_changes_label.setStyleSheet("color: #666; font-size: 12px;")
            salary_history_layout.addWidget(self.salary_changes_label)
            
            # View full history button
            view_history_btn = QPushButton("View Full Salary History")
            view_history_btn.clicked.connect(self.open_salary_history)
            view_history_btn.setStyleSheet("background-color: #1976d2; color: white; padding: 5px;")
            salary_history_layout.addWidget(view_history_btn)
            
            right_layout.addWidget(salary_history_groupbox)
            
            # Load salary history data
            self.load_salary_history_summary()

        # Add left and right columns to main content layout
        main_content_layout.addLayout(left_layout)
        main_content_layout.addLayout(right_layout)
        
        # Add main content to the overall layout
        self.content_layout.addLayout(main_content_layout)

        # Diagnostic: print employment widget identities and parents
        try:
            for key in ["Employee ID", "Role", "Job Title", "Position Level", "Department", "Functional Group", "Status", "Employment Type", "Date Joined"]:
                w = self.fields.get(key)
                try:
                    p = w.parent()
                except Exception:
                    p = None
                print(f"DIAG: field {key!r} id={id(w) if w is not None else None} parent={p}")
        except Exception:
            pass

        # Add auto-calculation for age based on date of birth
        def calculate_age():
            try:
                dob = self.fields["Date of Birth"].date().toPyDate()
                today = datetime.now(KL_TZ).date()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                self.fields["Age"].setText(f"Age: {age}")
            except Exception:
                pass

        # Connect age calculation
        try:
            self.fields["Date of Birth"].dateChanged.connect(calculate_age)
        except Exception:
            pass
        # Note: job title -> position/department autofill is handled via
        # the `self.job_title_combo.currentTextChanged.connect(self.autofill_job_title)` wiring
        # earlier. The previous inline attempt to access a mapping with an
        # undefined variable was removed because it could raise at runtime.

    def load_default_picture(self):
        """Load default profile picture"""
        try:
            if os.path.exists(self.default_avatar_path):
                pixmap = QPixmap(self.default_avatar_path)
            else:
                print(f"DEBUG: Default avatar not found at {self.default_avatar_path}")
                pixmap = self.create_placeholder_image()

            # Create circular crop
            path = QPainterPath()
            path.addEllipse(0, 0, 118, 118)
            clipped_pixmap = QPixmap(120, 120)
            clipped_pixmap.fill(Qt.transparent)
            painter = QPainter(clipped_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setClipPath(path)
            painter.setClipping(True)
            painter.drawPixmap(0, 0, pixmap.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            painter.end()
            self.picture_label.setPixmap(clipped_pixmap)
            print(f"DEBUG: Loaded default picture from {self.default_avatar_path}")
        except Exception as e:
            print(f"DEBUG: Error loading default picture: {str(e)}")
            pixmap = self.create_placeholder_image()
            self.picture_label.setPixmap(pixmap)

    def create_placeholder_image(self):
        pixmap = QPixmap(120, 120)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#888888"))
        painter.drawEllipse(0, 0, 118, 118)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 40))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "👤")
        painter.end()
        print("DEBUG: Created placeholder image")
        return pixmap

    def upload_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg)")
        if file_path:
            try:
                pixmap = QPixmap(file_path)
                if pixmap.isNull():
                    QMessageBox.warning(self, "Error", "Invalid image file.")
                    return
                path = QPainterPath()
                path.addEllipse(0, 0, 118, 118)
                scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                clipped_pixmap = QPixmap(120, 120)
                clipped_pixmap.fill(Qt.transparent)
                painter = QPainter(clipped_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setClipPath(path)
                painter.setClipping(True)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.picture_label.setPixmap(clipped_pixmap)
                self.profile_pic_path = file_path
                print(f"DEBUG: Profile picture selected: {file_path}")
            except Exception as e:
                print(f"DEBUG: Error uploading picture: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to upload picture: {str(e)}")
    
    def upload_resume(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Resume", "", "PDF Files (*.pdf)")
        if file_path:
            self.resume_path = file_path
            self.resume_label.setText(os.path.basename(file_path))

    # EPF/SOCSO methods removed - now using dedicated database columns for simplicity

    def combo(self, items, parent=None):
        # create combo with explicit parent to avoid accidental deletion of the
        # underlying C++ object when dialogs are garbage-collected
        combo_parent = parent or self
        combo = QComboBox(combo_parent)
        combo.addItems(items)
        return combo

    def date_edit(self, parent=None):
        # date edits created with explicit parent
        edit_parent = parent or self
        date_edit = QDateEdit(edit_parent)
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        return date_edit

    def _get_value(self, widget):
        """Return a string value from a widget safely.

        Prefers currentText (for QComboBox), then text(), then toPlainText(), else ''
        """
        try:
            if widget is None:
                return ''
            if hasattr(widget, 'currentText'):
                return widget.currentText() or ''
            if hasattr(widget, 'text'):
                return widget.text() or ''
            if hasattr(widget, 'toPlainText'):
                return widget.toPlainText() or ''
            return str(widget)
        except Exception:
            return ''

    def populate_form(self, data):
        # Map form fields to database field names
        field_mappings = {
            "Full Name": "full_name",
            "Gender": "gender",
            "Date of Birth": "date_of_birth",
            "NRIC": "nric",
            "Nationality": "nationality",
            "Citizenship": "citizenship",
            "Race": "race",
            "Religion": "religion",
            "Marital Status": "marital_status",
            "Number of Children": "number_of_children",
            "Spouse Working": "spouse_working",
            "Email": "email",
            "Phone": "phone_number",
            "Address": "address",
            "City": "city",
            "State": "state",
            "Zipcode": "zipcode",
            "Primary School Name": "primary_school_name",
            "Primary Location": "primary_location",
            "Primary Year Started": "primary_year_started",
            "Primary Year Completed": "primary_year_completed",
            "Primary Type": "primary_type",
            "Secondary School Name": "secondary_school_name",
            "Secondary Location": "secondary_location",
            "Secondary Year Started": "secondary_year_started",
            "Secondary Year Completed": "secondary_year_completed",
            "Secondary Qualification": "secondary_qualification",
            "Secondary Type": "secondary_type",
            "Secondary Stream": "secondary_stream",
            "Secondary Grades": "secondary_grades",
            "Tertiary Institution Name": "tertiary_institution",
            "Tertiary Location": "tertiary_location",
            "Tertiary Level": "tertiary_level",
            "Tertiary Institution Type": "tertiary_institution_type",
            "Tertiary Field": "tertiary_field",
            "Tertiary Major": "tertiary_major",
            "Tertiary Year Started": "tertiary_year_started",
            "Tertiary Year Completed": "tertiary_year_completed",
            "Tertiary Status": "tertiary_status",
            "Tertiary CGPA": "tertiary_cgpa",
            "Qualification": "highest_qualification",
            "Institution": "institution",
            "Graduation Year": "graduation_year",
            "Employee ID": "employee_id",
            "Role": "role",
            "Job Title": "job_title",
            "Department": "department",
            "Position Level": "position",
            "Status": "status",
            "Work Status": "work_status",
            "Payroll Status": "payroll_status",
            "Functional Group": "functional_group",
            "Employment Type": "employment_type",
            "Date Joined": "date_joined",
            "Contact Name": "emergency_name",
            "Relation": "emergency_relation",
            "Emergency Phone": "emergency_phone",
            # EPF/SOCSO Status Display Fields (read-only, auto-calculated)
            # These are populated by the update_epf_socso_status function, not from database
        }

        for form_field, db_field in field_mappings.items():
            value = data.get(db_field, "")
            widget = self.fields.get(form_field)
            if not widget:
                continue
            if isinstance(widget, QLineEdit) and form_field != "Age":
                widget.setText(str(value) if value else "")
            elif isinstance(widget, QComboBox):
                if value is not None:
                    # Handle boolean values for specific fields
                    if form_field == "Spouse Working":
                        widget.setCurrentText("Yes" if value else "No")
                    elif form_field == "Number of Children":
                        widget.setCurrentText(str(value))
                    else:
                        # Try to set the text, if not found, use first item
                        index = widget.findText(str(value))
                        if index >= 0:
                            widget.setCurrentIndex(index)
                        else:
                            widget.setCurrentText(str(value))
            elif isinstance(widget, QDateEdit):
                if value:
                    try:
                        if isinstance(value, str):
                            parsed_date = datetime.strptime(value, "%Y-%m-%d").date()
                        else:
                            parsed_date = value
                        widget.setDate(QDate.fromString(parsed_date.strftime("%Y-%m-%d"), "yyyy-MM-dd"))
                    except ValueError:
                        print(f"DEBUG: Error parsing date for {form_field}: {value}")
            elif isinstance(widget, QCheckBox):
                # Handle checkbox values more carefully
                if value is not None and value != "":
                    checkbox_value = bool(value)
                    widget.setChecked(checkbox_value)

        # Load profile picture if available
        if data.get("photo_url"):
            self.load_picture_from_url(data["photo_url"])

        # Explicitly call autofill for job title so Position/Department are populated
        try:
            jt = self.fields.get('Job Title')
            if jt and hasattr(jt, 'currentText'):
                self.autofill_job_title(jt.currentText())
        except Exception:
            pass

        # Calculate age after setting date of birth
        if self.fields["Date of Birth"].date().isValid():
            dob = self.fields["Date of Birth"].date().toPyDate()
            today = datetime.now(KL_TZ).date()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            self.fields["Age"].setText(f"Age: {age}")
        
        # Load EPF part selection for non-citizens
        if hasattr(self, 'epf_part_combo') and data.get("epf_part"):
            epf_part = data.get("epf_part")
            # Convert "part_a" to "Part A" format for display
            if epf_part:
                display_text = epf_part.replace("_", " ").title()  # "part_a" -> "Part A"
                index = self.epf_part_combo.findText(display_text)
                if index >= 0:
                    self.epf_part_combo.setCurrentIndex(index)
        
        # Update EPF/SOCSO status display after populating form
        self.update_epf_socso_status()

        # Ensure work/payroll status UI reflects DB values as well
        try:
            if data.get('work_status'):
                ws = data.get('work_status')
                idx = self.fields.get('Work Status').findText(ws) if self.fields.get('Work Status') else -1
                if idx >= 0:
                    self.fields.get('Work Status').setCurrentIndex(idx)
                else:
                    try:
                        self.fields.get('Work Status').setEditText(ws)
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            if data.get('payroll_status'):
                ps = data.get('payroll_status')
                idx = self.fields.get('Payroll Status').findText(ps) if self.fields.get('Payroll Status') else -1
                if idx >= 0:
                    self.fields.get('Payroll Status').setCurrentIndex(idx)
                else:
                    try:
                        self.fields.get('Payroll Status').setEditText(ps)
                    except Exception:
                        pass
        except Exception:
            pass

    def update_employment_info(self, data, force=False):
        """Conservatively update only the Employment Information fields from a dict.

        - data: dict containing keys like job_title, position, department, functional_group,
          employment_type, date_joined
        - force: if True, overwrite current values even if user has entered something
        """
        try:
            # helper to set combo safely
            def _set_combo(combo, val):
                if not combo:
                    return
                try:
                    cur = combo.currentText() if hasattr(combo, 'currentText') else combo.text()
                except Exception:
                    cur = ''
                if force or not cur:
                    if val is None:
                        return
                    idx = combo.findText(val)
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
                    else:
                        try:
                            combo.setEditText(val)
                        except Exception:
                            pass

            jt = data.get('job_title') or data.get('position') or ''
            pos = data.get('position') or ''
            dep = data.get('department') or ''
            fg = data.get('functional_group') or ''
            et = data.get('employment_type') or ''
            dj = data.get('date_joined') or data.get('start_date') or ''

            try:
                if jt:
                    _set_combo(self.fields.get('Job Title'), jt)
            except Exception:
                pass
            try:
                if pos:
                    _set_combo(self.fields.get('Position Level'), pos)
            except Exception:
                pass
            try:
                if dep:
                    _set_combo(self.fields.get('Department'), dep)
            except Exception:
                pass
            try:
                if fg:
                    _set_combo(self.fields.get('Functional Group'), fg)
            except Exception:
                pass
            try:
                if et:
                    _set_combo(self.fields.get('Employment Type'), et)
            except Exception:
                pass
            try:
                if dj:
                    # only set if force or current is empty
                    cur = ''
                    try:
                        cur = self.fields.get('Date Joined').date().toString('yyyy-MM-dd')
                    except Exception:
                        cur = ''
                    if force or not cur:
                        d = None
                        try:
                            d = QDate.fromString(dj, 'yyyy-MM-dd')
                        except Exception:
                            d = None
                        if d and d.isValid():
                            self.fields.get('Date Joined').setDate(d)
            except Exception:
                pass
        except Exception:
            pass

    def update_epf_socso_status(self):
        """Calculate and update EPF/SOCSO status based on official regulations"""
        try:
            from epf_socso_calculator import EPFSOCSCalculator
            calculator = EPFSOCSCalculator()
            
            # Get values from form
            citizenship = self.fields["Citizenship"].currentText()
            nationality = self.fields["Nationality"].text().strip()
            
            # Determine citizenship status
            is_malaysian = (
                nationality.lower() in ['malaysia', 'malaysian'] or
                citizenship == "Citizen"
            )
            is_pr = citizenship == "Permanent Resident"
            is_non_citizen = not is_malaysian and not is_pr
            
            # Calculate age
            try:
                from datetime import datetime
                from services.supabase_service import KL_TZ
                
                dob = self.fields["Date of Birth"].date().toPyDate()
                today = datetime.now(KL_TZ).date()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except:
                age = 0
            
            # Show/hide EPF part selection based on citizenship
            if hasattr(self, 'epf_part_widget'):
                if is_non_citizen:
                    # Show EPF part selection for non-citizens only
                    self.epf_part_widget.show()
                    
                    # Temporarily disconnect signal to prevent recursion
                    self.epf_part_combo.currentTextChanged.disconnect()
                    
                    # Update available options based on age for non-citizens
                    current_selection = self.epf_part_combo.currentText()
                    self.epf_part_combo.clear()
                    self.epf_part_combo.addItem("None")
                    
                    if age < 60:
                        # Under 60: Part A (pre-1998) and Part B (post-1998) options
                        self.epf_part_combo.addItem("Part A")
                        self.epf_part_combo.addItem("Part B")
                    else:
                        # 60 and above: Part C (pre-1998) and Part D (post-1998) options
                        self.epf_part_combo.addItem("Part C")
                        self.epf_part_combo.addItem("Part D")
                    
                    # Restore previous selection if still valid
                    index = self.epf_part_combo.findText(current_selection)
                    if index >= 0:
                        self.epf_part_combo.setCurrentIndex(index)
                    
                    # Reconnect signal
                    def on_epf_part_changed(text):
                        self.update_epf_socso_status()
                    self.epf_part_combo.currentTextChanged.connect(on_epf_part_changed)
                else:
                    # Hide EPF part selection for citizens and PRs (automatic)
                    self.epf_part_widget.hide()
            
            # Update EPF Status display
            if is_malaysian:
                if age < 60:
                    self.fields["EPF Status"].setText("Part A - Malaysian Citizen")
                else:
                    self.fields["EPF Status"].setText("Part E - Malaysian Citizen ≥60")
            elif is_pr:
                if age < 60:
                    self.fields["EPF Status"].setText("Part A - Permanent Resident")
                else:
                    self.fields["EPF Status"].setText("Part C - Permanent Resident ≥60")
            else:
                # Non-citizens depend on their selection
                selected_part = self.epf_part_combo.currentText()
                if selected_part and selected_part != "None":
                    part_descriptions = {
                        "Part A": "Part A - Non-citizen (Pre-1998 Election)",
                        "Part B": "Part B - Non-citizen (Post-1998 Election)",
                        "Part C": "Part C - Non-citizen ≥60 (Pre-1998)",
                        "Part D": "Part D - Non-citizen ≥60 (Post-1998)"
                    }
                    self.fields["EPF Status"].setText(part_descriptions.get(selected_part, selected_part))
                else:
                    self.fields["EPF Status"].setText("Not Selected")
            
            # Get actual calculated SOCSO category
            socso_category = calculator.calculate_socso_category(
                birth_date=self.fields["Date of Birth"].date().toString("yyyy-MM-dd"),
                nationality=nationality,
                citizenship=citizenship
            )
            
            # Update SOCSO Status display (Updated per PERKESO official regulations)
            if socso_category == 'Exempt':
                self.fields["SOCSO Status"].setText("Exempt")
            elif socso_category == 'Category1':
                if is_malaysian or is_pr:
                    self.fields["SOCSO Status"].setText("Category 1 (Malaysian/PR Mandatory)")
                else:
                    self.fields["SOCSO Status"].setText("Category 1 (Foreign Worker Mandatory)")
            elif socso_category == 'Category2':
                if is_malaysian or is_pr:
                    self.fields["SOCSO Status"].setText("Category 2 (Malaysian/PR Limited)")
                else:
                    self.fields["SOCSO Status"].setText("Category 2 (Foreign Worker Limited)")
            else:
                self.fields["SOCSO Status"].setText(f"Eligible - {socso_category}")
                
        except Exception as e:
            print(f"Error calculating EPF/SOCSO status: {e}")
            self.fields["EPF Status"].setText("Error")
            self.fields["SOCSO Status"].setText("Error")

    def load_picture_from_url(self, url):
        """Load picture from URL"""
        try:
            print(f"DEBUG: Loading picture from URL: {url}")
            with urlopen(url) as response:
                image_data = response.read()
            
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            
            if not pixmap.isNull():
                # Create circular crop
                path = QPainterPath()
                path.addEllipse(0, 0, 118, 118)
                scaled_pixmap = pixmap.scaled(120, 120, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                clipped_pixmap = QPixmap(120, 120)
                clipped_pixmap.fill(Qt.transparent)
                painter = QPainter(clipped_pixmap)
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setClipPath(path)
                painter.setClipping(True)
                painter.drawPixmap(0, 0, scaled_pixmap)
                painter.end()
                self.picture_label.setPixmap(clipped_pixmap)
                print("DEBUG: Profile picture loaded successfully from URL")
            else:
                print("DEBUG: Failed to load pixmap from URL data")
                self.load_default_picture()
        except Exception as e:
            print(f"DEBUG: Error loading picture from URL: {str(e)}")
            self.load_default_picture()

    def create_buttons(self):
        button_layout = QHBoxLayout()
        
        submit_btn = QPushButton("Save" if self.employee_data else "Add Employee")
        submit_btn.clicked.connect(self.submit)
        submit_btn.setStyleSheet("QPushButton { background-color: #3498db; color: white; }")
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet("QPushButton { background-color: #e74c3c; color: white; }")
        
        # Payroll Information button (only for existing employees or admins)
        if self.employee_data or self.is_admin:
            payroll_btn = QPushButton("💰 Payroll & Tax Relief")
            payroll_btn.clicked.connect(self.open_payroll_dialog)
            payroll_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; padding: 8px 16px; border: none; border-radius: 4px; font-weight: bold; }")
            button_layout.addWidget(payroll_btn)

        # Employee History button (only for existing employees)
        if self.employee_data:
            try:
                from gui.employee_history_dialog import EmployeeHistoryDialog
                history_btn = QPushButton("📜 History")
                history_btn.clicked.connect(self.open_history_dialog)
                history_btn.setStyleSheet("QPushButton { background-color: #607D8B; color: white; }")
                button_layout.addWidget(history_btn)
            except Exception:
                # If dialog can't be imported, skip gracefully
                pass
        
        # Print button (only for existing employees)
        if self.employee_data:
            print_btn = QPushButton("Print Profile")
            print_btn.clicked.connect(self.print_profile)
            print_btn.setStyleSheet("QPushButton { background-color: #27ae60; color: white; }")
            button_layout.addWidget(print_btn)
        
        button_layout.addStretch()
        button_layout.addWidget(submit_btn)
        button_layout.addWidget(cancel_btn)
        
        self.content_layout.addLayout(button_layout)

    def open_history_dialog(self):
        try:
            if not self.employee_data:
                QMessageBox.information(self, "Not saved", "Please save the employee first to view history.")
                return
            from gui.employee_history_dialog import EmployeeHistoryDialog
            dlg = EmployeeHistoryDialog(self.employee_data.get('employee_id') or self.employee_data.get('id') or self.employee_data.get('employee_id') )
            dlg.exec_()
        except Exception as e:
            print(f"DEBUG: Failed to open employee history dialog: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open history: {e}")

    def open_payroll_dialog(self):
        """Open the payroll information dialog"""
        try:
            # If this is a new employee, we need to save basic info first
            if not self.employee_data:
                reply = QMessageBox.question(self, "Save Employee First", 
                                           "Employee must be saved before setting up payroll information. Save now?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                
                if reply == QMessageBox.Yes:
                    self.submit()  # This will save the employee
                    if hasattr(self, 'saved_employee_data'):
                        # Open payroll dialog with newly saved employee data
                        payroll_dialog = PayrollInformationDialog(self.saved_employee_data, self, self.is_admin)
                        payroll_dialog.exec_()
                return
            
            # Open payroll dialog for existing employee
            payroll_dialog = PayrollInformationDialog(self.employee_data, self, self.is_admin)
            payroll_dialog.exec_()
            
        except Exception as e:
            print(f"DEBUG: Error opening payroll dialog: {e}")
            QMessageBox.warning(self, "Error", f"Failed to open payroll dialog: {e}")

    def submit(self):
        try:
            # Collect form data
            data = {
                "full_name": self._get_value(self.fields.get("Full Name")).strip() or "N/A",
                "gender": self._get_value(self.fields.get("Gender")) or "N/A",
                "date_of_birth": self.fields["Date of Birth"].date().toString("yyyy-MM-dd"),
                "nric": self._get_value(self.fields.get("NRIC")).strip() or "N/A",
                "nationality": self._get_value(self.fields.get("Nationality")).strip() or "N/A",
                "citizenship": self._get_value(self.fields.get("Citizenship")) or "N/A",
                "race": self._get_value(self.fields.get("Race")).strip() or "N/A",
                "religion": self._get_value(self.fields.get("Religion")).strip() or "N/A",
                "marital_status": self._get_value(self.fields.get("Marital Status")) or "N/A",
                "number_of_children": int(self._get_value(self.fields.get("Number of Children")) or "0"),
                "spouse_working": (self._get_value(self.fields.get("Spouse Working")) == "Yes"),
                "email": self._get_value(self.fields.get("Email")).strip() or "N/A",
                "username": self._get_value(self.fields.get("Username")).strip().lower() or "",
                "phone_number": self._get_value(self.fields.get("Phone")).strip() or "N/A",
                "address": self._get_value(self.fields.get("Address")).strip() or "N/A",
                "city": self._get_value(self.fields.get("City")).strip() or "N/A",
                "state": self._get_value(self.fields.get("State")).strip() or "N/A",
                "zipcode": self._get_value(self.fields.get("Zipcode")).strip() or "N/A",
                "primary_school_name": self._get_value(self.fields.get("Primary School Name")).strip() or "",
                "primary_location": self._get_value(self.fields.get("Primary Location")).strip() or "",
                "primary_year_started": self._get_value(self.fields.get("Primary Year Started")).strip() or "",
                "primary_year_completed": self._get_value(self.fields.get("Primary Year Completed")).strip() or "",
                "primary_type": self._get_value(self.fields.get("Primary Type")).strip() or "",
                "secondary_school_name": self._get_value(self.fields.get("Secondary School Name")).strip() or "",
                "secondary_location": self._get_value(self.fields.get("Secondary Location")).strip() or "",
                "secondary_year_started": self._get_value(self.fields.get("Secondary Year Started")).strip() or "",
                "secondary_year_completed": self._get_value(self.fields.get("Secondary Year Completed")).strip() or "",
                "secondary_qualification": self._get_value(self.fields.get("Secondary Qualification")).strip() or "",
                "secondary_type": self._get_value(self.fields.get("Secondary Type")).strip() or "",
                "secondary_stream": self._get_value(self.fields.get("Secondary Stream")).strip() or "",
                "secondary_grades": self._get_value(self.fields.get("Secondary Grades")).strip() or "",
                "tertiary_institution": self._get_value(self.fields.get("Tertiary Institution Name")).strip() or "",
                "tertiary_location": self._get_value(self.fields.get("Tertiary Location")).strip() or "",
                "tertiary_level": self._get_value(self.fields.get("Tertiary Level")).strip() or "",
                "tertiary_institution_type": self._get_value(self.fields.get("Tertiary Institution Type")).strip() or "",
                "tertiary_field": self._get_value(self.fields.get("Tertiary Field")).strip() or "",
                "tertiary_major": self._get_value(self.fields.get("Tertiary Major")).strip() or "",
                "tertiary_year_started": self._get_value(self.fields.get("Tertiary Year Started")).strip() or "",
                "tertiary_year_completed": self._get_value(self.fields.get("Tertiary Year Completed")).strip() or "",
                "tertiary_status": self._get_value(self.fields.get("Tertiary Status")).strip() or "",
                "tertiary_cgpa": self._get_value(self.fields.get("Tertiary CGPA")).strip() or "",
                "highest_qualification": self._get_value(self.fields.get("Qualification")).strip() or "N/A",
                "institution": self._get_value(self.fields.get("Institution")).strip() or "N/A",
                "graduation_year": int(self._get_value(self.fields.get("Graduation Year")) or "0"),
                "employee_id": self._get_value(self.fields.get("Employee ID")).strip() or "N/A",
                "role": self._get_value(self.fields.get("Role")) or "employee",
                "job_title": self._get_value(self.fields.get("Job Title")).strip() or "N/A",
                "position": self._get_value(self.fields.get("Position Level")).strip() or "N/A",
                "department": self._get_value(self.fields.get("Department")).strip() or "N/A",
                "functional_group": self._get_value(self.fields.get("Functional Group")).strip() or None,
                "status": self._get_value(self.fields.get("Status")) or "Active",
                "work_status": self._get_value(self.fields.get("Work Status")) or "On Duty",
                "payroll_status": self._get_value(self.fields.get("Payroll Status")) or "Active Payroll",
                "employment_type": self._get_value(self.fields.get("Employment Type")) or "Full-time",
                "date_joined": self.fields["Date Joined"].date().toString("yyyy-MM-dd"),
                "emergency_name": self._get_value(self.fields.get("Contact Name")).strip() or "N/A",
                "emergency_relation": self._get_value(self.fields.get("Relation")).strip() or "N/A",
                "emergency_phone": self._get_value(self.fields.get("Emergency Phone")).strip() or "N/A",
            }

            # Add EPF Part Selection for Non-Citizens (simplified string storage)
            if hasattr(self, 'epf_part_combo'):
                selected_part = self.epf_part_combo.currentText()
                if selected_part and selected_part != "None":
                    # Convert "Part A" to "part_a" format
                    data["epf_part"] = selected_part.lower().replace(" ", "_")
                else:
                    data["epf_part"] = None
            else:
                data["epf_part"] = None

            # Calculate EPF/SOCSO data (auto for citizens, consider selection for non-citizens)
            try:
                from epf_socso_calculator import calculate_epf_socso_eligibility
                
                # For non-citizens only, check EPF part selection from dropdown
                # Citizens and PRs get automatic calculation
                if data.get('citizenship') == 'Non-citizen':
                    # Get selected EPF part from dropdown
                    selected_part_text = self.epf_part_combo.currentText()
                    selected_epf_part = None
                    
                    if selected_part_text == 'Part A':
                        selected_epf_part = 'A'
                        data['epf_part'] = 'part_a'
                    elif selected_part_text == 'Part B':
                        selected_epf_part = 'B'
                        data['epf_part'] = 'part_b'
                    elif selected_part_text == 'Part C':
                        selected_epf_part = 'C'
                        data['epf_part'] = 'part_c'
                    elif selected_part_text == 'Part D':
                        selected_epf_part = 'D'
                        data['epf_part'] = 'part_d'
                    elif selected_part_text == 'Part E':
                        selected_epf_part = 'E'
                        data['epf_part'] = 'part_e'
                    else:
                        data['epf_part'] = None
                    
                    # Calculate with selected part override
                    eligibility = calculate_epf_socso_eligibility(data, selected_epf_part)
                    # Set the calculated SOCSO category in the data
                    if 'socso_category' in eligibility:
                        data['socso_category'] = eligibility['socso_category']
                else:
                    # Auto-calculate for citizens and permanent residents
                    eligibility = calculate_epf_socso_eligibility(data)
                    # Set the calculated EPF part in the data
                    if 'epf_part' in eligibility:
                        data['epf_part'] = eligibility['epf_part']
                    if 'socso_category' in eligibility:
                        data['socso_category'] = eligibility['socso_category']
                
                print(f"DEBUG: Auto-calculated EPF/SOCSO data: EPF Part={eligibility.get('epf_part', 'Unknown')}, SOCSO={eligibility['socso_category']}")
                
            except Exception as e:
                print(f"DEBUG: Error calculating EPF/SOCSO data: {str(e)}")
                # Use defaults if calculation fails
                pass

            print(f"DEBUG: Submitting data: {data}")
            print(f"DEBUG: EPF Part being saved: {data.get('epf_part', 'NOT SET')}")
            print(f"DEBUG: SOCSO Category being saved: {data.get('socso_category', 'NOT SET')}")

            # Validate required fields (for new employee also require username)
            required_fields = ["full_name", "email"]
            if not self.employee_data:  # adding new employee
                required_fields.append("username")
            for field in required_fields:
                if not data.get(field) or data[field] == "N/A":
                    QMessageBox.warning(self, "Validation Error", f"Please fill in the {field.replace('_', ' ').title()} field.")
                    return

            if self.employee_data:
                # Update existing employee
                result = update_employee(self.employee_data.get("id"), data)
                if not result:
                    QMessageBox.critical(self, "Error", "Failed to update employee.")
                    return

                # Handle profile picture upload if new picture selected
                if self.profile_pic_path:
                    upload_result = upload_profile_picture(data["employee_id"], self.profile_pic_path)
                    if not upload_result:
                        QMessageBox.warning(self, "Warning", "Employee updated but profile picture upload failed.")

                # Sync employment_history only when tracked employment fields change
                try:
                    tracked_keys = [
                        'job_title', 'position', 'department', 'functional_group',
                        'status', 'work_status', 'payroll_status', 'employment_type'
                    ]
                    prev = {k: (self.employee_data.get(k) if self.employee_data else None) for k in tracked_keys}
                    curr = {k: data.get(k) for k in tracked_keys}

                    def _norm(v):
                        return (str(v).strip() if isinstance(v, str) else v) or None

                    changed = {k for k in tracked_keys if _norm(prev.get(k)) != _norm(curr.get(k))}

                    if changed:
                        from services.supabase_employee_history import insert_employee_history_record, update_employee_history_record
                        from services.supabase_employee_history import upsert_employee_status
                        from services.supabase_service import KL_TZ, supabase
                        now_iso = datetime.now(KL_TZ).isoformat()
                        today_str = datetime.now(KL_TZ).strftime('%Y-%m-%d')

                        # Close the latest open history record (if any)
                        try:
                            emp_uuid = str(self.employee_data.get('id'))
                            # fetch latest open record id
                            resp = (
                                supabase.table('employee_history')
                                .select('id')
                                .eq('employee_id', emp_uuid)
                                .is_('end_date', None)
                                .order('start_date', desc=True)
                                .limit(1)
                                .execute()
                            )
                            if resp and getattr(resp, 'data', None):
                                rec_id = resp.data[0].get('id')
                                if rec_id:
                                    update_employee_history_record(rec_id, {'end_date': today_str, 'updated_at': now_iso})
                        except Exception as _e:
                            print(f"DEBUG: Failed to close previous history record: {_e}")

                        # Insert a new history snapshot starting today with the changed fields
                        try:
                            snapshot = {
                                'id': str(uuid.uuid4()),
                                'employee_id': emp_uuid,
                                'start_date': today_str,
                                'end_date': None,
                                'notes': f"Profile change via dialog; changed: {', '.join(sorted(changed))}",
                                'attachments': []
                            }
                            for k in tracked_keys:
                                snapshot[k] = curr.get(k)
                            insert_employee_history_record(snapshot)
                        except Exception as _e:
                            print(f"DEBUG: Failed to insert new history snapshot: {_e}")

                        # Upsert current snapshot to employee_status (best-effort)
                        try:
                            upsert_employee_status(data.get('employee_id') or '', {
                                'department': curr.get('department'),
                                'status': curr.get('status'),
                                'work_status': curr.get('work_status'),
                                'payroll_status': curr.get('payroll_status'),
                                'position': curr.get('position'),
                                'job_title': curr.get('job_title'),
                                'functional_group': curr.get('functional_group'),
                                'employment_type': curr.get('employment_type'),
                                'last_changed_by': (self.user_email or ''),
                                'last_changed_at': now_iso,
                            })
                        except Exception as _e:
                            print(f"DEBUG: Failed to upsert employee_status: {_e}")
                except Exception as e_hist:
                    print(f"DEBUG: Error during employment history sync: {e_hist}")

                QMessageBox.information(self, "Success", "Employee updated successfully!")
                # emit signal to notify listeners to refresh
                try:
                    emp_id = self.employee_data.get("id")
                    if emp_id:
                        self.employee_saved.emit(str(emp_id))
                except Exception:
                    pass
            else:
                # Add new employee
                # Supply a password: either from a password field if present or generate a fallback handled in service
                provided_password = None
                try:
                    # If dialog has a password QLineEdit stored in fields dict under 'Password'
                    pwd_widget = self.fields.get('Password')
                    if pwd_widget:
                        provided_password = pwd_widget.text().strip() or None
                except Exception:
                    pass
                result = add_employee_with_login(data, provided_password, role="employee")
                if not result or not result.get('success'):
                    QMessageBox.critical(self, "Error", "Failed to add employee.")
                    return

                new_emp_uuid = result.get('employee_id')
                QMessageBox.information(self, "Success", "Employee added successfully!")
                # emit signal with employee identifier if available
                try:
                    signal_id = new_emp_uuid or data.get('employee_id') or data.get('id')
                    if signal_id:
                        self.employee_saved.emit(str(signal_id))
                except Exception:
                    pass
                # Try to create a corresponding employee_history record for new employee (best-effort)
                try:
                    from services.supabase_employee_history import insert_employee_history_record, upsert_employee_status
                    from services.supabase_service import KL_TZ, supabase
                    # Resolve the canonical employees.id (UUID) for the new employee
                    emp_uuid = new_emp_uuid
                    if not emp_uuid:
                        try:
                            # Prefer lookup by business employee_id if provided, else by email
                            if data.get('employee_id'):
                                r = supabase.table('employees').select('id').eq('employee_id', data.get('employee_id')).limit(1).execute()
                                if r and getattr(r, 'data', None):
                                    emp_uuid = r.data[0].get('id')
                            if not emp_uuid and data.get('email'):
                                r2 = supabase.table('employees').select('id').eq('email', data.get('email')).limit(1).execute()
                                if r2 and getattr(r2, 'data', None):
                                    emp_uuid = r2.data[0].get('id')
                        except Exception as _e:
                            print(f"DEBUG: Failed to resolve new employee UUID for history seeding: {_e}")
                    # Only seed history if we have a valid UUID
                    if emp_uuid:
                        # Use date_joined as the start date for the initial snapshot
                        start_date = data.get('date_joined') or datetime.now(KL_TZ).strftime('%Y-%m-%d')
                        rec = {
                            'id': str(uuid.uuid4()),
                            'employee_id': str(emp_uuid),
                            'job_title': data.get('job_title') or None,
                            'position': data.get('position') or None,
                            'department': data.get('department') or None,
                            'status': data.get('status') or None,
                            'work_status': data.get('work_status') or None,
                            'payroll_status': data.get('payroll_status') or None,
                            'functional_group': data.get('functional_group') or None,
                            'employment_type': data.get('employment_type') or None,
                            'start_date': start_date,
                            'end_date': None,
                            'notes': 'Synced from profile add',
                            'attachments': []
                        }
                        insert_employee_history_record(rec)
                    else:
                        print("DEBUG: Skipping history seed; could not resolve employees.id for new record")
                    # Also seed employee_status snapshot using the business employee_id code
                    try:
                        now_iso = datetime.now(KL_TZ).isoformat()
                        upsert_employee_status(data.get('employee_id') or '', {
                            'department': data.get('department'),
                            'status': data.get('status'),
                            'work_status': data.get('work_status'),
                            'payroll_status': data.get('payroll_status'),
                            'position': data.get('position'),
                            'job_title': data.get('job_title'),
                            'functional_group': data.get('functional_group'),
                            'employment_type': data.get('employment_type'),
                            'last_changed_by': (self.user_email or ''),
                            'last_changed_at': now_iso,
                        })
                    except Exception as _e:
                        print(f"DEBUG: Failed to seed employee_status for new employee: {_e}")
                except Exception as e:
                    print(f"DEBUG: Failed to auto-create history for new employee: {e}")

            self.accept()

        except Exception as e:
            print(f"DEBUG: Error in submit: {str(e)}")
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")

    def print_profile(self):
        """Print employee profile"""
        try:
            data = {
                "full_name": self._get_value(self.fields.get("Full Name")).strip() or "N/A",
                "gender": self._get_value(self.fields.get("Gender")) or "N/A",
                "date_of_birth": (self.fields.get("Date of Birth").date().toString("yyyy-MM-dd") if self.fields.get("Date of Birth") else "N/A"),
                "nric": self._get_value(self.fields.get("NRIC")).strip() or "N/A",
                "nationality": self._get_value(self.fields.get("Nationality")).strip() or "N/A",
                "citizenship": self._get_value(self.fields.get("Citizenship")) or "N/A",
                "race": self._get_value(self.fields.get("Race")).strip() or "N/A",
                "religion": self._get_value(self.fields.get("Religion")).strip() or "N/A",
                "marital_status": self._get_value(self.fields.get("Marital Status")) or "N/A",
                "number_of_children": self._get_value(self.fields.get("Number of Children")) or "0",
                "spouse_working": self._get_value(self.fields.get("Spouse Working")) or "N/A",
                "email": self._get_value(self.fields.get("Email")).strip() or "N/A",
                "phone_number": self._get_value(self.fields.get("Phone")).strip() or "N/A",
                "address": self._get_value(self.fields.get("Address")).strip() or "N/A",
                "city": self._get_value(self.fields.get("City")).strip() or "N/A",
                "state": self._get_value(self.fields.get("State")).strip() or "N/A",
                "zipcode": self._get_value(self.fields.get("Zipcode")).strip() or "N/A",
                "primary_school_name": self._get_value(self.fields.get("Primary School Name")).strip() or "N/A",
                "primary_location": self._get_value(self.fields.get("Primary Location")).strip() or "N/A",
                "primary_year_started": self._get_value(self.fields.get("Primary Year Started")).strip() or "N/A",
                "primary_year_completed": self._get_value(self.fields.get("Primary Year Completed")).strip() or "N/A",
                "primary_type": self._get_value(self.fields.get("Primary Type")).strip() or "N/A",
                "secondary_school_name": self._get_value(self.fields.get("Secondary School Name")).strip() or "N/A",
                "secondary_location": self._get_value(self.fields.get("Secondary Location")).strip() or "N/A",
                "secondary_year_started": self._get_value(self.fields.get("Secondary Year Started")).strip() or "N/A",
                "secondary_year_completed": self._get_value(self.fields.get("Secondary Year Completed")).strip() or "N/A",
                "secondary_qualification": self._get_value(self.fields.get("Secondary Qualification")).strip() or "N/A",
                "secondary_type": self._get_value(self.fields.get("Secondary Type")).strip() or "N/A",
                "secondary_stream": self._get_value(self.fields.get("Secondary Stream")).strip() or "N/A",
                "secondary_grades": self._get_value(self.fields.get("Secondary Grades")).strip() or "N/A",
                "tertiary_institution": self._get_value(self.fields.get("Tertiary Institution Name")).strip() or "N/A",
                "tertiary_location": self._get_value(self.fields.get("Tertiary Location")).strip() or "N/A",
                "tertiary_level": self._get_value(self.fields.get("Tertiary Level")).strip() or "N/A",
                "tertiary_institution_type": self._get_value(self.fields.get("Tertiary Institution Type")).strip() or "N/A",
                "tertiary_field": self._get_value(self.fields.get("Tertiary Field")).strip() or "N/A",
                "tertiary_major": self._get_value(self.fields.get("Tertiary Major")).strip() or "N/A",
                "tertiary_year_started": self._get_value(self.fields.get("Tertiary Year Started")).strip() or "N/A",
                "tertiary_year_completed": self._get_value(self.fields.get("Tertiary Year Completed")).strip() or "N/A",
                "tertiary_status": self._get_value(self.fields.get("Tertiary Status")).strip() or "N/A",
                "tertiary_cgpa": self._get_value(self.fields.get("Tertiary CGPA")).strip() or "N/A",
                "qualification": self._get_value(self.fields.get("Qualification")).strip() or "N/A",
                "institution": self._get_value(self.fields.get("Institution")).strip() or "N/A",
                "graduation_year": self._get_value(self.fields.get("Graduation Year")).strip() or "N/A",
                "employee_id": self._get_value(self.fields.get("Employee ID")).strip() or "N/A",
                "job_title": self._get_value(self.fields.get("Job Title")).strip() or "N/A",
                "position": self._get_value(self.fields.get("Position Level")).strip() or "N/A",
                "department": self._get_value(self.fields.get("Department")).strip() or "N/A",
                "status": self._get_value(self.fields.get("Status")).strip() or "N/A",
                "employment_type": self._get_value(self.fields.get("Employment Type")).strip() or "N/A",
                "date_joined": (self.fields.get("Date Joined").date().toString("yyyy-MM-dd") if self.fields.get("Date Joined") else "N/A"),
                "basic_salary": self._get_value(self.fields.get("Basic Salary")).strip() or "N/A",
                "bank_account": self._get_value(self.fields.get("Bank Account")).strip() or "N/A",
                "epf_number": self._get_value(self.fields.get("EPF Number")).strip() or "N/A",
                "socso_number": self._get_value(self.fields.get("SOCSO Number")).strip() or "N/A",
                "contact_name": self._get_value(self.fields.get("Contact Name")).strip() or "N/A",
                "relation": self._get_value(self.fields.get("Relation")).strip() or "N/A",
                "emergency_phone": self._get_value(self.fields.get("Emergency Phone")).strip() or "N/A",
            }

            html_content = f"""
            <html>
            <head>
                <title>Employee Profile</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #2c3e50; text-align: center; }}
                    h3 {{ color: #34495e; border-bottom: 2px solid #3498db; padding-bottom: 5px; }}
                    ul {{ list-style-type: none; padding: 0; }}
                    li {{ margin: 5px 0; padding: 5px; background-color: #f8f9fa; border-left: 3px solid #3498db; }}
                    strong {{ color: #2c3e50; }}
                </style>
            </head>
            <body>
            <h1>Employee Profile</h1>
            <h3>Personal Information</h3>
            <ul>
                <li><strong>Full Name:</strong> {data.get('full_name', 'N/A')}</li>
                <li><strong>Gender:</strong> {data.get('gender', 'N/A')}</li>
                <li><strong>Date of Birth:</strong> {data.get('date_of_birth', 'N/A')}</li>
                <li><strong>NRIC:</strong> {data.get('nric', 'N/A')}</li>
                <li><strong>Nationality:</strong> {data.get('nationality', 'N/A')}</li>
                <li><strong>Citizenship:</strong> {data.get('citizenship', 'N/A')}</li>
                <li><strong>Race:</strong> {data.get('race', 'N/A')}</li>
                <li><strong>Religion:</strong> {data.get('religion', 'N/A')}</li>
                <li><strong>Marital Status:</strong> {data.get('marital_status', 'N/A')}</li>
                <li><strong>Number of Children:</strong> {data.get('number_of_children', 'N/A')}</li>
                <li><strong>Spouse Working:</strong> {data.get('spouse_working', 'N/A')}</li>
            </ul>
            <h3>Contact Information</h3>
            <ul>
                <li><strong>Email:</strong> {data.get('email', 'N/A')}</li>
                <li><strong>Phone:</strong> {data.get('phone_number', 'N/A')}</li>
                <li><strong>Address:</strong> {data.get('address', 'N/A')}</li>
                <li><strong>City:</strong> {data.get('city', 'N/A')}</li>
                <li><strong>State:</strong> {data.get('state', 'N/A')}</li>
                <li><strong>Zipcode:</strong> {data.get('zipcode', 'N/A')}</li>
            </ul>
            <h3>Education</h3>
            <ul>
                <li><strong>Highest Qualification:</strong> {data.get('qualification', 'N/A')}</li>
                <li><strong>Institution:</strong> {data.get('institution', 'N/A')}</li>
                <li><strong>Graduation Year:</strong> {data.get('graduation_year', 'N/A')}</li>
            </ul>
            <h3>Employment</h3>
            <ul>
                <li><strong>Employee ID:</strong> {data.get('employee_id', 'N/A')}</li>
                <li><strong>Job Title:</strong> {data.get('job_title', 'N/A')}</li>
                <li><strong>Department:</strong> {data.get('department', 'N/A')}</li>
                <li><strong>Status:</strong> {data.get('status', 'N/A')}</li>
                <li><strong>Employment Type:</strong> {data.get('employment_type', 'N/A')}</li>
                <li><strong>Date Joined:</strong> {data.get('date_joined', 'N/A')}</li>
            </ul>
            <h3>Emergency Contact</h3>
            <ul>
                <li><strong>Contact Name:</strong> {data.get('contact_name', 'N/A')}</li>
                <li><strong>Relation:</strong> {data.get('relation', 'N/A')}</li>
                <li><strong>Emergency Phone:</strong> {data.get('emergency_phone', 'N/A')}</li>
            </ul>
            """

            html_content += """
            </body>
            </html>
            """

            # Create a QTextDocument for printing
            document = QTextDocument()
            document.setHtml(html_content)

            # Create printer and show print dialog
            printer = QPrinter()
            print_dialog = QPrintDialog(printer, self)
            
            if print_dialog.exec_() == QPrintDialog.Accepted:
                document.print_(printer)
                QMessageBox.information(self, "Print", "Profile printed successfully!")

        except Exception as e:
            print(f"DEBUG: Error printing profile: {str(e)}")
            QMessageBox.critical(self, "Print Error", f"Failed to print profile: {str(e)}")

    def load_salary_history_summary(self):
        """Load and display salary history summary for admin view"""
        if not self.employee_data or not supabase:
            return
        
        try:
            employee_id = self.employee_data.get('id')
            if not employee_id:
                return
            
            # Get current salary with null checking
            basic_salary = self.employee_data.get('basic_salary')
            if basic_salary is None or basic_salary == '':
                current_salary = 0.0
            else:
                try:
                    current_salary = float(basic_salary)
                except (ValueError, TypeError):
                    current_salary = 0.0
            
            # Update current salary display
            self.current_salary_display.setText(f"RM {current_salary:,.2f}")
            
            # Get recent salary history (last 3 changes)
            response = supabase.table("salary_history").select("*").eq("employee_id", employee_id).order("effective_date", desc=True).limit(3).execute()
            
            if response.data:
                history_text = "Recent changes:\n"
                for entry in response.data:
                    effective_date = entry.get('effective_date', '')
                    change_amount = float(entry.get('change_amount', 0))
                    reason = entry.get('reason', 'Unknown')
                    
                    change_sign = "+" if change_amount >= 0 else ""
                    history_text += f"• {effective_date}: {change_sign}RM {change_amount:,.2f} ({reason})\n"
                
                self.salary_changes_label.setText(history_text.strip())
            else:
                self.salary_changes_label.setText("No salary history found")
                
        except Exception as e:
            print(f"DEBUG: Error loading salary history: {e}")
            self.salary_changes_label.setText("Error loading salary history")
    
    def open_salary_history(self):
        """Open the salary history tab in admin dashboard"""
        try:
            # This could either open a new window or signal to the parent to switch tabs
            QMessageBox.information(self, "Salary History", 
                "Please use the 'Salary History' tab in the Admin Dashboard to view and manage complete salary history.")
        except Exception as e:
            print(f"DEBUG: Error opening salary history: {e}")
    
    def refresh_salary_data(self):
        """Refresh salary data after changes"""
        if self.employee_data and supabase:
            try:
                # Reload employee data from database
                response = supabase.table("employees").select("*").eq("id", self.employee_data['id']).execute()
                if response.data:
                    self.employee_data = response.data[0]
                    # Refresh salary history summary if admin
                    if self.is_admin and hasattr(self, 'current_salary_display'):
                        self.load_salary_history_summary()
                        
            except Exception as e:
                print(f"DEBUG: Error refreshing salary data: {e}")
