import sip
from PyQt5.QtWidgets import QApplication
from gui.employee_history_tab import EmployeeHistoryTab

app = QApplication([])
w = EmployeeHistoryTab()

names = ['job_title_combo','position_combo','department_combo','employment_type_combo','start_date_input','submit_btn','record_table','tabs','avatar_label','name_label','header_label','subtitle_label','choose_emp_btn','view_profile_btn','instruction_label']
print('Checking sip.isdeleted for key attributes:')
for n in names:
    a = getattr(w, n, None)
    if a is None:
        print(n, '=> MISSING')
        continue
    try:
        deleted = sip.isdeleted(a)
    except Exception:
        deleted = 'sip.check failed'
    try:
        parent = a.parent()
        parent_type = type(parent).__name__ if parent else None
    except Exception as e:
        parent = None
        parent_type = f'parent_access_error: {e}'
    print(f"{n}: deleted={deleted}, parent={parent_type}, visible={getattr(a,'isVisible',lambda:False)()}")

print('\nFull __dict__ keys:')
for k in sorted(w.__dict__.keys()):
    try:
        val = w.__dict__[k]
        print(' -', k, 'type=', type(val).__name__, 'sip_deleted=', sip.isdeleted(val) if hasattr(val,'__class__') else 'N/A')
    except Exception:
        print(' -', k, 'type=?')

app.quit()
print('done')
