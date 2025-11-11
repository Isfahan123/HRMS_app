import json
import sys
import os

# Ensure project root on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import verify_tax_schema, print_tax_schema_report


def main():
    rep = verify_tax_schema()
    # Print pretty report to stdout
    print("\nTax schema verification:")
    for table, info in rep.items():
        status = info.get('status')
        missing = info.get('missing', [])
        opt = info.get('optional_missing', [])
        extra = info.get('accepted_required_set', [])
        print(f"- {table}: {status}")
        if extra:
            print(f"  accepted_required_set: {extra}")
        if missing:
            print(f"  missing: {missing}")
        if opt:
            print(f"  optional_missing: {opt}")

    # Also write JSON file for capture
    out_path = os.path.join(ROOT, 'schema_report.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(rep, f, indent=2)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
