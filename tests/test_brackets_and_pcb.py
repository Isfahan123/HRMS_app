import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.supabase_service import get_tax_bracket_details, calculate_lhdn_pcb_official


def test_get_tax_bracket_details_basic():
    # Given a mid-income annual amount, should return appropriate bracket
    M, R, B = get_tax_bracket_details(60000.0, {}, {'config_name': 'default'})
    assert M >= 50000.0
    assert 0.08 <= R <= 0.3
    assert B >= 0.0


def test_official_pcb_runs_minimal_inputs():
    payroll_inputs = {
        'accumulated_gross_ytd': 0.0,
        'accumulated_epf_ytd': 0.0,
        'accumulated_pcb_ytd': 0.0,
        'accumulated_zakat_ytd': 0.0,
        'individual_relief': 9000.0,
        'spouse_relief': 0.0,
        'child_relief': 2000.0,
        'child_count': 0,
        'disabled_individual': 0.0,
        'disabled_spouse': 0.0,
        'other_reliefs_ytd': 0.0,
        'other_reliefs_current': 0.0,
        'current_month_zakat': 0.0,
    }
    tax_config = {'config_name': 'default', 'non_resident_rate': 30.0, 'individual_tax_rebate': 400.0}
    result = calculate_lhdn_pcb_official(payroll_inputs, gross_monthly=5000.0, epf_monthly=550.0, tax_config=tax_config, month_year='08/2025')
    assert isinstance(result, float)
    assert result >= 0.0
