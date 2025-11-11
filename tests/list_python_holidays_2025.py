"""List python-holidays entries for Malaysia for 2025.

This script uses only the python-holidays adapter in `services/malaysia_holiday_service.py`.
It prints a compact summary grouped by location.
"""
import sys
import os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.malaysia_holiday_service import _get_raw_holidays_dict
from datetime import datetime

YEAR = 2025

def main():
    # list national first
    try:
        raw_nat = _get_raw_holidays_dict(YEAR, None)
    except Exception as e:
        print('Failed to get national holidays via python-holidays:', e)
        return

    # print national
    print('--- National (python-holidays) ---')
    for d in sorted(raw_nat.keys()):
        names = raw_nat[d]
        print(d.isoformat(), '|', '; '.join(names))

    # now per-state
    states = ['Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur', 'Labuan', 'Malacca',
              'Negeri Sembilan', 'Pahang', 'Penang', 'Perak', 'Perlis', 'Sabah',
              'Sarawak', 'Selangor', 'Terengganu', 'Putrajaya']

    for st in states:
        try:
            raw = _get_raw_holidays_dict(YEAR, st)
        except Exception as e:
            print(f'Failed to get holidays for {st}:', e)
            continue
        print(f'--- {st} (python-holidays) ---')
        for d in sorted(raw.keys()):
            names = raw[d]
            print(d.isoformat(), '|', '; '.join(names))

if __name__ == '__main__':
    main()
