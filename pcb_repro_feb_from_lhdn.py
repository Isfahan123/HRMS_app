import os, sys
from decimal import Decimal

# Ensure project root is on sys.path so 'services' can be imported when running from tools/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import calculate_lhdn_pcb_official, get_lhdn_tax_config


def main():
    # LHDN-provided February scenario
    period = '02/2025'
    Y1 = 11900.00  # gross_monthly (current)
    K1 = 1309.00   # EPF employee (current)

    # Prior month totals (January)
    accumulated_gross_ytd = 11900.00
    accumulated_epf_ytd = 1309.00
    accumulated_pcb_ytd = 1132.50  # X from January (rounded to 0.05)
    accumulated_zakat_ytd = 0.0

    # Reliefs
    D = 9000.00  # individual
    S = 4000.00  # spouse
    Du = 0.00    # disabled individual
    Su = 6000.00 # disabled spouse
    Q = 2000.00  # per child
    C = 1        # child count

    # LP (other reliefs): TP1 + SOCSO+EIS
    LP1 = 1041.65  # current month LP1
    sum_LP_ytd = 1041.65  # accumulated LP up to previous month

    # Build inputs exactly as our PCB function expects
    payroll_inputs = {
        'accumulated_gross_ytd': accumulated_gross_ytd,
        'accumulated_epf_ytd': accumulated_epf_ytd,
        'accumulated_pcb_ytd': accumulated_pcb_ytd,
        'accumulated_zakat_ytd': accumulated_zakat_ytd,
        'individual_relief': D,
        'spouse_relief': S,
        'disabled_individual': Du,
        'disabled_spouse': Su,
        'child_relief': Q,
        'child_count': C,
        'other_reliefs_ytd': sum_LP_ytd,
        'other_reliefs_current': LP1,
        'debug_pcb': True,
    }

    # Load tax config (contains rebates/thresholds; EPF annual cap defaults to 4000 if not set)
    tax_config = get_lhdn_tax_config('default') or {}
    # Force debug in config too, for clearer logs
    tax_config['debug_pcb'] = True

    pcb = calculate_lhdn_pcb_official(
        payroll_inputs,
        Y1,  # gross_monthly
        K1,  # epf_monthly
        tax_config,
        period,
    )
    print(f"\n>>> PCB (rounded to 0.05) for {period} = RM{pcb:.2f}")


if __name__ == '__main__':
    main()
