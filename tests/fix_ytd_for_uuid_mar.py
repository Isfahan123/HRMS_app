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

    # LHDN-aligned totals up to end of March
    # Option A (LHDN-derived X for April=1053.85 with our annual tax):
    # X_mar = 3323.70
    # Option B (sum of rounded Jan–Mar): 1174.15 + 1108.80 + 1082.75 = 3365.70
    X_mar = 3323.70
    SLP_mar = 1041.65 * 3                 # ΣLP up to Mar (TP1 + B20 per month)

    # Upsert/update Mar row
    sel = supabase.table('payroll_ytd_accumulated').select('id').eq('employee_email', email).eq('year', 2025).eq('month', 3).execute()
    payload = {
        'accumulated_pcb_ytd': float(X_mar),
        'accumulated_tax_reliefs_ytd': float(SLP_mar),
    }
    if sel and sel.data:
        supabase.table('payroll_ytd_accumulated').update(payload).eq('employee_email', email).eq('year', 2025).eq('month', 3).execute()
        print(f"Updated Mar YTD for {email}: X={X_mar:.2f}, ΣLP={SLP_mar:.2f}")
    else:
        ins = {'employee_email': email, 'year': 2025, 'month': 3}
        ins.update(payload)
        supabase.table('payroll_ytd_accumulated').insert(ins).execute()
        print(f"Inserted Mar YTD for {email}: X={X_mar:.2f}, ΣLP={SLP_mar:.2f}")


if __name__ == '__main__':
    main()
