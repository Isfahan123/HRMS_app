import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services.supabase_service import supabase, calculate_comprehensive_payroll

EXPECTED = {
    1: 1132.50,
    2: 1108.80,
    3: 1082.75,
    4: 1053.85,
    5: 1021.25,
    6: 984.05,
    7: 940.65,
    8: 888.60,
    9: 887.55,
    10: 887.50,
    11: 887.50,
    12: 887.50,
}

def find_employee(name: str):
    r = supabase.table('employees').select('*').eq('full_name', name).limit(1).execute()
    if r and getattr(r, 'data', None):
        return r.data[0]
    r = supabase.table('employees').select('*').ilike('full_name', f"%{name}%").limit(1).execute()
    if r and getattr(r, 'data', None):
        return r.data[0]
    return None


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else 'Ashabul Ashraf Bin Mustapha'
    year = int(sys.argv[2]) if len(sys.argv) > 2 else 2025

    emp = find_employee(name)
    if not emp:
        print('Employee not found for', name)
        return

    # Override profile per user instruction
    emp2 = dict(emp)
    emp2['marital_status'] = 'Married'
    emp2['spouse_working'] = False
    emp2['is_spouse_disabled'] = True
    emp2['number_of_children'] = 1

    base_inputs = {
        'tax_resident_status': emp.get('tax_resident_status') or ('Resident' if emp.get('is_resident', True) else 'Non-Resident'),
        'basic_salary': float(emp.get('basic_salary', 0.0) or 0.0),
        'allowances': {},
        'overtime_pay': 0.0,
        'commission': 0.0,
        'bonus': 0.0,
    }

    tp1_claims = {
        'parent_medical_care': 500.0,  # 1a
        'parent_dental': 500.0,        # 1b
    }

    print(f"Employee: {emp2.get('full_name')} | Basic: RM{base_inputs['basic_salary']:.2f} | Married, spouse not working & disabled, 1 child")
    for m in range(1, 13):
        period = f"{m:02d}/{year}"
        inputs = dict(base_inputs)
        inputs['tp1_relief_claims'] = tp1_claims
        res = calculate_comprehensive_payroll(emp2, inputs, period)
        actual = float(res.get('pcb_tax', 0.0) or 0.0)
        exp = EXPECTED.get(m)
        print(f"{period}: PCB RM{actual:.2f} | expected RM{(exp or 0.0):.2f} | delta RM{(actual-(exp or 0.0)):.2f}")

if __name__ == '__main__':
    main()
