import os
import requests
from datetime import datetime

CALENDARIFIC_API_KEY = "vcFzqfmid6eahZiEhBMefeFfNMDqwcqJ"


def fetch_calendarific_holidays(year: int, country: str = 'MY', state: str = None, include_national: bool = True, include_observances: bool = True):
    """Return list of (date_iso, name, locations) tuples from Calendarific if API key set.
    If CALENDARIFIC_API_KEY is not set, return empty list. If `state` is provided,
    only return holidays that are nationwide or that list the state in their locations.
    """
    if not CALENDARIFIC_API_KEY:
        return []
    url = 'https://calendarific.com/api/v2/holidays'
    params = {
        'api_key': CALENDARIFIC_API_KEY,
        'country': country,
        'year': year,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    holidays = data.get('response', {}).get('holidays', [])
    results = []

    # mapping of common state display names to tokens/abbreviations Calendarific may use
    state_token_map = {
        'johor': ['johor', 'jhr', 'jhr.'],
        'kedah': ['kedah', 'kdh'],
        'kelantan': ['kelantan', 'ktn'],
        'perlis': ['perlis', 'pls'],
        'negeri sembilan': ['negeri sembilan', 'nsn', 'n.s. sembilan'],
        'penang': ['penang', 'png', 'penang'],
        'perak': ['perak', 'prk'],
        'selangor': ['selangor', 'sgr'],
        'pahang': ['pahang', 'phg'],
        'melaka': ['melaka', 'mlk'],
        'sabah': ['sabah'],
        'sarawak': ['sarawak'],
        'labuan': ['labuan'],
        'kuala lumpur': ['kuala lumpur', 'k.l.', 'kuala lumpur', 'kuala lumpur'],
        'putrajaya': ['putrajaya', 'pjy'],
        'kelantan': ['kelantan', 'ktn'],
        'terengganu': ['terengganu', 'trg'],
        'perak': ['perak', 'prk'],
        'p. region': ['p region']
    }

    # normalize helper: returns set of tokens present in loc str
    def parse_loc_tokens(loc_string: str):
        if not loc_string:
            return set(), None
        s = str(loc_string).strip()
        s_lower = s.lower()

        # Detect explicit 'all' or 'nationwide'
        if s_lower in ('all', 'all malaysia', 'nationwide'):
            return set(), 'all'

        # Detect 'all except' patterns -> return exception tokens and marker
        if 'all except' in s_lower:
            # e.g. 'All except JHR, KDH, KTN, TRG'
            after = s_lower.split('all except', 1)[1]
            toks = [t.strip().strip('.') for t in after.replace('&', ',').split(',') if t.strip()]
            toks_set = set(toks)
            return toks_set, 'all-except'

        # Otherwise split by comma or '&' or 'and'
        parts = [p.strip().strip('.') for p in s_lower.replace('&', ',').replace(' and ', ',').split(',') if p.strip()]
        return set(parts), None

    for h in holidays:
        date_iso = h.get('date', {}).get('iso')
        name = h.get('name')
        # If requested, skip astronomical/observance entries by keyword or by type
        if not include_observances and isinstance(name, str):
            nlow = name.lower()
            skip_keywords = ('solstice', 'equinox', 'eclipse', 'meteor', 'astronom', 'astronomy')
            if any(k in nlow for k in skip_keywords):
                continue
        # Optionally, Calendarific includes a 'type' field; skip common non-holiday types
        if not include_observances:
            t = h.get('type') or ''
            if isinstance(t, str) and t.lower() in ('observance', 'season', 'other'):
                continue
        # Calendarific may include 'locations' or 'location' info; try several keys
        loc = ''
        for k in ('locations', 'location', 'locations_description'):
            val = h.get(k)
            if val:
                loc = val
                break
        # normalize to string
        try:
            loc_str = str(loc) if loc is not None else ''
        except Exception:
            loc_str = ''

        if date_iso and name:
            # normalize to YYYY-MM-DD
            try:
                date_iso_norm = datetime.fromisoformat(date_iso).date().isoformat()
            except Exception:
                date_iso_norm = date_iso.split('T')[0]

            include = True
            if state:
                st = state.strip().lower()

                toks, marker = parse_loc_tokens(loc_str)

                # Helper: check if the state matches any token via mapping
                def state_matches_tokens(state_name, tokens_set):
                    stn = state_name.strip().lower()
                    # direct substring
                    if stn in ' '.join(tokens_set):
                        return True
                    # check mapping table
                    for canon, aliases in state_token_map.items():
                        if stn == canon or stn in canon:
                            for a in aliases:
                                if a in tokens_set or a in ' '.join(tokens_set):
                                    return True
                    # direct token match
                    if stn in tokens_set:
                        return True
                    return False

                # If marker is 'all' -> include only if requested
                if marker == 'all':
                    include = bool(include_national)
                elif marker == 'all-except':
                    # include unless the state's token is in exception list
                    if state_matches_tokens(st, toks):
                        include = False
                    else:
                        include = True
                else:
                    # If tokens is empty, fall back to substring check
                    if not toks:
                        include = st in loc_str.lower() or loc_str.strip() == ''
                    else:
                        include = state_matches_tokens(st, toks)

            if include:
                results.append((date_iso_norm, name, loc_str))

    return results
