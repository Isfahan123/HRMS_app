import sys
import os

# Ensure imports from services
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase, calculate_comprehensive_payroll


def run_debug(full_name: str, months: list[int], year: int = 2025):
    try:
        # Try exact match then ilike
        resp = supabase.table('employees').select('*').eq('full_name', full_name).limit(1).execute()
        emp = resp.data[0] if resp and getattr(resp, 'data', None) else None
        if not emp:
            resp2 = supabase.table('employees').select('*').ilike('full_name', f"%{full_name}%").limit(1).execute()
            emp = resp2.data[0] if resp2 and getattr(resp2, 'data', None) else None
        if not emp:
            print(f"Employee not found: {full_name}")
            return

        basic_salary = 0.0
        try:
            basic_salary = float(emp.get('basic_salary', 0.0) or 0.0)
        except Exception:
            pass

        base_inputs = {
            'tax_resident_status': emp.get('tax_resident_status') or ('Resident' if emp.get('is_resident', True) else 'Non-Resident'),
            'basic_salary': basic_salary,
            'allowances': {},
            'overtime_pay': 0.0,
            'commission': 0.0,
            'bonus': 0.0,
            'debug_pcb': True,
        }

        print(f"Employee: {emp.get('full_name')} | Email: {emp.get('email')} | Salary: RM{basic_salary:.2f}")
        for m in months:
            period = f"{int(m):02d}/{int(year)}"
            print(f"\n=== DEBUG FOR {period} ===")
            res = calculate_comprehensive_payroll(emp, dict(base_inputs), period)
            pcb = float(res.get('pcb_tax', 0.0) or 0.0)
            gross = float(res.get('gross_income', 0.0) or 0.0)
            epf_emp = float(res.get('epf_employee', 0.0) or 0.0)
            print(f"Result: PCB RM{pcb:.2f} | Gross RM{gross:.2f} | EPF Emp RM{epf_emp:.2f}")
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == '__main__':
    target = 'Amir Mursyiddin Bin Mustapha'
    run_debug(target, [1, 2], 2025)
