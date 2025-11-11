import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase


def main():
    emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
    # Resolve email key
    r = supabase.table('employees').select('email').eq('id', emp_uuid).limit(1).execute()
    email = (r.data or [{}])[0].get('email')
    if not email:
        print('ERROR: employee email not found')
        return

    # LHDN-aligned totals up to end of February
    X_feb = 1132.50 + 1108.80   # Jan + Feb PCB
    SLP_feb = 1041.65 + 1041.65 # ΣLP up to Feb

    # Upsert/update Feb row
    sel = supabase.table('payroll_ytd_accumulated').select('id').eq('employee_email', email).eq('year', 2025).eq('month', 2).execute()
    payload = {
        'accumulated_pcb_ytd': float(X_feb),
        'accumulated_tax_reliefs_ytd': float(SLP_feb),
    }
    if sel and sel.data:
        supabase.table('payroll_ytd_accumulated').update(payload).eq('employee_email', email).eq('year', 2025).eq('month', 2).execute()
        print(f"Updated Feb YTD for {email}: X={X_feb:.2f}, ΣLP={SLP_feb:.2f}")
    else:
        ins = {'employee_email': email, 'year': 2025, 'month': 2}
        ins.update(payload)
        supabase.table('payroll_ytd_accumulated').insert(ins).execute()
        print(f"Inserted Feb YTD for {email}: X={X_feb:.2f}, ΣLP={SLP_feb:.2f}")


if __name__ == '__main__':
    main()
