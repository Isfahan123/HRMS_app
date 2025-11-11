import sys, traceback
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')
try:
    from gui.admin_sections.leave import leave_caps_editor
    print('Imported leave_caps_editor OK')
except Exception as e:
    print('Import failed:')
    traceback.print_exc()
    raise
