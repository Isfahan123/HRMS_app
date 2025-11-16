#!/usr/bin/env python3
"""
Startup script for HRMS Web Application
This script starts the FastAPI web server
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Ensure we're in the correct directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:
    import uvicorn
    from web_app import app
    
    # Get configuration from environment variables
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("WEB_PORT", "8000"))
    reload = os.getenv("WEB_RELOAD", "false").lower() == "true"
    environment = os.getenv("ENVIRONMENT", "production")
    
    print("=" * 60)
    print("HRMS Web Application")
    print("=" * 60)
    print(f"\nEnvironment: {environment}")
    print("\nStarting web server...")
    print("\nAccess the application at:")
    print(f"  → http://localhost:{port}")
    print("\nAPI documentation at:")
    print(f"  → http://localhost:{port}/docs (Swagger UI)")
    print(f"  → http://localhost:{port}/redoc (ReDoc)")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)
    print()
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        reload=reload,
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
