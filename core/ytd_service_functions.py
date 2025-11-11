# Add these functions to services/supabase_service.py for YTD accumulated data management

def get_employee_ytd_data(employee_email: str, year: int, month: int):
    """Get YTD accumulated data for an employee up to specified month"""
    try:
        print(f"DEBUG: Getting YTD data for {employee_email}, {year}/{month}")
        
        response = supabase.table("payroll_ytd_accumulated").select("*").eq(
            "employee_email", employee_email
        ).eq("year", year).eq("month", month).execute()
        
        if response.data:
            print(f"DEBUG: Found YTD data for {employee_email}")
            return response.data[0]
        else:
            print(f"DEBUG: No YTD data found for {employee_email}, initializing...")
            # Initialize YTD data for the year if not found
            return initialize_ytd_for_employee(employee_email, year, month)
            
    except Exception as e:
        print(f"DEBUG: Error getting YTD data: {e}")
        return None

def initialize_ytd_for_employee(employee_email: str, year: int, month: int):
    """Initialize YTD accumulated data for an employee"""
    try:
        print(f"DEBUG: Initializing YTD data for {employee_email}, {year}/{month}")
        
        # Get employee profile for default tax relief settings
        employee_data = get_user_by_email(employee_email)
        if not employee_data:
            print(f"DEBUG: Employee {employee_email} not found")
            return None
            
        # Calculate previous month's accumulated data if month > 1
        previous_month_data = None
        if month > 1:
            previous_month_data = get_employee_ytd_data(employee_email, year, month - 1)
        
        # Default YTD data structure
        ytd_data = {
            "employee_email": employee_email,
            "year": year,
            "month": month,
            
            # Initialize accumulated amounts (carry forward from previous month or start at 0)
            "accumulated_gross_salary_ytd": previous_month_data.get("accumulated_gross_salary_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_net_salary_ytd": previous_month_data.get("accumulated_net_salary_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_basic_salary_ytd": previous_month_data.get("accumulated_basic_salary_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_allowances_ytd": previous_month_data.get("accumulated_allowances_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_overtime_ytd": previous_month_data.get("accumulated_overtime_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_bonus_ytd": previous_month_data.get("accumulated_bonus_ytd", 0.0) if previous_month_data else 0.0,
            
            "accumulated_epf_employee_ytd": previous_month_data.get("accumulated_epf_employee_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_epf_employer_ytd": previous_month_data.get("accumulated_epf_employer_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_socso_employee_ytd": previous_month_data.get("accumulated_socso_employee_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_socso_employer_ytd": previous_month_data.get("accumulated_socso_employer_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_eis_employee_ytd": previous_month_data.get("accumulated_eis_employee_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_eis_employer_ytd": previous_month_data.get("accumulated_eis_employer_ytd", 0.0) if previous_month_data else 0.0,
            
            "accumulated_pcb_ytd": previous_month_data.get("accumulated_pcb_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_zakat_ytd": previous_month_data.get("accumulated_zakat_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_tax_reliefs_ytd": previous_month_data.get("accumulated_tax_reliefs_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_other_deductions_ytd": previous_month_data.get("accumulated_other_deductions_ytd", 0.0) if previous_month_data else 0.0,
            "accumulated_unpaid_leave_deduction_ytd": previous_month_data.get("accumulated_unpaid_leave_deduction_ytd", 0.0) if previous_month_data else 0.0,
            
            # Tax relief annual settings (from employee profile or defaults)
            "individual_relief": employee_data.get("individual_relief", 9000.0),  # LHDN 2025 default
            "spouse_relief": employee_data.get("spouse_relief", 0.0),
            "child_relief_per_child": employee_data.get("child_relief_per_child", 2000.0),  
            "child_count": employee_data.get("child_count", 0),
            "disabled_individual_relief": employee_data.get("disabled_individual_relief", 0.0),
            "disabled_spouse_relief": employee_data.get("disabled_spouse_relief", 0.0),
            
            # Employee tax context
            "is_resident": employee_data.get("is_resident", True),
            "is_individual_disabled": employee_data.get("is_individual_disabled", False),
            "is_spouse_disabled": employee_data.get("is_spouse_disabled", False),
            
            "created_by": "system"
        }
        
        # Insert into database
        response = supabase.table("payroll_ytd_accumulated").insert(ytd_data).execute()
        
        if response.data:
            print(f"DEBUG: YTD data initialized for {employee_email}")
            return response.data[0]
        else:
            print(f"DEBUG: Failed to initialize YTD data for {employee_email}")
            return None
            
    except Exception as e:
        print(f"DEBUG: Error initializing YTD data: {e}")
        return None

def update_employee_ytd_after_payroll(employee_email: str, year: int, month: int, payroll_data: dict):
    """Update YTD accumulated data after a payroll run"""
    try:
        print(f"DEBUG: Updating YTD data after payroll for {employee_email}, {year}/{month}")
        
        # Get current YTD data
        current_ytd = get_employee_ytd_data(employee_email, year, month)
        if not current_ytd:
            print(f"DEBUG: Could not get current YTD data for {employee_email}")
            return False
        
        # Calculate new accumulated values by adding current month's payroll
        updated_ytd = {
            "accumulated_gross_salary_ytd": float(current_ytd["accumulated_gross_salary_ytd"]) + float(payroll_data.get("gross_salary", 0)),
            "accumulated_net_salary_ytd": float(current_ytd["accumulated_net_salary_ytd"]) + float(payroll_data.get("net_salary", 0)),
            "accumulated_basic_salary_ytd": float(current_ytd["accumulated_basic_salary_ytd"]) + float(payroll_data.get("basic_salary", 0)),
            "accumulated_allowances_ytd": float(current_ytd["accumulated_allowances_ytd"]) + float(payroll_data.get("total_allowances", 0)),
            "accumulated_overtime_ytd": float(current_ytd["accumulated_overtime_ytd"]) + float(payroll_data.get("overtime_amount", 0)),
            "accumulated_bonus_ytd": float(current_ytd["accumulated_bonus_ytd"]) + float(payroll_data.get("bonus_amount", 0)),
            
            "accumulated_epf_employee_ytd": float(current_ytd["accumulated_epf_employee_ytd"]) + float(payroll_data.get("epf_employee", 0)),
            "accumulated_epf_employer_ytd": float(current_ytd["accumulated_epf_employer_ytd"]) + float(payroll_data.get("epf_employer", 0)),
            "accumulated_socso_employee_ytd": float(current_ytd["accumulated_socso_employee_ytd"]) + float(payroll_data.get("socso_employee", 0)),
            "accumulated_socso_employer_ytd": float(current_ytd["accumulated_socso_employer_ytd"]) + float(payroll_data.get("socso_employer", 0)),
            "accumulated_eis_employee_ytd": float(current_ytd["accumulated_eis_employee_ytd"]) + float(payroll_data.get("eis_employee", 0)),
            "accumulated_eis_employer_ytd": float(current_ytd["accumulated_eis_employer_ytd"]) + float(payroll_data.get("eis_employer", 0)),
            
            "accumulated_pcb_ytd": float(current_ytd["accumulated_pcb_ytd"]) + float(payroll_data.get("pcb", 0)),
            "accumulated_zakat_ytd": float(current_ytd["accumulated_zakat_ytd"]) + float(payroll_data.get("zakat_amount", 0)),
            "accumulated_unpaid_leave_deduction_ytd": float(current_ytd["accumulated_unpaid_leave_deduction_ytd"]) + float(payroll_data.get("unpaid_leave_deduction", 0)),
            
            # Store current month context
            "current_month_gross_salary": float(payroll_data.get("gross_salary", 0)),
            "current_month_epf_employee": float(payroll_data.get("epf_employee", 0)),
            "current_month_pcb_calculated": float(payroll_data.get("pcb", 0)),
            "current_month_zakat": float(payroll_data.get("zakat_amount", 0)),
            "current_month_tax_reliefs": float(payroll_data.get("tax_reliefs", 0)),
            
            "updated_by": "payroll_system",
            "updated_at": "now()"
        }
        
        # Update YTD record
        response = supabase.table("payroll_ytd_accumulated").update(updated_ytd).eq(
            "employee_email", employee_email
        ).eq("year", year).eq("month", month).execute()
        
        if response.data:
            print(f"DEBUG: YTD data updated successfully for {employee_email}")
            
            # Create next month's YTD record if it's not December
            if month < 12:
                next_month_ytd = get_employee_ytd_data(employee_email, year, month + 1)
                if not next_month_ytd:
                    initialize_ytd_for_employee(employee_email, year, month + 1)
            
            return True
        else:
            print(f"DEBUG: Failed to update YTD data for {employee_email}")
            return False
            
    except Exception as e:
        print(f"DEBUG: Error updating YTD data after payroll: {e}")
        return False

def get_ytd_for_pcb_calculation(employee_email: str, year: int, month: int):
    """Get YTD data formatted for PCB calculation"""
    try:
        ytd_data = get_employee_ytd_data(employee_email, year, month)
        if not ytd_data:
            return None
        
        # Format for PCB calculation (LHDN format)
        pcb_context = {
            # Accumulated values (∑ symbols from LHDN)
            "accumulated_gross_ytd": ytd_data["accumulated_gross_salary_ytd"],  # ∑(Y-K)
            "accumulated_epf_ytd": ytd_data["accumulated_epf_employee_ytd"],    # K
            "accumulated_pcb_ytd": ytd_data["accumulated_pcb_ytd"],             # X
            "accumulated_zakat_ytd": ytd_data["accumulated_zakat_ytd"],         # Z
            "accumulated_tax_reliefs_ytd": ytd_data["accumulated_tax_reliefs_ytd"], # ∑LP
            
            # Tax relief settings
            "individual_relief": ytd_data["individual_relief"],                 # D
            "spouse_relief": ytd_data["spouse_relief"],                         # S
            "child_relief": ytd_data["child_relief_per_child"],                 # Q
            "child_count": ytd_data["child_count"],                             # C
            "disabled_individual_relief": ytd_data["disabled_individual_relief"], # Du
            "disabled_spouse_relief": ytd_data["disabled_spouse_relief"],       # Su
            
            # Employee context
            "is_resident": ytd_data["is_resident"],
            "is_individual_disabled": ytd_data["is_individual_disabled"],
            "is_spouse_disabled": ytd_data["is_spouse_disabled"]
        }
        
        return pcb_context
        
    except Exception as e:
        print(f"DEBUG: Error getting YTD for PCB calculation: {e}")
        return None

def reset_ytd_for_new_year(employee_email: str, new_year: int):
    """Reset/initialize YTD data for a new year"""
    try:
        print(f"DEBUG: Resetting YTD data for {employee_email} for year {new_year}")
        
        # Initialize January of the new year with zero accumulated values
        january_data = initialize_ytd_for_employee(employee_email, new_year, 1)
        
        if january_data:
            print(f"DEBUG: YTD data reset successfully for {employee_email} year {new_year}")
            return True
        else:
            print(f"DEBUG: Failed to reset YTD data for {employee_email} year {new_year}")
            return False
            
    except Exception as e:
        print(f"DEBUG: Error resetting YTD for new year: {e}")
        return False

def get_all_employee_ytd_summary(year: int, month: int):
    """Get YTD summary for all employees (for admin dashboard)"""
    try:
        print(f"DEBUG: Getting YTD summary for all employees {year}/{month}")
        
        response = supabase.table("payroll_ytd_accumulated").select(
            "employee_email, accumulated_gross_salary_ytd, accumulated_pcb_ytd, accumulated_epf_employee_ytd"
        ).eq("year", year).eq("month", month).execute()
        
        if response.data:
            print(f"DEBUG: Found YTD data for {len(response.data)} employees")
            return response.data
        else:
            print(f"DEBUG: No YTD data found for {year}/{month}")
            return []
            
    except Exception as e:
        print(f"DEBUG: Error getting YTD summary: {e}")
        return []
