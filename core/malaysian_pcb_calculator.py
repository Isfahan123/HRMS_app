#!/usr/bin/env python3
"""
Malaysian PCB (Pay as You Earn) Calculator
Based on LHDN (Inland Revenue Board) Schedule 1 for 2025
"""

def calculate_malaysian_pcb(annual_gross_income, annual_epf_employee, marital_status="single", spouse_income=0.0, number_of_children=0):
    """
    Calculate Malaysian PCB (Pay as You Earn) tax based on current LHDN rates
    
    Parameters:
        pass
    - annual_gross_income: Annual gross salary
    - annual_epf_employee: Annual EPF employee contribution
    - marital_status: "single", "married", "divorced", "widowed"
    - spouse_income: Annual spouse income (if applicable)
    - number_of_children: Number of dependent children
    
    Returns:
        pass
    - dict with tax calculation details
    """
    
    # Calculate chargeable income
    chargeable_income = annual_gross_income - annual_epf_employee
    
    # Personal reliefs (2025 rates)
    personal_relief = 9000  # Basic personal relief
    spouse_relief = 0
    child_relief = 0
    
    # Determine additional reliefs based on marital status
    if marital_status.lower() in ["married"]:
        if spouse_income == 0 or spouse_income < 4000:  # Non-working spouse or very low income
            spouse_relief = 4000
        elif spouse_income < 9000:  # Working spouse with income below personal relief threshold
            spouse_relief = max(0, 4000 - (spouse_income - 4000))
    
    # Child relief (RM2,000 per child, max 6 children)
    child_relief = min(number_of_children * 2000, 12000)
    
    # Total reliefs
    total_reliefs = personal_relief + spouse_relief + child_relief
    
    # Taxable income after reliefs
    taxable_income = max(0, chargeable_income - total_reliefs)
    
    # Malaysian Income Tax Rates 2025 (Resident Individual)
    tax_brackets = [
        (5000, 0.0),      # First RM5,000 - 0%
        (15000, 0.01),    # Next RM15,000 (RM5,001 - RM20,000) - 1%
        (15000, 0.03),    # Next RM15,000 (RM20,001 - RM35,000) - 3%
        (15000, 0.06),    # Next RM15,000 (RM35,001 - RM50,000) - 6%
        (20000, 0.11),    # Next RM20,000 (RM50,001 - RM70,000) - 11%
        (30000, 0.19),    # Next RM30,000 (RM70,001 - RM100,000) - 19%
        (150000, 0.25),   # Next RM150,000 (RM100,001 - RM250,000) - 25%
        (150000, 0.26),   # Next RM150,000 (RM250,001 - RM400,000) - 26%
        (200000, 0.28),   # Next RM200,000 (RM400,001 - RM600,000) - 28%
        (float('inf'), 0.30)  # Above RM600,000 - 30%
    ]
    
    # Calculate tax
    annual_tax = 0
    remaining_income = taxable_income
    
    tax_breakdown = []
    
    for bracket_amount, rate in tax_brackets:
        if remaining_income <= 0:
            break
            
        taxable_in_bracket = min(remaining_income, bracket_amount)
        tax_in_bracket = taxable_in_bracket * rate
        annual_tax += tax_in_bracket
        
        if taxable_in_bracket > 0:
            tax_breakdown.append({
                'amount': taxable_in_bracket,
                'rate': rate * 100,
                'tax': tax_in_bracket
            })
        
        remaining_income -= taxable_in_bracket
    
    # Monthly PCB (divide annual tax by 12)
    monthly_pcb = annual_tax / 12
    
    return {
        'annual_gross_income': annual_gross_income,
        'annual_epf_employee': annual_epf_employee,
        'chargeable_income': chargeable_income,
        'personal_relief': personal_relief,
        'spouse_relief': spouse_relief,
        'child_relief': child_relief,
        'total_reliefs': total_reliefs,
        'taxable_income': taxable_income,
        'annual_tax': annual_tax,
        'monthly_pcb': monthly_pcb,
        'tax_breakdown': tax_breakdown,
        'effective_tax_rate': (annual_tax / annual_gross_income * 100) if annual_gross_income > 0 else 0
    }

def calculate_monthly_pcb(monthly_gross_salary, monthly_epf_employee, marital_status="single", spouse_annual_income=0.0, number_of_children=0):
    """
    Calculate monthly PCB from monthly salary
    
    Parameters:
        pass
    - monthly_gross_salary: Monthly gross salary
    - monthly_epf_employee: Monthly EPF employee contribution
    - marital_status: "single", "married", "divorced", "widowed"
    - spouse_annual_income: Annual spouse income
    - number_of_children: Number of dependent children
    
    Returns:
        pass
    - Monthly PCB amount
    """
    
    # Convert to annual figures
    annual_gross = monthly_gross_salary * 12
    annual_epf = monthly_epf_employee * 12
    
    # Calculate PCB
    result = calculate_malaysian_pcb(
        annual_gross, 
        annual_epf, 
        marital_status, 
        spouse_annual_income, 
        number_of_children
    )
    
    return result['monthly_pcb']

# Test the calculator
if __name__ == "__main__":
    print("=== Malaysian PCB Calculator Test ===")
    
    # Test case 1: Single person
    print("\n1. Single person, RM5,000/month:")
    result1 = calculate_malaysian_pcb(60000, 7200, "single", 0, 0)
    print(f"   Monthly PCB: RM{result1['monthly_pcb']:.2f}")
    print(f"   Annual Tax: RM{result1['annual_tax']:.2f}")
    print(f"   Effective Rate: {result1['effective_tax_rate']:.2f}%")
    
    # Test case 2: Married with non-working spouse
    print("\n2. Married, RM8,000/month, non-working spouse:")
    result2 = calculate_malaysian_pcb(96000, 11520, "married", 0, 0)
    print(f"   Monthly PCB: RM{result2['monthly_pcb']:.2f}")
    print(f"   Annual Tax: RM{result2['annual_tax']:.2f}")
    print(f"   Effective Rate: {result2['effective_tax_rate']:.2f}%")
    
    # Test case 3: Married with working spouse and children
    print("\n3. Married, RM10,000/month, spouse earns RM36,000/year, 2 children:")
    result3 = calculate_malaysian_pcb(120000, 14400, "married", 36000, 2)
    print(f"   Monthly PCB: RM{result3['monthly_pcb']:.2f}")
    print(f"   Annual Tax: RM{result3['annual_tax']:.2f}")
    print(f"   Effective Rate: {result3['effective_tax_rate']:.2f}%")
    print(f"   Personal Relief: RM{result3['personal_relief']}")
    print(f"   Spouse Relief: RM{result3['spouse_relief']}")
    print(f"   Child Relief: RM{result3['child_relief']}")
