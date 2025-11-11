import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase

def main(target_salary=11900.0, tolerance=5.0):
    try:
        resp = supabase.table('employees').select('id, full_name, email, basic_salary').execute()
        rows = resp.data or []
        target_low = float(target_salary) - float(tolerance)
        target_high = float(target_salary) + float(tolerance)
        matches = []
        for r in rows:
            try:
                s = float(r.get('basic_salary', 0.0) or 0.0)
            except Exception:
                s = 0.0
            if target_low <= s <= target_high:
                matches.append((r.get('id'), r.get('full_name'), r.get('email'), s))
        print(f"Found {len(matches)} employees with salary ~ {target_salary} (±{tolerance}):")
        for m in matches:
            print(f"  - id={m[0]} | name={m[1]} | email={m[2]} | salary={m[3]:.2f}")
    except Exception as e:
        print('ERROR:', e)

if __name__ == '__main__':
    main()
