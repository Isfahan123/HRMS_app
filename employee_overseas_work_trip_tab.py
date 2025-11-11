from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem, QFormLayout, QMessageBox, QTabWidget, QFileDialog, QDateEdit
from PyQt5.QtCore import Qt, QDate
from services.supabase_training_overseas import insert_overseas_work_trip_record, fetch_overseas_work_trip_records, update_overseas_work_trip_record, delete_overseas_work_trip_record, fetch_overseas_work_trip_with_employee
from services.supabase_service import upload_document_to_bucket
import os

class EmployeeOverseasWorkTripTab(QWidget):
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
        submit_layout.addWidget(QLabel("Submit Overseas Work/Trip Record"))
        # Multi-column layout to match admin UI
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
        # Trip Details
        self.purpose_input = QLineEdit()
        from gui.widgets.country_dropdown import CountryDropdown
        self.country_input = CountryDropdown()
        from gui.widgets.city_autocomplete import CityAutocompleteWidget
        self.city_widget = CityAutocompleteWidget(country_restriction=None)
        self.city_place_id = None
        def _capture_city(desc, pid):
            self.city_place_id = pid
        self.city_widget.citySelected.connect(_capture_city)
        def update_city_country():
            country = self.country_input.text().strip()
            self.city_widget.country_restriction = country
        self.country_input.countrySelected.connect(update_city_country)
        # Replace plain QLineEdit date inputs with QDateEdit
        self.start_date_input = QDateEdit()
        self.start_date_input.setDisplayFormat('yyyy-MM-dd')
        self.start_date_input.setCalendarPopup(True)
        self.start_date_input.setDate(QDate.currentDate())
        self.end_date_input = QDateEdit()
        self.end_date_input.setDisplayFormat('yyyy-MM-dd')
        self.end_date_input.setCalendarPopup(True)
        self.end_date_input.setDate(QDate.currentDate())
        self.duration_display = QLabel("0 days")
        self.start_date_input.dateChanged.connect(lambda _: self.update_duration())
        self.end_date_input.dateChanged.connect(lambda _: self.update_duration())
        form_col1.addRow("Purpose:", self.purpose_input)
        form_col1.addRow("Country:", self.country_input)
        form_col1.addRow("City:", self.city_widget)
        form_col2.addRow("Start Date:", self.start_date_input)
        form_col2.addRow("End Date:", self.end_date_input)
        form_col2.addRow("Duration:", self.duration_display)
        # Content & Outcomes
        self.objectives_input = QTextEdit()
        self.outcomes_input = QTextEdit()
        form_col2.addRow("Objectives:", self.objectives_input)
        form_col2.addRow("Outcomes:", self.outcomes_input)
        # Costs
        self.travel_cost_input = QLineEdit()
        self.accommodation_cost_input = QLineEdit()
        self.daily_allowance_input = QLineEdit()
        form_col3.addRow("Travel Cost:", self.travel_cost_input)
        form_col3.addRow("Accommodation Cost:", self.accommodation_cost_input)
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
        # View subtab (created inside __init__ to avoid constructing widgets at import time)
        view_tab = QWidget()
        view_layout = QVBoxLayout()
        view_layout.addWidget(QLabel("View Submitted Records"))
        view_layout.addLayout(filter_layout)
        self.employee_info_label = QLabel("")
        view_layout.addWidget(self.employee_info_label)
        # Table view (columns similar to admin view)
        self.record_table = QTableWidget()
        self.record_table.setColumnCount(6)
        self.record_table.setHorizontalHeaderLabels(["Location", "Trip Date", "Purpose", "Country", "Attachments", "Notes"])
        self.record_table.horizontalHeader().setStretchLastSection(True)
        view_layout.addWidget(self.record_table)
        # Connect double-click to edit/delete handler
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
        # duration updated — no side effects here; record loading is handled separately

    def submit_record(self):
        # Build payload from the form fields and upload attachments
        emp_id = self.employee_id
        # Use autocomplete text and stored place_id
        location = self.city_widget.text().strip()
        country = self.country_input.text().strip()
        purpose = self.purpose_input.text().strip() if isinstance(self.purpose_input, QLineEdit) else getattr(self.purpose_input, 'currentText', lambda: '')()
        description = self.objectives_input.toPlainText() if hasattr(self, 'objectives_input') else None
        notes = self.notes_input.toPlainText() if self.notes_input else None

        start_qd = self.start_date_input.date()
        end_qd = self.end_date_input.date()
        start_date_str = start_qd.toString('yyyy-MM-dd') if start_qd.isValid() else None
        end_date_str = end_qd.toString('yyyy-MM-dd') if end_qd.isValid() else None
        try:
            duration_days = max(start_qd.daysTo(end_qd) + 1, 0)
        except Exception:
            duration_days = None

        def _to_num(txt):
            try:
                s = str(txt).strip().replace(',','')
                return float(s) if s != '' else None
            except Exception:
                return None

        travel_cost = _to_num(self.travel_cost_input.text())
        accommodation = _to_num(self.accommodation_cost_input.text())
        daily_allowance = _to_num(self.daily_allowance_input.text())
        total_claim = (travel_cost or 0.0) + (accommodation or 0.0) + (daily_allowance or 0.0)

        # Validate minimal required fields
        missing = []
        if not emp_id:
            missing.append('Employee')
        if not location:
            missing.append('Location')
        if not start_qd.isValid():
            missing.append('Start Date')
        if missing:
            QMessageBox.warning(self, 'Input Error', f"Missing required fields: {', '.join(missing)}")
            return

        attachment_urls = []
        failed_uploads = []
        for file_path in (self.attachment_inputs or []):
            try:
                url = upload_document_to_bucket(file_path, str(emp_id))
            except Exception:
                url = None
            if url:
                if isinstance(url, str) and url.endswith('?'):
                    url = url.rstrip('?')
                attachment_urls.append(url)
            else:
                failed_uploads.append(os.path.basename(file_path))

        admin_notes = notes or ''
        if failed_uploads:
            admin_notes = (admin_notes + ' | ' if admin_notes else '') + f"Failed uploads: {', '.join(failed_uploads)}"

        data = {
            'employee_id': emp_id,
            'country': country or None,
            'location': location or None,
            'trip_date': start_date_str,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'duration': duration_days,
            'purpose': purpose or None,
            'description': description or None,
            'travel_costs': travel_cost,
            'accommodation_costs': accommodation,
            'daily_allowance': daily_allowance,
            'total_claim': total_claim,
            'attachment_url': ','.join(attachment_urls) if attachment_urls else None,
            'admin_notes': admin_notes or None,
            'city_place_id': self.city_place_id,
        }

        try:
            response = insert_overseas_work_trip_record(data)
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.warning(self, 'Error', f'Failed to submit record: {e}')
            return

        if (hasattr(response, 'status_code') and getattr(response, 'status_code') == 201) or (hasattr(response, 'data') and response.data):
            if failed_uploads:
                QMessageBox.information(self, 'Partial Success', f'Record submitted. But attachments failed: {', '.join(failed_uploads)}')
            else:
                QMessageBox.information(self, 'Success', 'Record submitted successfully.')
            # Clear form
            self.city_widget.clear(); self.city_place_id = None
            self.start_date_input.setDate(QDate.currentDate())
            self.end_date_input.setDate(QDate.currentDate())
            self.duration_display.setText('0 days')
            self.purpose_input.clear()
            self.objectives_input.clear()
            self.outcomes_input.clear()
            self.travel_cost_input.clear()
            self.accommodation_cost_input.clear()
            self.daily_allowance_input.clear()
            self.attachment_inputs = []
            self.attachment_btn.setText('Choose Files')
            self.notes_input.clear()
            self.load_records()
        else:
            # Try to extract some debug info
            try:
                parts = []
                if response is None:
                    parts.append('<no response: None>')
                else:
                    parts.append(f'type={type(response).__name__}')
                    if hasattr(response, 'status_code'):
                        parts.append(f'status_code={getattr(response, 'status_code')}')
                    if hasattr(response, 'error'):
                        parts.append(f'error={getattr(response, 'error')}')
                    if hasattr(response, 'data'):
                        parts.append(f'data={getattr(response, 'data')}')
                    try:
                        parts.append(f'repr={repr(response)}')
                    except Exception:
                        parts.append(f'str={str(response)}')
                details = ' | '.join([str(p) for p in parts])
            except Exception as e:
                details = f'<error extracting response details: {e}> | raw={repr(response)}'
            print(f'DEBUG: Failed to insert overseas_work_trip record. Detailed response: {details}')
            QMessageBox.warning(self, 'Error', f'Failed to submit record. Response: {details}')

    def load_records(self):
        try:
            self.record_table.clearContents()
            self.record_table.setRowCount(0)
            if not self.employee_id:
                return
            filters = {}
            date_filter = self.filter_date_input.text().strip()
            keyword_filter = self.filter_keyword_input.text().strip()
            if date_filter:
                filters["trip_date"] = date_filter
            records = fetch_overseas_work_trip_records(self.employee_id, filters)
            if records:
                row = 0
                for rec in records:
                    joined = fetch_overseas_work_trip_with_employee(rec['id'])
                    if keyword_filter and keyword_filter.lower() not in str(joined.get('location', '')).lower() and keyword_filter.lower() not in str(joined.get('purpose', '')).lower():
                        continue
                    pos = joined.get('job_title') or ''
                    emp_info = f"{joined.get('full_name', '')} | {joined.get('department', '')} | {pos}"
                    # update employee info label (first matching record will set it)
                    self.employee_info_label.setText(emp_info)

                    self.record_table.insertRow(row)
                    it0 = QTableWidgetItem(str(joined.get('location') or ''))
                    it0.setData(Qt.UserRole, rec)
                    self.record_table.setItem(row, 0, it0)
                    it1 = QTableWidgetItem(str(joined.get('trip_date') or ''))
                    self.record_table.setItem(row, 1, it1)
                    it2 = QTableWidgetItem(str(joined.get('purpose') or ''))
                    self.record_table.setItem(row, 2, it2)
                    it3 = QTableWidgetItem(str(joined.get('country') or ''))
                    self.record_table.setItem(row, 3, it3)
                    it4 = QTableWidgetItem(str(joined.get('attachment_url') or ''))
                    self.record_table.setItem(row, 4, it4)
                    it5 = QTableWidgetItem(str(joined.get('admin_notes') or ''))
                    self.record_table.setItem(row, 5, it5)
                    row += 1
            else:
                self.employee_info_label.setText("")
        except Exception:
            # If something goes wrong while loading records, keep UI responsive
            self.employee_info_label.setText("")

    def choose_attachments(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Attachments")
        self.attachment_inputs = files
        if files:
            self.attachment_btn.setText(f"{len(files)} file(s) selected")

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
        # Populate the autocomplete widget and related fields
        self.city_widget.setText(rec.get('location', ''))
        try:
            if rec.get('trip_date'):
                d = QDate.fromString(rec.get('trip_date'), 'yyyy-MM-dd')
                if d.isValid():
                    self.start_date_input.setDate(d)
        except Exception:
            pass
        self.purpose_input.setText(rec.get('purpose', ''))
        self.notes_input.setText(rec.get('admin_notes', ''))
        def save_edit():
            # Build a richer update payload consistent with admin behavior
            start_qd = self.start_date_input.date()
            end_qd = self.end_date_input.date()
            start_str = start_qd.toString('yyyy-MM-dd') if start_qd.isValid() else None
            end_str = end_qd.toString('yyyy-MM-dd') if end_qd.isValid() else None
            try:
                duration_days = max(start_qd.daysTo(end_qd) + 1, 0)
            except Exception:
                duration_days = None
            def _to_num(txt):
                try:
                    s = str(txt).strip().replace(',','')
                    return float(s) if s != '' else None
                except Exception:
                    return None

            travel_cost = _to_num(self.travel_cost_input.text())
            accommodation = _to_num(self.accommodation_cost_input.text())
            daily_allowance = _to_num(self.daily_allowance_input.text())
            total_claim = (travel_cost or 0.0) + (accommodation or 0.0) + (daily_allowance or 0.0)

            approval_date = None
            try:
                if hasattr(self.approval_date_input, 'date') and isinstance(self.approval_date_input.date(), QDate) and self.approval_date_input.date().isValid():
                    approval_date = self.approval_date_input.date().toString('yyyy-MM-dd')
                elif hasattr(self.approval_date_input, 'text'):
                    approval_date = self.approval_date_input.text().strip() or None
            except Exception:
                approval_date = None

            data = {
                'location': self.city_widget.text() or None,
                'city': self.city_widget.text() or None,
                'trip_date': start_str,
                'start_date': start_str,
                'end_date': end_str,
                'duration': duration_days,
                'purpose': self.purpose_input.text() if isinstance(self.purpose_input, QLineEdit) else getattr(self.purpose_input, 'currentText', lambda: '')(),
                'description': self.objectives_input.toPlainText() or None,
                'flight_details': None,
                'accommodation_details': None,
                'daily_allowance': daily_allowance,
                'course_fees': None,
                'travel_costs': travel_cost,
                'total_claim': total_claim,
                'approved_by': (self.nominated_by_input.text().strip() if hasattr(self, 'nominated_by_input') else None) or None,
                'approval_date': approval_date,
                'admin_notes': self.notes_input.toPlainText() or None,
                'city_place_id': self.city_place_id,
            }
            response = update_overseas_work_trip_record(rec['id'], data)
            # Accept either HTTP 200 or non-empty .data
            if (hasattr(response, 'status_code') and getattr(response, 'status_code') == 200) or (hasattr(response, 'data') and response.data):
                QMessageBox.information(self, 'Success', 'Record updated.')
                self.load_records()
            else:
                QMessageBox.warning(self, 'Error', 'Failed to update record.')
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
