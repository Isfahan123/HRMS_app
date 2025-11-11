import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services import supabase_service

print('LOCK_THRESHOLD=', supabase_service.LOGIN_LOCK_THRESHOLD)
print('LOCK_DURATION_MINUTES=', supabase_service.LOGIN_LOCK_DURATION_MINUTES)
print('HAS_LOCK_COLUMNS=', supabase_service.user_logins_has_lockout_columns())
print('OK')
