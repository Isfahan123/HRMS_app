#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'services'))

def test_updated_run_payroll():
    """Quick sanity test for PCB calculation.

    Prints two perspectives:
    - Official monthly PCB (uses divisor n+1 for the given month)
    - UI display monthly PCB (Annual Net Tax ÷ 12), which is what the admin preview shows
    """
    
    try:
        from supabase_service import (
            calculate_lhdn_pcb_official,
            get_default_tax_rates_config,
            get_tax_bracket_details,
        )
        
        # Test the function signature and parameters
        print('=== TESTING UPDATED FUNCTION ===')
        
        # Create test payroll inputs matching your example
        payroll_inputs = {
            'accumulated_gross_ytd': 170000.0,    # YTD gross before current month
            'accumulated_epf_ytd': 18700.0,       # YTD EPF before current month (realistic vs 1,870)
            'accumulated_pcb_ytd': 0.0,           # No previous PCB
            'accumulated_zakat_ytd': 0.0,         # No zakat
            'individual_relief': 9000.0,          # Standard relief
            'spouse_relief': 0.0,
            'disabled_individual': 0.0,
            'disabled_spouse': 0.0,
            'child_relief': 2000.0,
            'child_count': 0,
            'other_reliefs_ytd': 0.0,
            'other_reliefs_current': 41.65,       # Your example current relief
            'current_month_zakat': 0.0,
            'debug_pcb': True
        }
        
        # Test parameters
        gross_monthly = 17000.0
        epf_monthly = 1870.0
        tax_config = get_default_tax_rates_config()
        month_year = "11/2025"  # November 2025 (n+1 divisor => 2)
        
        print(f'Testing with:')
        print(f'  Gross Monthly: RM{gross_monthly:,.2f}')
        print(f'  EPF Monthly: RM{epf_monthly:,.2f}')
        print(f'  Accumulated Gross YTD: RM{payroll_inputs["accumulated_gross_ytd"]:,.2f}')
        print(f'  Accumulated EPF YTD: RM{payroll_inputs["accumulated_epf_ytd"]:,.2f}')
        print(f'  Month/Year: {month_year}')
        
        # Call the function with correct parameter order
        official_monthly = calculate_lhdn_pcb_official(
            payroll_inputs,
            gross_monthly,
            epf_monthly,
            tax_config,
            month_year
        )
        # Compute Annual Net Tax using the same bracket helper, then display Monthly PCB = Annual / 12
        # This mirrors the admin UI preview semantics
        # Annualization (same month profile across the year)
        annual_gross = gross_monthly * 12
        # EPF relief capped for PCB at RM4,000 unless overridden in config
        pcb_epf_cap = float(tax_config.get('pcb_epf_annual_cap', 4000.0) or 4000.0)
        epf_relief_capped = min(epf_monthly * 12, pcb_epf_cap)
        total_reliefs = (
            payroll_inputs['individual_relief'] +
            payroll_inputs['spouse_relief'] +
            payroll_inputs['disabled_individual'] +
            payroll_inputs['disabled_spouse'] +
            (payroll_inputs['child_relief'] * payroll_inputs['child_count']) +
            payroll_inputs['other_reliefs_ytd'] +
            payroll_inputs['other_reliefs_current'] +
            epf_relief_capped
        )
        P = max(0.0, annual_gross - total_reliefs)
        M, R, B = get_tax_bracket_details(P, {}, tax_config)
        annual_tax = ((P - M) * R + B) if P > M else B
        # Apply rebates when under threshold
        rebate_threshold = float(tax_config.get('rebate_threshold', 35000.0))
        if P <= rebate_threshold:
            annual_tax = max(0.0, annual_tax - (
                float(tax_config.get('individual_tax_rebate', 400.0)) +
                float(tax_config.get('spouse_tax_rebate', 400.0))
            ))
        ui_monthly = annual_tax / 12.0

        print(f'\n✅ CALCULATION RESULTS:')
        print(f'Official Monthly PCB (n+1 divisor): RM{official_monthly:,.2f}')
        print(f'UI Display Monthly PCB (Annual/12): RM{ui_monthly:,.2f}')
        print(f'Expected (UI display): RM2,678.30')
        print(f'Difference (UI): RM{abs(ui_monthly - 2678.30):,.2f}')

        if abs(ui_monthly - 2678.30) < 1.0:
            print('🎉 SUCCESS! UI display monthly matches expected!')
        elif abs(ui_monthly - 2678.30) < 10.0:
            print('✅ Very close (UI)! Minor difference within acceptable range.')
        else:
            print('❌ Still significant difference for UI expectation — check tax config/brackets.')
        
        return official_monthly, ui_monthly
            
    except Exception as e:
        print(f'❌ Error in calculation: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    test_updated_run_payroll()
