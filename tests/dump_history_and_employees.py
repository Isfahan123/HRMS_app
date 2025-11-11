import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.supabase_service import supabase

print('Fetching latest 20 employee_history rows...')
try:
    resp = supabase.table('employee_history').select('*').order('created_at', desc=True).limit(20).execute()
    rows = resp.data if resp and getattr(resp, 'data', None) else []
    print('HISTORY_COUNT=', len(rows))
    print(json.dumps(rows, default=str, indent=2))
except Exception as e:
    print('HISTORY_ERROR=', e)

print('\nFetching up to 20 employees (id, employee_id, email)...')
try:
    resp2 = supabase.table('employees').select('id, employee_id, email').limit(20).execute()
    rows2 = resp2.data if resp2 and getattr(resp2, 'data', None) else []
    print('EMP_COUNT=', len(rows2))
    print(json.dumps(rows2, default=str, indent=2))
except Exception as e:
    print('EMP_ERROR=', e)
