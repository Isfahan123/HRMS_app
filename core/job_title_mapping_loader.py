import json
import os

MAPPING_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'job_title_mapping.json')


def load_job_title_mapping():
    """Load the job title -> {position, department} mapping.

    Returns a dict where keys are job title strings and values are dicts with
    'position' and 'department' keys. Non-fatal on errors; returns an empty dict
    on failure.
    """
    try:
        with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


if __name__ == '__main__':
    m = load_job_title_mapping()
    print(f'Loaded {len(m)} job title mappings')
    # print a few samples
    for i, (k, v) in enumerate(list(m.items())[:10]):
        print(f"- {k} => position={v.get('position')} department={v.get('department')}")
