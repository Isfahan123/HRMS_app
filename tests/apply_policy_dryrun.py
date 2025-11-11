import os
import sys

# Ensure project root is on sys.path so imports of services.* work when run as a script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.leave_caps_service import apply_policy_to_db


if __name__ == '__main__':
    print('Running dry-run of apply_policy_to_db...')
    summary = apply_policy_to_db(dry_run=True)
    print('Summary:')
    for k, v in summary.items():
        if k == 'details':
            print(f"{k}: (showing up to 20 lines)")
            for line in v[:20]:
                print('  ', line)
        else:
            print(f"{k}: {v}")
