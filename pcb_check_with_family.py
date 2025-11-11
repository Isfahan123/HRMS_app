import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services.supabase_service import calculate_comprehensive_payroll, supabase

emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
period = '01/2025'

# Fetch employee (to get salary)
try:
    r = supabase.table('employees').select('*').eq('id', emp_uuid).limit(1).execute()
    emp = r.data[0] if r and getattr(r, 'data', None) else {'id': emp_uuid, 'employee_id': emp_uuid, 'full_name':'', 'email':''}
except Exception as e:
    print('DEBUG: failed to fetch employee, using stub:', e)
    emp = {'id': emp_uuid, 'employee_id': emp_uuid, 'full_name':'', 'email':''}

basic_salary = float(emp.get('basic_salary') or 11900.0)

inputs = {
    'tax_resident_status': 'Resident',
    'basic_salary': basic_salary,
    'allowances': {},
    'overtime_pay': 0.0,
    'commission': 0.0,
    'bonus': 0.0,
    'debug_pcb': True,
    # Family overrides to match LHDN example:
    'spouse_relief': 4000.0,           # S
    'disabled_spouse': 6000.0,         # Su
    'child_relief': 2000.0,            # Q per child
    'child_count': 1,                  # C
}

print('--- PCB with family overrides and TP1 for', period, '---')
res = calculate_comprehensive_payroll(emp, inputs, period)
print('PCB =', res.get('pcb_tax', res))
print('LP1 for PCB (other_reliefs_current) =', inputs.get('other_reliefs_current'))
