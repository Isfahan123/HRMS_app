from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QMessageBox, QHeaderView, QLineEdit, QComboBox, QLabel, QFileDialog, QScrollArea
from gui.filter_bar import ProfileFilterBar
from gui.actions_bar import ProfileActionsBar
from services.supabase_service import supabase, delete_employee, convert_utc_to_kl
from gui.employee_profile_dialog import EmployeeProfileDialog
from PyQt5.QtCore import Qt, QByteArray, pyqtSignal
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath, QFont, QColor
from datetime import datetime
import pytz
import re
import os
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from PyQt5.QtGui import QTextDocument
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QDesktopServices

class AdminProfileTab(QWidget):
    # Emitted when a row/employee is selected in the table
    employee_selected = pyqtSignal(object)
    def __init__(self, stacked_widget):
        super().__init__()
        print("DEBUG: AdminProfileTab initialization started")
        self.stacked_widget = stacked_widget
        self.sort_column = None
        self.sort_order = Qt.AscendingOrder
        self.KL_TZ = pytz.timezone('Asia/Kuala_Lumpur')
        self.default_avatar_path = os.path.join("assets", "default_avatar.png")
        
        # Track open employee profile dialogs for refreshing
        self.open_profile_dialogs = {}  # employee_id -> dialog reference
        
        self.init_ui()
        print("DEBUG: AdminProfileTab initialization completed")

    def init_ui(self):
        # Create main scroll area for the entire page
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        main_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Content widget that will be scrollable
        content_widget = QWidget()
        content_widget.setObjectName("scrollContent")

        layout = QVBoxLayout(content_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title Section
        title_label = QLabel("👥 Employee Management")
        title_label.setProperty("class", "heading")
        subtitle_label = QLabel("Manage employee profiles, documents, and information")
        subtitle_label.setProperty("class", "subheading")
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)

        # Filter and Search (extracted component)
        self.filter_bar = ProfileFilterBar()
        layout.addWidget(self.filter_bar)
        # Map legacy attributes to new widget controls for compatibility
        self.search_input = self.filter_bar.search_input
        self.department_filter = self.filter_bar.department_filter
        self.religion_filter = self.filter_bar.religion_filter
        self.clear_filters_btn = self.filter_bar.clear_btn
        self.refresh_employees_btn = self.filter_bar.refresh_btn
        # Wire signals
        self.search_input.textChanged.connect(self.load_employees)
        self.department_filter.currentIndexChanged.connect(self.load_employees)
        self.religion_filter.currentIndexChanged.connect(self.load_employees)
        self.clear_filters_btn.clicked.connect(self.clear_filters)
        self.refresh_employees_btn.clicked.connect(self.load_employees)

        # Actions (extracted component)
        self.actions_bar = ProfileActionsBar()
        layout.addWidget(self.actions_bar)
        # Map legacy attributes
        self.add_employee_btn = self.actions_bar.add_btn
        self.download_all_btn = self.actions_bar.download_all_btn
        self.print_all_btn = self.actions_bar.print_all_btn
        # Wire actions
        self.add_employee_btn.clicked.connect(self.add_employee)
        self.download_all_btn.clicked.connect(self.download_all_pdfs)
        self.print_all_btn.clicked.connect(self.print_all_profiles)

        # Employee table with modern styling - Make it much larger
        table_card = QWidget()
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(8, 8, 8, 8)
        table_layout.setSpacing(4)

        # Table header
        table_header = QLabel("📊 Employee Directory")
        table_layout.addWidget(table_header)

        self.table = QTableWidget()
        self.table.setColumnCount(11)  # Adjusted column count to include Work Status
        self.table.setHorizontalHeaderLabels([
            "👤 Profile",
            "📝 Name ↑↓",
            "🆔 Employee ID",
            "📧 Email ↑↓",
            "🏢 Department",
            "💼 Job Title",
            "📊 Status",
            "🏷️ Work Status",
            "🕌 Religion",
            "📄 Resume",
            "⚙️ Actions",
        ])

        # Modern table styling with better readability
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.horizontalHeader().sectionClicked.connect(self.sort_table)

        # Set proper column widths and table sizing
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)

        # Set flexible column widths for better alignment
        self.table.setColumnWidth(0, 80)  # Profile picture
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Name - flexible
        self.table.setColumnWidth(2, 120)  # Employee ID
        header.setSectionResizeMode(3, QHeaderView.Stretch)  # Email - flexible
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # Department - flexible
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # Job Title - flexible
        self.table.setColumnWidth(6, 100)  # Status
        self.table.setColumnWidth(7, 120)  # Religion
        self.table.setColumnWidth(8, 100)  # Resume
        self.table.setColumnWidth(9, 120)  # Actions

        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)  # We handle sorting manually
        self.table.setMinimumHeight(500)
        # Emit selected employee when a row is clicked
        self.table.itemClicked.connect(self.on_table_item_clicked)

        table_layout.addWidget(self.table)
        layout.addWidget(table_card)

        # Set the content widget in the scroll area
        main_scroll.setWidget(content_widget)

        # Create the main layout for this widget (fix layout conflict)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(main_scroll)
        self.setLayout(main_layout)

        # Temporarily disconnect signals during initialization to prevent premature loading
        try:
            self.search_input.textChanged.disconnect()
            self.department_filter.currentIndexChanged.disconnect()
            self.religion_filter.currentIndexChanged.disconnect()
        except Exception:
            pass

        # Load data
        self.load_departments()
        self.load_employees()

        # Reconnect signals after initialization
        self.search_input.textChanged.connect(self.load_employees)
        self.department_filter.currentIndexChanged.connect(self.load_employees)
        self.religion_filter.currentIndexChanged.connect(self.load_employees)

    def load_departments(self):
        try:
            response = supabase.table("employees").select("department").execute()
            if not response.data:
                # print("DEBUG: No employees found when loading departments")
                # Don't show warning popup - this is normal during initial load
                self.department_filter.clear()
                self.department_filter.addItem("All Departments")
                return
            departments = set(employee["department"] for employee in response.data if employee["department"])
            self.department_filter.clear()
            self.department_filter.addItem("All Departments")
            self.department_filter.addItems(sorted(departments))
            # print(f"DEBUG: Loaded {len(departments)} departments from {len(response.data)} employees")
        except Exception as e:
            # print(f"DEBUG: Error loading departments: {str(e)}")
            if "connection" in str(e).lower():
                QMessageBox.critical(self, "Error", "Network error: Unable to connect to the database.")
            else:
                QMessageBox.critical(self, "Error", f"Failed to load departments: {str(e)}")

    def sort_table(self, logical_index):
        if logical_index in [0, 7]:  # Skip Profile Picture and Actions
            return
        if self.sort_column == logical_index:
            self.sort_order = Qt.DescendingOrder if self.sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self.sort_column = logical_index
            self.sort_order = Qt.AscendingOrder
        self.load_employees()

    def on_table_item_clicked(self, item):
        """Emit the full employee dict when a row item with UserRole data (attached to the name column) is clicked."""
        try:
            emp = None
            # If the clicked item has user data with the employee dict, use that
            try:
                data = item.data(Qt.UserRole)
                if isinstance(data, dict):
                    emp = data
            except Exception:
                emp = None

            # If not found, try to find the name cell in the same row
            if not emp:
                row = item.row()
                name_item = self.table.item(row, 1)  # full_name column
                if name_item:
                    try:
                        data = name_item.data(Qt.UserRole)
                        if isinstance(data, dict):
                            emp = data
                    except Exception:
                        emp = None

            if emp:
                # Emit the signal with the employee dict
                self.employee_selected.emit(emp)
        except Exception as e:
            print(f"DEBUG: Error emitting employee_selected: {e}")

    def load_employees(self):
        try:
            # Build query
            query = supabase.table("employees").select("*")
            
            # Apply search filter
            search_text = self.search_input.text().strip()
            if search_text:
                search_text = re.sub(r'[^\w\s@.-]', '', search_text).lower()
                if len(search_text) > 100:
                    QMessageBox.warning(self, "Invalid Input", "Search query is too long (max 100 characters).")
                    return
                query = query.or_(f"full_name.ilike.%{search_text}%,email.ilike.%{search_text}%")

            # Apply department filter
            department = self.department_filter.currentText()
            if department != "All Departments":
                query = query.eq("department", department)
                
            # Apply religion filter
            religion = self.religion_filter.currentText()
            if religion != "All Religions":
                query = query.eq("religion", religion)

            response = query.execute()
            if not response.data:
                # print("DEBUG: No employees found matching current filters")
                self.table.setRowCount(0)
                # Only show message if there are actual filters applied
                search_text = self.search_input.text().strip()
                department = self.department_filter.currentText()
                religion = self.religion_filter.currentText()
                if search_text or (department and department != "All Departments") or (religion and religion != "All Religions"):
                    QMessageBox.information(self, "Info", "No employees found matching the criteria.")
                return
            employees = response.data
            # print(f"DEBUG: Fetched {len(employees)} employees")

            # Sort employees
            if self.sort_column is not None:
                sort_key = ["full_name", "employee_id", "email", "department", "job_title", "status"][self.sort_column - 1]
                employees.sort(key=lambda x: str(x.get(sort_key, "")).lower(), 
                              reverse=self.sort_order == Qt.DescendingOrder)

            self.table.setRowCount(len(employees))
            self.table.setColumnCount(11)
            self.table.setHorizontalHeaderLabels([
                "Profile Picture",
                "Full Name ↑↓", 
                "Employee ID", 
                "NRIC",
                "Email ↑↓", 
                "Department", 
                "Job Title", 
                "Status", 
                "Work Status",
                "Resume",
                "Actions"
            ])

            header = self.table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
            self.table.setColumnWidth(0, 70)
            for i in range(1, 8):  # Updated to include Status column (now column 7)
                header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
            # Resume and Actions columns will auto-size
            header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Resume
            header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Actions

            self.table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
            self.table.verticalHeader().setDefaultSectionSize(70)  # Increased to 70 for much better text fitting

            for row, employee in enumerate(employees):
                # Profile Picture with proper sizing
                photo_widget = QWidget()
                photo_layout = QHBoxLayout(photo_widget)
                photo_layout.setContentsMargins(5, 5, 5, 5)
                photo_layout.setAlignment(Qt.AlignCenter)
                
                photo_label = QLabel()
                photo_label.resize(60, 60)  # Initial size; allow resizing
                photo_label.setAlignment(Qt.AlignCenter)
                photo_label.setScaledContents(False)  # Prevent distortion
                photo_label

                if employee.get("photo_url"):
                    photo_url = employee["photo_url"]
                    parsed_url = urlparse(photo_url)
                    if parsed_url.scheme in ("http", "https"):
                        try:
                            response = urlopen(photo_url)
                            image_data = response.read()
                            pixmap = QPixmap()
                            pixmap.loadFromData(QByteArray(image_data))
                            if not pixmap.isNull():
                                # Create circular image with proper scaling
                                path = QPainterPath()
                                path.addEllipse(0, 0, 58, 58)
                                scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                                clipped_pixmap = QPixmap(60, 60)
                                clipped_pixmap.fill(Qt.transparent)
                                painter = QPainter(clipped_pixmap)
                                painter.setRenderHint(QPainter.Antialiasing)
                                painter.setClipPath(path)
                                painter.setClipping(True)
                                # Center the image
                                x_offset = (scaled_pixmap.width() - 60) // 2
                                y_offset = (scaled_pixmap.height() - 60) // 2
                                painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
                                painter.end()
                                photo_label.setPixmap(clipped_pixmap)
                            else:
                                self.load_default_picture(photo_label)
                        except (HTTPError, URLError, Exception):
                            self.load_default_picture(photo_label)
                    else:
                        self.load_default_picture(photo_label)
                else:
                    self.load_default_picture(photo_label)

                photo_layout.addWidget(photo_label)
                self.table.setCellWidget(row, 0, photo_widget)

                # Other columns (populate explicit keys only)
                for col, key in enumerate(["full_name", "employee_id", "nric", "email", "department", "job_title", "status", "work_status"], start=1):
                    # Note: `work_status` is a short-term availability field (e.g., On Duty, On Leave)
                    value = employee.get(key, "")
                    if key in ["created_at", "updated_at"] and value:
                        value = convert_utc_to_kl(value)
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(Qt.AlignCenter)
                    # Attach the full employee dict to the name column so handlers can retrieve it
                    if key == "full_name":
                        try:
                            item.setData(Qt.UserRole, employee)
                        except Exception:
                            pass
                    self.table.setItem(row, col, item)
                    
                resume_widget = QWidget()
                resume_layout = QHBoxLayout(resume_widget)
                resume_layout.setContentsMargins(8, 4, 8, 4)
                resume_layout.setSpacing(6)
                resume_layout.setAlignment(Qt.AlignCenter)

                # View Resume button with modern styling
                view_btn = QPushButton("View")
                view_btn.setMinimumSize(60, 40)
                view_btn.setMaximumSize(80, 50)
                view_btn.setToolTip(f"View resume for {employee.get('full_name', 'Employee')}")
                view_btn
                if employee.get("resume_url"):
                    view_btn.clicked.connect(lambda _, url=employee["resume_url"]: self.view_resume(url))
                else:
                    view_btn.setEnabled(False)
                resume_layout.addWidget(view_btn)

                # Download Resume button with modern styling
                download_btn = QPushButton("Download")
                download_btn.setMinimumSize(80, 40)
                download_btn.setMaximumSize(100, 50)
                download_btn.setToolTip(f"Download resume for {employee.get('full_name', 'Employee')}")
                download_btn
                if employee.get("resume_url"):
                    download_btn.clicked.connect(lambda _, url=employee["resume_url"]: self.download_resume(url))
                else:
                    download_btn.setEnabled(False)
                resume_layout.addWidget(download_btn)

                # Resume column is at position 9 (0-indexed)
                self.table.setCellWidget(row, 9, resume_widget)

                # Actions with modern styling
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(8, 4, 8, 4)
                action_layout.setSpacing(6)
                action_layout.setAlignment(Qt.AlignCenter)

                edit_btn = QPushButton("Edit")
                edit_btn.setMinimumSize(60, 40)
                edit_btn.setMaximumSize(80, 50)
                edit_btn.setToolTip(f"Edit profile for {employee.get('full_name', 'Employee')}")
                edit_btn
                edit_btn.clicked.connect(lambda _, emp=employee: self.edit_employee(emp))
                action_layout.addWidget(edit_btn)

                remove_btn = QPushButton("Delete")
                remove_btn.setMinimumSize(60, 40)
                remove_btn.setMaximumSize(80, 50)
                remove_btn.setToolTip(f"Remove {employee.get('full_name', 'Employee')}")
                remove_btn
                remove_btn.clicked.connect(lambda _, emp=employee: self.remove_employee(emp))
                action_layout.addWidget(remove_btn)
                
                # Actions column is at position 10 (0-indexed)
                self.table.setCellWidget(row, 10, action_widget)

        except Exception as e:
            # print(f"DEBUG: Error loading employees: {str(e)}")
            if "connection" in str(e).lower():
                QMessageBox.critical(self, "Error", "Network error: Unable to connect to the database.")
            elif "auth" in str(e).lower():
                QMessageBox.critical(self, "Error", "Authentication error: Please check your credentials.")
            else:
                QMessageBox.critical(self, "Error", f"Operation failed: {str(e)}")

    def load_default_picture(self, label):
        try:
            if os.path.exists(self.default_avatar_path):
                pixmap = QPixmap(self.default_avatar_path)
                if pixmap.isNull():
                    pixmap = self.create_placeholder_image()
            else:
                pixmap = self.create_placeholder_image()
            
            # Create circular clipped image with new 60x60 size
            path = QPainterPath()
            path.addEllipse(0, 0, 58, 58)
            clipped_pixmap = QPixmap(60, 60)
            clipped_pixmap.fill(Qt.transparent)
            painter = QPainter(clipped_pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setClipPath(path)
            painter.setClipping(True)
            scaled_pixmap = pixmap.scaled(60, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            # Center the image
            x_offset = (scaled_pixmap.width() - 60) // 2
            y_offset = (scaled_pixmap.height() - 60) // 2
            painter.drawPixmap(-x_offset, -y_offset, scaled_pixmap)
            painter.end()
            label.setPixmap(clipped_pixmap)
        except Exception as e:
            pixmap = self.create_placeholder_image()
            label.setPixmap(pixmap)

    def create_placeholder_image(self):
        pixmap = QPixmap(60, 60)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#888888"))
        painter.drawEllipse(0, 0, 58, 58)
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 24))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "👤")
        painter.end()
        return pixmap
    
    def load_filters(self):
        try:
            response = supabase.table("employees").select("religion, epf_part").execute()
            if not response.data:
                return

            religions = set(emp["religion"] for emp in response.data if emp.get("religion"))
            self.religion_filter.clear()
            self.religion_filter.addItem("All Religions")
            self.religion_filter.addItems(sorted(religions))

        except Exception as e:
            # print(f"DEBUG: Error loading filters: {str(e)}")
            pass

    def clear_filters(self):
        self.search_input.clear()
        self.department_filter.setCurrentIndex(0)
        self.load_employees()

    def edit_employee(self, employee_data):
        dialog = EmployeeProfileDialog(employee_data=employee_data, parent=self, is_admin=True)
        
        # Track the dialog for potential refreshing
        employee_id = employee_data.get('id') if employee_data else None
        if employee_id:
            self.open_profile_dialogs[employee_id] = dialog
            
            # Connect dialog finished signal to cleanup
            dialog.finished.connect(lambda: self.cleanup_dialog(employee_id))
        
        # connect saved signal so lists refresh when dialog saves
        try:
            dialog.employee_saved.connect(self._on_employee_saved)
        except Exception:
            pass
        if dialog.exec_():
            self.load_employees()
            self.load_departments()

    def add_employee(self):
        dialog = EmployeeProfileDialog(parent=self, is_admin=True)
        
        # For add employee, we don't have an ID yet, so we'll track it differently
        # We could use a temporary key, but since salary history doesn't apply to new employees,
        # we don't need to track this one for salary updates
        
        try:
            dialog.employee_saved.connect(self._on_employee_saved)
        except Exception:
            pass
        if dialog.exec_():
            self.load_employees()
            self.load_departments()
    
    def cleanup_dialog(self, employee_id):
        """Remove dialog reference when dialog is closed"""
        if employee_id in self.open_profile_dialogs:
            del self.open_profile_dialogs[employee_id]

    def _on_employee_saved(self, emp_id):
        """Centralized handler when an employee is saved (refresh lists and notify history tab)."""
        try:
            self.load_employees()
            self.load_departments()
            # notify history tab if present
            try:
                dashboard = self.parent() if self.parent() is not None else None
                if dashboard and hasattr(dashboard, 'employee_history_tab'):
                    try:
                        dashboard.employee_history_tab.load_records()
                        dashboard.employee_history_tab.load_employee_choices()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            pass
    
    def refresh_employee_dialogs(self, employee_id):
        """Refresh employee profile dialog when salary is updated"""
        # Attempt to fetch latest employee row and update employment-related fields
        try:
            if not supabase:
                return
            resp = supabase.table('employees').select('*').eq('id', employee_id).execute()
            latest = None
            if resp and getattr(resp, 'data', None):
                latest = resp.data[0]
        except Exception:
            latest = None

        if employee_id in self.open_profile_dialogs:
            dialog = self.open_profile_dialogs[employee_id]
            if dialog:
                # Refresh salary area as before
                try:
                    if hasattr(dialog, 'refresh_salary_data'):
                        dialog.refresh_salary_data()
                except Exception:
                    pass
                # Conservative employment info update: only overwrite blank fields unless forced
                try:
                    if latest and hasattr(dialog, 'update_employment_info'):
                        dialog.update_employment_info(latest, force=False)
                        print(f"DEBUG: Updated employment info in open dialog for {employee_id}")
                except Exception as e:
                    print(f"DEBUG: Error updating employment info for dialog {employee_id}: {e}")

    def remove_employee(self, employee):
        employee_name = employee.get("full_name", "Unknown")
        employee_id = employee.get("employee_id", "Unknown")
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to delete {employee_name} ({employee_id})?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            result = delete_employee(employee_id)
            if result.get("success"):
                # print(f"DEBUG: Employee {employee_id} deleted successfully")
                QMessageBox.information(self, "Success", "Employee deleted successfully.")
                self.load_employees()
                self.load_departments()
            else:
                error_msg = result.get("error", "Unknown error")
                # print(f"DEBUG: Failed to delete employee {employee_id}: {error_msg}")
                QMessageBox.critical(self, "Error", f"Operation failed: {error_msg}")
    
    def download_resume(self, url):
        try:
            # Prompt the user to select a location to save the file
            file_name = QFileDialog.getSaveFileName(self, "Save Resume", os.path.basename(url), "All Files (*.*)")[0]
            if not file_name:
                return  # User canceled the save dialog

            # Download the file
            response = urlopen(url)
            with open(file_name, "wb") as file:
                file.write(response.read())

            QMessageBox.information(self, "Success", f"Resume downloaded successfully to {file_name}")
        except HTTPError as e:
            QMessageBox.critical(self, "Error", f"Failed to download resume: HTTP Error {e.code}")
        except URLError as e:
            QMessageBox.critical(self, "Error", f"Failed to download resume: {e.reason}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")

    def generate_html_content(self, data):
        return f"""
            <h1 style='text-align: center;'>Employee Profile</h1>
            <h2 style='text-align: center;'>{data.get('full_name', 'N/A')}</h2>
            <h3 style='text-align: center;'>{data.get('email', 'N/A')}</h3>
            <h3>Personal Information</h3>
            <ul>
                <li><strong>Full Name:</strong> {data.get('full_name', 'N/A')}</li>
                <li><strong>Gender:</strong> {data.get('gender', 'N/A')}</li>
                <li><strong>Date of Birth:</strong> {data.get('date_of_birth', 'N/A')}</li>
                <li><strong>Nationality:</strong> {data.get('nationality', 'N/A')}</li>
                <li><strong>Marital Status:</strong> {data.get('marital_status', 'N/A')}</li>
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
                <li><strong>Highest Qualification:</strong> {data.get('highest_qualification', 'N/A')}</li>
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
            <h3>Payroll</h3>
            <ul>
                <li><strong>Basic Salary:</strong> {data.get('basic_salary', 'N/A')}</li>
                <li><strong>Bank Account:</strong> {data.get('bank_account', 'N/A')}</li>
                <li><strong>EPF Number:</strong> {data.get('epf_number', 'N/A')}</li>
                <li><strong>SOCSO Number:</strong> {data.get('socso_number', 'N/A')}</li>
            </ul>
            <h3>Optional Contributions</h3>
            <ul>
                <li><strong>SIP Monthly Amount:</strong> RM {data.get('sip_monthly_amount', '0.00')}</li>
                <li><strong>SIP Percentage:</strong> {data.get('sip_percentage', '0.0')}%</li>
                <li><strong>Additional EPF:</strong> RM {data.get('additional_epf', '0.00')}</li>
                <li><strong>Insurance Premium:</strong> RM {data.get('insurance_premium', '0.00')}</li>
                <li><strong>Other Deductions:</strong> RM {data.get('other_deductions', '0.00')}</li>
            </ul>
            <h3>Emergency Contact</h3>
            <ul>
                <li><strong>Contact Name:</strong> {data.get('emergency_name', 'N/A')}</li>
                <li><strong>Relation:</strong> {data.get('emergency_relation', 'N/A')}</li>
                <li><strong>Emergency Phone:</strong> {data.get('emergency_phone', 'N/A')}</li>
            </ul>
        """

    def download_all_pdfs(self):
        try:
            folder_path = QFileDialog.getExistingDirectory(self, "Select Directory to Save PDFs")
            if not folder_path:
                return

            query = supabase.table("employees").select("*")
            search_text = self.search_input.text().strip()
            if search_text:
                search_text = re.sub(r'[^\w\s@.-]', '', search_text).lower()
                query = query.or_(f"full_name.ilike.%{search_text}%,email.ilike.%{search_text}%")
            department = self.department_filter.currentText()
            if department != "All Departments":
                query = query.eq("department", department)
            response = query.execute()
            employees = response.data

            if not employees:
                QMessageBox.warning(self, "Warning", "No employees found to generate PDFs.")
                return

            for employee in employees:
                file_path = os.path.join(folder_path, f"{employee.get('full_name', 'employee')}_{employee['employee_id']}.pdf")
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(file_path)
                document = QTextDocument()
                document.setHtml(self.generate_html_content(employee))
                document.print_(printer)

            QMessageBox.information(self, "Success", f"PDFs saved to {folder_path}")
        except Exception as e:
            # print(f"DEBUG: Error generating PDFs: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate PDFs: {str(e)}")

    def print_all_profiles(self):
        try:
            query = supabase.table("employees").select("*")
            search_text = self.search_input.text().strip()
            if search_text:
                search_text = re.sub(r'[^\w\s@.-]', '', search_text).lower()
                query = query.or_(f"full_name.ilike.%{search_text}%,email.ilike.%{search_text}%")
            department = self.department_filter.currentText()
            if department != "All Departments":
                query = query.eq("department", department)
            response = query.execute()
            employees = response.data

            if not employees:
                QMessageBox.warning(self, "Warning", "No employees found to print.")
                return

            printer = QPrinter(QPrinter.HighResolution)
            dialog = QPrintDialog(printer, self)
            if dialog.exec_() == QPrintDialog.Accepted:
                for employee in employees:
                    document = QTextDocument()
                    document.setHtml(self.generate_html_content(employee))
                    document.print_(printer)
                QMessageBox.information(self, "Success", "All profiles sent to printer.")
        except Exception as e:
            # print(f"DEBUG: Error printing profiles: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to print profiles: {str(e)}")

    def view_resume(self, url):
        try:
            # Open the URL in the default browser or PDF viewer
            QDesktopServices.openUrl(QUrl(url))
        except Exception as e:
            # print(f"DEBUG: Failed to open resume URL: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to open resume: {str(e)}")