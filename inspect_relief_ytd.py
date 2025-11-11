import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase

def main():
    emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
    year = 2025
    try:
        rows = supabase.table('relief_ytd_accumulated').select('*')\
            .eq('employee_id', emp_uuid)\
            .eq('year', year)\
            .order('item_key', desc=False)\
            .execute().data or []
    except Exception as e:
        print('ERROR selecting relief_ytd_accumulated:', e)
        rows = []
    print(f"Found {len(rows)} rows in relief_ytd_accumulated for employee {emp_uuid} year {year}")
    for r in rows:
        try:
            print(f"- item_key={r.get('item_key')} claimed_ytd={r.get('claimed_ytd')} last_claim_year={r.get('last_claim_year')} id={r.get('id')}")
        except Exception:
            print(r)

if __name__ == '__main__':
    main()
