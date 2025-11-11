from services.supabase_service import submit_leave_request, calculate_working_days, supabase, update_leave_request_status
from datetime import datetime

print('START_DEBUG_SUBMIT_FLOW')
email = 'debug.test@example.com'
start = '2025-08-29'
end = '2025-09-02'
state_list = ['Perak']

print('DEBUG: calculating working days (pre-submit)')
wd = calculate_working_days(start, end)
print('DEBUG: working days pre-submit =', wd)

print('DEBUG: submitting leave request')
success = submit_leave_request(email, 'Annual', start, end, 'Debug submit for holiday check', None, None, False, None, state_list)
print('DEBUG: submit_leave_request returned', success)

# Find the inserted leave request
resp = supabase.table('leave_requests').select('*').ilike('employee_email', email).eq('start_date', start).eq('end_date', end).order('created_at', {'ascending': False}).limit(1).execute()
if resp and getattr(resp, 'data', None):
    row = resp.data[0]
    lid = row.get('id')
    print('DEBUG: found leave_request id =', lid)
    print('DEBUG: attempting to approve via update_leave_request_status')
    ok = update_leave_request_status(lid, 'approved', 'debug_admin@example.com')
    print('DEBUG: update_leave_request_status returned', ok)
else:
    print('DEBUG: could not find submitted leave request')

print('DONE')
