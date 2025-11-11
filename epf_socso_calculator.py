"""
EPF/SOCSO Calculator - Based on Official Malaysian Regulations
Handles all 5 EPF Parts (A, B, C, D, E) according to official EPF regulations
"""

from datetime import datetime, date
from typing import Tuple, Dict, Optional

class EPFSOCSCalculator:
    """
    Calculator for EPF and SOCSO contributions based on official Malaysian regulations.
    """
    
    @staticmethod
    def calculate_age(birth_date: str) -> int:
        """Calculate age from birth date string."""
        if isinstance(birth_date, str):
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        elif isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        
        today = date.today()
        age = today.year - birth_date.year
        if today.month < birth_date.month or (today.month == birth_date.month and today.day < birth_date.day):
            age -= 1
        return age
    
    @staticmethod
    def determine_citizenship_status(nationality: str, citizenship: str) -> Tuple[bool, bool, bool]:
        """
        Determine citizenship status.
        Returns: (is_malaysian, is_pr, is_non_citizen)
        """
        nationality = (nationality or "").lower().strip()
        citizenship = (citizenship or "").lower().strip()
        
        # Malaysian citizens
        is_malaysian = (
            nationality in ['malaysia', 'malaysian'] or
            citizenship in ['malaysian citizen', 'citizen', 'malaysian']
        )
        
        # Permanent residents
        is_pr = citizenship in ['permanent resident', 'pr']
        
        # Non-citizens (neither Malaysian nor PR)
        is_non_citizen = not is_malaysian and not is_pr
        
        return is_malaysian, is_pr, is_non_citizen
    
    @classmethod
    def calculate_epf_part(cls, birth_date: str, nationality: str, citizenship: str, 
                          election_date: Optional[str] = None) -> str:
        """
        Calculate EPF part based on official regulations.
        
        Args:
            birth_date: Employee's birth date
            nationality: Employee's nationality
            citizenship: Employee's citizenship status
            election_date: Date when non-citizen elected to contribute (if applicable)
        
        Returns:
            EPF part string: 'part_a', 'part_b', 'part_c', 'part_d', or 'part_e'
        """
        age = cls.calculate_age(birth_date)
        is_malaysian, is_pr, is_non_citizen = cls.determine_citizenship_status(nationality, citizenship)
        
        # Malaysian citizens
        if is_malaysian:
            if age < 60:
                return 'part_a'  # Part A: Malaysian citizens under 60
            else:
                return 'part_e'  # Part E: Malaysian citizens 60 and above
        
        # Permanent residents
        elif is_pr:
            if age < 60:
                return 'part_a'  # Part A: PRs under 60
            else:
                return 'part_c'  # Part C: PRs 60 and above
        
        # Non-citizens
        elif is_non_citizen:
            # For simplicity, assume post-1998 election unless specified
            # In a real system, you'd check the actual election date
            elected_before_aug_1998 = False
            if election_date:
                try:
                    election_dt = datetime.strptime(election_date, '%Y-%m-%d').date()
                    elected_before_aug_1998 = election_dt < date(1998, 8, 1)
                except:
                    pass
            
            if age < 60:
                if elected_before_aug_1998:
                    return 'part_a'  # Part A: Non-citizens under 60, elected before 1/8/1998
                else:
                    return 'part_b'  # Part B: Non-citizens under 60, elected on/after 1/8/1998
            else:
                if elected_before_aug_1998:
                    return 'part_c'  # Part C: Non-citizens 60+, elected before 1/8/1998
                else:
                    return 'part_d'  # Part D: Non-citizens 60+, elected on/after 1/8/1998
        
        # Default case (should not happen)
        return 'part_a'
    
    @classmethod
    def get_epf_part_description(cls, epf_part: str) -> str:
        """Get human-readable description of EPF part."""
        descriptions = {
            'part_a': 'Part A (Citizens <60, PRs <60, Non-citizens <60 pre-1998)',
            'part_b': 'Part B (Non-citizens <60 post-1998)',
            'part_c': 'Part C (PRs ≥60, Non-citizens ≥60 pre-1998)',
            'part_d': 'Part D (Non-citizens ≥60 post-1998)',
            'part_e': 'Part E (Malaysian citizens ≥60)'
        }
        return descriptions.get(epf_part, f'Unknown part: {epf_part}')
    
    @classmethod
    def calculate_socso_category(cls, birth_date: str, nationality: str, citizenship: str) -> str:
        """
        Calculate SOCSO category based on age and citizenship.
        Updated per PERKESO official regulations - Foreign workers ARE eligible!
        
        Returns:
            'Category 1' for all eligible employees under 55/60
            'Category 2' for employees 55+/60+ 
            'Foreign Worker First' for foreign workers under 55
            'Foreign Worker Second' for foreign workers 55+ or 60+
        """
        age = cls.calculate_age(birth_date)
        is_malaysian, is_pr, is_non_citizen = cls.determine_citizenship_status(nationality, citizenship)
        
        # All eligible employees follow the same SOCSO category system
        # regardless of citizenship (per PERKESO regulations)
        if is_malaysian or is_pr or is_non_citizen:
            if age < 60:
                return 'Category1'  # Under 60, mandatory coverage
            else:
                return 'Category2'  # 60 and above, limited coverage
        else:
            return 'Unknown'  # Fallback for unknown citizenship status
    
    @classmethod
    def calculate_epf_socso_status(cls, birth_date: str, nationality: str, citizenship: str, 
                                 basic_salary: float = 0, election_date: Optional[str] = None) -> Dict[str, str]:
        """
        Calculate comprehensive EPF and SOCSO status for an employee.
        
        Returns:
            Dictionary with EPF and SOCSO status information
        """
        age = cls.calculate_age(birth_date)
        is_malaysian, is_pr, is_non_citizen = cls.determine_citizenship_status(nationality, citizenship)
        
        # Calculate EPF part
        epf_part = cls.calculate_epf_part(birth_date, nationality, citizenship, election_date)
        epf_description = cls.get_epf_part_description(epf_part)
        
        # EPF Status
        if is_malaysian:
            epf_status = "Automatically Eligible (Malaysian Citizen)"
        elif is_pr:
            epf_status = "Automatically Eligible (Permanent Resident)"
        else:
            epf_status = f"Voluntary Contribution ({epf_part.upper()})"
        
        # SOCSO Status (Updated per PERKESO official regulations)
        socso_category = cls.calculate_socso_category(birth_date, nationality, citizenship)
        if socso_category == 'Category1':
            socso_status = "Mandatory (Malaysian/PR Under 60)"
        elif socso_category == 'Category2':
            socso_status = "Limited Coverage (Malaysian/PR 60+)"
        elif socso_category == 'Foreign Worker First':
            socso_status = "Mandatory (Foreign Worker Under 55)"
        elif socso_category == 'Foreign Worker Second':
            socso_status = "Mandatory (Foreign Worker 55+)"
        else:
            socso_status = "Unknown Status"
        
        return {
            'epf_status': epf_status,
            'epf_part': epf_part,
            'epf_description': epf_description,
            'socso_status': socso_status,
            'socso_category': socso_category,
            'age': age,
            'is_malaysian': is_malaysian,
            'is_pr': is_pr,
            'is_non_citizen': is_non_citizen
        }

# Convenience functions for backward compatibility
def calculate_epf_socso_status(birth_date: str, nationality: str, citizenship: str, 
                             basic_salary: float = 0) -> Dict[str, str]:
    """Backward compatibility function."""
    return EPFSOCSCalculator.calculate_epf_socso_status(
        birth_date, nationality, citizenship, basic_salary
    )

def get_epf_dropdown_options(birth_date: str, nationality: str, citizenship: str) -> list:
    """
    Get EPF dropdown options for non-citizens.
    For citizens and PRs, EPF is automatic.
    """
    age = EPFSOCSCalculator.calculate_age(birth_date)
    is_malaysian, is_pr, is_non_citizen = EPFSOCSCalculator.determine_citizenship_status(nationality, citizenship)
    
    if is_non_citizen:
        if age < 60:
            return [
                ('part_a', 'Part A (11% employer + 11% employee) - Pre-1998 Election'),
                ('part_b', 'Part B (13% employer + 11% employee) - Post-1998 Election')
            ]
        else:
            return [
                ('part_c', 'Part C (11% employer + 0% employee) - Pre-1998 Election'),
                ('part_d', 'Part D (13% employer + 0% employee) - Post-1998 Election')
            ]
    else:
        # Citizens and PRs have automatic EPF
        return []

def calculate_epf_socso_eligibility(employee_data: dict, selected_epf_part: str = None) -> dict:
    """
    Calculate EPF/SOCSO eligibility data for database storage.
    Returns data compatible with existing database columns.
    
    Args:
        employee_data: Dictionary with employee information
        selected_epf_part: Override EPF part for non-citizens
    
    Returns:
        Dictionary with calculated rates and participation status
    """
    try:
        birth_date = employee_data.get('date_of_birth', '')
        nationality = employee_data.get('nationality', '')
        citizenship = employee_data.get('citizenship', '')
        basic_salary = float(employee_data.get('basic_salary', 0))
        
        if not birth_date:
            # Return defaults if no birth date
            return {
                'epf_employee_rate': 11.00,
                'epf_employer_rate': 12.00,
                'epf_mandatory': False,
                'epf_part': None,
                'socso_category': 'Exempt',
                'socso_employee_rate': 0.00,
                'socso_employer_rate': 0.00,
                'socso_mandatory': False,
                'eis_eligible': False,
                'calculation_date': '2025-09-17',
                'employee_age': 0
            }
        
        # Calculate comprehensive status
        status = EPFSOCSCalculator.calculate_epf_socso_status(
            birth_date, nationality, citizenship, basic_salary
        )
        
        # Determine EPF part
        epf_part = None
        if selected_epf_part:
            # Use selected part for non-citizens
            epf_part = f'part_{selected_epf_part.lower()}'
        else:
            # Auto-calculate part
            epf_part = EPFSOCSCalculator.calculate_epf_part(birth_date, nationality, citizenship)
        
        # Calculate rates based on EPF part and SOCSO category
        epf_employee_rate = 11.00
        epf_employer_rate = 12.00
        epf_mandatory = status['is_malaysian'] or status['is_pr']
        
        # Adjust rates for specific EPF parts
        if epf_part in ['part_b', 'part_d']:
            epf_employer_rate = 13.00  # Part B and D have higher employer rate
        if epf_part in ['part_c', 'part_d'] and status['age'] >= 60:
            epf_employee_rate = 0.00  # Part C and D for 60+ have no employee contribution
        
        # SOCSO calculations (Updated per PERKESO official regulations)
        socso_category = status['socso_category']
        
        # Calculate SOCSO eligibility and rates
        if status['is_malaysian'] or status['is_pr']:
            # Traditional SOCSO for Malaysian citizens and PRs
            socso_mandatory = status['age'] < 60
            socso_employee_rate = 0.50 if socso_mandatory else 0.00
            socso_employer_rate = 1.75 if socso_mandatory else 0.00
        elif status['is_non_citizen']:
            # Foreign worker SOCSO (per PERKESO official rates)
            socso_mandatory = True  # All foreign workers with valid work permits
            socso_employee_rate = 0.50  # 0.5% for Invalidity Scheme
            socso_employer_rate = 1.75  # 1.25% Employment Injury + 0.5% Invalidity
        else:
            socso_mandatory = False
            socso_employee_rate = 0.00
            socso_employer_rate = 0.00
        
        # EIS calculations (Malaysian citizens and PRs only - not for foreign workers)
        eis_eligible = (status['is_malaysian'] or status['is_pr']) and status['age'] < 60
        
        return {
            'epf_employee_rate': epf_employee_rate,
            'epf_employer_rate': epf_employer_rate,
            'epf_mandatory': epf_mandatory,
            'epf_part': epf_part,
            'socso_category': socso_category,
            'socso_employee_rate': socso_employee_rate,
            'socso_employer_rate': socso_employer_rate,
            'socso_mandatory': socso_mandatory,
            'eis_eligible': eis_eligible,
            'calculation_date': '2025-09-17',
            'employee_age': status['age']
        }
        
    except Exception as e:
        print(f"Error in calculate_epf_socso_eligibility: {e}")
        # Return safe defaults
        return {
            'epf_employee_rate': 11.00,
            'epf_employer_rate': 12.00,
            'epf_mandatory': False,
            'epf_part': None,
            'socso_category': 'Exempt',
            'socso_employee_rate': 0.00,
            'socso_employer_rate': 0.00,
            'socso_mandatory': False,
            'eis_eligible': False,
            'calculation_date': '2025-09-17',
            'employee_age': 0
        }
