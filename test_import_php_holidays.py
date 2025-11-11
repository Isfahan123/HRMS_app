import json
import tempfile
from pathlib import Path
from scripts.import_php_holidays import import_from_file


def test_import_php_holidays_creates_state_overrides(tmp_path):
    # Create a small sample export JSON with two state holidays
    sample = [
        {"date": "2025-05-01", "name": "Labour Day", "state": "MY-01"},
        {"date": "2025-08-31", "name": "State Independence Day", "state": "MY-01"}
    ]
    src = tmp_path / 'sample.json'
    src.write_text(json.dumps(sample, ensure_ascii=False))

    overrides_path = tmp_path / 'overrides.json'

    processed = import_from_file(src, overrides_path, overwrite=False)
    assert processed == 2

    data = json.loads(overrides_path.read_text(encoding='utf-8'))
    assert '2025' in data
    dates = {it['date'] for it in data['2025'] if isinstance(it, dict)}
    assert '2025-05-01' in dates
    assert '2025-08-31' in dates
