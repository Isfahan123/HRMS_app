#!/usr/bin/env python3
"""
cPanel Deployment Diagnostic Script

Run this script via SSH or cPanel Terminal to diagnose deployment issues:
    source ~/virtualenv/YOUR_APP/3.11/bin/activate
    python scripts/diagnose_cpanel.py
"""

import sys
import os

def check_python_version():
    """Check Python version is compatible"""
    print(f"\n1. Python Version: {sys.version}")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("   ❌ FAIL: Python 3.8+ required")
        return False
    print("   ✅ PASS: Python version OK")
    return True

def check_required_packages():
    """Check if required packages are installed"""
    print("\n2. Checking required packages...")
    packages = [
        ('passlib', 'passlib'),
        ('pytz', 'pytz'),
        ('dotenv', 'python-dotenv'),
        ('requests', 'requests'),
        ('num2words', 'num2words'),
        ('flask', 'flask'),
        ('jinja2', 'jinja2'),
    ]
    
    all_ok = True
    for import_name, package_name in packages:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} - NOT INSTALLED")
            all_ok = False
    
    return all_ok

def check_app_files():
    """Check if required files exist"""
    print("\n3. Checking required files...")
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    required_files = [
        'passenger_wsgi.py',
        'web_app.py',
        'config.py',
        '.htaccess',
        'requirements.txt',
    ]
    
    all_ok = True
    for filename in required_files:
        filepath = os.path.join(app_dir, filename)
        if os.path.exists(filepath):
            print(f"   ✅ {filename}")
        else:
            print(f"   ❌ {filename} - MISSING")
            all_ok = False
    
    return all_ok

def check_env_file():
    """Check .env file configuration"""
    print("\n4. Checking .env configuration...")
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(app_dir, '.env')
    
    if not os.path.exists(env_path):
        print("   ❌ .env file not found")
        print("   → Create it from .env.example: cp .env.example .env")
        return False
    
    # Check for required variables
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    all_ok = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value and not value.startswith('your'):
            print(f"   ✅ {var} is configured")
        else:
            print(f"   ❌ {var} is not configured or has placeholder value")
            all_ok = False
    
    return all_ok

def check_app_imports():
    """Try to import the main app components"""
    print("\n5. Testing app imports...")
    
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    all_ok = True
    
    try:
        from config import config
        print("   ✅ config module")
    except Exception as e:
        print(f"   ❌ config module: {e}")
        all_ok = False
    
    try:
        from services.supabase_rest_client import create_client
        print("   ✅ supabase_rest_client module")
    except Exception as e:
        print(f"   ❌ supabase_rest_client module: {e}")
        all_ok = False
    
    try:
        from web_app import app
        print("   ✅ web_app Flask app")
    except Exception as e:
        print(f"   ❌ web_app module: {e}")
        all_ok = False
    
    try:
        from passenger_wsgi import application
        print("   ✅ passenger_wsgi WSGI app")
    except Exception as e:
        print(f"   ❌ passenger_wsgi module: {e}")
        all_ok = False
    
    return all_ok

def check_htaccess():
    """Check .htaccess configuration"""
    print("\n6. Checking .htaccess configuration...")
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    htaccess_path = os.path.join(app_dir, '.htaccess')
    
    if not os.path.exists(htaccess_path):
        print("   ❌ .htaccess not found")
        return False
    
    with open(htaccess_path, 'r') as f:
        content = f.read()
    
    issues = []
    
    if 'YOUR_CPANEL_USERNAME' in content:
        issues.append("Contains placeholder 'YOUR_CPANEL_USERNAME' - needs to be replaced")
    
    if 'YOUR_APP_FOLDER' in content:
        issues.append("Contains placeholder 'YOUR_APP_FOLDER' - needs to be replaced")
    
    # Check for hardcoded paths that don't match current user
    import pwd
    try:
        current_user = pwd.getpwuid(os.getuid()).pw_name
        home_dir = os.path.expanduser('~')
        if f'/home/{current_user}' not in content and home_dir not in content:
            issues.append(f"Python/app paths may not match your username ({current_user})")
    except Exception:
        pass
    
    if 'PassengerPython' not in content:
        issues.append("Missing PassengerPython directive")
    
    if 'PassengerAppRoot' not in content:
        issues.append("Missing PassengerAppRoot directive")
    
    if issues:
        print("   ⚠️ Potential issues found:")
        for issue in issues:
            print(f"      → {issue}")
        return False
    
    print("   ✅ .htaccess appears correctly configured")
    return True

def check_permissions():
    """Check file permissions"""
    print("\n7. Checking file permissions...")
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check key files
    files_to_check = [
        ('passenger_wsgi.py', '644'),
        ('web_app.py', '644'),
        ('.htaccess', '644'),
    ]
    
    all_ok = True
    for filename, expected in files_to_check:
        filepath = os.path.join(app_dir, filename)
        if os.path.exists(filepath):
            mode = oct(os.stat(filepath).st_mode)[-3:]
            if mode == expected:
                print(f"   ✅ {filename}: {mode}")
            else:
                print(f"   ⚠️ {filename}: {mode} (expected {expected})")
        else:
            print(f"   ❌ {filename}: not found")
            all_ok = False
    
    return all_ok

def main():
    print("=" * 60)
    print("HRMS cPanel Deployment Diagnostic")
    print("=" * 60)
    
    results = []
    results.append(("Python Version", check_python_version()))
    results.append(("Required Packages", check_required_packages()))
    results.append(("App Files", check_app_files()))
    results.append(("Environment Config", check_env_file()))
    results.append(("App Imports", check_app_imports()))
    results.append((".htaccess", check_htaccess()))
    results.append(("File Permissions", check_permissions()))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status}: {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("All checks passed! Your deployment should work.")
        print("\nNext steps:")
        print("1. Restart the app: touch passenger_wsgi.py")
        print("2. Visit your domain to test")
        print("3. Check https://your-domain.com/health for health check")
    else:
        print("Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("1. Install missing packages: pip install -r requirements.txt")
        print("2. Configure .env: cp .env.example .env && nano .env")
        print("3. Update .htaccess with your cPanel username and paths")
        print("4. Set permissions: chmod 644 passenger_wsgi.py .htaccess")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
