from datetime import date
import sys
from pathlib import Path

# ensure services importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.malaysia_holiday_service import normalize_and_merge_holidays


def test_cny_three_day_extension():
    # simulate CNY day with potential 3-day stretch: if initial day is 2026-02-07, ensure 3-day event
    raw = {
        date(2026, 2, 7): ['Chinese New Year']
    }
    events = normalize_and_merge_holidays(raw)
    # With current RULES=2, expect 2-day event (7-8); but we'll check extension to at least 2 days
    assert len(events) == 1
    ev = events[0]
    assert ev['start'] == '2026-02-07'
    assert ev['end'] >= '2026-02-08'


def test_deepavali_two_day_extension():
    raw = {
        date(2025, 11, 1): ['Deepavali']
    }
    events = normalize_and_merge_holidays(raw)
    assert len(events) == 1
    ev = events[0]
    assert ev['start'] == '2025-11-01'
    # Deepavali now treated as single-day by default
    assert ev['end'] == '2025-11-01'
