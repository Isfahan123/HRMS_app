import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services.supabase_service import supabase

EMP_UUID = '6859674e-413a-4d77-a5fe-d8948b220dc8'
YEAR = 2025

try:
    if hasattr(supabase, 'table'):
        q = supabase.table('tp1_monthly_details').select('year, month, details, other_reliefs_monthly, socso_eis_lp1_monthly').eq('employee_id', EMP_UUID).eq('year', YEAR).order('month', desc=False).execute()
        rows = getattr(q, 'data', []) or []
    else:
        rows = []
except Exception as e:
    print('ERROR querying tp1_monthly_details:', e)
    rows = []

print(f"Found {len(rows)} TP1 records for {EMP_UUID} in {YEAR}:")
for r in rows:
    det = r.get('details') or {}
    keys = ','.join(sorted(det.keys()))
    print(f"  - {r.get('month'):02d}/{r.get('year')}: items=[{keys}] other_reliefs_monthly={r.get('other_reliefs_monthly')} socso_eis_lp1_monthly={r.get('socso_eis_lp1_monthly')}")
