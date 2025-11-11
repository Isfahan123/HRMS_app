import sys
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')
from services.leave_caps_service import get_leave_caps, save_to_supabase

if __name__ == '__main__':
    data = get_leave_caps()
    if not data:
        print('No leave_caps.json found or empty')
        sys.exit(1)
    ok = save_to_supabase(data)
    if ok:
        print('Synced leave caps to Supabase (or saved to DB tables)')
    else:
        print('Failed to sync to Supabase - check services.supabase_service configuration')
        sys.exit(2)
