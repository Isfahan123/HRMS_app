# Malaysian PCB (Monthly Tax Deduction) Calculator
# Based on LHDN 2025 Tax Rates and Official Guidelines

from typing import Dict, Tuple
import math

class MalaysianPCBCalculator:
    """
    Official Malaysian PCB Calculator based on LHDN 2025 tax rates
    Implements progressive tax rates, reliefs, and rebates
    """
    
    # LHDN 2025 Progressive Tax Rates for Resident Individuals
    # Based on Official HASIL Tax Structure
    TAX_BRACKETS = [
        (5000, 0.00),      # A: 0 - 5,000: 0%
        (20000, 0.01),     # B: 5,001 - 20,000: 1% 
        (35000, 0.03),     # C: 20,001 - 35,000: 3%
        (50000, 0.06),     # D: 35,001 - 50,000: 6%
        (70000, 0.11),     # E: 50,001 - 70,000: 11%
        (100000, 0.19),    # F: 70,001 - 100,000: 19%
        (400000, 0.25),    # G: 100,001 - 400,000: 25%
        (600000, 0.26),    # H: 400,001 - 600,000: 26%
        (2000000, 0.28),   # I: 600,001 - 2,000,000: 28%
        (float('inf'), 0.30)  # J: Above 2,000,000: 30%
    ]
    
    # Standard Tax Reliefs (Annual)
    STANDARD_RELIEFS = {
        'personal': 9000,           # Personal relief
        'spouse': 4000,             # Spouse relief (if no income)
        'child_under_18': 2000,     # Per child under 18
        'child_tertiary': 8000,     # Per child in tertiary education
        'epf_max': 6000,            # EPF contribution relief (max)
        'life_insurance_max': 3000, # Life insurance premium relief (max)
        'medical_serious': 10000,   # Medical expenses for serious diseases
        'medical_checkup': 1000,    # Medical check-up expenses
        'lifestyle_max': 2500       # Lifestyle relief (books, computers, gym)
    }
    
    # Tax Rebate
    TAX_REBATE = 400  # For chargeable income ≤ RM35,000
    REBATE_THRESHOLD = 35000
    
    def __init__(self):
        pass
    
    def calculate_annual_tax(self, chargeable_income: float) -> Tuple[float, float]:
        """
        Calculate annual tax based on progressive rates
        Returns (gross_tax, net_tax_after_rebate)
        """
        if chargeable_income <= 0:
            return 0.0, 0.0
        
        gross_tax = 0.0
        remaining_income = chargeable_income
        previous_bracket = 0
        
        for bracket_limit, rate in self.TAX_BRACKETS:
            if remaining_income <= 0:
                break
                
            taxable_in_bracket = min(remaining_income, bracket_limit - previous_bracket)
            gross_tax += taxable_in_bracket * rate
            remaining_income -= taxable_in_bracket
            previous_bracket = bracket_limit
            
            if bracket_limit == float('inf'):
                break
        
        # Apply rebate for low income earners
        net_tax = gross_tax
        if chargeable_income <= self.REBATE_THRESHOLD:
            net_tax = max(0, gross_tax - self.TAX_REBATE)
        
        return gross_tax, net_tax
    
    def calculate_monthly_taxable_income(self, 
                                       gross_salary: float,
                                       unpaid_leave_deduction: float,
                                       epf_employee: float,
                                       socso_employee: float,
                                       eis_employee: float,
                                       other_deductions: float = 0.0) -> float:
        """
        Calculate monthly taxable income after deductions
        """
        net_salary = gross_salary - unpaid_leave_deduction
        total_deductions = epf_employee + socso_employee + eis_employee + other_deductions
        return net_salary - total_deductions
    
    def calculate_pcb(self, 
                     monthly_taxable_income: float,
                     reliefs: Dict[str, float] = None,
                     is_resident: bool = True) -> Dict[str, float]:
        """
        Calculate monthly PCB based on annualized income and reliefs
        
        Args:
            monthly_taxable_income: Monthly taxable income after statutory deductions
            reliefs: Dictionary of applicable reliefs
            is_resident: Whether employee is Malaysian tax resident
        
        Returns:
            Dictionary with calculation breakdown
        """
        if reliefs is None:
            reliefs = {'personal': self.STANDARD_RELIEFS['personal']}
        
        # Annualize income
        annual_taxable_income = monthly_taxable_income * 12
        
        # Non-resident flat rate
        if not is_resident:
            annual_tax = annual_taxable_income * 0.30
            monthly_pcb = annual_tax / 12
            return {
                'monthly_taxable_income': monthly_taxable_income,
                'annual_taxable_income': annual_taxable_income,
                'total_reliefs': 0,
                'chargeable_income': annual_taxable_income,
                'annual_gross_tax': annual_tax,
                'annual_net_tax': annual_tax,
                'monthly_pcb': monthly_pcb,
                'tax_rate': '30% (Non-resident)',
                'rebate_applied': 0
            }
        
        # Calculate total reliefs
        total_reliefs = sum(reliefs.values())
        
        # Calculate chargeable income
        chargeable_income = max(0, annual_taxable_income - total_reliefs)
        
        # Calculate tax
        gross_tax, net_tax = self.calculate_annual_tax(chargeable_income)
        
        # Monthly PCB
        monthly_pcb = net_tax / 12
        
        return {
            'monthly_taxable_income': monthly_taxable_income,
            'annual_taxable_income': annual_taxable_income,
            'total_reliefs': total_reliefs,
            'chargeable_income': chargeable_income,
            'annual_gross_tax': gross_tax,
            'annual_net_tax': net_tax,
            'monthly_pcb': monthly_pcb,
            'rebate_applied': gross_tax - net_tax,
            'effective_tax_rate': (net_tax / annual_taxable_income * 100) if annual_taxable_income > 0 else 0
        }
    
    def get_tax_bracket_info(self, chargeable_income: float) -> str:
        """Get tax bracket information for display"""
        if chargeable_income <= 0:
            return "No tax bracket (0% rate)"
        
        for i, (bracket_limit, rate) in enumerate(self.TAX_BRACKETS):
            if chargeable_income <= bracket_limit:
                if i == 0:
                    return f"Bracket 1: RM0 - RM{bracket_limit:,.0f} ({rate*100}%)"
                else:
                    prev_limit = self.TAX_BRACKETS[i-1][0]
                    if bracket_limit == float('inf'):
                        return f"Bracket {i+1}: Above RM{prev_limit:,.0f} ({rate*100}%)"
                    else:
                        return f"Bracket {i+1}: RM{prev_limit:,.0f} - RM{bracket_limit:,.0f} ({rate*100}%)"
        
        return "Above highest bracket (30%)"


# Example usage and test cases
def test_pcb_calculator():
    """Test the PCB calculator with the examples provided"""
    calc = MalaysianPCBCalculator()
    
    print("=== Malaysian PCB Calculator Test Cases ===\n")
    
    # Example 1: Employee Under 60, with Unpaid Leave
    print("Example 1: Employee Under 60, Unpaid Leave")
    print("Profile: RM3,000/month, single, 5 days unpaid leave")
    
    gross_salary = 3000
    unpaid_deduction = 500  # 5 days unpaid leave
    epf = 275  # 11% of RM2,500
    socso = 12.25  # Under 60
    eis = 5  # 0.2% of RM2,500
    
    monthly_taxable = calc.calculate_monthly_taxable_income(
        gross_salary, unpaid_deduction, epf, socso, eis
    )
    
    reliefs = {
        'personal': 9000,
        'epf': min(6000, epf * 12)  # EPF relief capped at RM6,000
    }
    
    result = calc.calculate_pcb(monthly_taxable, reliefs)
    
    print(f"Gross Salary: RM{gross_salary:,.2f}")
    print(f"Unpaid Leave Deduction: RM{unpaid_deduction:,.2f}")
    print(f"Net Salary: RM{gross_salary - unpaid_deduction:,.2f}")
    print(f"EPF: RM{epf:,.2f}")
    print(f"SOCSO: RM{socso:,.2f}")
    print(f"EIS: RM{eis:,.2f}")
    print(f"Monthly Taxable Income: RM{result['monthly_taxable_income']:,.2f}")
    print(f"Annual Taxable Income: RM{result['annual_taxable_income']:,.2f}")
    print(f"Total Reliefs: RM{result['total_reliefs']:,.2f}")
    print(f"Chargeable Income: RM{result['chargeable_income']:,.2f}")
    print(f"Annual Tax (Gross): RM{result['annual_gross_tax']:,.2f}")
    print(f"Rebate Applied: RM{result['rebate_applied']:,.2f}")
    print(f"Annual Tax (Net): RM{result['annual_net_tax']:,.2f}")
    print(f"Monthly PCB: RM{result['monthly_pcb']:,.2f}")
    print(f"Tax Bracket: {calc.get_tax_bracket_info(result['chargeable_income'])}")
    print()
    
    # Example 4: Higher Earner
    print("Example 4: Higher Earner")
    print("Profile: RM10,000/month, married with 1 child (under 18)")
    
    gross_salary = 10000
    epf = 900  # 9% of RM10,000
    socso = 24.65  # Capped
    eis = 10  # Capped
    
    monthly_taxable = calc.calculate_monthly_taxable_income(
        gross_salary, 0, epf, socso, eis
    )
    
    reliefs = {
        'personal': 9000,
        'spouse': 4000,
        'child_under_18': 2000,
        'epf': 6000  # Capped at RM6,000 for relief
    }
    
    result = calc.calculate_pcb(monthly_taxable, reliefs)
    
    print(f"Gross Salary: RM{gross_salary:,.2f}")
    print(f"EPF: RM{epf:,.2f}")
    print(f"SOCSO: RM{socso:,.2f}")
    print(f"EIS: RM{eis:,.2f}")
    print(f"Monthly Taxable Income: RM{result['monthly_taxable_income']:,.2f}")
    print(f"Annual Taxable Income: RM{result['annual_taxable_income']:,.2f}")
    print(f"Total Reliefs: RM{result['total_reliefs']:,.2f}")
    print(f"Chargeable Income: RM{result['chargeable_income']:,.2f}")
    print(f"Annual Tax (Gross): RM{result['annual_gross_tax']:,.2f}")
    print(f"Annual Tax (Net): RM{result['annual_net_tax']:,.2f}")
    print(f"Monthly PCB: RM{result['monthly_pcb']:,.2f}")
    print(f"Effective Tax Rate: {result['effective_tax_rate']:.2f}%")
    print(f"Tax Bracket: {calc.get_tax_bracket_info(result['chargeable_income'])}")

if __name__ == "__main__":
    test_pcb_calculator()
