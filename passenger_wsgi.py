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
    
    # Try to log to file
    try:
        log_dir = os.path.join(os.path.dirname(__file__), 'log')
        os.makedirs(log_dir, exist_ok=True)
        with open(os.path.join(log_dir, 'passenger_error.log'), 'a') as f:
            from datetime import datetime
            f.write(f"\n[{datetime.now()}] {error_msg}\n")
    except:
        pass
    
    # Re-raise the error so Passenger shows it
    raise

# Convert FastAPI ASGI application to WSGI
# Passenger expects a WSGI application, but FastAPI is ASGI
# The asgiref library provides the bridge between them
try:
    from asgiref.wsgi import WsgiToAsgi
    application = WsgiToAsgi(app)
except ImportError as e:
    raise ImportError(
        "asgiref is required for Passenger deployment. "
        "Install it with: pip install asgiref"
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
