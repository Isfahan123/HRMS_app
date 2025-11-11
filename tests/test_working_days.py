import os
import sys
from datetime import date, timedelta

# make repo root importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import calculate_working_days
from core.holidays_service import get_holidays_for_year, canonical_state_name


def list_excluded_dates(start: date, end: date, state=None):
    excluded = []
    holidays = set()
    years = set()
    cur = start
    while cur <= end:
        years.add(cur.year)
        cur += timedelta(days=1)
    for y in years:
        hs, details = get_holidays_for_year(y, state=state)
        holidays.update(hs)
    cur = start
    while cur <= end:
        if cur.weekday() >= 5:
            excluded.append((cur, 'WEEKEND'))
        elif cur in holidays:
            excluded.append((cur, 'HOLIDAY'))
        cur += timedelta(days=1)
    return excluded


if __name__ == '__main__':
    # Example range (choose a sample around Deepavali / Hari Raya in 2025)
    start = date(2025, 11, 1)
    end = date(2025, 11, 15)
    state = 'PERAK'  # sample Malaysian state
    print(f"Testing working days from {start} to {end} for state={state}")
    wd = calculate_working_days(start.isoformat(), end.isoformat(), state=canonical_state_name(state))
    print(f"Calculated working days (service): {wd}")
    excluded = list_excluded_dates(start, end, state=canonical_state_name(state))
    print('Excluded dates (weekends and holidays):')
    for d, reason in excluded:
        print(' -', d.isoformat(), reason)
