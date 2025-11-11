# Diagnostic: try inserting a holiday and fetching it back
import os, sys
this_dir = os.path.dirname(os.path.abspath(__file__))
proj_root = os.path.abspath(os.path.join(this_dir, '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from services.supabase_service import insert_calendar_holiday, find_calendar_holidays_by_date

TEST_DATE = '2025-10-16'
TEST_NAME = 'Diag test holiday'
TEST_STATE = None

print('Attempting insert...')
try:
    ok = insert_calendar_holiday(TEST_DATE, TEST_NAME, state=TEST_STATE, is_national=False, is_observance=False, created_by='diag')
    print('insert returned:', ok)
except Exception as e:
    print('insert raised:', repr(e))

print('\nFetching rows for date...')
try:
    rows = find_calendar_holidays_by_date(TEST_DATE, state=TEST_STATE)
    print('rows count:', len(rows))
    for r in rows:
        print(r)
except Exception as e:
    print('find raised:', repr(e))
