from datetime import date
import sys
from pathlib import Path

# Ensure repo root is on sys.path so `services` package resolves during pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.malaysia_holiday_service import normalize_and_merge_holidays


def test_merge_chinese_new_year_two_days():
    raw = {
        date(2025, 1, 28): ['Chinese New Year'],
        date(2025, 1, 29): ['Chinese New Year Holiday']
    }
    events = normalize_and_merge_holidays(raw)
    assert len(events) == 1
    ev = events[0]
    assert ev['start'] == '2025-01-28'
    assert ev['end'] == '2025-01-29'
    assert 'Chinese New Year' in ev['names'][0] or 'Chinese New Year' in ev['primary']
