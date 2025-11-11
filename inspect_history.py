import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from services.supabase_service import get_employee_history

identifier = 'amyryn123_507ec2cd'
print('Querying get_employee_history for identifier:', identifier)
rows = get_employee_history(identifier, limit=10, offset=0)
print('RESULT_COUNT=', len(rows))
print(json.dumps(rows, default=str, indent=2))
