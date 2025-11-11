from datetime import date
import sys
from pathlib import Path

# ensure services package importable
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from services.malaysia_holiday_service import normalize_and_merge_holidays


def test_hari_raya_two_day_extension():
    # Hari Raya (single entry) should get a second day added/merged
    raw = {
        date(2025, 4, 21): ['Hari Raya Aidilfitri']
    }
    events = normalize_and_merge_holidays(raw)
    # Expect a merged event spanning 21-22 April
    assert len(events) == 1
    ev = events[0]
    assert ev['start'] == '2025-04-21'
    assert ev['end'] == '2025-04-22'
    assert 'Hari Raya' in ev['primary'] or any('Hari Raya' in n for n in ev['names'])
