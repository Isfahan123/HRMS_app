#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

from supabase_service import calculate_lhdn_pcb_official

def test_updated_calculation():
    """Test the updated LHDN PCB calculation"""
    
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
    epf_monthly = 1870.0     # K1 input
    current_month = 11       # November (11th month)

    print('=== TESTING UPDATED LHDN PCB CALCULATION ===')
    print(f'Gross Monthly (Y1): RM{gross_monthly:,.2f}')
    print(f'EPF Monthly (input): RM{epf_monthly:,.2f}')
    print(f'Current Month: {current_month}')
    
    try:
        result = calculate_lhdn_pcb_official(gross_monthly, epf_monthly, current_month, payroll_inputs)
        
        print(f'\\n✅ CALCULATION RESULTS:')
        print(f'Calculated PCB: RM{result:,.2f}')
        print(f'Expected PCB: RM2,678.30')
        print(f'Difference: RM{abs(result - 2678.30):,.2f}')
        
        if abs(result - 2678.30) < 1.0:
            print('🎉 SUCCESS! Calculation matches expected result!')
        elif abs(result - 2678.30) < 10.0:
            print('✅ Very close! Minor difference within acceptable range.')
        else:
            print('❌ Still significant difference.')
            
    except Exception as e:
        print(f'❌ Error in calculation: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_updated_calculation()
