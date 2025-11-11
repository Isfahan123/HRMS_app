import sys
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')
from services.leave_caps_service import get_caps_for_years, get_leave_types
print('caps for 1.5:', get_caps_for_years(1.5))
print('caps for 3:', get_caps_for_years(3))
print('caps for 6:', get_caps_for_years(6))
print('leave types:', get_leave_types())
