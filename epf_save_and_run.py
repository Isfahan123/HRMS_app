import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import (
    get_variable_percentage_config,
    save_variable_percentage_config,
    calculate_epf_with_bonus,
    get_epf_contributions_for_wage
)

def save_test_config():
    cfg = get_variable_percentage_config('default') or {}
    print('Current config (snippet):', {k: cfg.get(k) for k in ['epf_part_a_employer_bonus','epf_part_c_employer_bonus']})
    cfg['epf_part_a_employer_bonus'] = 15.0
    cfg['epf_part_c_employer_bonus'] = 8.0
    ok = save_variable_percentage_config(cfg)
    print('Saved test config OK:', ok)
    cfg2 = get_variable_percentage_config('default')
    print('Reloaded config (snippet):', {k: cfg2.get(k) for k in ['epf_part_a_employer_bonus','epf_part_c_employer_bonus']})
    return ok


def run_smoke():
    tests = [
        (4800.0, 500.0, 'part_a'),
        (4800.0, 500.0, 'part_c'),
        (4800.0, 0.0, 'part_a'),
        (6000.0, 0.0, 'part_a'),
    ]
    for basic, bonus, part in tests:
        emp, employer = calculate_epf_with_bonus(basic, bonus, part)
        print(f"Test basic={basic}, bonus={bonus}, part={part} -> employee={emp}, employer={employer}")
    total = 4800.0 + 500.0
    print('--- compare banded lookup for total wage (4800+500) part_a ---')
    print(get_epf_contributions_for_wage(total, 'part_a'))

if __name__ == '__main__':
    ok = save_test_config()
    if ok:
        run_smoke()
    else:
        print('Failed to save config; aborting smoke run')
