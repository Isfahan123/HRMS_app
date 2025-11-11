import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase


def get_employee(uuid: str) -> dict:
    try:
        r = supabase.table('employees').select('*').eq('id', uuid).limit(1).execute()
        if r and getattr(r, 'data', None):
            return r.data[0]
    except Exception as e:
        print('ERROR fetching employee:', e)
    return {'id': uuid}


def ensure_ytd(employee_email: str, year: int, month: int, x_pcb: float, sum_lp: float) -> None:
    # Read current row
    sel = supabase.table('payroll_ytd_accumulated').select('*')\
        .eq('employee_email', employee_email).eq('year', year).eq('month', month).execute()
    exists = bool(sel and getattr(sel, 'data', None))
    payload = {
        'accumulated_pcb_ytd': float(x_pcb),
        'accumulated_tax_reliefs_ytd': float(sum_lp),
    }
    if exists:
        supabase.table('payroll_ytd_accumulated').update(payload)\
            .eq('employee_email', employee_email).eq('year', year).eq('month', month).execute()
        print(f"Updated YTD for {employee_email} {month:02d}/{year} -> X={x_pcb:.2f}, ΣLP={sum_lp:.2f}")
    else:
        ins = {'employee_email': employee_email, 'year': year, 'month': month}
        ins.update(payload)
        supabase.table('payroll_ytd_accumulated').insert(ins).execute()
        print(f"Inserted YTD for {employee_email} {month:02d}/{year} -> X={x_pcb:.2f}, ΣLP={sum_lp:.2f}")


def main():
    emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
    emp = get_employee(emp_uuid)
    email = emp.get('email') or emp.get('employee_email')
    if not email:
        print('ERROR: Employee email not found; cannot patch YTD row keyed by email.')
        return
    # Target LHDN-aligned YTD for January
    ensure_ytd(email, 2025, 1, x_pcb=1132.50, sum_lp=1041.65)


if __name__ == '__main__':
    main()
