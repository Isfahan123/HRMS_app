from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout,
    QMessageBox, QComboBox, QDateEdit, QHBoxLayout, QGroupBox,
    QScrollArea, QGridLayout, QFileDialog, QTextEdit, QCheckBox
)
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtCore import QDate, Qt, QByteArray
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QTextDocument, QFont, QColor
from datetime import datetime, date
from services.supabase_service import insert_employee, update_employee, delete_profile_picture, upload_profile_picture, supabase, KL_TZ, convert_utc_to_kl
import re
import os
import uuid
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
import pytz

class EmployeeProfileTab(QWidget):
    def __init__(self, stacked_widget, user_email=None):
        super().__init__()
        self.stacked_widget = stacked_widget
        self.user_email = user_email
        self.employee_data = None
        self.profile_pic_path = None
        self.resume_path = None
        self.is_admin = False  # Employee profile tab is always for regular employees
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)

        self.create_sections()
        self.create_buttons()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

        # Load employee data if user_email is provided
        if self.user_email:
            self.load_employee_data()

    def create_sections(self):
        self.fields = {}
        
        # Create main horizontal layout container
        main_horizontal_layout = QHBoxLayout()
        
        # --- LEFT COLUMN: Personal and Contact Information ---
        left_column = QWidget()
        left_layout = QVBoxLayout(left_column)
        
        # --- Profile picture and resume (top of left column) ---
        picture_resume_widget = QWidget()
        picture_resume_layout = QVBoxLayout(picture_resume_widget)
        picture_resume_layout.setAlignment(Qt.AlignCenter)
        
        # Profile picture
        self.picture_label = QLabel()
        self.picture_label.resize(120, 120)
        self.picture_label.setAlignment(Qt.AlignCenter)
        self.picture_label.setScaledContents(True)

        self.default_avatar_path = os.path.join("assets", "default_avatar.png")
        self.load_default_picture()

        # Upload button - disabled for read-only view
        self.upload_btn = QPushButton("Upload Picture")
        self.upload_btn.setFixedWidth(120)
        self.upload_btn.setEnabled(False)  # Read-only
        self.upload_btn.clicked.connect(self.upload_picture)

        picture_resume_layout.addWidget(self.picture_label)
        picture_resume_layout.addWidget(self.upload_btn)
        
        # Resume upload - disabled for read-only view
        resume_widget = QWidget()
        resume_layout = QHBoxLayout(resume_widget)
        resume_layout.setContentsMargins(0, 0, 0, 0)

        self.resume_label = QLabel("No file selected")
        self.resume_upload_btn = QPushButton("Upload Resume")
        self.resume_upload_btn.setEnabled(False)  # Read-only
        self.resume_upload_btn.clicked.connect(self.upload_resume)

        resume_layout.addWidget(self.resume_label)
        resume_layout.addWidget(self.resume_upload_btn)
        
        picture_resume_layout.addWidget(resume_widget)
        picture_resume_layout.addStretch()
        
        left_layout.addWidget(picture_resume_widget)
        
        # --- RIGHT COLUMN: Employment Information ---
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        
        # Personal Information
        personal_groupbox = QGroupBox("Personal Information")
        personal_form = QFormLayout()
        personal_groupbox.setLayout(personal_form)
        
        personal_fields = [
            ("Full Name", QLineEdit()),
            ("Gender", self.combo(["Male", "Female", "Other"])),
            ("Date of Birth", self.date_edit()),
            ("Age", QLabel("Age: -")),
            ("NRIC", QLineEdit()),
            ("Nationality", QLineEdit()),
            ("Citizenship", self.combo(["Citizen", "Non-citizen", "Permanent Resident"])),
            ("Race", QLineEdit()),
            ("Religion", QLineEdit()),
            ("Marital Status", self.combo(["Single", "Married", "Divorced", "Widowed"])),
            ("Number of Children", self.combo([str(i) for i in range(0, 11)])),
            ("Spouse Working", self.combo(["Yes", "No"]))
        ]
        
        for label, widget in personal_fields:
            personal_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget
            # Make all fields read-only
            if hasattr(widget, 'setReadOnly'):
                widget.setReadOnly(True)
            elif hasattr(widget, 'setEnabled'):
                widget.setEnabled(False)

        # Add EPF election fields to personal form (read-only)
        epf_label = QLabel("EPF Election:")
        epf_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        personal_form.addRow(epf_label)
        
        self.epf_election_group = QWidget()
        epf_layout = QVBoxLayout(self.epf_election_group)
        epf_layout.setContentsMargins(0, 0, 0, 0)

        # EPF Part display (automatically determined by system)
        self.epf_part_label = QLabel("EPF Contribution Part:")
        self.epf_part_value = QLineEdit()
        self.epf_part_value.setReadOnly(True)
        self.epf_part_value.setStyleSheet("background-color: #f0f0f0;")
        
        epf_part_layout = QHBoxLayout()
        epf_part_layout.addWidget(self.epf_part_label)
        epf_part_layout.addWidget(self.epf_part_value)
        epf_layout.addLayout(epf_part_layout)
        
        # EPF explanation label
        self.epf_explanation = QLabel("EPF part is automatically determined based on age, nationality, and citizenship.")
        self.epf_explanation.setStyleSheet("color: #666; font-style: italic; font-size: 10px;")
        epf_layout.addWidget(self.epf_explanation)

        # Read-only EPF election checkboxes (initialized here to avoid missing attribute errors)
        # These are displayed only for informational purposes in the profile view.
        self.epf_before_1998 = QCheckBox("Elected before 1 Aug 1998")
        self.epf_before_1998.setEnabled(False)
        self.epf_after_1998 = QCheckBox("Elected on or after 1 Aug 1998")
        self.epf_after_1998.setEnabled(False)
        self.epf_after_1998_2001 = QCheckBox("Elected on or after 1 Aug 1998 (para 3) / on or after 1 Aug 2001 (para 6)")
        self.epf_after_1998_2001.setEnabled(False)

        epf_layout.addWidget(self.epf_before_1998)
        epf_layout.addWidget(self.epf_after_1998)
        epf_layout.addWidget(self.epf_after_1998_2001)
        
        # Add to fields dictionary
        self.fields["Elected before 1 Aug 1998"] = self.epf_before_1998
        self.fields["Elected on or after 1 Aug 1998"] = self.epf_after_1998
        self.fields["Elected on or after 1 Aug 1998 under paragraph 3 / on or after 1 Aug 2001 under paragraph 6 of First Schedule"] = self.epf_after_1998_2001
        
        personal_form.addRow(self.epf_election_group)
        self.epf_election_group.hide()  # Hidden by default

        left_layout.addWidget(personal_groupbox)
        
        # Add Contact Info to left column
        contact_groupbox = QGroupBox("Contact Information")
        contact_form = QFormLayout()
        contact_groupbox.setLayout(contact_form)
        
        contact_fields = [
            ("Email", QLineEdit()),
            ("Phone", QLineEdit()),
            ("Address", QLineEdit()),
            ("City", QLineEdit()),
            ("State", self.combo([
                "Johor", "Kedah", "Kelantan", "Melaka", "Negeri Sembilan", "Pahang", "Perak", "Perlis",
                "Pulau Pinang", "Sabah", "Sarawak", "Selangor", "Terengganu", "Kuala Lumpur", "Labuan", "Putrajaya"
            ])),
            ("Zipcode", QLineEdit())
        ]
        
        for label, widget in contact_fields:
            contact_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget
            # Make all fields read-only
            if hasattr(widget, 'setReadOnly'):
                widget.setReadOnly(True)
            elif hasattr(widget, 'setEnabled'):
                widget.setEnabled(False)

        left_layout.addWidget(contact_groupbox)
        
        # --- RIGHT COLUMN: Employment Information ---
        
        # Employment Details
        employment_groupbox = QGroupBox("Employment Information")
        employment_form = QFormLayout()
        employment_groupbox.setLayout(employment_form)
        
        employment_fields = [
            ("Employee ID", QLineEdit()),
            ("Role", self.combo(["employee", "admin"])),
            ("Job Title", self.combo(["Manager", "Executive", "Intern", "Supervisor", "Developer", "Analyst"])),
            ("Department", self.combo(["HR", "IT", "Finance", "Sales", "Marketing", "Engineering", "Admin"])),
            ("Status", self.combo(["Active", "Inactive", "Resigned", "Terminated", "Suspended", "Retired"])),
            ("Employment Type", self.combo(["Full-time", "Part-time", "Contract"])),
            ("Date Joined", self.date_edit()),
        ]
        
        for label, widget in employment_fields:
            employment_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget
            # Make all fields read-only
            if hasattr(widget, 'setReadOnly'):
                widget.setReadOnly(True)
            elif hasattr(widget, 'setEnabled'):
                widget.setEnabled(False)

        right_layout.addWidget(employment_groupbox)
        
        # Education
        education_groupbox = QGroupBox("Education")
        education_form = QFormLayout()
        education_groupbox.setLayout(education_form)
        
        education_fields = [
            ("Qualification", self.combo(["SPM", "STPM", "Diploma", "Degree", "Master", "PhD"])),
            ("Institution", QLineEdit()),
            ("Graduation Year", self.date_edit(format="yyyy"))
        ]
        
        for label, widget in education_fields:
            education_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget
            # Make all fields read-only
            if hasattr(widget, 'setReadOnly'):
                widget.setReadOnly(True)
            elif hasattr(widget, 'setEnabled'):
                widget.setEnabled(False)
            
        right_layout.addWidget(education_groupbox)
        
        # Emergency Contact
        emergency_groupbox = QGroupBox("Emergency Contact")
        emergency_form = QFormLayout()
        emergency_groupbox.setLayout(emergency_form)
        
        emergency_fields = [
            ("Contact Name", QLineEdit()),
            ("Relation", self.combo(["Parent", "Spouse", "Sibling", "Friend", "Colleague", "Other"])),
            ("Emergency Phone", QLineEdit())
        ]
        
        for label, widget in emergency_fields:
            emergency_form.addRow(QLabel(label + ":"), widget)
            self.fields[label] = widget
            # Make all fields read-only
            if hasattr(widget, 'setReadOnly'):
                widget.setReadOnly(True)
            elif hasattr(widget, 'setEnabled'):
                widget.setEnabled(False)
            
        right_layout.addWidget(emergency_groupbox)
        
        # Add both columns to main horizontal layout
        main_horizontal_layout.addWidget(left_column)
        main_horizontal_layout.addWidget(right_column)
        
        # Add main horizontal layout to content layout
        self.content_layout.addLayout(main_horizontal_layout)

        # --- Show/hide logic for citizenship, nationality, and EPF election fields ---
        def nationality_changed():
            nat = self.fields["Nationality"].text().strip().lower()
            if nat in ("malaysia", "malaysian"):
                self.epf_election_group.show()
                self.update_epf_options_visibility()
            else:
                self.epf_election_group.hide()

        def citizenship_changed(value):
            value = value.strip().lower()
            if value in ("permanent resident", "non-citizen"):
                self.epf_election_group.show()
                self.reset_epf_fields()
                self.update_epf_options_visibility()
            else:
                self.epf_election_group.hide()
                self.reset_epf_fields()

        def dob_changed():
            """Update EPF options when date of birth changes"""
            self.calculate_age()
            citizenship_value = self.fields["Citizenship"].currentText().strip().lower()
            if citizenship_value in ("citizen", "permanent resident", "non-citizen"):
                self.update_epf_options_visibility()

        # Connect signals (read-only, but still functional for display logic)
        self.fields["Nationality"].textChanged.connect(nationality_changed)
        self.fields["Citizenship"].currentTextChanged.connect(citizenship_changed)
        self.fields["Date of Birth"].dateChanged.connect(dob_changed)

    def reset_epf_fields(self):
        """Reset EPF part display"""
        if hasattr(self, 'epf_part_value'):
            self.epf_part_value.setText("Not determined")

    def update_epf_options_visibility(self):
        """Update EPF part display based on employee's details"""
        try:
            # EPF part is automatically determined by the system
            # This function is kept for compatibility but doesn't need to do anything
            # since EPF part is loaded from the database
            pass
        except Exception as e:
            print(f"DEBUG: Error updating EPF options visibility: {str(e)}")
            print(f"DEBUG: Error updating EPF options visibility: {str(e)}")

    def show_epf_info(self, text):
        """Helper method to show EPF information text"""
        if not hasattr(self, 'epf_info_label'):
            self.epf_info_label = QLabel()
            self.epf_info_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px; background-color: #ecf0f1; border-radius: 3px;")
            self.epf_election_group.layout().addWidget(self.epf_info_label)
        self.epf_info_label.setText(text)
        self.epf_info_label.show()
        self.epf_election_group.show()

    def create_buttons(self):
        btn_layout = QHBoxLayout()
        # Only show view/export buttons - no editing allowed
        self.download_pdf_btn = QPushButton("Download PDF")
        self.print_btn = QPushButton("Print Profile")
        btn_layout.addStretch()
        btn_layout.addWidget(self.download_pdf_btn)
        btn_layout.addWidget(self.print_btn)

        self.download_pdf_btn.clicked.connect(self.download_pdf)
        self.print_btn.clicked.connect(self.print_profile)

        self.content_layout.addLayout(btn_layout)

    def combo(self, items):
        combo = QComboBox()
        combo.addItems(items)
        return combo

    def date_edit(self, format="yyyy-MM-dd"):
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat(format)
        date_edit.setDate(QDate.currentDate())
        return date_edit

    def calculate_age(self):
        dob = self.fields["Date of Birth"].date().toPyDate()
        today = datetime.now(KL_TZ).date()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        self.fields["Age"].setText(f"Age: {age}")

    def create_section(self, title, fields):
        groupbox = QGroupBox(title)
        grid = QGridLayout()
        result = {}
        for i, (label, widget) in enumerate(fields):
            grid.addWidget(QLabel(label + ":"), i, 0)
            grid.addWidget(widget, i, 1)
            result[label] = widget
        groupbox.setLayout(grid)
        self.content_layout.addWidget(groupbox)
        return result

    def load_default_picture(self):
        # Load default profile picture
        if os.path.exists(self.default_avatar_path):
            pixmap = QPixmap(self.default_avatar_path)
            self.picture_label.setPixmap(pixmap.scaled(118, 118, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))
            print(f"DEBUG: Loaded default avatar from {self.default_avatar_path}")
        else:
            print(f"DEBUG: Default avatar not found at {self.default_avatar_path}, creating placeholder")
            self.create_placeholder_image()

    def create_placeholder_image(self):
        # Create a circular placeholder image with user icon
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

    def populate_form(self, data):
        print(f"DEBUG: Populating form with data: {data}")
        self.employee_data = data
        if not data:
            print("DEBUG: No employee data provided, clearing form")
            self.clear_form()
            return

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
            "Qualification": "highest_qualification",
            "Institution": "institution",
            "Graduation Year": "graduation_year",
            "Employee ID": "employee_id",
            "Role": "role",
            "Job Title": "job_title",
            "Department": "department",
            "Employment Type": "employment_type",
            "Date Joined": "date_joined",
            "Status": "status",
            "Contact Name": "emergency_name",
            "Relation": "emergency_relation",
            "Emergency Phone": "emergency_phone",
        }

        for form_field, db_field in field_mappings.items():
            value = data.get(db_field, "")
            widget = self.fields.get(form_field)
            if not widget:
                print(f"DEBUG: No widget found for field {form_field}")
                continue

            print(f"DEBUG: Setting {form_field} to value: {value}")
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
                        widget.setCurrentText(str(value))
                else:
                    widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                # Handle EPF checkbox fields
                widget.setChecked(bool(value))
            elif isinstance(widget, QDateEdit):
                if form_field == "Graduation Year" and value:
                    try:
                        widget.setDate(QDate(int(value), 1, 1))
                    except (ValueError, TypeError):
                        widget.setDate(datetime.now(KL_TZ).date())
                elif value and form_field in ["Date of Birth", "Date Joined"]:
                    try:
                        # Convert the date string to a QDate object
                        dt = datetime.strptime(value, "%Y-%m-%d")  # Adjust format if needed
                        widget.setDate(QDate(dt.year, dt.month, dt.day))
                    except Exception as e:
                        print(f"DEBUG: Failed to parse date for {form_field}: {value} ({e})")
                        widget.setDate(datetime.now(KL_TZ).date())
                elif value:
                    widget.setDate(datetime.now(KL_TZ).date())

        # Handle allowances - extract from JSON object
        allowances_data = data.get("allowances", {})
        if isinstance(allowances_data, dict):
            # Set individual allowance fields from JSON data
            if "Meal Allowance" in self.fields:
                self.fields["Meal Allowance"].setText(str(allowances_data.get("meal", 0.0)))
            if "Transport Allowance" in self.fields:
                self.fields["Transport Allowance"].setText(str(allowances_data.get("transport", 0.0)))
            if "Medical Allowance" in self.fields:
                self.fields["Medical Allowance"].setText(str(allowances_data.get("medical", 0.0)))
            if "Phone Allowance" in self.fields:
                self.fields["Phone Allowance"].setText(str(allowances_data.get("phone", 0.0)))
            if "Other Allowances" in self.fields:
                self.fields["Other Allowances"].setText(str(allowances_data.get("other", 0.0)))
        
        # Handle EPF part display
        epf_part = data.get("epf_part", "")
        if hasattr(self, 'epf_part_value'):
            if epf_part:
                epf_display = f"Part {epf_part.upper()}" if epf_part else "Not determined"
                self.epf_part_value.setText(epf_display)
            else:
                self.epf_part_value.setText("Not determined")
                    
        # Show EPF section if employee has citizenship status
        citizenship_value = self.fields["Citizenship"].currentText()
        if citizenship_value.lower() in ("citizen", "permanent resident", "non-citizen"):
            self.epf_election_group.show()
        else:
            self.epf_election_group.hide()
        
        # Load profile picture if available
        profile_url = data.get("profile_picture_url") or data.get("photo_url")
        if profile_url:
            try:
                response = urlopen(profile_url)
                image_data = response.read()
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                
                # Create circular clipped version
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
                print(f"DEBUG: Loaded profile picture from URL: {profile_url}")
            except Exception as e:
                print(f"DEBUG: Failed to load profile picture from URL: {e}")
                self.load_default_picture()
        else:
            self.load_default_picture()

    def clear_form(self):
        """Clear all form fields"""
        for field_name, widget in self.fields.items():
            if isinstance(widget, QLineEdit):
                widget.clear()
            elif isinstance(widget, QComboBox):
                widget.setCurrentIndex(0)
            elif isinstance(widget, QCheckBox):
                widget.setChecked(False)
            elif isinstance(widget, QDateEdit):
                widget.setDate(QDate.currentDate())

    # Note: Submit and Cancel methods removed - this tab is read-only for employees

    def download_pdf(self):
        try:
            # Similar PDF generation as in dialog
            QMessageBox.information(self, "PDF", "PDF download functionality to be implemented.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate PDF: {str(e)}")

    def print_profile(self):
        try:
            # Similar print functionality as in dialog
            QMessageBox.information(self, "Print", "Print functionality to be implemented.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print profile: {str(e)}")

    def load_employee_data(self):
        """Load current employee data from database"""
        if self.user_email:
            try:
                # Get employee data from Supabase
                response = supabase.table("employees").select("*").eq("email", self.user_email).execute()
                if response.data:
                    self.populate_form(response.data[0])
                    print(f"DEBUG: Loaded employee data for {self.user_email}")
                else:
                    print(f"DEBUG: No employee data found for {self.user_email}")
            except Exception as e:
                print(f"DEBUG: Error loading employee data: {str(e)}")
                QMessageBox.critical(self, "Error", f"Failed to load employee data: {str(e)}")
