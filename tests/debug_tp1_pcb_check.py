from services.supabase_service import calculate_comprehensive_payroll

# Minimal employee and payroll inputs
employee = {
    'employee_id': 'E001',
    'id': '00000000-0000-0000-0000-000000000000',
    'full_name': 'Test Employee',
    'email': 'test@example.com',
}

base_inputs = {
    'tax_resident_status': 'Resident',
    'basic_salary': 5000.0,
    'allowances': {},
    'overtime_pay': 0.0,
    'commission': 0.0,
    'bonus': 0.0,
}

month_year = '10/2025'

# Run A: Without TP1 claims
res_a = calculate_comprehensive_payroll(employee, dict(base_inputs), month_year)
pcb_a = res_a.get('pcb_tax', None)

# Run B: With TP1 claims: 1a + 1b = 500 each
inputs_b = dict(base_inputs)
inputs_b['tp1_relief_claims'] = {
    'parent_medical_care': 500.0,  # 1a
    'parent_dental': 500.0,        # 1b
}
res_b = calculate_comprehensive_payroll(employee, inputs_b, month_year)
pcb_b = res_b.get('pcb_tax', None)

print('PCB without TP1:', pcb_a)
print('PCB with TP1 (1a+1b=500 each):', pcb_b)
try:
    if pcb_a is not None and pcb_b is not None:
        diff = round(float(pcb_a) - float(pcb_b), 2)
        print('PCB decrease (expected >= 0.00):', diff)
except Exception as e:
    print('DEBUG: Could not compute diff:', e)

# Show whether the engine derived LP1 from TP1
calc_details_a = res_a.get('calculation_details', {})
calc_details_b = res_b.get('calculation_details', {})
print('A details:', calc_details_a)
print('B details:', calc_details_b)
