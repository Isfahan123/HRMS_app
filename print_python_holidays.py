"""Print python-holidays-only Malaysia holidays for a year as JSON.

Usage:
  python tools/print_python_holidays.py 2025

This uses `get_holidays_python_only` (no DB/overrides).
"""
import sys
import os
import json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.holidays_service import get_holidays_python_only

if __name__ == '__main__':
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    hs, details = get_holidays_python_only(year)
    out = {
        'year': year,
        'count': len(hs),
        'dates': sorted(list(d.isoformat() for d in hs)),
        'details': details
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))
