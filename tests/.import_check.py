import importlib
try:
    importlib.import_module('gui.employee_history_tab')
    print('IMPORT_OK: gui.employee_history_tab')
except Exception as e:
    print('IMPORT_FAIL:', type(e).__name__, e)
    raise
