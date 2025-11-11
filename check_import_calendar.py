import sys, traceback
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')
try:
    import gui.calendar_tab as ct
    print('IMPORT_OK')
except Exception:
    traceback.print_exc()
    raise
