from datetime import datetime, date
from typing import List, Tuple, Optional
import traceback

from services.supabase_employee_history import fetch_employee_history_records
from services.supabase_service import supabase
import re
import math


def _parse_date(d: Optional[str]) -> Optional[date]:
    if not d:
        return None
    try:
        return datetime.strptime(d, '%Y-%m-%d').date()
    except Exception:
        return None


def _merge_intervals(intervals: List[Tuple[date, date]]) -> List[Tuple[date, date]]:
    """Merge overlapping intervals. Intervals are (start, end) with start <= end."""
    if not intervals:
        return []
    # sort by start
    intervals = sorted(intervals, key=lambda x: x[0])
    merged = []
    cur_start, cur_end = intervals[0]
    for s, e in intervals[1:]:
        if s <= cur_end:
            # overlapping -> extend end
            if e > cur_end:
                cur_end = e
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = s, e
    merged.append((cur_start, cur_end))
    return merged


def calculate_cumulative_service(employee_id: str, as_of_date: Optional[date] = None) -> dict:
    """Calculate cumulative service for an employee using employee_history records.

    Returns dict: {'days': int, 'years': float}
    """
    try:
        if as_of_date is None:
            as_of_date = datetime.now().date()

        # fetch history rows - ensure we pass the UUID 'id' field if employee_id is not a UUID
        lookup_id = employee_id
        # simple UUID v4-ish pattern matcher
        uuid_re = re.compile(r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$')
        try:
            if not uuid_re.match(str(employee_id)):
                # try to resolve by employee_id (string) or email
                try:
                    resp = supabase.table('employees').select('id').eq('employee_id', employee_id).execute()
                    if resp and getattr(resp, 'data', None):
                        lookup_id = resp.data[0].get('id')
                    else:
                        resp2 = supabase.table('employees').select('id').eq('email', employee_id).execute()
                        if resp2 and getattr(resp2, 'data', None):
                            lookup_id = resp2.data[0].get('id')
                        else:
                            # cannot resolve -> return empty
                            return {'days': 0, 'years': 0.0}
                except Exception:
                    return {'days': 0, 'years': 0.0}
        except Exception:
            lookup_id = employee_id

        rows = fetch_employee_history_records(lookup_id, None) or []
        intervals: List[Tuple[date, date]] = []
        total_raw_days = 0
        for r in rows:
            s = _parse_date(r.get('start_date'))
            e = _parse_date(r.get('end_date'))
            if not s:
                # skip malformed or missing start
                continue
            if not e:
                e = as_of_date
            # ensure ordering
            if e < s:
                # skip invalid interval
                continue
            intervals.append((s, e))
            # add raw interval length for "total" (before merging overlaps)
            try:
                total_raw_days += (e - s).days
            except Exception:
                pass

        if not intervals:
            return {'days': 0, 'years': 0.0, 'total_days': 0, 'total_years': 0.0}

        merged = _merge_intervals(intervals)
        total_days = 0
        for s, e in merged:
            # use difference in days (same approach as existing code)
            total_days += (e - s).days

        years = total_days / 365.25
        total_years = total_raw_days / 365.25
        return {
            'days': total_days,
            'years': years,
            'total_days': total_raw_days,
            'total_years': total_years
        }
    except Exception:
        traceback.print_exc()
        return {'days': 0, 'years': 0.0}


def format_years(years_float: float) -> str:
    """Format a fractional number of years as "Xy Ym".

    Example: 3.25 -> "3y 3m" (because .25*12 = 3 months).
    Returns an empty string when the input is falsy or <= 0.
    """
    try:
        if not years_float or float(years_float) <= 0:
            return ''
        yrs = int(math.floor(float(years_float)))
        months = int(round((float(years_float) - yrs) * 12))
        # carry if rounding produced 12 months
        if months >= 12:
            yrs += 1
            months = 0
        return f"{yrs}y {months}m"
    except Exception:
        return ''
