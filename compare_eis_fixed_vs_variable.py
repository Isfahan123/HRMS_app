import os
import sys
from typing import Tuple

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import (
    supabase,
    get_eis_contributions,
    load_statutory_limits_configuration,
    get_variable_percentage_config,
)


def _to_float(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return float(d)


def _infer_age(val) -> int:
    try:
        if isinstance(val, str):
            import re
            m = re.search(r"\d+", val)
            return int(m.group(0)) if m else 30
        return int(val)
    except Exception:
        return 30


def _infer_citizenship_flag(emp) -> bool:
    try:
        cit = (emp.get('citizenship') or emp.get('nationality') or '').strip().lower()
    except Exception:
        cit = ''
    if cit:
        if any(k in cit for k in ('malaysian','malaysia','citizen','permanent','pr')):
            return True
        if any(k in cit for k in ('foreign','expat','non-malaysian','non malaysian','non-citizen','non citizen')):
            return False
    # Default permissive if unknown
    return True


def _is_intern(emp) -> bool:
    pos = (emp.get('position') or emp.get('job_title') or '')
    return 'intern' in str(pos).strip().lower()


def compute_variable_eis(gross: float, age: int, is_citizen_or_pr: bool, is_intern: bool,
                         eis_ceiling: float, eis_rate_emp: float, eis_rate_empr: float) -> Tuple[float, float, str]:
    base = min(max(0.0, gross), max(0.0, eis_ceiling))
    eligible = (not is_intern) and is_citizen_or_pr and (18 <= age < 60) and base > 0.0 and eis_rate_emp > 0.0
    if not eligible:
        reason = 'ineligible'
        if is_intern:
            reason = 'intern'
        elif not is_citizen_or_pr:
            reason = 'non-citizen/PR'
        elif not (18 <= age < 60):
            reason = 'age-out-of-range'
        elif base <= 0.0:
            reason = 'no-gross/ceiling-0'
        elif eis_rate_emp <= 0.0:
            reason = 'rate-0'
        return 0.0, 0.0, reason
    # Prefer official table values if available
    try:
        tbl_emp, tbl_empr, _ = get_eis_contributions(gross, 'eis')
        tbl_emp = _to_float(tbl_emp, 0.0)
        tbl_empr = _to_float(tbl_empr, 0.0)
    except Exception:
        tbl_emp, tbl_empr = 0.0, 0.0
    if tbl_emp > 0.0:
        return round(tbl_emp, 2), round(tbl_empr, 2), ''
    # Fallback to rate-based if table not present/seeded
    emp_amt = base * (eis_rate_emp / 100.0)
    empr_amt = base * (eis_rate_empr / 100.0)
    return round(emp_amt, 2), round(empr_amt, 2), ''


def main():
    limits = load_statutory_limits_configuration('default') or {}
    var_cfg = get_variable_percentage_config('default') or {}
    eis_ceiling = _to_float(limits.get('eis_ceiling', 6000.0) or 6000.0)
    eis_rate_emp = _to_float(var_cfg.get('eis_employee_rate', 0.2))
    eis_rate_empr = _to_float(var_cfg.get('eis_employer_rate', 0.2))

    # Pull employees
    er = supabase.table('employees').select('*').execute()
    emps = er.data or []

    print("name,email,gross,age,citizen_or_pr,intern,fixed_eis_emp,variable_eis_emp,diff,flag")
    mismatches = 0
    for e in emps:
        name = e.get('full_name') or ''
        email = e.get('email') or ''
        age = _infer_age(e.get('age', 30))
        citizen_flag = _infer_citizenship_flag(e)
        intern_flag = _is_intern(e)

        base = _to_float(e.get('basic_salary', 0.0))
        allowances = e.get('allowances') or {}
        if isinstance(allowances, str):
            try:
                import json
                p = json.loads(allowances)
                if isinstance(p, dict):
                    allowances = p
                else:
                    allowances = {}
            except Exception:
                allowances = {}
        total_allowances = sum(_to_float(v, 0.0) for v in (allowances.values() if isinstance(allowances, dict) else []))
        gross = base + total_allowances

        # Fixed (table) EIS
        try:
            fixed_emp, fixed_empr, _ = get_eis_contributions(gross, 'eis')
            fixed_emp = round(_to_float(fixed_emp, 0.0), 2)
        except Exception:
            fixed_emp = 0.0

        # Variable (rate) EIS
        var_emp, var_empr, reason = compute_variable_eis(gross, age, citizen_flag, intern_flag,
                                                         eis_ceiling, eis_rate_emp, eis_rate_empr)

        diff = round(var_emp - fixed_emp, 2)
        flag = ''
        if (fixed_emp == 0.0 and var_emp > 0.0) or (fixed_emp > 0.0 and var_emp == 0.0) or abs(diff) > 0.05:
            flag = 'MISMATCH'
            mismatches += 1

        print(f"{name},{email},{gross:.2f},{age},{citizen_flag},{intern_flag},{fixed_emp:.2f},{var_emp:.2f},{diff:.2f},{flag}")

    print(f"TOTAL mismatches: {mismatches}")


if __name__ == '__main__':
    main()
