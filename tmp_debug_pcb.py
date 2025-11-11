import os, sys
# Ensure project root is on sys.path so 'services' can be imported when running from tools/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services.supabase_service import calculate_comprehensive_payroll, supabase

emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
try:
    r = supabase.table('employees').select('*').eq('id', emp_uuid).limit(1).execute()
    emp = r.data[0] if r and getattr(r, 'data', None) else {'id': emp_uuid, 'employee_id': emp_uuid, 'full_name':'', 'email':''}
except Exception as e:
    print('DEBUG: failed to fetch employee, using stub:', e)
    emp = {'id': emp_uuid, 'employee_id': emp_uuid, 'full_name':'', 'email':''}

# Try to infer a salary; fallback to higher salary to see PCB effect
basic_salary = 0.0
try:
    bs = emp.get('basic_salary', 0.0)
    basic_salary = float(bs or 0.0)
except Exception:
    basic_salary = 0.0
if basic_salary == 0.0:
    basic_salary = 15000.0

period = '01/2025'

# With TP1 auto-loaded
inputs = {
    'tax_resident_status': 'Resident',
    'basic_salary': basic_salary,
    'allowances': {},
    'overtime_pay': 0.0,
    'commission': 0.0,
    'bonus': 0.0,
    'debug_pcb': True,
}
print('--- With TP1 auto-loaded for', period, '---')
res = calculate_comprehensive_payroll(emp, inputs, period)
print('PCB with TP1 auto =', res.get('pcb_tax', res))
print('LP1 base cash =', inputs.get('lp1_base_cash'))
print('LP1 for PCB =', inputs.get('other_reliefs_current'))

# Without TP1 (force empty claims)
inputs2 = dict(inputs)
# Provide a non-empty dict with a sentinel key so auto-load doesn't override;
# unknown key will be ignored by the catalog and result in zero TP1.
inputs2['tp1_relief_claims'] = {'__empty__': 0}
print('\n--- With TP1 forced empty for', period, '---')
res2 = calculate_comprehensive_payroll(emp, inputs2, period)
print('PCB without TP1 =', res2.get('pcb_tax', res2))
print('LP1 base cash (forced empty) =', inputs2.get('lp1_base_cash'))
print('LP1 for PCB (forced empty) =', inputs2.get('other_reliefs_current'))
