"""Adapter to provide Malaysia holidays using the `holidays` Python package.

This module is defensive: different `holidays` releases expose slightly
different construction APIs. The adapter attempts several common ways of
building a Malaysia calendar so it works with both legacy (0.35-era) and
newer (0.8x/0.81-era) releases.

Exposes fetch_malaysia_holidays(year, country='MY', state=None, include_national=True, include_observances=True)
which returns a list of tuples (date_iso, name, location)

If `holidays` is not installed or cannot be used, this adapter raises
ImportError so callers can fall back to Calendarific or another provider.
"""
from datetime import date
import logging

logger = logging.getLogger(__name__)


def _instantiate_holidays_calendar(holidays_mod, year: int, state: str | None = None):
    """Try several common constructors for the holidays calendar.

    Returns an object that supports .items() or iteration mapping date->name.
    """
    # 1) Newer helper: country_holidays (many newer versions expose this)
    try:
        if hasattr(holidays_mod, 'country_holidays'):
            try:
                # Try with common state arg names
                if state:
                    for state_kw in ('subdiv', 'prov', 'state'):
                        try:
                            return holidays_mod.country_holidays('MY', **{state_kw: state}, years=[year])
                        except Exception:
                            continue
                return holidays_mod.country_holidays('MY', years=[year])
            except Exception:
                pass

    except Exception:
        pass

    # 2) Classic CountryHoliday API
    try:
        if hasattr(holidays_mod, 'CountryHoliday'):
            try:
                if state:
                    for kw in ({'prov': state}, {'subdiv': state}, {'state': state}):
                        try:
                            return holidays_mod.CountryHoliday('MY', years=[year], **kw)
                        except Exception:
                            continue
                return holidays_mod.CountryHoliday('MY', years=[year])
            except Exception:
                pass
    except Exception:
        pass

    # 3) Country-specific class (e.g., holidays.Malaysia)
    try:
        if hasattr(holidays_mod, 'Malaysia'):
            try:
                return getattr(holidays_mod, 'Malaysia')(years=[year])
            except Exception:
                pass
    except Exception:
        pass

    # 4) Fallback: empty HolidayBase
    try:
        if hasattr(holidays_mod, 'HolidayBase'):
            return holidays_mod.HolidayBase()
    except Exception:
        pass

    raise RuntimeError('Unable to construct holidays calendar from installed holidays package')


def fetch_malaysia_holidays(year, country='MY', state=None, include_national=True, include_observances=True):
    try:
        import holidays as holidays_mod
    except Exception as exc:
        raise ImportError('python-holidays package not available') from exc

    # instantiate calendar using multiple strategies
    try:
        cal = _instantiate_holidays_calendar(holidays_mod, year, state)
    except Exception as exc:
        logger.debug('holidays calendar construction failed: %s', exc)
        raise

    out = []

    # Different versions expose iteration differently; try items(), then fallback.
    try:
        if hasattr(cal, 'items'):
            iterable = cal.items()
        else:
            # some versions support iterating and use .get(date) to fetch name
            iterable = ((d, cal.get(d) if hasattr(cal, 'get') else cal[d]) for d in cal)

        for d, name in sorted(iterable):
            try:
                iso = d.isoformat()
            except Exception:
                iso = str(d)
            out.append((iso, name, state or 'MY'))
    except Exception:
        # As a last resort, attempt to iterate keys and look up
        try:
            for d in sorted(list(cal)):
                try:
                    name = cal.get(d) if hasattr(cal, 'get') else str(cal[d])
                    iso = d.isoformat() if hasattr(d, 'isoformat') else str(d)
                    out.append((iso, name, state or 'MY'))
                except Exception:
                    continue
        except Exception:
            # give up and propagate
            raise

    return out


def _get_raw_holidays_dict(year: int, state: str | None = None):
    """Return dict mapping datetime.date -> list of names using python-holidays calendar."""
    try:
        import holidays as holidays_mod
    except Exception as exc:
        raise ImportError('python-holidays package not available') from exc

    cal = _instantiate_holidays_calendar(holidays_mod, year, state)
    result = {}
    try:
        if hasattr(cal, 'items'):
            iterable = cal.items()
        else:
            iterable = ((d, cal.get(d) if hasattr(cal, 'get') else cal[d]) for d in cal)
        for d, name in iterable:
            try:
                # name may be a list or a string
                if isinstance(name, (list, tuple)):
                    names = [str(n) for n in name]
                else:
                    names = [str(name)]
                result[d] = result.get(d, []) + names
            except Exception:
                continue
    except Exception:
        # fallback iteration
        for d in list(cal):
            try:
                name = cal.get(d) if hasattr(cal, 'get') else str(cal[d])
                result[d] = result.get(d, []) + ([name] if not isinstance(name, (list, tuple)) else list(name))
            except Exception:
                continue
    return result


def _normalize_name_for_grouping(name: str) -> str:
    """Normalize a holiday name for grouping/merging.

    Removes ordinal/day qualifiers and generic words like 'holiday' or 'observed',
    and lowercases the result for comparison.
    """
    import re

    s = name.lower()
    # remove parenthetical qualifiers
    s = re.sub(r"\([^)]*\)", "", s)
    # remove common qualifier words
    s = re.sub(r"\b(holiday|observed|public holiday)\b", "", s)
    # remove ordinal/day tokens: second, 2nd, day 2, day 1, first, 1st
    s = re.sub(r"\b(second|2nd|first|1st|day\s*\d+|\b2\b|\b1\b)\b", "", s)
    # collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _ensure_additional_days(raw: dict) -> dict:
    """Add extra days for known multi-day holidays when missing.

    Rules implemented:
    - Chinese New Year: ensure next day exists (second day)
    - Hari Raya / Eid (identified by 'hari raya' or 'eid' in name): ensure next day exists
    Returns a new dict with added entries.
    """
    from datetime import timedelta
    import re

    out = dict(raw)
    dates = sorted(out.keys())

    # Rules: list of tuples (matcher_func, extra_days)
    # matcher_func(name_lower) -> True if rule applies
    RULES = [
        # Chinese New Year often has 2 or 3 days public holiday; ensure at least 2 days
        (lambda nm: 'chinese new year' in nm or 'cny' in nm, 2),
        # Hari Raya / Eid al-Fitr: ensure 2 days
        (lambda nm: 'hari raya' in nm or 'eid' in nm or 'aidilfitri' in nm or 'aidil fitri' in nm, 2),
        # (Removed Deepavali auto-extension — Deepavali is usually single-day; use overrides for state-specific extensions)
    ]

    for d in dates:
        names = out.get(d, [])
        for name in names:
            ln = name.lower()
            for matcher, days in RULES:
                try:
                    if not matcher(ln):
                        continue
                except Exception:
                    continue

                # skip if name already indicates multi-day/second-day
                if re.search(r"\b(second|2nd|third|3rd|holiday|observed|day\s*2|day\s*3|day\s*2nd)\b", ln):
                    break

                # Ensure we have entries for the next (days-1) dates
                for i in range(1, days):
                    nxt = d + timedelta(days=i)
                    if nxt.year != d.year:
                        break
                    if nxt not in out:
                        suffix = 'Second Day' if i == 1 else f'Day {i+1}'
                        out[nxt] = out.get(nxt, []) + [f"{name} ({suffix})"]
                break

    return out


def normalize_and_merge_holidays(raw: dict) -> list:
    """Normalize and merge a raw mapping date->list(names) into events.

    Returns a list of events: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD', 'names': [...], 'primary': '...'}
    Consecutive dates with the same normalized base name are merged into a single event.
    """
    from datetime import timedelta

    if not raw:
        return []

    # ensure extra days for known holiday types
    raw2 = _ensure_additional_days(raw)

    # build mapping and sort dates
    items = sorted(raw2.items(), key=lambda x: x[0])

    events = []
    current_start = None
    current_end = None
    current_names = []
    current_norm = None

    for d, names in items:
        # compute normalized name for grouping using first name as representative
        rep_name = names[0] if names else ''
        norm = _normalize_name_for_grouping(rep_name)

        if current_start is None:
            # start new event
            current_start = d
            current_end = d
            current_names = list(dict.fromkeys(names))
            current_norm = norm
            continue

        # check if d is consecutive to current_end and normalized names match
        if (d - current_end).days == 1 and (norm == current_norm or norm == ''):
            # extend current event
            current_end = d
            for n in names:
                if n not in current_names:
                    current_names.append(n)
        else:
            # flush current event
            events.append({
                'start': current_start.isoformat(),
                'end': current_end.isoformat(),
                'names': current_names,
                'primary': current_names[0] if current_names else ''
            })
            # start new event
            current_start = d
            current_end = d
            current_names = list(dict.fromkeys(names))
            current_norm = norm

    # flush final
    if current_start is not None:
        events.append({
            'start': current_start.isoformat(),
            'end': current_end.isoformat(),
            'names': current_names,
            'primary': current_names[0] if current_names else ''
        })

    return events


def get_normalized_holiday_events(year: int, state: str | None = None) -> list:
    """Top-level helper that fetches python-holidays data and returns normalized events."""
    raw = _get_raw_holidays_dict(year, state)
    return normalize_and_merge_holidays(raw)
