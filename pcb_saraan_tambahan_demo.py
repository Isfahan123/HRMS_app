import os
import sys

# Ensure project root is on sys.path so `services` can be imported when running from tools/
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import calculate_pcb_additional_remuneration

# Reproduce the user's worksheet for a January case (n=11)
# Given values:
# Y1=11,900.00, K1=1,309.00, Y2=11,900.00, K2≈244.65 (A)
# D=9,000; S=4,000; Du=0; Su=6,000; Q=2,000; C=1; ΣLP=0; LP1=1,041.65
# Z=0; X=0; Yt=1,000; Kt=500

month_year = "01/2025"  # January -> n=11, n+1=12

payroll_inputs = {
    # YTD state (zeros for January example)
    'accumulated_gross_ytd': 0.0,
    'accumulated_epf_ytd': 0.0,
    'accumulated_pcb_ytd': 0.0,  # X
    'accumulated_zakat_ytd': 0.0,  # Z

    # Reliefs
    'individual_relief': 9000.0,  # D
    'spouse_relief': 4000.0,      # S
    'disabled_individual': 0.0,   # Du
    'disabled_spouse': 6000.0,    # Su
    'child_relief': 2000.0,       # Q
    'child_count': 1,             # C

    # Other reliefs
    'other_reliefs_ytd': 0.0,        # ΣLP
    'other_reliefs_current': 1041.65, # LP1

    # Current month zakat
    'current_month_zakat': 0.0,

    # Optional toggles
    'debug_pcb': False,
}

# Minimal tax config — defaults use official rounding (ceil to RM0.05) and divisor n+1
# PCB EPF annual cap is taken from tax_relief_max_config or defaults to 4,000.

tax_config = {
    'config_name': 'default',
    # You can force options here if needed:
    # 'rounding_mode': 'ceiling_0_05',
    # 'divisor_mode': 'n_plus_1',
    # 'include_lp1_in_annual': True,
}

Y1 = 11900.0
K1 = 1309.0
Yt = 1000.0
Kt = 500.0

res = calculate_pcb_additional_remuneration(
    payroll_inputs=payroll_inputs,
    gross_monthly=Y1,
    epf_monthly=K1,
    tax_config=tax_config,
    month_year=month_year,
    additional_gross=Yt,
    additional_epf=Kt,
)

print("\n— Demo: PCB with Saraan Tambahan (January) —")
print(f"n={int(res.get('n', 0))}, n+1={int(res.get('n_plus_1', 0))}")
print(f"K2 (monthly)≈ {res.get('K2_monthly')}")
print(f"K2 (with Yt/Kt)≈ {res.get('K2_with_YtKt')}")
print(f"P (monthly)≈ {res.get('P_monthly')}")
print(f"P (with Yt/Kt)≈ {res.get('P_with_YtKt')}")
print(f"PCB(A) raw: {res['pcb_A_raw']:.2f}  rounded: {res['pcb_A_rounded']:.2f}")
print(f"CS (annual tax with Yt/Kt): {res['CS_annual_tax']:.2f}")
print(f"PCB(C) raw: {res['pcb_C_raw']:.2f}  rounded: {res['pcb_C_rounded']:.2f}")
print(f"PCB total raw (A - zakat + C): {res['pcb_total_raw']:.2f}")
print(f"PCB total rounded (A - zakat + C): {res['pcb_total_rounded']:.2f}")
