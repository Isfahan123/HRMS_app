import os
import sys
from typing import Optional

# Ensure we can import from services
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase, calculate_comprehensive_payroll

def find_employee_by_full_name(full_name: str) -> Optional[dict]:
    try:
        resp = supabase.table('employees').select('*').eq('full_name', full_name).limit(1).execute()
        if resp and getattr(resp, 'data', None):
            return resp.data[0]
        resp2 = supabase.table('employees').select('*').ilike('full_name', f"%{full_name}%").limit(5).execute()
        if resp2 and getattr(resp2, 'data', None):
            return resp2.data[0]
    except Exception as e:
        print(f"ERROR: failed to query employees: {e}")
    return None


def trace_for_months(full_name: str, months: list[int], year: int = 2025) -> None:
    os.environ['HRMS_PCB_DEBUG'] = '1'  # enable detailed PCB internals

    emp = find_employee_by_full_name(full_name)
    if not emp:
        print(f"Employee not found for full_name='{full_name}'")
        return

    try:
        basic_salary = float(emp.get('basic_salary', 0.0) or 0.0)
    except Exception:
        basic_salary = 0.0

    default_inputs = {
        'tax_resident_status': emp.get('tax_resident_status') or ('Resident' if emp.get('is_resident', True) else 'Non-Resident'),
        'basic_salary': basic_salary,
        'allowances': {},
        'overtime_pay': 0.0,
        'commission': 0.0,
        'bonus': 0.0,
    }

    print(f"TRACE for: {emp.get('full_name')} | Email: {emp.get('email')} | Salary: RM{basic_salary:.2f}")
    print("month, pcb, epf_emp, gross")
    for m in months:
        month_year = f"{int(m):02d}/{year}"
        try:
            # calculate_comprehensive_payroll prints detailed PCB internals when HRMS_PCB_DEBUG=1
            result = calculate_comprehensive_payroll(emp, dict(default_inputs), month_year)
            pcb = float(result.get('pcb_tax', 0.0) or 0.0)
            epf_emp = float(result.get('epf_employee', 0.0) or 0.0)
            gross = float(result.get('gross_income', 0.0) or 0.0)
            print(f"{month_year}, {pcb:.2f}, {epf_emp:.2f}, {gross:.2f}")
        except Exception as e:
            print(f"{month_year}, ERROR: {e}")


if __name__ == '__main__':
    name = 'Amir Mursyiddin Bin Mustapha'
    months = list(range(1, 13))
    year = 2025
    trace_for_months(name, months, year)
