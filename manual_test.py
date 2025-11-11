#!/usr/bin/env python3

def manual_lhdn_calculation():
    """Manual calculation to understand the discrepancy"""
    
    print('=== MANUAL LHDN PCB CALCULATION ===')
    
    # Your values
    accumulated_gross = 170000.0  # 10 months previous
    accumulated_epf = 1870.0      # K (previous EPF)
    Y1 = 17000.0                  # Current month gross
    epf_monthly_input = 1870.0    # EPF input (but should this be limited?)
    current_month = 11            # November
    individual_relief = 9000.0    # D
    other_reliefs_current = 41.65 # LP1
    
    print(f'Inputs:')
    print(f'Accumulated Gross (10 months): RM{accumulated_gross:,.2f}')
    print(f'Accumulated EPF: RM{accumulated_epf:,.2f}')
    print(f'Current Month Gross (Y1): RM{Y1:,.2f}')
    print(f'Current Month EPF (input): RM{epf_monthly_input:,.2f}')
    print(f'Individual Relief (D): RM{individual_relief:,.2f}')
    print(f'Other Reliefs Current (LP1): RM{other_reliefs_current:,.2f}')
    
    # Calculate with EPF limitation
    K1_limited = min(epf_monthly_input, 4000.0 / 12)  # Limited to RM333.33
    n = 12 - current_month  # n = 1
    Y2 = Y1  # Future month estimate
    
    remaining_epf_limit = max(0, 4000.0 - accumulated_epf - K1_limited)
    K2_limited = min(remaining_epf_limit / n if n > 0 else 0, K1_limited)
    
    print(f'\\nCalculation with EPF limitation:')
    print(f'K1 (limited to RM333.33): RM{K1_limited:,.2f}')
    print(f'n (remaining months): {n}')
    print(f'Remaining EPF limit: RM{remaining_epf_limit:,.2f}')
    print(f'K2 (future EPF): RM{K2_limited:,.2f}')
    
    future_gross_limited = Y2 * n
    future_epf_limited = K2_limited * n
    total_reliefs = individual_relief + other_reliefs_current
    
    P_limited = (accumulated_gross + Y1 + future_gross_limited) - (accumulated_epf + K1_limited + future_epf_limited) - total_reliefs
    P_limited = max(0, P_limited)
    
    print(f'P with EPF limitation: RM{P_limited:,.2f}')
    
    # Calculate without EPF limitation (using full amounts)
    K1_full = epf_monthly_input  # Full amount
    K2_full = epf_monthly_input  # Assume same for future month
    
    future_gross_full = Y2 * n
    future_epf_full = K2_full * n
    
    P_full = (accumulated_gross + Y1 + future_gross_full) - (accumulated_epf + K1_full + future_epf_full) - total_reliefs
    P_full = max(0, P_full)
    
    print(f'P without EPF limitation: RM{P_full:,.2f}')
    print(f'Your expected P: RM190,958.42')
    
    # Tax calculation for both scenarios
    print(f'\\n=== TAX CALCULATION ===')
    
    # Find tax bracket for P_full (your expected value)
    def calculate_tax(P):
        if P <= 5000:
            return 0
        elif P <= 20000:
            return (P - 0) * 0.01
        elif P <= 35000:
            return (P - 20000) * 0.03 + 200
        elif P <= 50000:
            return (P - 35000) * 0.08 + 650
        elif P <= 70000:
            return (P - 50000) * 0.14 + 1850
        elif P <= 100000:
            return (P - 70000) * 0.21 + 4650
        elif P <= 400000:
            return (P - 100000) * 0.24 + 10950
        else:
            return (P - 400000) * 0.245 + 82950
    
    # Apply individual tax rebate RM400
    tax_before_rebate = calculate_tax(P_full)
    annual_tax = max(0, tax_before_rebate - 400)
    
    print(f'Annual tax before rebate: RM{tax_before_rebate:,.2f}')
    print(f'Individual tax rebate: RM400.00')
    print(f'Annual tax after rebate: RM{annual_tax:,.2f}')
    print(f'Your expected annual tax: RM32,139.60')
    
    # PCB calculation
    n_plus_1 = n + 1  # 2 months (current + remaining)
    pcb = annual_tax / n_plus_1
    print(f'\\nPCB = {annual_tax:,.2f} / {n_plus_1} = RM{pcb:,.2f}')
    print(f'Your expected PCB: RM2,678.30')

if __name__ == '__main__':
    manual_lhdn_calculation()
