"""
Backfill working_days for older approved leave requests that don't have it yet.

Safety:
- Read-only compute via services.calculate_working_days.
- Directly updates leave_requests. Does NOT call update_leave_request_status to avoid balance double-counting.

Usage:
  python tools/backfill_working_days.py [--year 2025] [--limit 500]
"""
from datetime import datetime, date
import argparse

try:
    from services.supabase_service import supabase, calculate_working_days, get_leave_request_states
except Exception as e:
    raise SystemExit(f"Cannot import services.supabase_service: {e}")


def iter_missing_requests(target_year: int | None, limit: int | None):
    q = supabase.table("leave_requests").select(
        "id, employee_email, leave_type, start_date, end_date, status, is_half_day"
    ).eq("status", "approved").is_("working_days", None)
    if target_year:
        q = q.gte("start_date", f"{target_year}-01-01").lte("start_date", f"{target_year}-12-31")
    res = q.execute()
    rows = res.data or []
    if limit:
        rows = rows[:limit]
    return rows


def compute_days_for_row(row: dict) -> float:
    if row.get("is_half_day"):
        return 0.5
    sd = row.get("start_date")
    ed = row.get("end_date")
    if not sd or not ed:
        return 0.0
    # Try to find explicit state selection
    try:
        states = get_leave_request_states(row.get("id"))
        state = states[0] if states else None
    except Exception:
        state = None
    return float(calculate_working_days(sd, ed, state=state))


def backfill(year: int | None, limit: int | None, dry_run: bool):
    missing = iter_missing_requests(year, limit)
    print(f"Found {len(missing)} approved leave rows missing working_days")
    updated = 0
    for r in missing:
        days = compute_days_for_row(r)
        if dry_run:
            print(f"DRY-RUN id={r['id']} {r['start_date']}..{r['end_date']} -> {days}")
            continue
        try:
            supabase.table("leave_requests").update({"working_days": days}).eq("id", r["id"]).execute()
            updated += 1
        except Exception as e:
            print(f"Failed to update id={r['id']}: {e}")
    print(f"Backfill complete. Updated {updated} rows")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=None, help="Limit to start_date year")
    ap.add_argument("--limit", type=int, default=None, help="Max rows to process")
    ap.add_argument("--dry-run", action="store_true", help="Print planned updates without writing")
    args = ap.parse_args()
    backfill(args.year, args.limit, args.dry_run)


if __name__ == "__main__":
    main()
