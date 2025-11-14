#!/usr/bin/env python3
"""
Startup script for HRMS Web Application
This script starts the FastAPI web server
"""

import sys
import os

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    import uvicorn
    from web_app import app
    
    print("=" * 60)
    print("HRMS Web Application")
    print("=" * 60)
    print("\nStarting web server...")
    print("\nAccess the application at:")
    print("  → http://localhost:8000")
    print("\nAPI documentation at:")
    print("  → http://localhost:8000/docs (Swagger UI)")
    print("  → http://localhost:8000/redoc (ReDoc)")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
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
