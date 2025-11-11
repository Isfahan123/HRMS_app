import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import sys
# ensure project root is on sys.path so `gui` package can be imported
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
from PyQt5.QtWidgets import QApplication
from gui.employee_history_tab import EmployeeHistoryTab

app = QApplication.instance() or QApplication([])
# instantiate offscreen
print('Instantiating EmployeeHistoryTab...')
tab = EmployeeHistoryTab(None, employee_id='00000000-0000-0000-0000-000000000000')
print('Done')
# Inspect widget attributes
print('Has job_title_combo:', hasattr(tab, 'job_title_combo'))
print('Has func_group_combo:', hasattr(tab, 'func_group_combo'))
print('Has department_combo:', hasattr(tab, 'department_combo'))

# Show counts
print('job_title count:', tab.job_title_combo.count())
print('department count:', tab.department_combo.count())

# Try setting Department to IT and observe functional groups
try:
    tab.department_combo.setCurrentText('IT')
    print('Set department current text to IT')
except Exception as e:
    print('Failed to set department text:', e)

print('After setting dept to IT -> func groups:', [tab.func_group_combo.itemText(i) for i in range(tab.func_group_combo.count())])
print('After setting dept to IT -> job titles count:', tab.job_title_combo.count())
print('Sample job titles (first 20):', [tab.job_title_combo.itemText(i) for i in range(min(20, tab.job_title_combo.count()))])

# Now set functional group to Development if present
if tab.func_group_combo.findText('Development') >= 0:
    tab.func_group_combo.setCurrentText('Development')
    print('After setting func group Development -> job titles:', [tab.job_title_combo.itemText(i) for i in range(min(20, tab.job_title_combo.count()))])
else:
    print('Development not present in func groups')

app.quit()
