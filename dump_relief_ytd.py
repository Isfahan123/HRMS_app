import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase

EMP_UUID = '6859674e-413a-4d77-a5fe-d8948b220dc8'
YEAR = 2025

try:
    q = supabase.table('relief_ytd_accumulated').select('employee_id,year,item_key,claimed_ytd,last_claim_year').eq('employee_id', EMP_UUID).eq('year', YEAR).order('item_key', desc=False).execute()
    rows = getattr(q, 'data', []) or []
except Exception as e:
    print('ERROR querying relief_ytd_accumulated:', e)
    rows = []

print(f"relief_ytd_accumulated rows for {EMP_UUID} in {YEAR}: {len(rows)}")
for r in rows:
    print(f"  - {r.get('item_key')}: claimed_ytd={r.get('claimed_ytd')} last_claim_year={r.get('last_claim_year')}")
