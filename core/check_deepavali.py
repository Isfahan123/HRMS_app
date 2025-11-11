"""Check whether Deepavali / Sarawak holidays appear when fetching All Malaysia."""
import sys
import os

# ensure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.holidays_service import get_holidays_for_year


if __name__ == '__main__':
    hs, details = get_holidays_for_year(2025)
    matches = {d: details[d] for d in details if any('deepavali' in s.lower() or 'sarawak' in s.lower() for s in details[d])}
    print('Total holiday dates:', len(hs))
    print('Matches for Deepavali/Sarawak sample:')
    for d, vals in matches.items():
        print(d, vals)
