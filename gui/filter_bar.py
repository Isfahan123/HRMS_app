from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton
from PyQt5.QtCore import Qt

class ProfileFilterBar(QWidget):
    """Reusable filter/search bar for Admin Profile tab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "filter-container")
        self.setFixedHeight(35)

        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(8, 8, 8, 8)

        # Search
        self.search_label = QLabel("🔍 Search:")
        self.search_label.setFixedWidth(50)
        self.search_label.setMaximumHeight(25)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, email, or employee ID...")
        self.search_input.setProperty("class", "search")
        self.search_input.setFixedHeight(25)
        self.search_input.setMinimumWidth(280)
        self.search_input.setMaximumWidth(350)
        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)

        # Department
        self.dept_label = QLabel("🏢 Dept:")
        self.dept_label.setFixedWidth(50)
        self.dept_label.setMaximumHeight(25)
        self.department_filter = QComboBox()
        self.department_filter.addItem("All Departments")
        self.department_filter.setFixedHeight(25)
        self.department_filter.setMinimumWidth(140)
        self.department_filter.setMaximumWidth(180)
        layout.addWidget(self.dept_label)
        layout.addWidget(self.department_filter)

        # Religion
        self.religion_label = QLabel("🔌 Rel:")
        self.religion_label.setFixedWidth(40)
        self.religion_label.setMaximumHeight(25)
        self.religion_filter = QComboBox()
        self.religion_filter.addItem("All Religions")
        self.religion_filter.setFixedHeight(25)
        self.religion_filter.setMinimumWidth(140)
        self.religion_filter.setMaximumWidth(180)
        layout.addWidget(self.religion_label)
        layout.addWidget(self.religion_filter)

        # Clear & Refresh
        self.clear_btn = QPushButton("🔄 Clear Filters")
        self.clear_btn.setProperty("class", "secondary")
        layout.addWidget(self.clear_btn)

        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.setProperty("class", "secondary")
        layout.addWidget(self.refresh_btn)

        layout.addStretch()
