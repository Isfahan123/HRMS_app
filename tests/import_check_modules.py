import sys
sys.path.insert(0, '.')
import importlib
try:
    importlib.import_module('gui.employee_history_tab')
    importlib.import_module('gui.admin_profile_tab')
    importlib.import_module('gui.admin_dashboard_window')
    print('Modules imported OK')
except Exception:
    import traceback
    traceback.print_exc()
    raise
