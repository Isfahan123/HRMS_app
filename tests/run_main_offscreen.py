import os
import runpy
import sys

# Ensure project root is on sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
print('Running main.py with QT_QPA_PLATFORM=offscreen')
try:
    runpy.run_path(os.path.join(project_root, 'main.py'), run_name='__main__')
except SystemExit:
    # main.py may call sys.exit(); treat as normal
    pass
except Exception:
    import traceback
    traceback.print_exc()
