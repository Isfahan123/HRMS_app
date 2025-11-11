import os
import sys
from typing import Optional, Dict

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import (
    supabase,
    compute_variable_epf_for_part,
    load_statutory_limits_configuration,
    get_variable_percentage_config,
)


def _parse_date(s: str):
    from datetime import datetime
    return datetime.strptime(s, "%Y-%m-%d")


def _parse_any(val):
    try:
        from datetime import datetime as _dt
        s = str(val).strip()
        for f in ("%Y-%m-%d","%d/%m/%Y","%Y/%m/%d","%Y-%m","%Y/%m","%m/%Y","%m-%Y"):
            try:
                dt = _dt.strptime(s, f)
                if f in ("%Y-%m","%Y/%m","%m/%Y","%m-%Y"):
                    if f in ("%m/%Y","%m-%Y"):
                        mm, yy = [int(x) for x in s.replace('-', '/').split('/')]
                        return _dt(yy, mm, 1)
                    yy, mm = [int(x) for x in s.replace('-', '/').split('/')]
                    return _dt(yy, mm, 1)
                return dt
            except Exception:
                continue
    except Exception:
        return None


def _to_float(v, d=0.0):
    try:
        return float(v)
    except Exception:
        return float(d)


def audit(month: int, year: int):
    limits = load_statutory_limits_configuration('default') or {}
    var_cfg = get_variable_percentage_config('default') or {}
    eis_ceiling = _to_float(limits.get('eis_ceiling', 6000.0) or 6000.0)
    eis_rate_cfg_emp = _to_float(var_cfg.get('eis_employee_rate', 0.2))
    eis_rate_cfg_empr = _to_float(var_cfg.get('eis_employer_rate', 0.2))

    # Fetch employees
    er = supabase.table('employees').select('*').execute()
    emps = er.data or []

    print("name,email,age,citizenship,gross,eis_emp_calc,eis_reason")
    for e in emps:
        name = e.get('full_name') or ''
        email = e.get('email') or ''
        # Determine age
        age = 30
        try:
            ar = e.get('age', 30)
            if isinstance(ar, str):
                import re
                m = re.search(r"\d+", ar)
                age = int(m.group(0)) if m else 30
            else:
                age = int(ar)
        except Exception:
            age = 30
        # Citizenship inference
        try:
            cit = (e.get('citizenship') or e.get('nationality') or '').strip().lower()
        except Exception:
            cit = ''
        is_citizen_or_pr = None
        if cit:
            if any(k in cit for k in ('malaysian','malaysia','citizen','permanent','pr')):
                is_citizen_or_pr = True
            if any(k in cit for k in ('foreign','expat','non-malaysian','non malaysian','non-citizen','non citizen')):
                is_citizen_or_pr = False
        if is_citizen_or_pr is None:
            # Default permissive
            is_citizen_or_pr = True

        # Intern detection
        pos = (e.get('position') or e.get('job_title') or '')
        is_intern = 'intern' in str(pos).strip().lower()

        # Gross for month
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

        # EPF part heuristic
        epf_part = 'part_a' if age < 60 else 'part_e'
        epf_dec = compute_variable_epf_for_part(epf_part, gross, age, limits, var_cfg)

        # EIS base
        eis_base = min(gross, eis_ceiling)

        # UI rates not available here; rely on config
        eis_emp_rate = eis_rate_cfg_emp
        eis_empr_rate = eis_rate_cfg_empr

        # Eligibility
        elig = (not is_intern) and is_citizen_or_pr and (18 <= age < 60) and (eis_base > 0.0) and (eis_emp_rate > 0.0)
        if elig:
            eis_emp = eis_base * (eis_emp_rate / 100.0)
            if eis_emp <= 0.0:
                reason = 'calculated<=0'
            else:
                # Check latest payroll_runs if present for this employee to compare
                reason = ''
        else:
            # Determine reason
            if is_intern:
                reason = 'intern'
            elif not is_citizen_or_pr:
                reason = 'non-citizen/PR'
            elif not (18 <= age < 60):
                reason = 'age-out-of-range'
            elif eis_base <= 0.0:
                reason = 'no-gross/ceiling-0'
            elif eis_emp_rate <= 0.0:
                reason = 'rate-0'
            else:
                reason = 'unknown'
            eis_emp = 0.0

        # If EIS is 0, print row
        if eis_emp == 0.0:
            print(f"{name},{email},{age},{cit},{gross:.2f},{eis_emp:.2f},{reason}")


if __name__ == '__main__':
    # Default to current month if needed; for now use 2025-06 as example
    from datetime import date
    today = date.today()
    audit(today.month, today.year)
