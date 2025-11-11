import sys
from typing import Optional

# Ensure we can import from services
import os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase, calculate_comprehensive_payroll


def find_employee_by_full_name(full_name: str) -> Optional[dict]:
    """Fetch an employee row by full_name (case-insensitive, partial match allowed)."""
    try:
        # Prefer exact match first
        resp = supabase.table('employees').select('*').eq('full_name', full_name).limit(1).execute()
        if resp and getattr(resp, 'data', None):
            return resp.data[0]
        # Fallback to ilike contains
        resp2 = supabase.table('employees').select('*').ilike('full_name', f"%{full_name}%").limit(5).execute()
        if resp2 and getattr(resp2, 'data', None):
            return resp2.data[0]
    except Exception as e:
        print(f"ERROR: failed to query employees: {e}")
    return None


def run_for_months(full_name: str, months: list[str], year: int = 2025) -> None:
    emp = find_employee_by_full_name(full_name)
    if not emp:
        print(f"Employee not found for full_name='{full_name}'")
        return

    # Derive inputs
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
        # Let service enrich monthly_deductions / YTD based on email & id
    }

    print(f"Employee: {emp.get('full_name')} | Email: {emp.get('email')} | Salary: RM{basic_salary:.2f}")

    for m in months:
        month_year = f"{int(m):02d}/{year}"
        try:
            result = calculate_comprehensive_payroll(emp, dict(default_inputs), month_year)
            pcb = float(result.get('pcb_tax', 0.0) or 0.0)
            epf_emp = float(result.get('epf_employee', 0.0) or 0.0)
            gross = float(result.get('gross_income', 0.0) or 0.0)
            print(f"{month_year} => PCB: RM{pcb:.2f} | Gross: RM{gross:.2f} | EPF Emp: RM{epf_emp:.2f}")
        except Exception as e:
            print(f"{month_year} => ERROR: {e}")


if __name__ == '__main__':
    # Target employee name and months Jan–Feb; adjust year if needed
    full_name = 'Amir Mursyiddin Bin Mustapha'
    months = [1, 2, 3, 4, 5, 6]
    year = 2025
    print(f"Running PCB calc for '{full_name}' for months {months} in {year}...")
    run_for_months(full_name, months, year)
