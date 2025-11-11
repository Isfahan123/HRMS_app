from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QListWidgetItem, QFormLayout, QMessageBox, QComboBox, QTabWidget, QFileDialog, QDateEdit
from PyQt5.QtCore import Qt
from services.supabase_training_overseas import insert_overseas_work_trip_record, fetch_overseas_work_trip_records, update_overseas_work_trip_record, delete_overseas_work_trip_record, fetch_overseas_work_trip_with_employee
from services.supabase_service import upload_document_to_bucket
from services.supabase_employee import fetch_employee_list
from PyQt5.QtCore import QDate

class AdminOverseasWorkTripTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Fetch employees including their UUID `id`, employee code, and full name
        try:
            from services.supabase_service import supabase
            resp = supabase.table('employees').select('id, employee_id, full_name').execute()
            if resp.data:
                # list of tuples: (uuid id, employee_code, full_name)
                self.employee_list = [(r.get('id'), r.get('employee_id'), r.get('full_name')) for r in resp.data]
            else:
                self.employee_list = []
        except Exception:
            # Fallback to existing helper which returns (employee_code, full_name)
            # and adapt to the new shape by leaving uuid as None
            fallback = fetch_employee_list()
            self.employee_list = [(None, emp_code, full_name) for emp_code, full_name in fallback]
        main_layout = QVBoxLayout()
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
        submit_layout.addWidget(QLabel("Submit Overseas Work/Trip Record for Employee"))
        # Three-column form layout
        columns_layout = QHBoxLayout()
        form_col1 = QFormLayout()
        form_col2 = QFormLayout()
        form_col3 = QFormLayout()

        # Employee selector
        self.employee_select = QComboBox()
        self.employee_select.addItem("Select Employee")
        for emp_uuid, emp_code, full_name in self.employee_list:
            # Use UUID id as itemData (if available), display name with code
            display = f"{full_name} ({emp_code})"
            self.employee_select.addItem(display, emp_uuid or emp_code)
        form_col1.addRow("Employee:", self.employee_select)

        # Record Type and Details
        self.record_type_input = QComboBox()
        self.record_type_input.addItems(["Trip", "Work Assignment", "Training"])
        from gui.country_dropdown import CountryDropdown
        self.country_input = CountryDropdown()
        self.purpose_input = QComboBox()
        self.purpose_input.addItems(["Meeting","Client Visit","Conference","Training","Project","Others"])
        self.description_input = QTextEdit()
        self.start_date_input = QDateEdit(QDate.currentDate())
        self.start_date_input.setCalendarPopup(True)
        self.end_date_input = QDateEdit(QDate.currentDate())
        self.end_date_input.setCalendarPopup(True)
        self.duration_display = QLabel("0 days")
        self.start_date_input.dateChanged.connect(self.update_duration)
        self.end_date_input.dateChanged.connect(self.update_duration)

        # Column 1
        form_col1.addRow("Type of Record:", self.record_type_input)
        form_col1.addRow("Country:", self.country_input)

        # Column 2
        form_col2.addRow("Purpose:", self.purpose_input)
        form_col2.addRow("Start Date:", self.start_date_input)
        form_col2.addRow("End Date:", self.end_date_input)
        form_col2.addRow("Duration:", self.duration_display)

        # Column 3
        form_col3.addRow("Description / Notes:", self.description_input)

        # Travel Arrangements (Column 3)
        self.flight_details_input = QTextEdit()
        self.accommodation_details_input = QTextEdit()
        form_col3.addRow("Flight Details:", self.flight_details_input)
        form_col3.addRow("Accommodation Details:", self.accommodation_details_input)

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
        self.per_diem_input = QLineEdit()
        self.per_diem_input.setPlaceholderText("0.00")
        self.course_fees_input = QLineEdit()
        self.course_fees_input.setPlaceholderText("0.00")
        self.travel_costs_input = QLineEdit()
        self.travel_costs_input.setPlaceholderText("0.00")
        self.total_cost_display = QLabel("0.00")
        for w in (self.per_diem_input, self.course_fees_input, self.travel_costs_input):
            w.textChanged.connect(self.update_total_cost)
        form_col2.addRow("Allowance / Per Diem:", self.per_diem_input)
        form_col2.addRow("Course Fees:", self.course_fees_input)
        form_col2.addRow("Travel Costs:", self.travel_costs_input)
        form_col2.addRow("Total Cost:", self.total_cost_display)

        form_col1.addRow("City:", self.city_widget)
        self.approved_by_input = QLineEdit()
        # Use QDateEdit for approval date so we store a consistent ISO date
        self.approval_date_input = QDateEdit(QDate.currentDate())
        self.approval_date_input.setCalendarPopup(True)
        self.approval_date_input.setDisplayFormat("yyyy-MM-dd")
        form_col2.addRow("Approved By:", self.approved_by_input)
        form_col2.addRow("Approval Date:", self.approval_date_input)

        # Notes / Attachments (Column 3)
        self.notes_input = QTextEdit()
        self.attachment_inputs = []
        self.attachment_btn = QPushButton("Choose Files")
        self.attachment_btn.clicked.connect(self.choose_attachments)
        form_col3.addRow("Supporting Documents:", self.attachment_btn)
        form_col3.addRow("Notes:", self.notes_input)

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
        view_layout.addWidget(QLabel("View All Overseas Work/Trip Records"))
        view_layout.addLayout(filter_layout)
        self.employee_info_label = QLabel("")
        view_layout.addWidget(self.employee_info_label)
        self.record_list = QListWidget()
        view_layout.addWidget(self.record_list)
        self.filter_employee_select = QComboBox()
        self.filter_employee_select.addItem("All Employees")
        for emp_uuid, emp_code, full_name in self.employee_list:
            self.filter_employee_select.addItem(f"{full_name} ({emp_code})", emp_uuid or emp_code)
        self.filter_employee_select.currentIndexChanged.connect(self.load_records)
        view_layout.addWidget(QLabel("Filter by Employee:"))
        view_layout.addWidget(self.filter_employee_select)
        refresh_btn = QPushButton("Refresh Records")
        refresh_btn.clicked.connect(self.load_records)
        view_layout.addWidget(refresh_btn)
        view_tab.setLayout(view_layout)

        self.tab_widget.addTab(submit_tab, "Submit Record")
        self.tab_widget.addTab(view_tab, "View Records")
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Double click to edit/delete - connect once
        self.record_list.itemDoubleClicked.connect(self.handle_edit_delete)

        # Initial load
        self.load_records()

        self.tab_widget.addTab(submit_tab, "Submit Record")
        self.tab_widget.addTab(view_tab, "View Records")
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)

        # Double click to edit/delete - connect once
        self.record_list.itemDoubleClicked.connect(self.handle_edit_delete)

        # Initial load
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
        total = to_num(self.per_diem_input.text()) + to_num(self.course_fees_input.text()) + to_num(self.travel_costs_input.text())
        self.total_cost_display.setText(f"{total:,.2f}")

    def choose_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        self.attachment_inputs = files
        if files:
            self.attachment_btn.setText(f"{len(files)} file(s) selected")

    def submit_record(self):
        emp_index = self.employee_select.currentIndex()
        selected_emp_token = self.employee_select.itemData(emp_index)
        # The employees table uses a UUID primary key (`id`), while the UI shows
        # an employee code (employee_id). Resolve the selected token to the UUID
        # before inserting into overseas_work_trip_records which expects a UUID.
        from services.supabase_service import supabase
        import uuid as _uuid
        employee_uuid = None
        if selected_emp_token:
            # If it's already a UUID string, use it; otherwise query mapping
            try:
                _uuid.UUID(str(selected_emp_token))
                employee_uuid = str(selected_emp_token)
            except Exception:
                try:
                    resp = supabase.table('employees').select('id').eq('employee_id', selected_emp_token).limit(1).execute()
                    if resp.data:
                        employee_uuid = resp.data[0].get('id')
                except Exception:
                    employee_uuid = None
        emp_id = employee_uuid
        # Ensure emp_id is a valid UUID string; if not, try one more lookup by employee_id
        import uuid as _uuid
        try:
            if emp_id:
                _uuid.UUID(str(emp_id))
        except Exception:
            # Attempt to resolve by employee_id (the displayed code)
            try:
                resp2 = supabase.table('employees').select('id').eq('employee_id', selected_emp_token).limit(1).execute()
                if resp2.data:
                    emp_id = resp2.data[0].get('id')
            except Exception:
                emp_id = None
        # Prefer the autocomplete widget's current text (keeps place_id linkage)
        location = self.city_widget.text().strip()
        record_type = self.record_type_input.currentText()
        country = self.country_input.text().strip()
        purpose = self.purpose_input.currentText()
        description = self.description_input.toPlainText()
        notes = self.notes_input.toPlainText()
        # Normalize dates
        start_qd = self.start_date_input.date()
        end_qd = self.end_date_input.date()
        start_date_str = start_qd.toString("yyyy-MM-dd") if start_qd.isValid() else None
        end_date_str = end_qd.toString("yyyy-MM-dd") if end_qd.isValid() else None
        try:
            duration_days = max(start_qd.daysTo(end_qd) + 1, 0)
        except Exception:
            duration_days = None
        # Costs and numeric fields
        def _to_num(txt):
            try:
                s = str(txt).strip().replace(',','')
                return float(s) if s != '' else None
            except Exception:
                return None
        per_diem = _to_num(self.per_diem_input.text())
        course_fees = _to_num(self.course_fees_input.text())
        travel_costs = _to_num(self.travel_costs_input.text())
        # If total cost display has formatting, try to parse it as fallback
        total_claim = _to_num(self.total_cost_display.text()) or ( (per_diem or 0.0) + (course_fees or 0.0) + (travel_costs or 0.0) )
        # Approval info
        approval_by = self.approved_by_input.text().strip()
        approval_date_str = None
        try:
            if isinstance(self.approval_date_input, QDateEdit) and self.approval_date_input.date().isValid():
                approval_date_str = self.approval_date_input.date().toString("yyyy-MM-dd")
        except Exception:
            approval_date_str = None
        # Better validation: report exactly which required fields are missing
        missing = []
        if not emp_id:
            missing.append('Employee')
        if not location:
            missing.append('Location')
        # Use QDate validity check rather than string truthiness
        if not self.start_date_input.date().isValid():
            missing.append('Start Date')
        if missing:
            QMessageBox.warning(self, "Input Error", f"Missing required fields: {', '.join(missing)}")
            # focus the first missing widget
            first = missing[0]
            if first == 'Employee':
                self.employee_select.setFocus()
            elif first == 'Location':
                self.city_widget.setFocus()
            elif first == 'Start Date':
                self.start_date_input.setFocus()
            return
        # Final sanity check: emp_id must be a UUID string now
        try:
            if not emp_id:
                raise ValueError('employee id unresolved')
            _uuid.UUID(str(emp_id))
        except Exception:
            QMessageBox.warning(self, "Input Error", "Selected employee could not be resolved to internal ID. Please re-select the employee.")
            self.employee_select.setFocus()
            return
        attachment_urls = []
        failed_uploads = []
        for file_path in self.attachment_inputs:
            url = upload_document_to_bucket(file_path, str(emp_id))
            if url:
                attachment_urls.append(url)
            else:
                failed_uploads.append(os.path.basename(file_path))
        # Keep a concise admin_notes but also send structured fields where schema supports them
        extra_lines = [
            f"Type: {record_type}",
            f"Country: {country}",
            f"Description: {description}",
        ]
        # Always include a human-readable costs line so data isn't lost if numeric columns are missing
        costs_line = f"Costs - Daily Allowance: {self.per_diem_input.text().strip()} | Course Fees: {self.course_fees_input.text().strip()} | Travel: {self.travel_costs_input.text().strip()} | Total: {self.total_cost_display.text()}"
        notes = (notes + " | " + " | ".join([s for s in extra_lines if s]) + " | " + costs_line).strip(" |")
        # If some uploads failed, append a short note so the information isn't lost
        if failed_uploads:
            notes = (notes or '') + " | " + f"Failed uploads: {', '.join(failed_uploads)}"

        data = {
            "employee_id": emp_id,
            "record_type": record_type,
            "country": country or None,
            "location": location or None,
            # trip_date is required in the DB (not-null); use start_date as the canonical trip_date
            "trip_date": start_date_str,
            "city": location or None,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "duration": duration_days,
            "purpose": purpose,
            "description": description or None,
            "flight_details": self.flight_details_input.toPlainText() or None,
            "accommodation_details": self.accommodation_details_input.toPlainText() or None,
            "daily_allowance": per_diem,
            "course_fees": course_fees,
            "travel_costs": travel_costs,
            "total_claim": total_claim,
            "approved_by": approval_by or None,
            "approval_date": approval_date_str,
            "attachment_url": ",".join(attachment_urls) if attachment_urls else None,
        "admin_notes": notes or None,
            "city_place_id": self.city_place_id,
        }
        try:
            response = insert_overseas_work_trip_record(data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, "Error", f"Failed to submit record: {str(e)}")
            return
        # Inspect response for success/failure
        if (hasattr(response, 'status_code') and getattr(response, 'status_code') == 201) or (hasattr(response, 'data') and response.data):
            # If uploads failed, show success-with-warnings rather than an error popup
            if failed_uploads:
                print(f"DEBUG: Record inserted but {len(failed_uploads)} attachment(s) failed: {failed_uploads}")
                QMessageBox.information(self, "Partial Success", f"Record submitted successfully. However, the following attachments failed to upload: {', '.join(failed_uploads)}")
            else:
                QMessageBox.information(self, "Success", "Record submitted successfully.")
            # Clear form inputs
            self.city_widget.clear()
            self.purpose_input.setCurrentIndex(0)
            self.description_input.clear()
            self.notes_input.clear()
            self.per_diem_input.clear()
            self.course_fees_input.clear()
            self.travel_costs_input.clear()
            self.total_cost_display.setText("0.00")
            self.attachment_inputs = []
            self.attachment_btn.setText("Choose Files")
            today = QDate.currentDate()
            self.start_date_input.setDate(today)
            self.end_date_input.setDate(today)
            self.update_duration()
            self.load_records()
        else:
            # Try to extract useful info from the response and log full repr for debugging
            try:
                parts = []
                if response is None:
                    parts.append("<no response: None>")
                else:
                    parts.append(f"type={type(response).__name__}")
                    # Common Supabase response attributes
                    if hasattr(response, 'status_code'):
                        parts.append(f"status_code={getattr(response, 'status_code')}")
                    if hasattr(response, 'error'):
                        parts.append(f"error={getattr(response, 'error')}")
                    if hasattr(response, 'data'):
                        parts.append(f"data={getattr(response, 'data')}")
                    if hasattr(response, 'text'):
                        parts.append(f"text={getattr(response, 'text')}")
                    # Fallback to string/repr
                    try:
                        parts.append(f"repr={repr(response)}")
                    except Exception:
                        parts.append(f"str={str(response)}")
                details = " | ".join([str(p) for p in parts])
            except Exception as e:
                details = f"<error extracting response details: {e}> | raw={repr(response)}"
            print(f"DEBUG: Failed to insert overseas_work_trip record. Detailed response: {details}")
            QMessageBox.warning(self, "Error", f"Failed to submit record. Response: {details}")

    def load_records(self):
        self.record_list.clear()
        emp_index = self.filter_employee_select.currentIndex()
        emp_id = self.filter_employee_select.itemData(emp_index)
        filters = {}
        date_filter = self.filter_date_input.text().strip()
        keyword_filter = self.filter_keyword_input.text().strip()
        if date_filter:
            filters["trip_date"] = date_filter
        if emp_index != 0:
            filters["employee_id"] = emp_id
        records = fetch_overseas_work_trip_records(None, filters)
        emp_info_displayed = False
        if records:
            for rec in records:
                joined = fetch_overseas_work_trip_with_employee(rec['id'])
                if not emp_info_displayed and joined:
                    pos = joined.get('job_title') or ''
                    emp_info = f"Employee: {joined.get('full_name', '')}\nDepartment: {joined.get('department', '')}\nJob Title: {pos}\nEmail: {joined.get('email', '')}"
                    self.employee_info_label.setText(emp_info)
                    emp_info_displayed = True
                if keyword_filter and keyword_filter.lower() not in str(joined.get('location', '')).lower() and keyword_filter.lower() not in str(joined.get('purpose', '')).lower():
                    continue
                item_text = f"{joined.get('location')} ({joined.get('trip_date')}): {joined.get('purpose')} | Attachments: {joined.get('attachment_url')} | Notes: {joined.get('admin_notes')}"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, rec)
                self.record_list.addItem(item)
        else:
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
        from PyQt5.QtCore import QDate
    # Set the autocomplete widget text and restore place_id if available
        self.city_widget.setText(rec.get('location', ''))
        self.city_place_id = rec.get('city_place_id') if rec.get('city_place_id') else None
        d = rec.get('trip_date', '') or ''
        if d:
            qd = QDate.fromString(d, 'yyyy-MM-dd')
            if qd.isValid():
                self.start_date_input.setDate(qd)
        self.purpose_input.setCurrentText(rec.get('purpose', ''))
        self.notes_input.setText(rec.get('admin_notes', ''))
        def save_edit():
            # Build update payload with same normalized fields
            start_str = self.start_date_input.date().toString('yyyy-MM-dd') if self.start_date_input.date().isValid() else None
            end_str = self.end_date_input.date().toString('yyyy-MM-dd') if self.end_date_input.date().isValid() else None
            try:
                duration_days = max(self.start_date_input.date().daysTo(self.end_date_input.date()) + 1, 0)
            except Exception:
                duration_days = None
            def _to_num(txt):
                try:
                    s = str(txt).strip().replace(',','')
                    return float(s) if s != '' else None
                except Exception:
                    return None
            per_diem = _to_num(self.per_diem_input.text())
            course_fees = _to_num(self.course_fees_input.text())
            travel_costs = _to_num(self.travel_costs_input.text())
            approval_date = None
            try:
                if isinstance(self.approval_date_input, QDateEdit) and self.approval_date_input.date().isValid():
                    approval_date = self.approval_date_input.date().toString('yyyy-MM-dd')
            except Exception:
                approval_date = None
            data = {
                "location": self.city_widget.text() or None,
                "city": self.city_widget.text() or None,
                "start_date": start_str,
                "end_date": end_str,
                "duration": duration_days,
                "purpose": self.purpose_input.currentText(),
                "flight_details": self.flight_details_input.toPlainText() or None,
                "accommodation_details": self.accommodation_details_input.toPlainText() or None,
                "daily_allowance": per_diem,
                "course_fees": course_fees,
                "travel_costs": travel_costs,
                "total_claim": _to_num(self.total_cost_display.text()) or None,
                "approved_by": self.approved_by_input.text().strip() or None,
                "approval_date": approval_date,
                "admin_notes": self.notes_input.toPlainText() or None,
                "city_place_id": self.city_place_id,
            }
            response = update_overseas_work_trip_record(rec['id'], data)
            if hasattr(response, 'status_code') and response.status_code == 200:
                QMessageBox.information(self, "Success", "Record updated.")
                self.load_records()
            else:
                QMessageBox.warning(self, "Error", "Failed to update record.")
        save_btn = QPushButton("Save Edit")
        save_btn.clicked.connect(save_edit)
        self.tab_widget.currentWidget().layout().addWidget(save_btn)

    def delete_record(self, rec):
        confirm = QMessageBox.question(self, "Confirm Delete", "Delete this record?", QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            response = delete_overseas_work_trip_record(rec['id'])
            if hasattr(response, 'status_code') and response.status_code == 200:
                QMessageBox.information(self, "Success", "Record deleted.")
                self.load_records()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete record.")

    def load_employee_list(self):
        try:
            from services.supabase_service import supabase
            resp = supabase.table('employees').select('id, employee_id, full_name').execute()
            if resp.data:
                self.employee_list = [(r.get('id'), r.get('employee_id'), r.get('full_name')) for r in resp.data]
            else:
                self.employee_list = []
        except Exception:
            fallback = fetch_employee_list()
            self.employee_list = [(None, emp_code, full_name) for emp_code, full_name in fallback]
