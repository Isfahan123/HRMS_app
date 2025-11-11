import sys
import os
from typing import Optional

# Ensure repo root is importable
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase, calculate_comprehensive_payroll


def find_employee_by_full_name(full_name: str) -> Optional[dict]:
    """Find an employee by case-insensitive name; prefer exact match, else ilike contains."""
    try:
        exact = supabase.table('employees').select('*').eq('full_name', full_name).limit(1).execute()
        if exact and getattr(exact, 'data', None):
            return exact.data[0]
        like = supabase.table('employees').select('*').ilike('full_name', f"%{full_name}%").limit(5).execute()
        if like and getattr(like, 'data', None):
            return like.data[0]
    except Exception as e:
        print(f"ERROR: employees query failed: {e}")
    return None


def run_all_months_for_name(full_name: str, year: int = 2025):
    emp = find_employee_by_full_name(full_name)
    if not emp:
        print(f"Employee not found for full_name='{full_name}'")
        return

    try:
        basic_salary = float(emp.get('basic_salary', 0.0) or 0.0)
    except Exception:
        basic_salary = 0.0

    base_inputs = {
        'tax_resident_status': emp.get('tax_resident_status') or ('Resident' if emp.get('is_resident', True) else 'Non-Resident'),
        'basic_salary': basic_salary,
        'allowances': {},
        'overtime_pay': 0.0,
        'commission': 0.0,
        'bonus': 0.0,
    }

    print(f"Employee: {emp.get('full_name')} | Email: {emp.get('email')} | Basic: RM{basic_salary:.2f}")
    for m in range(1, 13):
        period = f"{m:02d}/{year}"
        try:
            res = calculate_comprehensive_payroll(emp, dict(base_inputs), period)
            pcb = float(res.get('pcb_tax', 0.0) or 0.0)
            gross = float(res.get('gross_income', 0.0) or 0.0)
            epf_emp = float(res.get('epf_employee', 0.0) or 0.0)
            print(f"{period} => PCB: RM{pcb:.2f} | Gross: RM{gross:.2f} | EPF Emp: RM{epf_emp:.2f}")
        except Exception as e:
            print(f"{period} => ERROR: {e}")


if __name__ == '__main__':
    # Usage: python tools/run_pcb_for_name_all_months.py "Full Name" [year]
    if len(sys.argv) < 2:
        target_name = 'Ashabul Ashraf Bin Mustapha'
        year = 2025
    else:
        target_name = sys.argv[1]
        try:
            year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025
        except Exception:
            year = 2025
    print(f"Running monthly PCB for '{target_name}' in {year}...")
    run_all_months_for_name(target_name, year)
