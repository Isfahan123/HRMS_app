import traceback
from PyQt5.QtWidgets import QApplication

try:
    app = QApplication([])
    try:
        from gui.employee_history_tab import EmployeeHistoryTab
        try:
            w = EmployeeHistoryTab()
            print('CONSTRUCTED OK')
        except Exception:
            print('ERROR during EmployeeHistoryTab().__init__:')
            traceback.print_exc()
    except Exception:
        print('ERROR importing EmployeeHistoryTab:')
        traceback.print_exc()
except Exception:
    print('ERROR creating QApplication:')
    traceback.print_exc()
finally:
    try:
        app.quit()
    except Exception:
        pass
