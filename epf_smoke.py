import os
import sys

# Ensure project root is on sys.path so 'services' package can be imported when
# running scripts from the tools directory.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from services.supabase_service import calculate_epf_with_bonus, get_epf_contributions_for_wage

if __name__ == '__main__':
    tests = [
        (4800.0, 500.0, 'part_a'),  # basic <=5k, total >5k -> Part A bonus rule
        (4800.0, 500.0, 'part_c'),  # Part C bonus rule
        (4800.0, 0.0, 'part_a'),    # no bonus
        (6000.0, 0.0, 'part_a'),    # basic >5k no rule
    ]

    for basic, bonus, part in tests:
        emp, employer = calculate_epf_with_bonus(basic, bonus, part)
        print(f"Test basic={basic}, bonus={bonus}, part={part} -> employee={emp}, employer={employer}")

    # Compare with banded lookup for the total wage
    total = 4800.0 + 500.0
    print("--- compare banded lookup for total wage (4800+500) part_a ---")
    print(get_epf_contributions_for_wage(total, 'part_a'))
