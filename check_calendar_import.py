# Headless import check for gui.calendar_tab
import os, sys, traceback
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
print('PYTHONPATH:', sys.path[0])
try:
    from gui.calendar_tab import CalendarTab
    print('Imported gui.calendar_tab OK')
except Exception as e:
    print('Failed to import gui.calendar_tab:')
    traceback.print_exc()
    raise
