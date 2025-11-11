import os
import json
from datetime import date, datetime, timedelta
from typing import List, Set, Dict, Tuple

from services.supabase_service import _probe_table_exists, supabase

# Mapping/normalization for Malaysian states and common labels.
STATE_NAME_MAP = {
    # common full names (ensure capitalization)
    'johor': 'Johor', 'kedah': 'Kedah', 'kelantan': 'Kelantan', 'kuala lumpur': 'Kuala Lumpur',
    'labuan': 'Labuan', 'malacca': 'Malacca', 'negeri sembilan': 'Negeri Sembilan', 'pahang': 'Pahang',
    'penang': 'Penang', 'perak': 'Perak', 'perlis': 'Perlis', 'sabah': 'Sabah', 'sarawak': 'Sarawak',
    'selangor': 'Selangor', 'terengganu': 'Terengganu', 'putrajaya': 'Putrajaya', 'putrajaya ': 'Putrajaya',
    # codes sometimes used by external sources
    'my-01': 'Johor', 'my-02': 'kedah',
}

# Short codes for display in compact holiday detail strings (used in calendar view)
STATE_ABBREV = {
    'Johor': 'JHR', 'Kedah': 'KDH', 'Kelantan': 'KTN', 'Kuala Lumpur': 'KUL',
    'Labuan': 'LBN', 'Malacca': 'MLK', 'Negeri Sembilan': 'NSN', 'Pahang': 'PHG',
    'Penang': 'PNG', 'Perak': 'PRK', 'Perlis': 'PLS', 'Putrajaya': 'PJY',
    'Sabah': 'SBH', 'Sarawak': 'SWK', 'Selangor': 'SGR', 'Terengganu': 'TRG',
    'National': 'NAT'
}


def canonical_state_name(ui_value: str | None) -> str | None:
    """Map various UI state labels into canonical names that python-holidays expects.

    Returns None for nationwide / All Malaysia.
    """
    if not ui_value:
        return None
    s = str(ui_value).strip()
    if not s:
        return None
    low = s.lower()
    if low in ('all malaysia', 'my', 'malaysia', 'all'):
        return None

    # Map common UI labels to canonical ones used elsewhere in this codebase
    UI_MAP = {
        'johore': 'Johor', 'johor': 'Johor', 'johore': 'Johor', 'johor ': 'Johor',
        'kedah': 'Kedah', 'kelantan': 'Kelantan', 'melaka': 'Malacca', 'malacca': 'Malacca',
        'negeri sembilan': 'Negeri Sembilan', 'pahang': 'Pahang', 'perak': 'Perak', 'perlis': 'Perlis',
        'pulau pinang': 'Penang', 'penang': 'Penang', 'selangor': 'Selangor', 'terengganu': 'Terengganu',
        'kuala lumpur': 'Kuala Lumpur', 'putrajaya': 'Putrajaya', 'labuan': 'Labuan',
        'sabah': 'Sabah', 'sarawak': 'Sarawak', 'johor': 'Johor', 'melaka': 'Malacca',
        # variants
        'pulau pinang': 'Penang', 'pulau pinang ': 'Penang', 'putrajaya ': 'Putrajaya'
    }

    mapped = UI_MAP.get(low)
    if mapped:
        return mapped

    # Try to title-case single token labels
    return s.title()


def normalize_location_label(raw: str | None) -> str:
    """Normalize various forms of state/location labels into human-friendly text.

    Examples:
      None -> 'National'
      'MY' -> 'National'
      'Perak' -> 'Perak'
      'perak' -> 'Perak'
      'National except Sarawak' -> preserved
    """
    if raw is None:
        return 'National'
    s = str(raw).strip()
    if not s:
        return 'National'
    low = s.lower()
    if low in ('my', 'malaysia', 'national'):
        return 'National'
    # if phrase contains words like 'except' or '&' or ',' then preserve as-is (title-cased)
    if 'except' in low or '&' in s or ',' in s:
        # title-case but preserve specific uppercase sequences
        return ' '.join([w.capitalize() for w in s.split()])
    # direct mapping
    mapped = STATE_NAME_MAP.get(low)
    if mapped:
        return mapped
    # fallback: return title-cased single token
    return s.title()
from typing import List, Set, Dict, Tuple

from services.supabase_service import _probe_table_exists, supabase


def get_holidays_for_year(year: int, state: str = None, include_national: bool = True, include_observances: bool = True) -> Tuple[Set[date], Dict[str, List[str]]]:
    """Return (set_of_dates, details_dict) for holidays in `year`.
    Prefers DB table 'calendar_holidays' if present. Runtime now uses python-holidays only.
    """
    # Use python-holidays only as requested
    return get_holidays_python_only(year, state)


def _compact_holiday_details(details: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Compact and deduplicate holiday detail strings per date.

    Input values are lists like ['python-holidays:Deepavali [Sarawak]', 'python-holidays:Deepavali [Johor]']
    This will return values like ['python-holidays:Deepavali [Johor, Sarawak]'].
    """
    import re
    out: Dict[str, List[str]] = {}

    for d, vals in details.items():
        groups = {}
        for v in vals:
            try:
                # try to parse provider:name [location]
                m = re.match(r"^([^:]+):\s*(.*?)\s*(?:\[(.*)\])?$", v)
                if m:
                    provider = m.group(1).strip()
                    name = m.group(2).strip()
                    loc_raw = m.group(3) or ''
                    # split locations by comma and strip
                    locs = [l.strip() for l in loc_raw.split(',')] if loc_raw else []
                else:
                    # fallback: put entire string under generic provider
                    provider = 'misc'
                    name = v
                    locs = []
                key = f"{provider}:{name}"
                s = groups.get(key, set())
                for l in locs:
                    if l:
                        s.add(l)
                groups[key] = s
            except Exception:
                # on parse error, just keep raw value under misc
                groups.setdefault(f"misc:{v}", set())

        # build compacted strings
        compacted = []
        for key, locset in groups.items():
            provider, name = key.split(':', 1)
            if locset:
                # map known state names to abbreviations; leave complex phrases intact
                mapped = []
                for l in sorted(locset):
                    # preserve phrases containing 'except' or '&' or ',' as-is
                    if 'except' in l.lower() or '&' in l or ',' in l:
                        mapped.append(l)
                        continue
                    # normalize then map
                    norm = normalize_location_label(l)
                    abbr = STATE_ABBREV.get(norm, None)
                    mapped.append(abbr if abbr is not None else norm)

                compacted.append(f"{provider}:{name} [{', '.join(mapped)}]")
            else:
                compacted.append(f"{provider}:{name}")

        out[d] = compacted

    return out


def get_holidays_python_only(year: int, state: str | None = None) -> Tuple[Set[date], Dict[str, List[str]]]:
    """Return holidays for `year` using python-holidays ONLY (no DB or overrides).

    Returns the same shape as `get_holidays_for_year`: (set_of_dates, details_dict)
    where details are compacted provider:name [locations].
    """
    results: Set[date] = set()
    holiday_details: Dict[str, List[str]] = {}
    try:
        from services.malaysia_holiday_service import get_normalized_holiday_events

        # If state is None, gather national + per-state union as before, but only from python-holidays
        def _add_events(ev_list, loc_label_override=None):
            for ev in ev_list:
                try:
                    start = datetime.fromisoformat(ev.get('start')).date()
                    end = datetime.fromisoformat(ev.get('end')).date()
                    primary = ev.get('primary') or (ev.get('names') or [''])[0]
                    loc_label = loc_label_override or ev.get('location') or 'MY'
                    cur = start
                    while cur <= end:
                        results.add(cur)
                        loc_label_norm = normalize_location_label(loc_label)
                        holiday_details.setdefault(cur.isoformat(), []).append(f"python-holidays:{primary} [{loc_label_norm}]")
                        cur = cur + timedelta(days=1)
                except Exception:
                    continue

        if state is None:
            # national
            try:
                evs = get_normalized_holiday_events(year, None)
                _add_events(evs, loc_label_override='National')
            except Exception:
                pass
            # per-state union
            MALAYSIAN_STATES = [
                'Johor', 'Kedah', 'Kelantan', 'Kuala Lumpur', 'Labuan', 'Malacca',
                'Negeri Sembilan', 'Pahang', 'Penang', 'Perak', 'Perlis', 'Sabah',
                'Sarawak', 'Selangor', 'Terengganu', 'Putrajaya'
            ]
            for st in MALAYSIAN_STATES:
                try:
                    evs = get_normalized_holiday_events(year, st)
                    _add_events(evs, loc_label_override=st)
                except Exception:
                    continue
        else:
            evs = get_normalized_holiday_events(year, state)
            _add_events(evs, loc_label_override=state)

    except Exception:
        # If adapter fails, return empty
        return set(), {}

    try:
        holiday_details = _compact_holiday_details(holiday_details)
    except Exception:
        pass

    return results, holiday_details


if __name__ == '__main__':
    import sys
    y = int(sys.argv[1]) if len(sys.argv) > 1 else datetime.now().year
    hs, details = get_holidays_for_year(y)
    print(f"Holidays for {y}: {sorted([d.isoformat() for d in hs])}")
    print('Details sample:', {k: details[k] for k in list(details)[:10]})
    from datetime import date, datetime, timedelta
