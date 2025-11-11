"""
Check for multi-day holiday names per state for 2025 using Calendarific and DB
Run: python tools/check_multi_day_by_state_2025.py
"""
from collections import defaultdict
from datetime import datetime
from services.calendarific_service import fetch_calendarific_holidays
from services import supabase_service as ss

STATES = [
    None, # All Malaysia
    'Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur', 'Labuan', 'Malacca',
    'Negeri Sembilan', 'Pahang', 'Penang', 'Perak', 'Perlis', 'Sabah', 'Sarawak',
    'Selangor', 'Terengganu'
]

YEAR = 2025


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


def find_consecutive_spans(sorted_dates):
    spans = []
    if not sorted_dates:
        return spans
    cur = [sorted_dates[0]]
    for a, b in zip(sorted_dates, sorted_dates[1:]):
        if (b - a).days == 1:
            cur.append(b)
        else:
            if len(cur) >= 2:
                spans.append(list(cur))
            cur = [b]
    if len(cur) >= 2:
        spans.append(list(cur))
    return spans


def check_calendarific_for_state(state):
    sname = 'All Malaysia' if state is None else state
    print(f"\nCalendarific: checking state {sname} for {YEAR}...")
    holidays = fetch_calendarific_holidays(YEAR, country='MY', state=None if state is None else state, include_national=True, include_observances=True)
    name_dates = defaultdict(set)
    for date_iso, name, loc in holidays:
        if not name:
            continue
        d = parse_date(date_iso)
        if d:
            name_dates[name.strip()].add(d)
    out = {}
    for name, dates in name_dates.items():
        if len(dates) >= 2:
            sdates = sorted(dates)
            out[name] = {
                'dates': sdates,
                'consecutive_spans': find_consecutive_spans(sdates)
            }
    return out


def check_db_for_state(state):
    sname = 'All Malaysia' if state is None else state
    print(f"\nDB: checking state {sname} for {YEAR}...")
    out = {}
    try:
        rows = ss.find_calendar_holidays_for_year(YEAR, state=state)
    except Exception as e:
        print('  DB query failed:', e)
        rows = []
    name_dates = defaultdict(set)
    for r in rows:
        name = (r.get('name') or '').strip()
        if not name:
            continue
        d = None
        try:
            d = parse_date(r.get('date'))
        except Exception:
            d = None
        if d:
            name_dates[name].add(d)
    for name, dates in name_dates.items():
        if len(dates) >= 2:
            sdates = sorted(dates)
            out[name] = {
                'dates': sdates,
                'consecutive_spans': find_consecutive_spans(sdates)
            }
    return out


if __name__ == '__main__':
    overall = {'calendarific': {}, 'db': {}}
    for st in STATES:
        cal_multi = check_calendarific_for_state(st)
        db_multi = check_db_for_state(st)
        overall['calendarific'][st] = cal_multi
        overall['db'][st] = db_multi

    print('\n\nSummary: Calendarific multi-day entries per state (2025):')
    for st, mapping in overall['calendarific'].items():
        sname = 'All Malaysia' if st is None else st
        if mapping:
            print(f"\nState: {sname}")
            for name, info in mapping.items():
                print(f"- {name}: {len(info['dates'])} dates -> {[d.isoformat() for d in info['dates']]}")
                for sp in info['consecutive_spans']:
                    print('  consecutive span:', [d.isoformat() for d in sp])

    print('\n\nSummary: DB multi-day entries per state (2025):')
    for st, mapping in overall['db'].items():
        sname = 'All Malaysia' if st is None else st
        if mapping:
            print(f"\nState: {sname}")
            for name, info in mapping.items():
                print(f"- {name}: {len(info['dates'])} dates -> {[d.isoformat() for d in info['dates']]}")
                for sp in info['consecutive_spans']:
                    print('  consecutive span:', [d.isoformat() for d in sp])

    print('\nDone.')
