"""Quick import smoke test for CalendarTab add holiday dialog.
This script ensures the repository root is on sys.path so 'gui' imports resolve
when running the script from the scripts/ folder.
"""
import os
import sys

# Add project root (parent of scripts/) to sys.path
this_dir = os.path.dirname(os.path.abspath(__file__))
proj_root = os.path.abspath(os.path.join(this_dir, '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

try:
    from gui.calendar_tab import CalendarTab
    print('CalendarTab import OK')
    # check that method exists
    if hasattr(CalendarTab, 'add_override_dialog') and hasattr(CalendarTab, 'add_override_for_selected'):
        print('Add override methods present')
    else:
        print('Add override methods MISSING')
except Exception as e:
    print('Import FAILED:', e)
