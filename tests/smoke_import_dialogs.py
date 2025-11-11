# smoke import test for employee dialogs
import sys, os
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
try:
    from gui.employee_profile_dialog import EmployeeProfileDialog
    from gui.employee_history_tab import EmployeeHistoryTab
    print('Imported EmployeeProfileDialog and EmployeeHistoryTab OK')
except Exception as e:
    print('Import failed:', e)
    raise
