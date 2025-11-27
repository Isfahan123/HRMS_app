"""
Passenger WSGI entry point for HRMS (FastAPI)
"""

import sys
import os

# Ensure app directory added to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass

# Import FastAPI app
try:
    from web_app import app
except Exception as e:
    import traceback
    log_path = os.path.join(os.path.dirname(__file__), "passenger_error.log")
    with open(log_path, "a") as f:
        f.write("\n--- Import Error ---\n")
        f.write(str(e) + "\n")
        f.write(traceback.format_exc() + "\n")
    raise

# Convert ASGI → WSGI (FastAPI → Passenger)
try:
    from a2wsgi import ASGIAdapter
    application = ASGIAdapter(app)
except Exception as e:
    raise RuntimeError(
        "a2wsgi failed — ensure a2wsgi is installed in requirements.txt"
    ) from e

# Optional debug
if os.environ.get("DEBUG") == "1":
    print("Passenger WSGI initialized")
