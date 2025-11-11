print("Testing imports...")

try:
    import sys
    sys.path.append('services')
    print("Path added")
    
    from supabase_service import get_default_tax_rates_config
    print("get_default_tax_rates_config imported")
    
    from supabase_service import calculate_lhdn_pcb_official
    print("calculate_lhdn_pcb_official imported")
    
    # Get config
    config = get_default_tax_rates_config()
    print(f"Config loaded: {type(config)}")
    
    # Test data
    payroll_inputs = {
        'accumulated_gross_ytd': 170000.0,
        'accumulated_epf_ytd': 1870.0,
        'accumulated_pcb_ytd': 0.0,
        'accumulated_zakat_ytd': 0.0,
        'individual_relief': 9000.0,
        'other_reliefs_current': 41.65,
        'current_month_zakat': 0.0,
        'debug_pcb': True
    }
    print("Test data created")
    
    # Call function
    result = calculate_lhdn_pcb_official(
        payroll_inputs, 17000.0, 1870.0, config, '11/2025'
    )
    print(f"SUCCESS: PCB = RM{result:.2f}")
    
except ImportError as e:
    print(f"Import error: {e}")
except Exception as e:
    print(f"Other error: {e}")
    import traceback
    traceback.print_exc()
