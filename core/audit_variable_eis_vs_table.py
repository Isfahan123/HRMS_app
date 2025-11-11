import os
import sys

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


def _citizenship_flag(emp) -> bool:
    # Robust classifier: evaluate negatives before positives, use whole-token checks where possible
    try:
        cit = (emp.get('citizenship') or emp.get('nationality') or '').strip().lower()
    except Exception:
        cit = ''
    txt = cit.replace('-', ' ').replace('_', ' ')
    tokens = {t for t in txt.split() if t}
    negatives = {'foreign', 'expat', 'non', 'nonmalaysian', 'nonmalaysian', 'nonmalaysia', 'noncitizen', 'non citizen', 'non-malaysian', 'non-malaysia'}
    # If explicit "non-citizen" phrase, treat as non-eligible
    if 'non-citizen' in cit or 'non citizen' in cit:
        return False
    if any(word in cit for word in ('foreign', 'expat')):
        return False
    if 'non' in tokens and ('citizen' in tokens or 'malaysian' in tokens or 'malaysia' in tokens):
        return False
    # Positives
    if any(k in cit for k in ('malaysian', 'malaysia', 'citizen', 'permanent', 'pr')):
        return True
    return True  # default permissive


def _is_intern(emp) -> bool:
    pos = (emp.get('position') or emp.get('job_title') or '')
    return 'intern' in str(pos).strip().lower()


def main():
    limits = load_statutory_limits_configuration('default') or {}
    var_cfg = get_variable_percentage_config('default') or {}
    eis_ceiling = _to_float(limits.get('eis_ceiling', 6000.0) or 6000.0)
    eis_rate_emp = _to_float(var_cfg.get('eis_employee_rate', 0.2))
    eis_rate_empr = _to_float(var_cfg.get('eis_employer_rate', 0.2))

    er = supabase.table('employees').select('*').execute()
    emps = er.data or []

    print("name,email,gross,age,citizen_or_pr,intern,fixed_table_eis,var_expected_eis,reason")
    anomalies = 0
    for e in emps:
        name = e.get('full_name') or ''
        email = e.get('email') or ''
        age = _infer_age(e.get('age', 30))
        is_c_pr = _citizenship_flag(e)
        is_intern = _is_intern(e)

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
        total_allow = sum(_to_float(v, 0.0) for v in (allowances.values() if isinstance(allowances, dict) else []))
        gross = base + total_allow

        # Fixed table EIS
        try:
            f_emp, f_empr, _ = get_eis_contributions(gross, 'eis')
            f_emp = _to_float(f_emp, 0.0)
        except Exception:
            f_emp = 0.0

        # Variable expected (GUI rules): eligibility gate first
        base_cap = min(gross, eis_ceiling)
        eligible = (not is_intern) and is_c_pr and (18 <= age < 60) and base_cap > 0.0 and eis_rate_emp > 0.0
        if not eligible:
            var_emp = 0.0
            reason = (
                'intern' if is_intern else
                ('non-citizen/PR' if not is_c_pr else
                 ('age-out-of-range' if not (18 <= age < 60) else
                  ('no-gross/ceiling-0' if base_cap <= 0.0 else
                   ('rate-0' if eis_rate_emp <= 0.0 else 'unknown'))))
            )
        else:
            # Table-first; rate fallback
            try:
                t_emp, t_empr, _ = get_eis_contributions(gross, 'eis')
                t_emp = _to_float(t_emp, 0.0)
            except Exception:
                t_emp = 0.0
            if t_emp > 0.0:
                var_emp = t_emp
            else:
                var_emp = base_cap * (eis_rate_emp / 100.0)
            reason = ''

        # Flag anomaly: table says >0 but variable expects 0 (excluding interns and true non-citizens)
        if f_emp > 0.0 and var_emp == 0.0 and reason not in ('intern', 'non-citizen/PR'):
            anomalies += 1
            print(f"{name},{email},{gross:.2f},{age},{is_c_pr},{is_intern},{f_emp:.2f},{var_emp:.2f},{reason}")

    print(f"TOTAL anomalies (eligible but var=0 while table>0): {anomalies}")


if __name__ == '__main__':
    main()
