import os, sys, datetime
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from services.supabase_service import upsert_tp1_monthly_details, supabase

EMP_UUID = '6859674e-413a-4d77-a5fe-d8948b220dc8'
YEAR = 2025
MONTH = 1
DETAILS = {
    'parent_dental': 500.0,
    'parent_medical_care': 500.0,
}
AGG = {
    'other_reliefs_monthly': 0.0,
    'socso_eis_lp1_monthly': 0.0,
    'zakat_monthly': 0.0,
}

ok = upsert_tp1_monthly_details(EMP_UUID, YEAR, MONTH, DETAILS, AGG)
print('restore ok?', ok)
