import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services import supabase_service as svc

# Force variable percentage mode without touching DB settings
svc.get_payroll_settings = lambda: {
    'calculation_method': 'variable',
    'active_variable_config': 'default'
}

def run_case(label, dob, basic_salary, allowances=None):
    employee = {
        'employee_id': f'E-{label}',
        'id': '00000000-0000-0000-0000-000000000000',
        'full_name': f'Test {label}',
        'email': f'{label.lower()}@example.com',
        'date_of_birth': dob,
        'nationality': 'Malaysia',
        'citizenship': 'Citizen'
    }
    payroll_inputs = {
        'tax_resident_status': 'Resident',
        'basic_salary': float(basic_salary),
        'allowances': allowances or {},
        'overtime_pay': 0.0,
        'commission': 0.0,
        'bonus': 0.0,
    }
    result = svc.calculate_comprehensive_payroll(employee, payroll_inputs, '09/2025')
    summary_keys = [
        'gross_income', 'epf_employee', 'epf_employer',
        'socso_employee', 'socso_employer',
        'eis_employee', 'eis_employer',
        'pcb_tax', 'net_salary'
    ]
    summary = {k: round(float(result.get(k, 0.0) or 0.0), 2) for k in summary_keys}
    details = (result.get('calculation_details') or {})
    print(f'CASE {label}: DOB={dob} SAL={basic_salary}')
    print('  EPF_RATE_SOURCE', details.get('epf_rate_source'))
    print('  EPF_BASE_CEILING_APPLIED?', details.get('epf_ceiling_applied'))
    print('  SUMMARY', summary)


# Case A: Under-60, moderate salary
run_case('A_UNDER60', '1990-01-01', 5000.0, {'transport': 200.0, 'phone': 100.0})

# Case B: Over-60 with >RM20k salary to trigger no EPF cap & Stage 2 rates
run_case('B_OVER60_20KPLUS', '1958-01-01', 25000.0)
