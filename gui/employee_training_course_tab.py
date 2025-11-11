from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QFormLayout, QMessageBox, QTabWidget, QFileDialog, QDateEdit
from PyQt5.QtCore import Qt, QDate
from services.supabase_training_overseas import insert_training_course_record, fetch_training_course_records, update_training_course_record, delete_training_course_record, fetch_training_course_with_employee
from services.supabase_service import upload_document_to_bucket
import os


def _to_num(txt):
    try:
        s = str(txt).strip().replace(',', '')
        return float(s) if s != '' else None
    except Exception:
        return None

class EmployeeTrainingCourseTab(QWidget):
    def __init__(self, parent=None, employee_id=None):
        super().__init__(parent)
        self.employee_id = employee_id
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
        submit_layout.addWidget(QLabel("Submit Training/Course Record"))
        # Use a multi-column form layout (three columns) to match admin layout
        columns_layout = QHBoxLayout()
        form_col1 = QFormLayout()
        form_col2 = QFormLayout()
        form_col3 = QFormLayout()
        # Employee Info
        self.name_input = QLineEdit()
        self.staff_id_input = QLineEdit()
        self.position_input = QLineEdit()
        self.department_input = QLineEdit()
        form_col1.addRow("Name:", self.name_input)
        form_col1.addRow("Staff ID:", self.staff_id_input)
        form_col1.addRow("Position:", self.position_input)
        form_col1.addRow("Department:", self.department_input)
        # Training Details
        self.course_title_input = QLineEdit()
        self.provider_input = QLineEdit()
        # Backwards-compatible aliases expected by some edit handlers
        self.course_name_input = self.course_title_input
        from gui.country_dropdown import CountryDropdown
        self.country_input = CountryDropdown()
        from gui.city_autocomplete import CityAutocompleteWidget
        self.city_widget = CityAutocompleteWidget(country_restriction=None)
        self.city_place_id = None
        def _capture_city(desc, pid):
            self.city_place_id = pid
        self.city_widget.citySelected.connect(_capture_city)
        def update_city_country():
            country = self.country_input.text().strip()
            self.city_widget.country_restriction = country
        self.country_input.countrySelected.connect(update_city_country)
        # Use QDateEdit for robust date handling and duration calculation
        self.start_date_input = QDateEdit()
        self.start_date_input.setDisplayFormat('yyyy-MM-dd')
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input = QDateEdit()
        self.end_date_input.setDisplayFormat('yyyy-MM-dd')
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        self.duration_display = QLabel("0 days")
        # dateChanged passes QDate; use lambda to call update_duration without args
        self.start_date_input.dateChanged.connect(lambda _: self.update_duration())
        self.end_date_input.dateChanged.connect(lambda _: self.update_duration())
        form_col1.addRow("Course/Training Title:", self.course_title_input)
        form_col1.addRow("Provider/Institution:", self.provider_input)
        form_col1.addRow("Country:", self.country_input)
        form_col1.addRow("City:", self.city_widget)
        form_col2.addRow("Start Date:", self.start_date_input)
        form_col2.addRow("End Date:", self.end_date_input)
        form_col2.addRow("Duration:", self.duration_display)
        # Content & Outcomes
        self.objectives_input = QTextEdit()
        # alias for older code paths
        self.course_desc_input = self.objectives_input
        self.certification_input = QLineEdit()
        self.skills_input = QTextEdit()
        form_col2.addRow("Objectives/Syllabus:", self.objectives_input)
        form_col2.addRow("Certification Received:", self.certification_input)
        form_col2.addRow("Skills Acquired:", self.skills_input)
        # Costs
        self.course_fees_input = QLineEdit()
        self.travel_accommodation_input = QLineEdit()
        self.daily_allowance_input = QLineEdit()
        form_col3.addRow("Course Fees:", self.course_fees_input)
        form_col3.addRow("Travel & Accommodation:", self.travel_accommodation_input)
        form_col3.addRow("Daily Allowance:", self.daily_allowance_input)
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
        form_col3.addRow("Notes:", self.notes_input)
        form_col3.addRow("Attachments:", self.attachment_btn)
        # Assemble columns
        columns_layout.addLayout(form_col1)
        columns_layout.addLayout(form_col2)
        columns_layout.addLayout(form_col3)
        submit_layout.addLayout(columns_layout)
        submit_btn = QPushButton("Submit Record")
        submit_btn.clicked.connect(self.submit_record)
        submit_layout.addWidget(submit_btn)
        submit_tab.setLayout(submit_layout)

        # View subtab
        view_tab = QWidget()
        view_layout = QVBoxLayout()
        view_layout.addWidget(QLabel("View Submitted Records"))
        view_layout.addLayout(filter_layout)
        self.employee_info_label = QLabel("")
        view_layout.addWidget(self.employee_info_label)

        # Table view (columns similar to admin view)
        self.record_table = QTableWidget()
        self.record_table.setColumnCount(6)
        self.record_table.setHorizontalHeaderLabels(["Course/Training", "Date", "Provider", "Country", "Attachments", "Notes"])
        self.record_table.horizontalHeader().setStretchLastSection(True)
        view_layout.addWidget(self.record_table)

        # Connect double-click on any cell to edit/delete flow. We attach the full record to a cell's user data.
        self.record_table.itemDoubleClicked.connect(self.handle_edit_delete)

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
        # Use QDate objects from QDateEdit to compute duration
        try:
            start = self.start_date_input.date()
            end = self.end_date_input.date()
            if start.isValid() and end.isValid():
                days = start.daysTo(end) + 1
                if days > 0:
                    self.duration_display.setText(f"{days} days")
                else:
                    self.duration_display.setText("Invalid dates")
            else:
                self.duration_display.setText("0 days")
        except Exception:
            self.duration_display.setText("Invalid dates")

    def choose_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        self.attachment_inputs = files
        if files:
            self.attachment_btn.setText(f"{len(files)} file(s) selected")

    def submit_record(self):
        # Use the title and start_date fields present in this form
        title = self.course_title_input.text().strip()
        date = self.start_date_input.date().toString('yyyy-MM-dd')
        desc = (self.objectives_input.toPlainText() or "").strip()
        notes = (self.notes_input.toPlainText() or "").strip()
        if not title or not date:
            QMessageBox.warning(self, "Input Error", "Course title and start date are required.")
            return
        # Upload attachments (collect successful urls and record failed filenames)
        attachment_urls = []
        failed_uploads = []
        for file_path in (self.attachment_inputs or []):
            try:
                url = upload_document_to_bucket(file_path, str(self.employee_id))
            except Exception:
                url = None
            if url:
                if isinstance(url, str) and url.endswith('?'):
                    url = url.rstrip('?')
                attachment_urls.append(url)
            else:
                failed_uploads.append(os.path.basename(file_path))

        data = {
            "employee_id": self.employee_id,
            # Preserve legacy and new names
            "course_name": title,
            "course_title": title,
            "course_date": date,
            "start_date": date,
            "end_date": self.end_date_input.date().toString('yyyy-MM-dd'),
            "duration": None,
            "description": desc,
            "objectives": self.objectives_input.toPlainText() or None,
            "certification": self.certification_input.text().strip() or None,
            "skills": self.skills_input.toPlainText() or None,
            "provider": self.provider_input.text().strip() or None,
            "country": self.country_input.text().strip() or None,
            "city": self.city_widget.text().strip() or None,
            "attachment_url": ",".join(attachment_urls) if attachment_urls else None,
            "admin_notes": notes or None,
            "nominated_by": (self.nominated_by_input.text().strip() if hasattr(self, 'nominated_by_input') else None) or None,
            "approval_date": (self.approval_date_input.text().strip() if hasattr(self, 'approval_date_input') and hasattr(self.approval_date_input, 'text') else None) or None,
            "feedback": (self.feedback_input.toPlainText() if hasattr(self, 'feedback_input') else None) or None,
            "supervisor_evaluation": (self.supervisor_eval_input.toPlainText() if hasattr(self, 'supervisor_eval_input') else None) or None,
            "city_place_id": self.city_place_id,
            # Numeric cost fields
            "course_fees": _to_num(self.course_fees_input.text()),
            "travel_accommodation": _to_num(self.travel_accommodation_input.text()),
            "daily_allowance": _to_num(self.daily_allowance_input.text()),
            "total_cost": (_to_num(self.course_fees_input.text()) or 0.0) + (_to_num(self.travel_accommodation_input.text()) or 0.0) + (_to_num(self.daily_allowance_input.text()) or 0.0),
        }
        response = insert_training_course_record(data)
        is_success = False
        if hasattr(response, 'status_code') and getattr(response, 'status_code') == 201:
            is_success = True
        elif hasattr(response, 'data') and response.data:
            is_success = True

        if is_success:
            if failed_uploads:
                # Best-effort: append failed names to admin_notes in DB if we have created id
                try:
                    created_id = None
                    if hasattr(response, 'data') and isinstance(response.data, (list, tuple)) and len(response.data) > 0:
                        created_id = response.data[0].get('id')
                    elif hasattr(response, 'data') and isinstance(response.data, dict):
                        created_id = response.data.get('id')
                    if created_id:
                        update_training_course_record(created_id, {"admin_notes": data.get('admin_notes','') + f" | Failed attachments: {', '.join(failed_uploads)}"})
                except Exception:
                    pass
                QMessageBox.information(self, "Partial Success", f"Record submitted successfully. However, the following attachments failed to upload: {', '.join(failed_uploads)}")
            else:
                QMessageBox.information(self, "Success", "Record submitted successfully.")
            # Clear fields
            self.course_title_input.clear()
            self.start_date_input.setDate(QDate.currentDate())
            self.end_date_input.setDate(QDate.currentDate())
            self.objectives_input.clear()
            self.attachment_inputs = []
            self.attachment_btn.setText("Choose Files")
            self.notes_input.clear()
            self.city_widget.clear(); self.city_place_id = None
            self.load_records()
        else:
            QMessageBox.warning(self, "Error", "Failed to submit record.")
    def load_records(self):
        # Populate the QTableWidget with records. We store the raw record dict on the first cell's UserRole so
        # the edit/delete handlers can retrieve it.
        try:
            self.record_table.clearContents()
            self.record_table.setRowCount(0)
            if not self.employee_id:
                return
            filters = {}
            date_filter = self.filter_date_input.text().strip()
            keyword_filter = self.filter_keyword_input.text().strip()
            if date_filter:
                filters["course_date"] = date_filter
            records = fetch_training_course_records(self.employee_id, filters)
            emp_info_displayed = False
            if records:
                row = 0
                for rec in records:
                    joined = fetch_training_course_with_employee(rec['id'])
                    if not emp_info_displayed and joined:
                        pos = joined.get('job_title') or ''
                        emp_info = f"Employee: {joined.get('full_name', '')}\nDepartment: {joined.get('department', '')}\nJob Title: {pos}\nEmail: {joined.get('email', '')}"
                        self.employee_info_label.setText(emp_info)
                        emp_info_displayed = True
                    # Keyword filtering
                    if keyword_filter and keyword_filter.lower() not in str(joined.get('course_name', '')).lower() and keyword_filter.lower() not in str(joined.get('description', '')).lower():
                        continue

                    self.record_table.insertRow(row)
                    # Column 0: Course/Training
                    item0 = QTableWidgetItem(str(joined.get('course_name') or ''))
                    item0.setData(Qt.UserRole, rec)
                    self.record_table.setItem(row, 0, item0)
                    # Column 1: Date
                    item1 = QTableWidgetItem(str(joined.get('course_date') or ''))
                    self.record_table.setItem(row, 1, item1)
                    # Column 2: Provider
                    item2 = QTableWidgetItem(str(joined.get('provider') or ''))
                    self.record_table.setItem(row, 2, item2)
                    # Column 3: Country
                    item3 = QTableWidgetItem(str(joined.get('country') or ''))
                    self.record_table.setItem(row, 3, item3)
                    # Column 4: Attachments
                    item4 = QTableWidgetItem(str(joined.get('attachment_url') or ''))
                    self.record_table.setItem(row, 4, item4)
                    # Column 5: Notes
                    item5 = QTableWidgetItem(str(joined.get('admin_notes') or ''))
                    self.record_table.setItem(row, 5, item5)

                    row += 1
            else:
                self.employee_info_label.setText("")
        except Exception:
            # Keep UI responsive if something unexpected happens while loading
            self.employee_info_label.setText("")

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
        # Simple inline edit (could be a dialog for full edit)
        self.course_name_input.setText(rec.get('course_name', ''))
        # If there is a stored date string, try to set it on a QDateEdit if applicable
        try:
            if rec.get('course_date'):
                d = QDate.fromString(rec.get('course_date'), 'yyyy-MM-dd')
                if d.isValid():
                    self.start_date_input.setDate(d)
                    self.end_date_input.setDate(d)
        except Exception:
            pass
        self.course_desc_input.setText(rec.get('description', ''))
        self.notes_input.setText(rec.get('admin_notes', ''))
        # Attachments not editable inline for simplicity
        def save_edit():
            # Build update payload consistent with admin fields
            def _to_num(txt):
                try:
                    s = str(txt).strip().replace(',', '')
                    return float(s) if s != '' else None
                except Exception:
                    return None

            start_qd = self.start_date_input.date()
            end_qd = self.end_date_input.date()
            start_str = start_qd.toString('yyyy-MM-dd') if start_qd.isValid() else None
            end_str = end_qd.toString('yyyy-MM-dd') if end_qd.isValid() else None
            try:
                duration_days = max(start_qd.daysTo(end_qd) + 1, 0)
            except Exception:
                duration_days = None

            course_fees = _to_num(self.course_fees_input.text()) if hasattr(self, 'course_fees_input') else None
            travel_accom = _to_num(self.travel_accommodation_input.text()) if hasattr(self, 'travel_accommodation_input') else None
            daily_allow = _to_num(self.daily_allowance_input.text()) if hasattr(self, 'daily_allowance_input') else None
            total_cost = (course_fees or 0.0) + (travel_accom or 0.0) + (daily_allow or 0.0)

            approval_date = None
            try:
                if hasattr(self.approval_date_input, 'date') and isinstance(self.approval_date_input.date(), QDate) and self.approval_date_input.date().isValid():
                    approval_date = self.approval_date_input.date().toString('yyyy-MM-dd')
            except Exception:
                approval_date = None

            data = {
                'course_name': self.course_name_input.text() or None,
                'course_title': self.course_title_input.text() or None,
                'course_date': self.start_date_input.date().toString('yyyy-MM-dd') if self.start_date_input.date().isValid() else None,
                'start_date': start_str,
                'end_date': end_str,
                'duration': duration_days,
                'description': self.course_desc_input.toPlainText() or None,
                'objectives': self.course_desc_input.toPlainText() or None,
                'certification': (self.certification_input.text() if hasattr(self, 'certification_input') else None) or None,
                'skills': (self.skills_input.text() if hasattr(self, 'skills_input') else None) or None,
                'provider': (self.provider_input.text() if hasattr(self, 'provider_input') else None) or None,
                'country': (self.country_input.text() if hasattr(self, 'country_input') else None) or None,
                'city': self.city_widget.text() or None,
                'city_place_id': getattr(self, 'city_place_id', None),
                'course_fees': course_fees,
                'travel_accommodation': travel_accom,
                'daily_allowance': daily_allow,
                'total_cost': total_cost,
                'admin_notes': self.notes_input.toPlainText() or None,
                'nominated_by': (self.nominated_by_input.text() if hasattr(self, 'nominated_by_input') else None) or None,
                'approval_date': approval_date,
                'feedback': (self.feedback_input.toPlainText() if hasattr(self, 'feedback_input') else None) or None,
                'supervisor_evaluation': (self.supervisor_eval_input.toPlainText() if hasattr(self, 'supervisor_eval_input') else None) or None,
            }

            response = update_training_course_record(rec['id'], data)
            if (hasattr(response, 'status_code') and getattr(response, 'status_code') in (200, 201)) or (hasattr(response, 'data') and response.data):
                QMessageBox.information(self, "Success", "Record updated.")
                self.course_name_input.clear()
                # Clear QDateEdit to today
                self.start_date_input.setDate(QDate.currentDate())
                self.end_date_input.setDate(QDate.currentDate())
                self.course_desc_input.clear()
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
            if (hasattr(response, 'status_code') and getattr(response, 'status_code') == 200) or (hasattr(response, 'data') and response.data):
                QMessageBox.information(self, "Success", "Record deleted.")
                self.load_records()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete record.")
