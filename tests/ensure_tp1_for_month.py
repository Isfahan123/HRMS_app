import os, sys
from typing import Dict

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase


def upsert_tp1(employee_id: str, year: int, month: int, details: Dict[str, float]):
    payload = {
        'details': details,
        # Keep meta zeros; LP1 is computed during payroll run
        'other_reliefs_monthly': 0.0,
        'socso_eis_lp1_monthly': 0.0,
    }
    try:
        # Try update first; if no row, insert
        sel = supabase.table('tp1_monthly_details').select('employee_id').eq('employee_id', employee_id).eq('year', year).eq('month', month).limit(1).execute()
        exists = bool(sel and getattr(sel, 'data', None))
        if exists:
            res = supabase.table('tp1_monthly_details').update(payload).eq('employee_id', employee_id).eq('year', year).eq('month', month).execute()
            print(f"Updated TP1 for {employee_id} {month:02d}/{year}")
        else:
            ins = dict(payload)
            ins.update({'employee_id': employee_id, 'year': year, 'month': month})
            res = supabase.table('tp1_monthly_details').insert(ins).execute()
            print(f"Inserted TP1 for {employee_id} {month:02d}/{year}")
    except Exception as e:
        print('ERROR upserting tp1_monthly_details:', e)


def main():
    # Target employee UUID from your logs
    emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
    year = 2025
    # Map 1a + 1b into our internal keys
    details = {
        'parent_medical_care': 500.0,
        'parent_dental': 500.0,
    }
    for m in (1, 2, 3, 4, 5):
        upsert_tp1(emp_uuid, year, m, details)


if __name__ == '__main__':
    main()
