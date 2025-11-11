#!/usr/bin/env python3
import sys
import os
# Ensure project root is on sys.path
proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

from services.supabase_service import calculate_lhdn_pcb_official

def test_lhdn_calculation():
    """Test LHDN PCB calculation with user's exact example"""
    
    # Your exact example values
    payroll_inputs = {
        'accumulated_gross_ytd': 170000.0,    # Previous 10 months
        'accumulated_epf_ytd': 1870.0,        # K (previous EPF)
        'accumulated_pcb_ytd': 0.0,           # X (no previous PCB)
        'accumulated_zakat_ytd': 0.0,         # Z (no zakat)
        'individual_relief': 9000.0,          # D
        'spouse_relief': 0.0,                 # S
        'disabled_individual': 0.0,           # Du
        'disabled_spouse': 0.0,              # Su
        'child_relief': 0.0,                 # Q
        'child_count': 0,                    # C
        'other_reliefs_ytd': 0.0,           # Sum of LP
        'other_reliefs_current': 41.65,     # LP1 current month
        'current_month_zakat': 0.0
    }

    gross_monthly = 17000.0  # Y1
    epf_monthly = 1870.0     # K1 - but should be limited to RM333.33 (4000/12)
    current_month = 11       # November (11th month)

    print('=== DEBUGGING LHDN PCB CALCULATION ===')
    print(f'Gross Monthly (Y1): RM{gross_monthly:,.2f}')
    print(f'EPF Monthly (K1): RM{epf_monthly:,.2f}')
    print(f'EPF Limited to RM333.33: RM{min(epf_monthly, 4000.0/12):,.2f}')
    print(f'Current Month: {current_month}')
    print(f'Accumulated Gross YTD: RM{payroll_inputs["accumulated_gross_ytd"]:,.2f}')
    print(f'Accumulated EPF YTD (K): RM{payroll_inputs["accumulated_epf_ytd"]:,.2f}')
    
    # Manual step-by-step calculation
    accumulated_gross = payroll_inputs['accumulated_gross_ytd']
    accumulated_epf = payroll_inputs['accumulated_epf_ytd']
    Y1 = gross_monthly
    K1 = min(epf_monthly, 4000.0 / 12)  # EPF limited to RM333.33 monthly
    n = 12 - current_month  # n = 1 (remaining months)
    Y2 = Y1  # Estimate future months same as current
    
    # Calculate remaining EPF allowance
    remaining_epf_limit = max(0, 4000.0 - accumulated_epf - K1)
    K2 = min(remaining_epf_limit / n if n > 0 else 0, K1)
    
    print(f'\\nStep-by-step calculation:')
    print(f'n (remaining months): {n}')
    print(f'n+1: {n+1}')
    print(f'K1 (EPF this month, limited): RM{K1:,.2f}')
    print(f'Remaining EPF limit: RM{remaining_epf_limit:,.2f}')
    print(f'K2 (future EPF per month): RM{K2:,.2f}')
    
    # Calculate P (Annual taxable income)
    future_gross = Y2 * n if n > 0 else 0
    future_epf = K2 * n if n > 0 else 0
    individual_relief = payroll_inputs['individual_relief']
    other_reliefs_current = payroll_inputs['other_reliefs_current']
    
    total_gross = accumulated_gross + Y1 + future_gross
    total_epf = accumulated_epf + K1 + future_epf
    total_reliefs = individual_relief + other_reliefs_current
    
    P = total_gross - total_epf - total_reliefs
    P = max(0, P)
    
    print(f'\\nP Calculation:')
    print(f'Total Gross Income: {accumulated_gross:,.2f} + {Y1:,.2f} + {future_gross:,.2f} = RM{total_gross:,.2f}')
    print(f'Total EPF: {accumulated_epf:,.2f} + {K1:,.2f} + {future_epf:,.2f} = RM{total_epf:,.2f}')
    print(f'Total Reliefs: {individual_relief:,.2f} + {other_reliefs_current:,.2f} = RM{total_reliefs:,.2f}')
    print(f'P (Annual Taxable Income): RM{P:,.2f}')
    print(f'Expected P from your calculation: RM190,958.42')
    
    # Call the actual function
    try:
        result = calculate_lhdn_pcb_official(gross_monthly, epf_monthly, current_month, payroll_inputs)
        print(f'\\nActual PCB Result: RM{result:,.2f}')
        print(f'Expected PCB Result: RM2,678.30')
        print(f'Difference: RM{abs(result - 2678.30):,.2f}')
        
        if abs(result - 2678.30) < 1.0:
            print('✅ CALCULATION MATCHES!')
        else:
            print('❌ CALCULATION DIFFERS!')
            
    except Exception as e:
        print(f'Error in calculation: {e}')

if __name__ == '__main__':
    test_lhdn_calculation()
