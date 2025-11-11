try:
    import sys
    sys.path.append('services')
    from supabase_service import calculate_lhdn_pcb_official, get_default_tax_rates_config
    
    print("Functions imported successfully")
    
    # Test data
    payroll_inputs = {
        'accumulated_gross_ytd': 170000.0,
        'accumulated_epf_ytd': 1870.0,
        'accumulated_pcb_ytd': 0.0,
        'accumulated_zakat_ytd': 0.0,
        'individual_relief': 9000.0,
        'other_reliefs_current': 41.65,
        'current_month_zakat': 0.0
    }
    
    # Get tax config
    tax_config = get_default_tax_rates_config()
    print("Tax config loaded")
    
    # Test the calculation
    result = calculate_lhdn_pcb_official(
        payroll_inputs,
        17000.0,      # gross_monthly
        1870.0,       # epf_monthly  
        tax_config,   # tax_config
        '11/2025'     # month_year
    )
    
    print(f'PCB Result: RM{result:.2f}')
    print(f'Expected: RM2,678.30')
    print(f'Difference: RM{abs(result - 2678.30):.2f}')
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
