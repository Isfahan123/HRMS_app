import os, sys, json
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase


def upsert_payroll_config(emp_id: str, flags: dict):
    # Merge into payroll_configurations.tax_relief_data JSON
    try:
        resp = supabase.table('payroll_configurations').select('id, tax_relief_data').eq('employee_id', emp_id).limit(1).execute()
        row = (resp.data or [None])[0]
        if row:
            data = row.get('tax_relief_data') or {}
            if not isinstance(data, dict):
                data = {}
            data.update(flags)
            supabase.table('payroll_configurations').update({'tax_relief_data': data}).eq('id', row.get('id')).execute()
        else:
            supabase.table('payroll_configurations').insert({'employee_id': emp_id, 'tax_relief_data': dict(flags)}).execute()
    except Exception as e:
        print('WARN: payroll_configurations update failed:', e)


def main():
    emp_uuid = '6859674e-413a-4d77-a5fe-d8948b220dc8'
    # Employees: set marital status, spouse working flag, number of children
    # Update only common columns first (avoid unknown-column failures)
    try:
        supabase.table('employees').update({
            'marital_status': 'Married',
            'spouse_working': 'No',
            'number_of_children': 1,
        }).eq('id', emp_uuid).execute()
        print('Updated employees marital/children flags')
    except Exception as e:
        print('WARN updating employees marital/children:', e)
    # Try OKU spouse-only column if it exists in this schema (ignore failure)
    try:
        supabase.table('employees').update({'is_spouse_disabled': True}).eq('id', emp_uuid).execute()
        print('Updated employees.is_spouse_disabled')
    except Exception as e:
        print('WARN updating employees.is_spouse_disabled:', e)

    # Payroll configurations: set OKU flags in tax_relief_data JSON
    upsert_payroll_config(emp_uuid, {
        'is_spouse_disabled': True,
        'is_individual_disabled': False,
    })
    print('Ensured payroll_configurations.tax_relief_data flags')


if __name__ == '__main__':
    main()
