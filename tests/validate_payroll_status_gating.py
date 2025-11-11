import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.supabase_service import process_payroll_and_generate_payslip

# Minimal employees to validate gating behavior without touching DB
inactive_emp = {
    'employee_id': 'EMP-INACTIVE-001',
    'full_name': 'Inactive Person',
    'email': 'inactive@example.com',
    'payroll_status': 'Inactive Payroll',
    'status': 'Active',
}

terminated_emp = {
    'employee_id': 'EMP-TERM-002',
    'full_name': 'Terminated Person',
    'email': 'terminated@example.com',
    'payroll_status': 'Active Payroll',
    'status': 'Terminated',
}

active_emp = {
    'employee_id': 'EMP-ACTIVE-003',
    'full_name': 'Active Person',
    'email': 'active@example.com',
    'payroll_status': 'Active Payroll',
    'status': 'Active',
}

# Minimal payroll inputs; for inactive/terminated the function should skip before any DB work
inputs = {
    'basic_salary': 0.0,
    'allowances': {},
}

print('--- Validate payroll_status gating ---')
res1 = process_payroll_and_generate_payslip(inactive_emp, dict(inputs), '11/2025', generate_pdf=False)
print('Inactive payroll_status =>', res1)
assert res1.get('skipped') is True, 'Expected inactive payroll_status to skip processing'

print('--- Validate employment status gating ---')
res2 = process_payroll_and_generate_payslip(terminated_emp, dict(inputs), '11/2025', generate_pdf=False)
print('Terminated employment status =>', res2)
assert res2.get('skipped') is True, 'Expected terminated employment status to skip processing'

print('--- Sanity for active (may fail later due to DB, but should not skip immediately) ---')
res3 = process_payroll_and_generate_payslip(active_emp, dict(inputs), '11/2025', generate_pdf=False)
print('Active employee =>', res3)
# We don't assert success here because downstream DB calls may fail in local runs; just ensure it didn't skip
assert not res3.get('skipped'), 'Active employee should not be skipped'

print('OK: Gating checks behaved as expected')
