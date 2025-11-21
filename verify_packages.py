#!/usr/bin/env python3
"""
Package verification script for HRMS deployment
Used by .cpanel.yml to verify package installation
"""

def verify_packages():
    """Verify that critical packages are installed"""
    packages = ['fastapi', 'uvicorn', 'asgiref', 'supabase']
    all_installed = True
    
    for pkg in packages:
        try:
            __import__(pkg)
            print(f'✓ {pkg} installed')
        except ImportError:
            print(f'✗ {pkg} NOT installed')
            all_installed = False
    
    return all_installed

if __name__ == '__main__':
    import sys
    success = verify_packages()
    sys.exit(0 if success else 1)
