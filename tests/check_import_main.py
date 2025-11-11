# Tiny import check to surface import-time errors
import os
import sys

# Ensure project root is on sys.path when running from tools/
ROOT = os.path.dirname(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    import main
    print('Imported main OK')
except Exception:
    import traceback
    traceback.print_exc()
    raise
