import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import calculate_lhdn_pcb_official, get_default_tax_rates_config

def run(case: str):
    tax = get_default_tax_rates_config()
    tax['debug_pcb'] = True
    # Simulate February: use prior-month YTD (January) as context
    # Assume Jan PCB already paid X = 2678.30
    payroll_inputs = {
        'accumulated_gross_ytd': 17000.0,       # Jan gross
        'accumulated_epf_ytd': 1870.0,          # Jan EPF
        'accumulated_pcb_ytd': 2678.30,         # X (Jan PCB)
        'accumulated_zakat_ytd': 0.0,
        'individual_relief': 9000.0,
        'spouse_relief': 0.0,
        'disabled_individual': 0.0,
        'disabled_spouse': 0.0,
        'child_relief': 0.0,
        'child_count': 0,
        'other_reliefs_ytd': 0.0,
        'other_reliefs_current': 41.65 if case=='with_b20' else 0.0,
        'current_month_zakat': 0.0,
        'debug_pcb': True,
    }
    gross_monthly = 17000.0
    epf_monthly = 1870.0
    month_year = '02/2025'
    result = calculate_lhdn_pcb_official(
        payroll_inputs,
        gross_monthly,
        epf_monthly,
        tax,
        month_year
    )
    print(f"Case {case}: Feb PCB = RM{result:.2f}")

if __name__ == '__main__':
    run('with_b20')
    run('no_b20')
