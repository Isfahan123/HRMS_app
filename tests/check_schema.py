"""
Schema checker for HRMS_app

Checks presence of auditing snapshot columns on public.payroll_runs and writes:
- schema_report.json: machine-readable report
- schema_check_output.txt: human-readable summary

Usage:
  python check_schema.py

Relies on Supabase client configured in services.supabase_service.
"""

import json
from datetime import datetime

from services.supabase_service import supabase


def probe_column_exists(table: str, column: str) -> bool:
    """Return True iff the given column exists on table by attempting a select.
    Uses PostgREST error 42703 (undefined_column) as negative signal.
    """
    try:
        # Limit 0 to avoid data payload
        supabase.table(table).select(column).limit(0).execute()
        return True
    except Exception as e:
        try:
            # Supabase Python client typically raises a dict-like error
            msg = getattr(e, "args", [None])[0]
            if isinstance(msg, dict) and msg.get("code") == "42703":
                return False
        except Exception:
            pass
        # Best-effort: treat other errors as missing
        return False


def main():
    target_table = "payroll_runs"
    required_cols = [
        # EPF relief cap snapshots
        "epf_relief_cap_annual",
        "epf_relief_used_ytd",
        "epf_relief_remaining",
        # SOCSO+EIS LP1 (B20) snapshots
        "socso_eis_lp1_cap_annual",
        "socso_eis_lp1_claimed_ytd",
        "socso_eis_lp1_remaining",
    ]

    helpful_cols = [
        # Commonly referenced by app for joins/filters
        "employee_email",
    ]

    report = {
        "table": target_table,
        "timestamp": datetime.now().isoformat(),
        "required": {},
        "helpful": {},
        "all_present": True,
    }

    for col in required_cols:
        exists = probe_column_exists(target_table, col)
        report["required"][col] = exists
        report["all_present"] = report["all_present"] and exists

    for col in helpful_cols:
        report["helpful"][col] = probe_column_exists(target_table, col)

    # Write machine-readable JSON
    with open("schema_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Write human-readable summary
    lines = [
        f"Schema check for public.{target_table} @ {report['timestamp']}",
        "",
        "Required columns:",
    ]
    for col, ok in report["required"].items():
        lines.append(f"  - {col}: {'OK' if ok else 'MISSING'}")
    lines.append("")
    lines.append("Helpful columns:")
    for col, ok in report["helpful"].items():
        lines.append(f"  - {col}: {'OK' if ok else 'MISSING'}")
    lines.append("")
    lines.append(f"All required present: {'YES' if report['all_present'] else 'NO'}")

    out = "\n".join(lines)
    with open("schema_check_output.txt", "w", encoding="utf-8") as f:
        f.write(out + "\n")

    print(out)


if __name__ == "__main__":
    main()
