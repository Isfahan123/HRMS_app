from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QFormLayout, QMessageBox, QComboBox, QTabWidget, QFileDialog, QDateEdit
from PyQt5.QtCore import Qt
from services.supabase_training_overseas import insert_training_course_record, fetch_training_course_records, update_training_course_record, delete_training_course_record, fetch_training_course_with_employee
from services.supabase_service import upload_document_to_bucket
import os
from services.supabase_employee import fetch_employee_list
from gui.widgets.city_autocomplete import CityAutocompleteWidget
from PyQt5.QtCore import QDate

class AdminTrainingCourseTab(QWidget):
    # ...existing code...
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration_display = QLabel("0 days")
        # fetch_employee_list() now returns tuples of (id, employee_id, full_name)
        self.employee_list = fetch_employee_list()
        self.certification_input = QLineEdit()
        self.objectives_input = QTextEdit()
        self.skills_input = QTextEdit()
        self.attachment_inputs = []
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # Advanced filter controls
        self.filter_date_input = QLineEdit()
        self.filter_keyword_input = QLineEdit()
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by Date:"))
        filter_layout.addWidget(self.filter_date_input)
        filter_layout.addWidget(QLabel("Keyword:"))
        filter_layout.addWidget(self.filter_keyword_input)

        # Submit subtab
        submit_tab = QWidget()
        submit_layout = QVBoxLayout()
        submit_layout.addWidget(QLabel("Submit Training/Course Record for Employee"))
        # Three-column form layout
        columns_layout = QHBoxLayout()
        form_col1 = QFormLayout()
        form_col2 = QFormLayout()
        form_col3 = QFormLayout()
        self.employee_select = QComboBox()
        self.employee_select.addItem("Select Employee")
        for emp_uuid, emp_code, full_name in self.employee_list:
            display = f"{full_name} ({emp_code})"
            # store UUID if available, otherwise store the employee code for a later lookup
            self.employee_select.addItem(display, emp_uuid or emp_code)
        form_col1.addRow("Employee:", self.employee_select)
        # Record Type and Training Details
        self.record_type_input = QComboBox()
        self.record_type_input.addItems(["Training", "Course"])
        self.course_title_input = QLineEdit()
        self.provider_input = QLineEdit()
        # Country selection replaced by CountryDropdown widget (searchable)
        # City autocomplete widget
        self.city_widget = CityAutocompleteWidget(country_restriction=None)
        self.city_place_id = None
        def _capture_city(desc, pid):
            self.city_place_id = pid
        self.city_widget.citySelected.connect(_capture_city)
        from PyQt5.QtCore import QDate
        self.start_date_input = QDateEdit(QDate.currentDate()); self.start_date_input.setCalendarPopup(True); self.start_date_input.setDisplayFormat('yyyy-MM-dd')
        self.end_date_input = QDateEdit(QDate.currentDate()); self.end_date_input.setCalendarPopup(True); self.end_date_input.setDisplayFormat('yyyy-MM-dd')
        # Auto-calculate duration when dates change
        self.start_date_input.dateChanged.connect(lambda _: self.update_duration())
        self.end_date_input.dateChanged.connect(lambda _: self.update_duration())
        def update_city_country():
            country = self.country_input.text().strip()
            self.city_widget.country_restriction = country
        from gui.widgets.country_dropdown import CountryDropdown
        self.country_input = CountryDropdown()
        self.country_input.countrySelected.connect(update_city_country)
        form_col1.addRow("Course/Training Title:", self.course_title_input)
        form_col1.addRow("Provider/Institution:", self.provider_input)
        form_col1.addRow("Country:", self.country_input)
        form_col1.addRow("City:", self.city_widget)
        # Column 2
        form_col2.addRow("Start Date:", self.start_date_input)
        form_col2.addRow("End Date:", self.end_date_input)
        form_col2.addRow("Duration:", self.duration_display)
        # Content & Outcomes
        form_col2.addRow("Certification Received:", self.certification_input)
        form_col2.addRow("Objectives/Syllabus:", self.objectives_input)
        form_col2.addRow("Skills Acquired:", self.skills_input)
        # Costs (currency numeric)
        self.course_fees_input = QLineEdit(); self.course_fees_input.setPlaceholderText("0.00")
        self.travel_accommodation_input = QLineEdit(); self.travel_accommodation_input.setPlaceholderText("0.00")
        self.daily_allowance_input = QLineEdit(); self.daily_allowance_input.setPlaceholderText("0.00")
        self.total_cost_display = QLabel("0.00")
        for w in (self.course_fees_input, self.travel_accommodation_input, self.daily_allowance_input):
            w.textChanged.connect(self.update_total_cost)
        # Column 3
        form_col3.addRow("Course Fees:", self.course_fees_input)
        form_col3.addRow("Travel & Accommodation:", self.travel_accommodation_input)
        form_col3.addRow("Daily Allowance:", self.daily_allowance_input)
        form_col3.addRow("Total Cost:", self.total_cost_display)
        # Approvals
        self.nominated_by_input = QLineEdit()
        self.approval_date_input = QLineEdit()
        form_col3.addRow("Nominated By:", self.nominated_by_input)
        form_col3.addRow("Approval Date:", self.approval_date_input)
        # Evaluation
        self.feedback_input = QTextEdit()
        self.supervisor_eval_input = QTextEdit()
        form_col3.addRow("Employee Feedback:", self.feedback_input)
        form_col3.addRow("Supervisor Evaluation:", self.supervisor_eval_input)
        # Notes / Attachments
        self.notes_input = QTextEdit()
        self.attachment_inputs = []
        self.attachment_btn = QPushButton("Choose Files")
        self.attachment_btn.clicked.connect(self.choose_attachments)
        form_col3.addRow("Attachments:", self.attachment_btn)
        form_col3.addRow("Notes:", self.notes_input)
        # Assemble columns
        columns_layout.addLayout(form_col1)
        columns_layout.addLayout(form_col2)
        columns_layout.addLayout(form_col3)
        submit_layout.addLayout(columns_layout)
        # (Removed read-only employee detail fields and autofill; keeping selection only)

        submit_btn = QPushButton("Submit Record")
        submit_btn.clicked.connect(self.submit_record)
        submit_layout.addWidget(submit_btn)
        submit_tab.setLayout(submit_layout)

        # View subtab
        view_tab = QWidget()
        view_layout = QVBoxLayout()
        view_layout.addWidget(QLabel("View All Training/Course Records"))
        view_layout.addLayout(filter_layout)
        self.employee_info_label = QLabel("")
        view_layout.addWidget(self.employee_info_label)
        self.record_list = QListWidget()
        view_layout.addWidget(self.record_list)
        self.filter_employee_select = QComboBox()
        self.filter_employee_select.addItem("All Employees")
        for emp_uuid, emp_code, full_name in self.employee_list:
            display = f"{full_name} ({emp_code})"
            # store UUID when available, otherwise store employee code for later resolution
            self.filter_employee_select.addItem(display, emp_uuid or emp_code)
        self.filter_employee_select.currentIndexChanged.connect(self.load_records)
        view_layout.addWidget(QLabel("Filter by Employee:"))
        view_layout.addWidget(self.filter_employee_select)
        refresh_btn = QPushButton("Refresh Records")
        refresh_btn.clicked.connect(self.load_records)
        view_layout.addWidget(refresh_btn)
        view_tab.setLayout(view_layout)

        self.tab_widget.addTab(submit_tab, "Submit Record")
        self.tab_widget.addTab(view_tab, "View Records")
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)
        self.load_records()

    def update_duration(self):
        try:
            start = self.start_date_input.date(); end = self.end_date_input.date()
            days = start.daysTo(end) + 1
            self.duration_display.setText(f"{max(days,0)} days")
        except Exception:
            self.duration_display.setText("Invalid dates")

    def update_total_cost(self):
        def to_num(txt):
            try: return float(txt)
            except: return 0.0
        total = to_num(self.course_fees_input.text()) + to_num(self.travel_accommodation_input.text()) + to_num(self.daily_allowance_input.text())
        self.total_cost_display.setText(f"{total:,.2f}")

    def choose_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        self.attachment_inputs = files
        if files:
            self.attachment_btn.setText(f"{len(files)} file(s) selected")

    def submit_record(self):
        emp_index = self.employee_select.currentIndex()
        selected_emp_token = self.employee_select.itemData(emp_index)
        # Resolve to UUID if we were given an employee code
        emp_id = None
        if selected_emp_token:
            import uuid as _uuid
            try:
                _uuid.UUID(str(selected_emp_token))
                emp_id = str(selected_emp_token)
            except Exception:
                # lookup by employee_id
                try:
                    from services.supabase_service import supabase
                    resp = supabase.table('employees').select('id').eq('employee_id', selected_emp_token).limit(1).execute()
                    if resp.data:
                        emp_id = resp.data[0].get('id')
                except Exception:
                    emp_id = None
        title = self.course_title_input.text().strip()
        # Prefer start_date as the canonical course_date but include start/end separately
        start_qd = self.start_date_input.date()
        end_qd = self.end_date_input.date()
        start_date_str = start_qd.toString('yyyy-MM-dd') if start_qd.isValid() else None
        end_date_str = end_qd.toString('yyyy-MM-dd') if end_qd.isValid() else None
        try:
            duration_days = max(start_qd.daysTo(end_qd) + 1, 0)
        except Exception:
            duration_days = None
        # Use objectives as primary description
        desc = (self.objectives_input.toPlainText() or "").strip()
        # Compose admin_notes with extra fields so we don't require schema changes
        total_cost = getattr(self, 'total_cost_display', QLabel("0.00")).text()
        def to_num(txt):
            try:
                return float(str(txt).replace(',',''))
            except Exception:
                return 0.0
        course_fees = to_num(self.course_fees_input.text())
        travel_accommodation = to_num(self.travel_accommodation_input.text())
        daily_allowance = to_num(self.daily_allowance_input.text())
        notes_lines = [
            self.notes_input.toPlainText().strip(),
            f"Type: {self.record_type_input.currentText()}",
            f"Provider: {self.provider_input.text().strip()}",
            f"Country/City: {self.country_input.text()} / {self.city_widget.text().strip()}",
            f"Certification: {self.certification_input.text().strip()}",
            f"Skills: {self.skills_input.toPlainText().strip()}",
            f"Costs - Course: {self.course_fees_input.text().strip()} | Travel/Accom: {self.travel_accommodation_input.text().strip()} | Daily: {self.daily_allowance_input.text().strip()} | Total: {total_cost}",
        ]
        notes = " | ".join([s for s in notes_lines if s])
        if emp_index == 0 or not title or not start_date_str:
            QMessageBox.warning(self, "Input Error", "Employee, title, and start date are required.")
            return
        # Upload attachments (collect successful urls and record failed filenames)
        attachment_urls = []
        failed_uploads = []
        for file_path in (self.attachment_inputs or []):
            try:
                url = upload_document_to_bucket(file_path, str(emp_id))
            except Exception as e:
                # Upload helper should log full traceback; capture filename for UI
                url = None
            if url:
                # Normalize trailing '?' from some Supabase public URLs
                if isinstance(url, str) and url.endswith('?'):
                    url = url.rstrip('?')
                attachment_urls.append(url)
            else:
                failed_uploads.append(os.path.basename(file_path))
        # Build full payload with both legacy and new column names so DB can persist as available
        data = {
            "employee_id": emp_id,
            # keep legacy "course_name" as primary identifier and also set course_title
            "course_name": title,
            "course_title": title,
            # use start_date as canonical course_date while also sending start/end
            "course_date": start_date_str,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "duration": duration_days,
            "description": desc,
            "objectives": self.objectives_input.toPlainText() or None,
            "certification": self.certification_input.text().strip() or None,
            "skills": self.skills_input.toPlainText() or None,
            "provider": self.provider_input.text().strip() or None,
            "country": self.country_input.text().strip() or None,
            "city": self.city_widget.text().strip() or None,
            "attachment_url": ",".join(attachment_urls) if attachment_urls else None,
            "admin_notes": notes or None,
            "nominated_by": self.nominated_by_input.text().strip() or None,
            "approval_date": (self.approval_date_input.text().strip() if hasattr(self.approval_date_input, 'text') else None) or None,
            "feedback": self.feedback_input.toPlainText() or None,
            "supervisor_evaluation": self.supervisor_eval_input.toPlainText() or None,
            "city_place_id": self.city_place_id,
            # Numeric cost fields (parsed floats) so DB can persist them if schema present
            "course_fees": course_fees,
            "travel_accommodation": travel_accommodation,
            "daily_allowance": daily_allowance,
            "total_cost": to_num(total_cost),
        }
        response = insert_training_course_record(data)
        # Treat either a 201 status or a non-empty .data as success (Supabase client can return APIResponse)
        is_success = False
        if hasattr(response, 'status_code') and getattr(response, 'status_code') == 201:
            is_success = True
        elif hasattr(response, 'data') and response.data:
            is_success = True

        if is_success:
            # If uploads failed, show success with warning rather than an error popup
            if failed_uploads:
                # Append failed filenames into admin_notes so there's a persisted trace
                if failed_uploads:
                    data_note = f" | Failed attachments: {', '.join(failed_uploads)}"
                    # Try to update the admin_notes in the DB record if possible (best-effort)
                    try:
                        # If response contains created record id, append to the record
                        created_id = None
                        if hasattr(response, 'data') and isinstance(response.data, (list, tuple)) and len(response.data) > 0:
                            created_id = response.data[0].get('id')
                        elif hasattr(response, 'data') and isinstance(response.data, dict):
                            created_id = response.data.get('id')
                        if created_id:
                            update_training_course_record(created_id, {"admin_notes": data.get('admin_notes','') + data_note})
                    except Exception:
                        pass
                QMessageBox.information(self, "Partial Success", f"Record submitted successfully. However, the following attachments failed to upload: {', '.join(failed_uploads)}")
            else:
                QMessageBox.information(self, "Success", "Record submitted successfully.")
            # Clear new-form fields
            self.course_title_input.clear()
            self.provider_input.clear()
            self.city_widget.clear(); self.city_place_id = None
            self.objectives_input.clear()
            self.certification_input.clear()
            self.skills_input.clear()
            self.course_fees_input.clear()
            self.travel_accommodation_input.clear()
            self.daily_allowance_input.clear()
            self.total_cost_display.setText("0.00")
            self.start_date_input.setDate(QDate.currentDate())
            self.end_date_input.setDate(QDate.currentDate())
            self.record_type_input.setCurrentIndex(0)
            self.attachment_inputs = []
            self.attachment_btn.setText("Choose Files")
            self.notes_input.clear()
            self.load_records()
        else:
            QMessageBox.warning(self, "Error", "Failed to submit record.")

    def load_records(self):
        self.record_list.clear()
        emp_index = self.filter_employee_select.currentIndex()
        emp_id = self.filter_employee_select.itemData(emp_index)
        filters = {}
        date_filter = self.filter_date_input.text().strip()
        keyword_filter = self.filter_keyword_input.text().strip()
        if date_filter:
            filters["course_date"] = date_filter
        if emp_index != 0:
            filters["employee_id"] = emp_id
        records = fetch_training_course_records(None, filters)
        emp_info_displayed = False
        if records:
            for rec in records:
                joined = fetch_training_course_with_employee(rec['id'])
                if not emp_info_displayed and joined:
                    pos = joined.get('job_title') or ''
                    emp_info = f"Employee: {joined.get('full_name', '')}\nDepartment: {joined.get('department', '')}\nJob Title: {pos}\nEmail: {joined.get('email', '')}"
                    self.employee_info_label.setText(emp_info)
                    emp_info_displayed = True
                if keyword_filter and keyword_filter.lower() not in str(joined.get('course_name', '')).lower() and keyword_filter.lower() not in str(joined.get('description', '')).lower():
                    continue
                item_text = f"{joined.get('course_name')} ({joined.get('course_date')}): {joined.get('description')} | Attachments: {joined.get('attachment_url')} | Notes: {joined.get('admin_notes')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, rec)
                self.record_list.addItem(item)
        else:
            self.employee_info_label.setText("")
        self.record_list.itemDoubleClicked.connect(self.handle_edit_delete)

    def handle_edit_delete(self, item):
        rec = item.data(Qt.UserRole)
        msg_box = QMessageBox()
        msg_box.setText("Edit or Delete this record?")
        edit_btn = msg_box.addButton("Edit", QMessageBox.ActionRole)
        delete_btn = msg_box.addButton("Delete", QMessageBox.ActionRole)
        cancel_btn = msg_box.addButton(QMessageBox.Cancel)
        msg_box.exec_()
        if msg_box.clickedButton() == edit_btn:
            self.edit_record(rec)
        elif msg_box.clickedButton() == delete_btn:
            self.delete_record(rec)

    def edit_record(self, rec):
        from PyQt5.QtCore import QDate
        self.course_title_input.setText(rec.get('course_name', ''))
        d = rec.get('course_date', '') or ''
        if d:
            qd = QDate.fromString(d, 'yyyy-MM-dd')
            if qd.isValid():
                self.start_date_input.setDate(qd)
        self.objectives_input.setText(rec.get('description', ''))
        self.notes_input.setText(rec.get('admin_notes', ''))
        def save_edit():
            # Compose an update payload with the richer set of fields
            start_str = self.start_date_input.date().toString('yyyy-MM-dd') if self.start_date_input.date().isValid() else None
            end_str = self.end_date_input.date().toString('yyyy-MM-dd') if self.end_date_input.date().isValid() else None
            try:
                duration_days = max(self.start_date_input.date().daysTo(self.end_date_input.date()) + 1, 0)
            except Exception:
                duration_days = None
            data = {
                "course_name": self.course_title_input.text(),
                "course_title": self.course_title_input.text(),
                "course_date": start_str,
                "start_date": start_str,
                "end_date": end_str,
                "duration": duration_days,
                "description": self.objectives_input.toPlainText(),
                "objectives": self.objectives_input.toPlainText(),
                "admin_notes": self.notes_input.toPlainText(),
                "provider": self.provider_input.text().strip() or None,
                "country": self.country_input.text().strip() or None,
                "city": self.city_widget.text().strip() or None,
                "certification": self.certification_input.text().strip() or None,
                "skills": self.skills_input.toPlainText() or None,
                "nominated_by": self.nominated_by_input.text().strip() or None,
                "approval_date": (self.approval_date_input.text().strip() if hasattr(self.approval_date_input, 'text') else None) or None,
                "feedback": self.feedback_input.toPlainText() or None,
                "supervisor_evaluation": self.supervisor_eval_input.toPlainText() or None,
                "city_place_id": self.city_place_id,
            }
            response = update_training_course_record(rec['id'], data)
            # Accept either 200 or non-empty .data as success
            if (hasattr(response, 'status_code') and getattr(response, 'status_code') == 200) or (hasattr(response, 'data') and response.data):
                QMessageBox.information(self, "Success", "Record updated.")
                self.course_title_input.clear()
                self.objectives_input.clear()
                self.start_date_input.setDate(QDate.currentDate())
                self.notes_input.clear()
                self.load_records()
            else:
                QMessageBox.warning(self, "Error", "Failed to update record.")
        save_btn = QPushButton("Save Edit")
        save_btn.clicked.connect(save_edit)
        self.tab_widget.currentWidget().layout().addWidget(save_btn)

    def delete_record(self, rec):
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this record?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            response = delete_training_course_record(rec['id'])
            # Accept either 200 or non-empty .data as success
            if (hasattr(response, 'status_code') and getattr(response, 'status_code') == 200) or (hasattr(response, 'data') and response.data):
                QMessageBox.information(self, "Success", "Record deleted.")
                self.load_records()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete record.")

    def load_employee_list(self):
        self.employee_list = fetch_employee_list()
