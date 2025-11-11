import os
import sys
from typing import Optional, Dict

ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import (
    supabase,
    calculate_lhdn_pcb_official,
    compute_variable_epf_for_part,
    load_statutory_limits_configuration,
    get_variable_percentage_config,
    load_tax_rates_configuration,
)


def _parse_any_date_local(val):
    try:
        if not val:
            return None
        from datetime import datetime as _dt
        s = str(val).strip()
        fmts = [
            '%Y-%m-%d', '%Y/%m/%d',
            '%d/%m/%Y', '%d-%m-%Y',
            '%Y-%m', '%Y/%m',
            '%m/%Y', '%m-%Y',
        ]
        for f in fmts:
            try:
                dt = _dt.strptime(s, f)
                if f in ('%Y-%m', '%Y/%m', '%m/%Y', '%m-%Y'):
                    parts = s.replace('-', '/').split('/')
                    if f in ('%m/%Y', '%m-%Y'):
                        mm, yy = int(parts[0]), int(parts[1])
                        return _dt(yy, mm, 1)
                    else:
                        yy, mm = int(parts[0]), int(parts[1])
                        return _dt(yy, mm, 1)
                return dt
            except Exception:
                continue
        return None
    except Exception:
        return None


def find_employee_by_full_name(full_name: str) -> Optional[dict]:
    try:
        resp = supabase.table('employees').select('*').eq('full_name', full_name).limit(1).execute()
        if resp and getattr(resp, 'data', None):
            return resp.data[0]
        resp2 = supabase.table('employees').select('*').ilike('full_name', f"%{full_name}%").limit(5).execute()
        if resp2 and getattr(resp2, 'data', None):
            return resp2.data[0]
    except Exception as e:
        print(f"ERROR: failed to query employees: {e}")
    return None


def _to_float(x, d=0.0):
    try:
        return float(x)
    except Exception:
        return float(d)


def trace_variable_path(full_name: str, months: list[int], year: int = 2025):
    emp = find_employee_by_full_name(full_name)
    if not emp:
        print(f"Employee not found for '{full_name}'")
        return

    print(f"GUI-path TRACE for: {emp.get('full_name')} | Email: {emp.get('email')}")

    # Static configs
    limits_cfg = load_statutory_limits_configuration('default') or {}
    var_cfg = get_variable_percentage_config('default') or {}
    tax_cfg = load_tax_rates_configuration() or {}

    # Resolve EPF part via simple heuristic: use age and assume Part A for <60
    age_raw = emp.get('age', 30)
    if isinstance(age_raw, str):
        import re as _re
        m = _re.search(r"\d+", age_raw)
        age = int(m.group(0)) if m else 30
    else:
        try:
            age = int(age_raw)
        except Exception:
            age = 30
    epf_part = 'part_a' if age < 60 else 'part_e'

    gross_base = _to_float(emp.get('basic_salary', 0.0))
    try:
        allowances = emp.get('allowances') or {}
        if isinstance(allowances, str):
            import json as _json
            _parsed = _json.loads(allowances)
            if isinstance(_parsed, dict):
                allowances = _parsed
            else:
                allowances = {}
    except Exception:
        allowances = {}
    total_allowances = sum(_to_float(v, 0.0) for v in (allowances.values() if isinstance(allowances, dict) else []))

    print("month, pcb_gui, ytd_source, X(prev_pcb), ΣLP(ytd), LP1(this), K1(epf), Y1(gross)")

    # Track some in-memory YTD to compare with DB reads (does not persist)
    X_mem = 0.0
    LP1_cap_used = 0.0

    for m in months:
        # Month-year context
        month_year = f"{m:02d}/{year}"
        Y1 = gross_base + total_allowances  # no bonus here for simplicity

        # Compute variable EPF
        epf_dec = compute_variable_epf_for_part(epf_part, Y1, age, limits_cfg, var_cfg)
        K1 = _to_float(epf_dec.get('employee', 0.0))

        # Load YTD from DB (previous month snapshot) like GUI path
        ytd_source = 'none'
        ytd: Dict[str, float] = {
            'accumulated_gross': 0.0,
            'accumulated_epf': 0.0,
            'accumulated_pcb': 0.0,
            'accumulated_zakat': 0.0,
            'accumulated_other_reliefs': 0.0,
        }
        try:
            email = (emp.get('email') or '').lower()
            if email:
                prev_m = 12 if m == 1 else m - 1
                prev_y = year - 1 if m == 1 else year
                resp = supabase.table('payroll_ytd_accumulated').select('*') \
                    .eq('employee_email', email) \
                    .eq('year', prev_y) \
                    .eq('month', prev_m) \
                    .execute()
                if resp and resp.data:
                    row = resp.data[0]
                    ytd = {
                        'accumulated_gross': _to_float(row.get('accumulated_gross_salary_ytd', 0.0)),
                        'accumulated_epf': _to_float(row.get('accumulated_epf_employee_ytd', 0.0)),
                        'accumulated_pcb': _to_float(row.get('accumulated_pcb_ytd', 0.0)),
                        'accumulated_zakat': _to_float(row.get('accumulated_zakat_ytd', 0.0)),
                        'accumulated_other_reliefs': _to_float(row.get('accumulated_tax_reliefs_ytd', 0.0)),
                    }
                    ytd_source = 'ytd_table'
                else:
                    # Fallback: sum prior payroll_runs
                    pr = supabase.table('payroll_runs').select('gross_salary, epf_employee, pcb, payroll_date').eq('employee_id', emp.get('id')).execute()
                    rows = pr.data or []
                    if rows:
                        ref = _parse_any_date_local(f"{year}-{m:02d}-01")
                        prior = []
                        for r in rows:
                            try:
                                dtp = _parse_any_date_local(r.get('payroll_date'))
                                if ref and dtp and dtp < ref:
                                    prior.append(r)
                            except Exception:
                                pass
                        if prior:
                            ytd = {
                                'accumulated_gross': sum(_to_float(r.get('gross_salary', 0), 0.0) for r in prior),
                                'accumulated_epf': sum(_to_float(r.get('epf_employee', 0), 0.0) for r in prior),
                                'accumulated_pcb': sum(_to_float(r.get('pcb', 0), 0.0) for r in prior),
                                'accumulated_zakat': 0.0,
                                'accumulated_other_reliefs': 0.0,
                            }
                            ytd_source = 'runs_agg'
        except Exception as e:
            print(f"WARN: YTD lookup failed for {month_year}: {e}")

        # Compute SOCSO+EIS LP1 like GUI path: read prior month claims from payroll_monthly_deductions cap 350/year
        ytd_b20_claimed = 0.0
        try:
            md = supabase.table('payroll_monthly_deductions').select('socso_eis_lp1_monthly, month, year') \
                .eq('employee_id', emp.get('id')).eq('year', year).lt('month', m).execute()
            for r in (md.data or []):
                ytd_b20_claimed += _to_float(r.get('socso_eis_lp1_monthly', 0.0))
        except Exception:
            pass
        remaining_b20 = max(0.0, 350.0 - ytd_b20_claimed)
        # In GUI, SOCSO and EIS amounts are computed from rates; we approximate with the EPF base and a typical employee share ceiling (RM6000) and rates from var_cfg
        socso_rate_emp = _to_float(var_cfg.get('socso_act4_employee_rate') or var_cfg.get('socso_employee_rate') or 0.5)
        eis_rate_emp = _to_float(var_cfg.get('eis_employee_rate') or 0.2)
        socso_eis_base = min(Y1, _to_float(limits_cfg.get('socso_ceiling', 6000.0)))
        b20_this = min(remaining_b20, socso_eis_base * (socso_rate_emp/100.0 + eis_rate_emp/100.0))

        # Compose PCB inputs like GUI path
        payroll_inputs = {
            'accumulated_gross_ytd': ytd['accumulated_gross'],
            'accumulated_epf_ytd': ytd['accumulated_epf'],
            'accumulated_pcb_ytd': ytd['accumulated_pcb'],
            'accumulated_zakat_ytd': ytd['accumulated_zakat'],
            'individual_relief': tax_cfg.get('individual_relief', 9000.0),
            'spouse_relief': _to_float(emp.get('spouse_relief', 0.0)),
            'child_relief': tax_cfg.get('child_relief', 2000.0),
            'child_count': int(emp.get('child_count', emp.get('number_of_children', 0)) or 0),
            'disabled_individual': _to_float(emp.get('disabled_individual', 0.0)),
            'disabled_spouse': _to_float(emp.get('disabled_spouse', 0.0)),
            'other_reliefs_ytd': ytd['accumulated_other_reliefs'] + ytd_b20_claimed,
            'other_reliefs_current': round(b20_this, 2),
            'current_month_zakat': 0.0,
            'debug_pcb': True,
        }

        pcb = calculate_lhdn_pcb_official(payroll_inputs, Y1, K1, tax_cfg, month_year)

        print(f"{month_year}, {pcb:.2f}, {ytd_source}, {ytd['accumulated_pcb']:.2f}, {ytd['accumulated_other_reliefs']+ytd_b20_claimed:.2f}, {round(b20_this,2):.2f}, {K1:.2f}, {Y1:.2f}")


if __name__ == '__main__':
    name = 'Amir Mursyiddin Bin Mustapha'
    months = [1,2,3,4,5,6]
    trace_variable_path(name, months, 2025)
