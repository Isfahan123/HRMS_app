import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import sys
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)
from PyQt5.QtWidgets import QApplication
from gui.employee_profile_dialog import EmployeeProfileDialog

app = QApplication.instance() or QApplication([])
print('Instantiating EmployeeProfileDialog...')
# minimal sample data with several fields
sample = {
    'full_name': 'Test User',
    'email': 'test@example.com',
    'phone_number': '0123456789',
    'job_title': 'Software Engineer',
    'department': 'IT',
    'position': 'Senior',
    'date_of_birth': '1990-01-01',
    'employee_id': 'E123'
}
try:
    # instantiate without data to avoid automatic populate in __init__
    dlg = EmployeeProfileDialog(employee_data=None)
    print('Dialog created without data; fields keys:', list(dlg.fields.keys()))
    # Inspect widgets parents and types
    for k, w in dlg.fields.items():
        try:
            parent = w.parent()
        except Exception:
            parent = None
        print(f"Field: {k!r}, type: {type(w)}, parent: {parent}")
    print('Now calling populate_form(sample)')
    try:
        dlg.populate_form(sample)
        print('populate_form completed')
    except Exception:
        import traceback
        print('populate_form raised:')
        traceback.print_exc()
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    app.quit()
