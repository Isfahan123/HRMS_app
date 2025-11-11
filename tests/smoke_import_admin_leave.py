import sys
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')

try:
    from gui.admin_leave_tab_mod import AdminLeaveTab
    print('Imported AdminLeaveTab OK')
except Exception as e:
    print('Import failed:', e)
    raise
