#!/usr/bin/env python3

def test_different_interpretations():
    """Test different interpretations of the LHDN formula"""
    
    print('=== TESTING DIFFERENT INTERPRETATIONS ===')
    
    # If your expected values are correct:
    P_expected = 190958.42
    annual_tax_expected = 32139.60
    pcb_expected = 2678.30
    
    print(f'Your expected values:')
    print(f'P = RM{P_expected:,.2f}')
    print(f'Annual Tax = RM{annual_tax_expected:,.2f}')
    print(f'Monthly PCB = RM{pcb_expected:,.2f}')
    
    # Reverse engineering: If PCB = 2678.30, what should the denominator be?
    # PCB = Annual Tax / denominator
    # denominator = Annual Tax / PCB
    implied_denominator = annual_tax_expected / pcb_expected
    print(f'\\nReverse engineering:')
    print(f'Implied denominator = {annual_tax_expected:,.2f} / {pcb_expected:,.2f} = {implied_denominator:.2f}')
    
    # This suggests the formula might be annual tax divided by 12 months, not (n+1)
    pcb_annual_divided_by_12 = annual_tax_expected / 12
    print(f'If divided by 12 months: RM{pcb_annual_divided_by_12:,.2f}')
    
    # Or maybe it's for the remaining period including current month
    current_month = 11
    remaining_months_including_current = 12 - current_month + 1  # 2 months
    pcb_for_remaining = annual_tax_expected / remaining_months_including_current
    print(f'If for remaining {remaining_months_including_current} months: RM{pcb_for_remaining:,.2f}')
    
    # Or maybe there's accumulated PCB to consider
    # If there were previous PCB payments, the formula would be:
    # PCB = (Annual Tax - Accumulated PCB) / (n+1)
    
    # Let's also check the tax calculation with your P value
    print(f'\\n=== TAX CALCULATION WITH YOUR P VALUE ===')
    P = P_expected
    
    # Tax brackets for 2025
    if P <= 5000:
        M, R, B = 0, 0.00, 0
    elif P <= 20000:
        M, R, B = 0, 0.01, 0
    elif P <= 35000:
        M, R, B = 20000, 0.03, 200
    elif P <= 50000:
        M, R, B = 35000, 0.08, 650
    elif P <= 70000:
        M, R, B = 50000, 0.14, 1850
    elif P <= 100000:
        M, R, B = 70000, 0.21, 4650
    elif P <= 400000:
        M, R, B = 100000, 0.24, 10950
    else:
        M, R, B = 400000, 0.245, 82950
    
    print(f'Tax bracket for P = RM{P:,.2f}:')
    print(f'M = RM{M:,.2f}')
    print(f'R = {R:.3f} ({R*100:.1f}%)')
    print(f'B = RM{B:,.2f}')
    
    # Calculate tax using LHDN formula: ((P-M) × R + B)
    tax_before_rebate = ((P - M) * R + B) if P > M else B
    individual_rebate = 400.0
    annual_tax_calculated = max(0, tax_before_rebate - individual_rebate)
    
    print(f'\\nTax calculation:')
    print(f'Tax before rebate = ({P:,.2f} - {M:,.2f}) × {R:.3f} + {B:,.2f} = RM{tax_before_rebate:,.2f}')
    print(f'Tax after RM400 rebate = RM{annual_tax_calculated:,.2f}')
    print(f'Your expected = RM{annual_tax_expected:,.2f}')
    print(f'Difference = RM{abs(annual_tax_calculated - annual_tax_expected):,.2f}')
    
    # Maybe the issue is with how I'm calculating P
    # Let me recalculate P based on your step-by-step calculation
    print(f'\\n=== RECALCULATING P ===')
    
    # From your calculation:
    # Total annual gross = 170,000 + 17,000 + 17,000 = 204,000
    # Total EPF = You said should be 4,073.35
    # Total reliefs = 9,000 + 41.65 = 9,041.65
    
    total_gross = 204000.0
    total_epf = 4073.35  # Your calculation
    total_reliefs = 9041.65
    
    P_your_method = total_gross - total_epf - total_reliefs
    print(f'Your method: {total_gross:,.2f} - {total_epf:,.2f} - {total_reliefs:,.2f} = RM{P_your_method:,.2f}')
    
    # The total EPF of 4,073.35 suggests:
    # Accumulated: 1,870 + Current limited: 333.33 + Future: 1,870 = 4,073.33
    # But if we use full EPF amounts: 1,870 + 1,870 + 1,870 = 5,610
    # Your calculation suggests: 1,870 + 333.33 + 1,870 = 4,073.33
    
    print(f'\\nEPF breakdown analysis:')
    print(f'If accumulated: 1,870 + current limited: 333.33 + future: 1,870 = {1870 + 333.33 + 1870:,.2f}')
    print(f'Your total EPF: {total_epf:,.2f}')

if __name__ == '__main__':
    test_different_interpretations()
