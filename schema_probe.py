# One-off script to probe employees table columns using project's supabase client
import json, sys, os
# ensure repo root is on sys.path so local imports work when run from terminal
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from services.supabase_service import supabase
except Exception as e:
    print('IMPORT_ERROR:' + str(e))
    sys.exit(0)

if not supabase:
    print('SUPABASE_NOT_CONFIGURED')
    sys.exit(0)

try:
    r = supabase.table('employees').select('*').limit(1).execute()
    data = getattr(r, 'data', None)
    if data and len(data) > 0:
        print('SAMPLE_KEYS:' + json.dumps(list(data[0].keys())))
    else:
        print('NO_EMPLOYEE_ROWS')
except Exception as e:
    print('ERROR:' + str(e))
