# Compute years of service for given employee handles
import os, sys
this_dir = os.path.dirname(os.path.abspath(__file__))
proj_root = os.path.abspath(os.path.join(this_dir, '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from datetime import datetime, date
from services.supabase_service import supabase

HANDLES = ['Test3Account3', 'Test1Account1']
AS_OF = date(2025, 10, 15)

# helper
def compute_years(joined_date_str, as_of=AS_OF):
    joined = datetime.strptime(joined_date_str, '%Y-%m-%d').date()
    try:
        from dateutil.relativedelta import relativedelta
        rd = relativedelta(as_of, joined)
        completed = rd.years
        fractional = rd.years + rd.months/12.0 + rd.days/365.25
        return completed, round(fractional, 4)
    except Exception:
        days = (as_of - joined).days
        completed = int(days // 365.25)
        fractional = days / 365.25
        return completed, round(fractional, 4)

for h in HANDLES:
    try:
        resp = supabase.table('employees').select('id, employee_id, email, full_name, date_joined').eq('employee_id', h).limit(1).execute()
        rows = resp.data if resp and getattr(resp, 'data', None) else []
        if not rows:
            print(f"{h}: not found in employees table")
            continue
        r = rows[0]
        jd = r.get('date_joined')
        if not jd:
            print(f"{h}: no date_joined")
            continue
        completed, frac = compute_years(jd)
        print(f"{h}: date_joined={jd} -> completed_years={completed}, fractional_years={frac}")
    except Exception as e:
        print(f"{h}: query error: {e}")
