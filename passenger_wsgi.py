"""
HRMS Web Application - Passenger WSGI Entry Point

This file is the entry point for Passenger (cPanel Python hosting).
It converts the FastAPI ASGI application to a WSGI application
that Passenger can serve.

Compatible with:
- Exabytes cPanel hosting
- General cPanel with Passenger
- Any hosting provider that supports Passenger for Python

DO NOT MODIFY unless you know what you're doing!
"""

import sys
import os
import re

# Ensure the application directory is in the Python path
# This allows imports to work correctly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
# This must be done before importing the application
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, environment variables
    # must be set via cPanel or server configuration
    pass

# Import the FastAPI application
try:
    from web_app import app
except ImportError as e:
    # If imports fail, log the error for debugging
    import traceback
    error_msg = f"Failed to import web_app: {e}\n{traceback.format_exc()}"
    
    # Check for common missing module issues
    missing_module = None
    error_str = str(e)
    if "No module named" in error_str:
        # Extract the module name from the error
        match = re.search(r"No module named ['\"]?([^'\"]+)['\"]?", error_str)
        if match:
            missing_module = match.group(1)
    
    # Create helpful error message
    app_dir = os.path.dirname(os.path.abspath(__file__))
    helpful_msg = f"""
================================================================================
HRMS Application Import Error
================================================================================
Error: {e}

Python Path: {sys.executable}
Working Directory: {app_dir}
Python Version: {sys.version}
"""
    
    if missing_module:
        helpful_msg += f"""
Missing Module: {missing_module}

FIX: Run the following commands to install dependencies:

    1. Activate your virtual environment:
       source ~/virtualenv/HRMS_app/3.11/bin/activate
    
    2. Install dependencies:
       cd {app_dir}
       pip install -r requirements.txt
    
    3. Restart Passenger:
       touch passenger_wsgi.py

See CPANEL_DEPLOYMENT.md for detailed deployment instructions.
================================================================================
"""
    
    # Try to log to file
    try:
        log_dir = os.path.join(app_dir, 'log')
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, 'passenger_error.log'), 'a') as f:
            from datetime import datetime
            f.write(f"\n[{datetime.now()}] {helpful_msg}\n")
            f.write(f"Full traceback:\n{traceback.format_exc()}\n")
    except:
        pass
    
    # Print to stderr for Passenger logs
    print(helpful_msg, file=sys.stderr)
    
    # Re-raise the error so Passenger shows it
    raise

# Convert FastAPI ASGI application to WSGI
# Passenger expects a WSGI application, but FastAPI is ASGI
# The a2wsgi library provides the correct ASGI → WSGI bridge
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError as e:
    raise ImportError(
        "a2wsgi is required for Passenger deployment. "
        "Install it with: pip install a2wsgi"
    ) from e

# For debugging: print successful initialization
# This will appear in Passenger logs
# Set DEBUG=1 or DEBUG=true in environment to enable
debug_enabled = os.environ.get('DEBUG', '').lower() in ('1', 'true')
if debug_enabled:
    print("✓ HRMS WSGI application initialized successfully")
    print(f"✓ Python path: {sys.path[0]}")
    print(f"✓ Application type: {type(application)}")
    print(f"✓ FastAPI app: {app.title}")
