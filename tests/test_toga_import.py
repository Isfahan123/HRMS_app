"""
Non-GUI Toga check: import toga and print available and selected backend.
This is safe to run in headless environments.
"""
import sys

try:
    import toga
    backends = getattr(toga, 'platform', None)
    print('toga import succeeded')
    try:
        # Print implementation module path
        import inspect
        print('toga implementation:', inspect.getmodule(toga).__file__)
    except Exception:
        pass
    # If toga.platform exists, attempt to show the platform module name
    try:
        import toga.platform
        print('toga.platform available')
    except Exception:
        pass
    sys.exit(0)
except Exception as e:
    print('toga import failed:', repr(e))
    sys.exit(2)
