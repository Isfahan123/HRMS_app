import traceback
import importlib
import sys
import os
from PyQt5 import QtWidgets

# Ensure project root is on sys.path so 'gui' package can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    print(f'Inserted project root into sys.path: {project_root}')

orig_init = QtWidgets.QWidget.__init__

def wrapper(self, *args, **kwargs):
    if QtWidgets.QApplication.instance() is None:
        print("--- Widget created before QApplication detected ---")
        traceback.print_stack(limit=10)
    return orig_init(self, *args, **kwargs)

QtWidgets.QWidget.__init__ = wrapper

modules_to_test = [
    'gui.login_window',
    'gui.dashboard_window',
    'gui.admin_dashboard_window',
    'gui.employee_training_course_tab',
    'gui.employee_overseas_work_trip_tab',
    'gui.employee_profile_tab',
]

for m in modules_to_test:
    try:
        print(f"Importing {m}...")
        importlib.import_module(m)
        print(f"Imported {m} OK\n")
    except Exception as e:
        print(f"Importing {m} raised: {e}\n")
        # continue to next module

print("Done")
