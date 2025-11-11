import sys, json
sys.path.insert(0, r'c:\Users\hi\Downloads\hrms_app')

from services.leave_caps_service import get_leave_caps, save_to_supabase, load_from_supabase

print('Loading local payload from data/leave_caps.json...')
payload = get_leave_caps()
print(json.dumps(payload, indent=2))

print('\nPushing payload to Supabase...')
ok = save_to_supabase(payload)
print('save_to_supabase returned:', ok)

print('\nAttempting to load back from Supabase (load_from_supabase())...')
db = load_from_supabase()
print('DB payload read (truncated if large):')
print(json.dumps(db, indent=2))

print('\nDone')
