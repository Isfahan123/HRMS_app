import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import supabase

EMP_UUID = '6859674e-413a-4d77-a5fe-d8948b220dc8'
YEAR = 2025
ITEM = 'diagnostic_dummy'


def main():
    print('Testing insert/upsert into relief_ytd_accumulated...')
    payload = {
        'employee_id': EMP_UUID,
        'year': YEAR,
        'item_key': ITEM,
        'claimed_ytd': 1.23,
        'last_claim_year': YEAR,
    }
    try:
        res = supabase.table('relief_ytd_accumulated').upsert(payload, on_conflict='employee_id,year,item_key').execute()
        print('Upsert response:', getattr(res, 'data', None))
    except Exception as e:
        print('Upsert raised exception:', e)
        return
    # Fetch
    try:
        rt = supabase.table('relief_ytd_accumulated').select('*').eq('employee_id', EMP_UUID).eq('year', YEAR).eq('item_key', ITEM).limit(1).execute()
        print('Select after upsert -> rows:', len(getattr(rt, 'data', []) or []))
    except Exception as e:
        print('Select raised exception:', e)
        return
    # Cleanup
    try:
        supabase.table('relief_ytd_accumulated').delete().eq('employee_id', EMP_UUID).eq('year', YEAR).eq('item_key', ITEM).execute()
        print('Cleanup delete issued.')
    except Exception as e:
        print('Delete raised exception:', e)

if __name__ == '__main__':
    main()
