from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QListWidget, QFormLayout, QMessageBox, QComboBox, QTabWidget

# Training/Course Record Tab (Admin)
class AdminTrainingCourseTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # Submit subtab
        submit_tab = QWidget()
        submit_layout = QVBoxLayout()
        submit_layout.addWidget(QLabel("Submit Training/Course Record for Employee"))
        form_layout = QFormLayout()
        self.employee_select = QComboBox()
        self.employee_select.addItem("Select Employee")
        # TODO: Populate with real employee list
        self.employee_select.addItems(["E001", "E002", "E003"])
        self.course_name_input = QLineEdit()
        self.course_date_input = QLineEdit()
        self.course_desc_input = QTextEdit()
        form_layout.addRow("Employee:", self.employee_select)
        form_layout.addRow("Course Name:", self.course_name_input)
        form_layout.addRow("Date:", self.course_date_input)
        form_layout.addRow("Description:", self.course_desc_input)
        submit_layout.addLayout(form_layout)
        submit_btn = QPushButton("Submit Record")
        submit_btn.clicked.connect(self.submit_record)
        submit_layout.addWidget(submit_btn)
        submit_tab.setLayout(submit_layout)

        # View subtab
        view_tab = QWidget()
        view_layout = QVBoxLayout()
        view_layout.addWidget(QLabel("View All Training/Course Records"))
        self.record_list = QListWidget()
        view_layout.addWidget(self.record_list)
        view_tab.setLayout(view_layout)

        self.tab_widget.addTab(submit_tab, "Submit Record")
        self.tab_widget.addTab(view_tab, "View Records")
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def submit_record(self):
        employee = self.employee_select.currentText()
        name = self.course_name_input.text()
        date = self.course_date_input.text()
        desc = self.course_desc_input.toPlainText()
        if employee == "Select Employee" or not name or not date:
            QMessageBox.warning(self, "Input Error", "Employee, course name, and date are required.")
            return
        self.record_list.addItem(f"{employee}: {name} ({date}): {desc}")
        self.course_name_input.clear()
        self.course_date_input.clear()
        self.course_desc_input.clear()

# Overseas Work/Trip Record Tab (Admin)
class AdminOverseasWorkTripTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        self.tab_widget = QTabWidget()

        # Submit subtab
        submit_tab = QWidget()
        submit_layout = QVBoxLayout()
        submit_layout.addWidget(QLabel("Submit Overseas Work/Trip Record for Employee"))
        form_layout = QFormLayout()
        self.employee_select = QComboBox()
        self.employee_select.addItem("Select Employee")
        # TODO: Populate with real employee list
        self.employee_select.addItems(["E001", "E002", "E003"])
        self.trip_location_input = QLineEdit()
        self.trip_date_input = QLineEdit()
        self.trip_purpose_input = QTextEdit()
        form_layout.addRow("Employee:", self.employee_select)
        form_layout.addRow("Location:", self.trip_location_input)
        form_layout.addRow("Date:", self.trip_date_input)
        form_layout.addRow("Purpose:", self.trip_purpose_input)
        submit_layout.addLayout(form_layout)
        submit_btn = QPushButton("Submit Record")
        submit_btn.clicked.connect(self.submit_record)
        submit_layout.addWidget(submit_btn)
        submit_tab.setLayout(submit_layout)

        # View subtab
        view_tab = QWidget()
        view_layout = QVBoxLayout()
        view_layout.addWidget(QLabel("View All Overseas Work/Trip Records"))
        self.record_list = QListWidget()
        view_layout.addWidget(self.record_list)
        view_tab.setLayout(view_layout)

        self.tab_widget.addTab(submit_tab, "Submit Record")
        self.tab_widget.addTab(view_tab, "View Records")
        layout.addWidget(self.tab_widget)
        self.setLayout(layout)

    def submit_record(self):
        employee = self.employee_select.currentText()
        location = self.trip_location_input.text()
        date = self.trip_date_input.text()
        purpose = self.trip_purpose_input.toPlainText()
        if employee == "Select Employee" or not location or not date:
            QMessageBox.warning(self, "Input Error", "Employee, location, and date are required.")
            return
        self.record_list.addItem(f"{employee}: {location} ({date}): {purpose}")
        self.trip_location_input.clear()
        self.trip_date_input.clear()
        self.trip_purpose_input.clear()
