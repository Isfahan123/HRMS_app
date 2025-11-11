import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase, process_payroll_and_generate_payslip


def fetch_employee(emp_uuid: str) -> dict:
    try:
        r = supabase.table('employees').select('*').eq('id', emp_uuid).limit(1).execute()
        if r and getattr(r, 'data', None):
            return r.data[0]
    except Exception as e:
        print('DEBUG: failed to fetch employee:', e)
    return {'id': emp_uuid, 'employee_id': emp_uuid, 'full_name': '', 'email': ''}


def main():
    emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
    emp = fetch_employee(emp_uuid)
    try:
        basic_salary = float(emp.get('basic_salary', 11900.0) or 11900.0)
    except Exception:
        basic_salary = 11900.0

    inputs = {
        'tax_resident_status': 'Resident',
        'basic_salary': basic_salary,
        'allowances': {},
        'overtime_pay': 0.0,
        'commission': 0.0,
        'bonus': 0.0,
        'debug_pcb': True,
    }
    res = process_payroll_and_generate_payslip(emp, inputs, '01/2025', generate_pdf=False)
    print('Saved January payroll:', res.get('success'), res.get('error'))


if __name__ == '__main__':
    main()
