import sys, os
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
	sys.path.insert(0, ROOT)
from services.supabase_service import load_tax_rates_configuration

cfg = load_tax_rates_configuration('default') or {}
print('tax_rates_config:', cfg)
print('rounding_mode:', cfg.get('rounding_mode', 'ceiling_0_05'))
print('divisor_mode:', cfg.get('divisor_mode', 'n_plus_1'))
print('include_lp1_in_annual:', cfg.get('include_lp1_in_annual', True))
