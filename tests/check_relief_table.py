import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase

def main():
    try:
        supabase.table('relief_ytd_accumulated').select('*').limit(1).execute()
        print('relief_ytd_accumulated: OK (select succeeded)')
    except Exception as e:
        print('relief_ytd_accumulated: NOT ACCESSIBLE ->', e)

    try:
        supabase.table('tp1_monthly_details').select('*').limit(1).execute()
        print('tp1_monthly_details: OK')
    except Exception as e:
        print('tp1_monthly_details: NOT ACCESSIBLE ->', e)

if __name__ == '__main__':
    main()
