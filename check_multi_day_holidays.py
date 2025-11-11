"""
Check for holiday names that occur on 2+ distinct dates in the DB and Calendarific
Run: python tools/check_multi_day_holidays.py
"""
from collections import defaultdict
from datetime import datetime

# Local project imports
from services import supabase_service as ss
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


def check_db():
    print('Checking DB table calendar_holidays...')
    out = {}
    try:
        if not ss._probe_table_exists('calendar_holidays'):
            print('  table calendar_holidays not present')
            return out
        # select only commonly-available columns; some DBs may not have 'source'
        resp = ss.supabase.table('calendar_holidays').select('id,date,name,state').execute()
        rows = resp.data if resp and getattr(resp, 'data', None) else []
    except Exception as e:
        print('  DB query failed:', e)
        rows = []

    name_dates = defaultdict(set)
    for r in rows:
        name = (r.get('name') or '').strip()
        if not name:
            continue
        d = parse_date(r.get('date'))
        if d:
            name_dates[name].add(d)

    for name, dates in name_dates.items():
        if len(dates) >= 2:
            out[name] = sorted(dates)
    return out


def check_calendarific(start_year=2023, end_year=None):
    if end_year is None:
        end_year = datetime.now().year
    print(f'Checking Calendarific from {start_year} to {end_year}...')
    cal_map = defaultdict(lambda: defaultdict(set))
    for year in range(start_year, end_year + 1):
        try:
            holidays = fetch_calendarific_holidays(year, country='MY', state=None, include_national=True, include_observances=True)
        except Exception as e:
            print('  Calendarific fetch failed for', year, e)
            holidays = []
        for date_iso, name, loc in holidays:
            if not name:
                continue
            d = parse_date(date_iso)
            if not d:
                continue
            cal_map[name][year].add(d)
    # collapse to names with 2+ dates in a year
    out = {}
    for name, years in cal_map.items():
        for year, dates in years.items():
            if len(dates) >= 2:
                out.setdefault(name, {})[year] = sorted(dates)
    return out


if __name__ == '__main__':
    db_multi = check_db()
    if db_multi:
        print('\nMulti-day holidays in DB:')
        for name, dates in db_multi.items():
            print(f"- {name}: {len(dates)} dates -> {[d.isoformat() for d in dates]}")
    else:
        print('\nNo multi-day holidays found in DB')

    cal_multi = check_calendarific(start_year=2023)
    if cal_multi:
        print('\nMulti-day holidays in Calendarific:')
        for name, years in cal_multi.items():
            for year, dates in years.items():
                print(f"- {name} ({year}): {len(dates)} dates -> {[d.isoformat() for d in dates]}")
    else:
        print('\nNo multi-day holidays found in Calendarific (2023+).')

    print('\nDone.')
