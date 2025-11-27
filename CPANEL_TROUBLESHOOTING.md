# cPanel Troubleshooting Guide

If the cPanel Python GUI module installation "doesn't seem to work", follow these steps:

## Quick Fixes

### 1. Install Dependencies Manually via SSH

The cPanel Python GUI can sometimes fail. Install packages via SSH instead:

```bash
# Connect to your server via SSH
ssh your-username@your-domain.com

# Navigate to your app directory
cd ~/public_html/HRMS_app  # or wherever your app is located

# Activate the virtual environment (adjust path as needed)
source ~/virtualenv/HRMS_app/3.11/bin/activate

# Install minimal dependencies (most compatible)
pip install -r requirements-minimal.txt

# Restart the app
touch passenger_wsgi.py
```

### 2. If pip install fails

Try installing packages one by one:

```bash
pip install passlib
pip install pytz
pip install python-dotenv
pip install requests
pip install num2words
pip install flask
pip install jinja2
```

### 3. Check .htaccess Configuration

The `.htaccess` file must have correct paths. Edit it:

```bash
nano .htaccess
```

Replace the placeholder paths with your actual paths:

```apache
# Replace YOUR_USERNAME with your cPanel username
# Replace YOUR_APP with your app folder name
PassengerPython /home/YOUR_USERNAME/virtualenv/YOUR_APP/3.11/bin/python
PassengerAppRoot /home/YOUR_USERNAME/public_html/YOUR_APP
```

### 4. Run Diagnostic Script

```bash
source ~/virtualenv/HRMS_app/3.11/bin/activate
python scripts/diagnose_cpanel.py
```

This will check:
- Python version
- Installed packages
- Required files
- Environment configuration
- File permissions

### 5. Check Error Logs

```bash
# Check Passenger error log
cat ~/public_html/HRMS_app/log/passenger.log

# Check application error log
cat ~/public_html/HRMS_app/passenger_error.log

# Check cPanel error log
cat ~/logs/error.log | tail -50
```

## Common Errors and Solutions

### "Module not found" errors
```bash
pip install -r requirements-minimal.txt --force-reinstall
touch passenger_wsgi.py
```

### "503 Service Unavailable"
1. Check virtual environment is activated
2. Verify .htaccess paths are correct
3. Restart app: `touch passenger_wsgi.py`

### "Internal Server Error (500)"
1. Check .env file exists and has valid credentials
2. Check Passenger logs for detailed error
3. Run diagnostic: `python scripts/diagnose_cpanel.py`

### "An error occurred during installation of modules"
This is the cPanel GUI error. Use SSH installation instead (see step 1 above).

## File Permissions

Set correct permissions:

```bash
cd ~/public_html/HRMS_app
find . -type f -exec chmod 644 {} \;
find . -type d -exec chmod 755 {} \;
```

## Environment Variables

Make sure .env exists and has valid values:

```bash
cp .env.example .env
nano .env
```

Set these required values:
- `SUPABASE_URL=https://your-project.supabase.co`
- `SUPABASE_KEY=your-service-role-key`

## Test the App

After fixes, test:

```bash
# Test imports
python -c "from passenger_wsgi import application; print('OK')"

# Restart
touch passenger_wsgi.py

# Check health endpoint
curl https://your-domain.com/health
```

## Still Not Working?

1. Contact your hosting provider about Python support
2. Check if your hosting plan supports Passenger
3. Verify Python 3.8+ is available
4. Check cPanel → Metrics → Errors for server logs
