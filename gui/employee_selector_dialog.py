from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QLabel
from PyQt5.QtCore import Qt
from services.supabase_service import supabase


class EmployeeSelectorDialog(QDialog):
    """Modal dialog presenting a simple searchable list of employees.

    Returns the selected employee dict via the `selected` attribute after accept().
    """
    def __init__(self, parent=None, prefilter=None):
        super().__init__(parent)
        self.setWindowTitle('Select employee')
        self.resize(700, 400)
        self.selected = None
        self.prefilter = prefilter or ''

        layout = QVBoxLayout(self)

        header = QLabel('Search employees by name or email')
        layout.addWidget(header)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText('Type to search (name or email)')
        self.search_input.setText(self.prefilter)
        search_btn = QPushButton('Search')
        search_btn.clicked.connect(self.on_search)
        search_row.addWidget(self.search_input)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Name', 'Employee ID', 'Email', 'Department'])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemDoubleClicked.connect(self.on_double)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.ok_btn = QPushButton('OK')
        self.ok_btn.clicked.connect(self.on_ok)
        self.cancel_btn = QPushButton('Cancel')
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.ok_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        # initial load
        self.load_employees(self.prefilter)

    def on_search(self):
        self.load_employees(self.search_input.text().strip())

    def load_employees(self, q=''):
        try:
            query = supabase.table('employees').select('*')
            if q:
                q = q.replace("'", "")
                query = query.or_(f"full_name.ilike.%{q}%,email.ilike.%{q}%")
            resp = query.execute()
            rows = resp.data or []
        except Exception:
            rows = []

        self.table.setRowCount(0)
        for i, emp in enumerate(rows):
            self.table.insertRow(i)
            name = emp.get('full_name') or ''
            eid = emp.get('employee_id') or emp.get('id') or ''
            email = emp.get('email') or ''
            dept = emp.get('department') or ''
            it0 = QTableWidgetItem(str(name))
            it0.setData(Qt.UserRole, emp)
            self.table.setItem(i, 0, it0)
            self.table.setItem(i, 1, QTableWidgetItem(str(eid)))
            self.table.setItem(i, 2, QTableWidgetItem(str(email)))
            self.table.setItem(i, 3, QTableWidgetItem(str(dept)))

    def current_selected_employee(self):
        sel = self.table.currentRow()
        if sel == -1:
            return None
        item = self.table.item(sel, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def on_double(self, item):
        emp = item.data(Qt.UserRole)
        if emp:
            self.selected = emp
            self.accept()

    def on_ok(self):
        emp = self.current_selected_employee()
        if emp:
            self.selected = emp
            self.accept()
        else:
            # nothing selected: noop
            return
