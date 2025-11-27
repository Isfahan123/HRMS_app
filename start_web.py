#!/usr/bin/env python3
"""
Startup script for HRMS Web Application
This script starts the Flask web server
"""

import sys
import os

# Check Python version compatibility
# Required: Python 3.9+ (packages: supabase, holidays, pandas require 3.9+)
MIN_PYTHON_VERSION = (3, 9)
if sys.version_info < MIN_PYTHON_VERSION:
    print("=" * 60)
    print("ERROR: Incompatible Python Version")
    print("=" * 60)
    print(f"\nYour Python version: {sys.version}")
    print(f"Minimum required: Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]}+")
    print("\nThe following packages require Python 3.9+:")
    print("  - supabase")
    print("  - holidays")
    print("  - pandas")
    print("\nPlease upgrade to Python 3.9 or higher (3.11 recommended).")
    print("=" * 60)
    sys.exit(1)

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    from web_app import app
    
    # Get configuration from environment variables
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8000"))
    debug = os.getenv("WEB_RELOAD", "false").lower() == "true" or os.getenv("DEBUG", "false").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "production")
    
    print("=" * 60)
    print("HRMS Web Application (Flask)")
    print("=" * 60)
    print(f"\nEnvironment: {environment}")
    print("\nStarting web server...")
    print("\nAccess the application at:")
    print(f"  → http://localhost:{port}")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    app.run(
        host=host, 
        port=port,
        debug=debug
    )
    
except KeyboardInterrupt:
    print("\n\nShutting down server...")
    sys.exit(0)
except ImportError as e:
    print(f"\nError: Missing required package: {e}")
    print("\nPlease install required packages:")
    print("  pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"\nError starting server: {e}")
    sys.exit(1)
