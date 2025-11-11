import os, sys
ROOT = r'c:\Users\hi\Downloads\hrms_app'
if ROOT not in sys.path: 
    sys.path.insert(0, ROOT)
from services.supabase_service import supabase, calculate_comprehensive_payroll

# Force variable mode
def mock_get_payroll_settings():
    return {'calculation_method': 'variable', 'active_variable_config': 'default'}

import services.supabase_service as svc
svc.get_payroll_settings = mock_get_payroll_settings

# Find employee
resp = supabase.table('employees').select('*').ilike('full_name', '%Amir Mursyiddin%').limit(1).execute()
emp = resp.data[0] if resp.data else None
if not emp:
    print('Employee not found')
    exit()

print(f'VARIABLE MODE: {emp.get("full_name")} | Email: {emp.get("email")} | Salary: RM{float(emp.get("basic_salary", 0) or 0):.2f}')

base_inputs = {
    'tax_resident_status': 'Resident',
    'basic_salary': float(emp.get('basic_salary', 0) or 0),
    'allowances': {},
    'overtime_pay': 0.0,
    'commission': 0.0,
    'bonus': 0.0,
}

for m in [1, 2, 3, 4, 5, 6]:
    period = f'{m:02d}/2025'
    try:
        res = calculate_comprehensive_payroll(emp, dict(base_inputs), period)
        pcb = float(res.get('pcb_tax', 0) or 0)
        gross = float(res.get('gross_income', 0) or 0)
        epf_emp = float(res.get('epf_employee', 0) or 0)
        print(f'{period} => PCB: RM{pcb:.2f} | Gross: RM{gross:.2f} | EPF Emp: RM{epf_emp:.2f}')
    except Exception as e:
        print(f'{period} => ERROR: {e}')