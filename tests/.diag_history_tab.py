import sys
from PyQt5.QtWidgets import QApplication

try:
    from gui.employee_history_tab import EmployeeHistoryTab
except Exception as e:
    print('IMPORT_FAIL', e)
    raise

app = QApplication([])
try:
    w = EmployeeHistoryTab()
    print('Created EmployeeHistoryTab')
    print('job_title count:', w.job_title_combo.count())
    print('position count:', w.position_combo.count())
    print('department count:', w.department_combo.count())
    print('employment_type count:', w.employment_type_combo.count())
    print('header label:', w.header_label.text())
    print('tabs count:', w.tabs.count())
except Exception as e:
    print('ERROR', e)
finally:
    app.quit()
