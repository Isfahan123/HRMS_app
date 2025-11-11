"""Leave calendar helpers.

Minimal helper used by leave and payroll flows to decide whether a date
should deduct leave. It delegates holiday lookups to
``services.holidays_service.get_holidays_for_year`` which implements the
DB-first aggregation of Calendarific + overrides.
"""

from datetime import date, datetime
from typing import Iterable, Optional, Union

from services.holidays_service import get_holidays_for_year


def _to_date(d: Union[date, datetime, str]) -> date:
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, str):
        return datetime.strptime(d, "%Y-%m-%d").date()
    raise TypeError("check_date must be a date, datetime or ISO date string YYYY-MM-DD")


def _is_weekend(d: date) -> bool:
    # Saturday (5) and Sunday (6) are considered weekend days
    return d.weekday() >= 5


def is_leave_deductible(
    check_date: Union[date, datetime, str],
    states: Optional[Iterable[str]] = None,
    include_observances: bool = True,
    include_national: bool = True,
) -> bool:
    """Return True when a date should be deducted as leave.

    Returns:
        True  => date should be deducted (working day)
        False => date should NOT be deducted (weekend or holiday)
    """
    d = _to_date(check_date)

    # Weekends are not deductible
    if _is_weekend(d):
        return False

    year = d.year

    # Global scan when no states provided: ignore state-scoped overrides
    if not states:
        _, details = get_holidays_for_year(
            year, state=None, include_national=include_national, include_observances=include_observances
        )
        key = d.isoformat()
        if key not in details:
            return True

        for entry in details.get(key, []):
            s = str(entry or "")
            # DB or local overrides may be state-scoped (contain state=...)
            if ("db:" in s) or ("override:" in s):
                if "state=" in s:
                    continue
                return False
            if "calendarific:" in s:
                if include_national:
                    return False
                continue

        return True

    # With states provided: OR logic across states - if any state marks the
    # date as a holiday, the date is not deductible.
    for st in states:
        st_clean = st.strip() if st else None
        holidays_set, _ = get_holidays_for_year(
            year, state=st_clean, include_national=include_national, include_observances=include_observances
        )
        if d in holidays_set:
            return False

    return True
