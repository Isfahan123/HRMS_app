from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QHeaderView
from PyQt5.QtCore import Qt
from services.supabase_service import get_employee_history
from datetime import datetime

class EmployeeHistoryDialog(QDialog):
    def __init__(self, employee_id: str, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.setWindowTitle('Employee History')
        self.setModal(True)
        self.setMinimumSize(700, 400)
        self.page = 0
        self.per_page = 50
        self.init_ui()
        self.load_page()

    def init_ui(self):
        layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f'History for: {self.employee_id}'))
        header_layout.addStretch()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Filter (client-side)')
        self.search_box.textChanged.connect(self.apply_filter)
        header_layout.addWidget(self.search_box)
        layout.addLayout(header_layout)

        # Map columns to the actual employee_history schema
        # Fields: created_at, company, job_title, position, department, start_date, end_date, notes
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(['When', 'Company', 'Job Title', 'Position', 'Department', 'Start', 'End', 'Notes'])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        # Allow sorting by clicking column headers
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.prev_btn = QPushButton('Previous')
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton('Next')
        self.next_btn.clicked.connect(self.next_page)
        self.refresh_btn = QPushButton('Refresh')
        self.refresh_btn.clicked.connect(self.load_page)
        btn_layout.addStretch()
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.prev_btn)
        btn_layout.addWidget(self.next_btn)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def load_page(self):
        rows = get_employee_history(self.employee_id, limit=self.per_page, offset=self.page * self.per_page)
        self._rows = rows or []
        self.apply_filter()

    def apply_filter(self):
        q = self.search_box.text().strip().lower()
        filtered = [r for r in self._rows if q in (str(r).lower())]
        self.table.setRowCount(len(filtered))
        for i, r in enumerate(filtered):
            when = r.get('created_at') or r.get('updated_at') or ''
            company = r.get('company') or ''
            job_title = r.get('job_title') or ''
            position = r.get('position') or ''
            department = r.get('department') or ''
            start_date = r.get('start_date') or ''
            end_date = r.get('end_date') or ''
            notes = r.get('notes') or r.get('admin_notes') or ''
            # Format minimal date strings if needed
            def _fmt(d):
                try:
                    if not d:
                        return ''
                    # If already a string, try to parse ISO-like
                    if isinstance(d, str):
                        try:
                            dt = datetime.fromisoformat(d)
                            return dt.strftime('%Y-%m-%d %H:%M')
                        except Exception:
                            return d
                    if isinstance(d, (int, float)):
                        return str(d)
                    # Assume it's a date/datetime object
                    return d.strftime('%Y-%m-%d')
                except Exception:
                    return ''

            self.table.setItem(i, 0, QTableWidgetItem(_fmt(when)))
            self.table.setItem(i, 1, QTableWidgetItem(str(company)))
            self.table.setItem(i, 2, QTableWidgetItem(str(job_title)))
            self.table.setItem(i, 3, QTableWidgetItem(str(position)))
            self.table.setItem(i, 4, QTableWidgetItem(str(department)))
            self.table.setItem(i, 5, QTableWidgetItem(_fmt(start_date)))
            self.table.setItem(i, 6, QTableWidgetItem(_fmt(end_date)))
            self.table.setItem(i, 7, QTableWidgetItem(str(notes)))

    def next_page(self):
        self.page += 1
        self.load_page()

    def prev_page(self):
        if self.page > 0:
            self.page -= 1
            self.load_page()
