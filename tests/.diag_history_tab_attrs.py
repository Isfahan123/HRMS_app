import sys
from PyQt5.QtWidgets import QApplication

from gui.employee_history_tab import EmployeeHistoryTab

app = QApplication([])
try:
    w = EmployeeHistoryTab()
    print('attrs:', sorted([a for a in dir(w) if not a.startswith('_')]))
    print('has header_label?', hasattr(w, 'header_label'))
    if hasattr(w, 'header_label'):
        print('header_label text:', w.header_label.text())
finally:
    app.quit()
