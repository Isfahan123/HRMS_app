"""
Fetch Calendarific holidays for 2025 and list holiday names that occur on 2+ distinct dates.
Run: python tools/check_calendarific_2025.py
"""
from collections import defaultdict
from datetime import datetime
from services.calendarific_service import fetch_calendarific_holidays


def parse_date(d):
    if not d:
        return None
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            try:
                return datetime.strptime(d.split('T')[0], '%Y-%m-%d').date()
            except Exception:
                return None
    return None


year = 2025
print(f'Fetching Calendarific holidays for {year}...')
holidays = fetch_calendarific_holidays(year, country='MY', state=None, include_national=True, include_observances=True)

name_dates = defaultdict(set)
for date_iso, name, loc in holidays:
    if not name:
        continue
    d = parse_date(date_iso)
    if not d:
        continue
    name_dates[name.strip()].add(d)

multi = {n: sorted(list(ds)) for n, ds in name_dates.items() if len(ds) >= 2}

if multi:
    print('\nMulti-day holiday names in Calendarific for 2025:')
    for name, dates in sorted(multi.items(), key=lambda x: (-len(x[1]), x[0])):
        print(f"- {name}: {len(dates)} dates -> {[d.isoformat() for d in dates]}")
else:
    print('\nNo multi-day holiday names found for 2025 in Calendarific')

print('\nDone.')
