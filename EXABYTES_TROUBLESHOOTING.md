# Exabytes Deployment Troubleshooting Guide

## 🔍 Subdomain Shows No Result - Common Fixes

If you see a blank page, error, or no result when accessing your subdomain, follow these steps:

---

## Quick Diagnostic Checklist

Run through these checks in order:

### 1. Check Passenger Logs (Most Important!)

```bash
# Via SSH or cPanel Terminal
cd ~/public_html/hrms
cat log/passenger.log

# Or check recent errors
tail -n 100 log/passenger.log
```

**What to look for:**
- Import errors (missing modules)
- File not found errors
- Permission denied errors
- Database connection errors

---

## Common Issues & Solutions

### Issue 1: "503 Service Unavailable" or Blank Page

**Likely Cause**: Application not starting, dependencies not installed, or wrong paths

**Solution 1 - Verify .htaccess Paths**:
```bash
# Via SSH or cPanel Terminal
cd ~/public_html/hrms
nano .htaccess
```

Check these lines match YOUR actual setup:
```apache
# Replace 'yourusername' with YOUR actual cPanel username
PassengerPython /home/yourusername/virtualenv/hrms/3.11/bin/python
PassengerAppRoot /home/yourusername/public_html/hrms
```

**Example**: If your cPanel username is `john123`, it should be:
```apache
PassengerPython /home/john123/virtualenv/hrms/3.11/bin/python
PassengerAppRoot /home/john123/public_html/hrms
```

**Solution 2 - Check Python App Configuration**:
1. Go to cPanel → **Setup Python App**
2. Find your application
3. Verify settings:
   - **Application Root**: `/home/yourusername/public_html/hrms`
   - **Application URL**: Should match your subdomain
   - **Startup File**: `passenger_wsgi.py`
   - **Entry Point**: `application`

**Solution 3 - Install Dependencies**:
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

---

### Issue 2: "500 Internal Server Error"

**Likely Cause**: Missing `.env` file or incorrect configuration

**Solution 1 - Create/Check .env File**:
```bash
cd ~/public_html/hrms
ls -la .env
```

If file doesn't exist:
```bash
cp .env.example .env
nano .env
```

Add your Supabase credentials:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_RELOAD=false
ENVIRONMENT=production
```

**Solution 2 - Test Import**:
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
python3 -c "from web_app import app; print('OK')"
```

If you see errors, they'll tell you what's wrong.

---

### Issue 3: Python Version Mismatch

**Likely Cause**: Virtual environment path in `.htaccess` doesn't match actual version

**Solution - Find Correct Python Version**:
```bash
# List available virtual environments
ls -la ~/virtualenv/hrms/

# You might see: 3.8, 3.9, 3.10, 3.11, etc.
```

Update `.htaccess` to match:
```apache
# If you have Python 3.9
PassengerPython /home/yourusername/virtualenv/hrms/3.9/bin/python

# If you have Python 3.10
PassengerPython /home/yourusername/virtualenv/hrms/3.10/bin/python
```

Then restart:
```bash
touch ~/public_html/hrms/passenger_wsgi.py
```

---

### Issue 4: Files Not in Correct Directory

**Likely Cause**: Application files are in wrong location

**Solution - Verify File Structure**:
```bash
cd ~/public_html/hrms
ls -la
```

You should see:
- `passenger_wsgi.py` ✓
- `web_app.py` ✓
- `.htaccess` ✓
- `requirements.txt` ✓
- `.env` ✓

If files are missing or in a subfolder, move them:
```bash
# If files are in a subfolder
cd ~/public_html/hrms
mv subfolder_name/* .
```

---

### Issue 5: Permission Errors

**Solution - Fix Permissions**:
```bash
cd ~/public_html/hrms
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
chmod +x start_web.py setup_cpanel.sh
touch passenger_wsgi.py
```

---

### Issue 6: Subdomain Configuration

**Solution - Verify Subdomain Setup**:

1. Go to cPanel → **Domains** → **Subdomains**
2. Check subdomain points to correct directory:
   - Document Root: `/home/yourusername/public_html/hrms`

3. Go to cPanel → **Setup Python App**
4. Verify **Application URL** matches your subdomain
5. Click **Edit** → **Save** → **Restart**

---

### Issue 7: Application Not Restarted

**Solution - Force Restart**:
```bash
cd ~/public_html/hrms
touch passenger_wsgi.py
mkdir -p tmp
touch tmp/restart.txt
```

Or via cPanel:
- **Setup Python App** → Find your app → **Restart**

---

## Step-by-Step Verification Process

Follow these steps in order:

### Step 1: Check cPanel Python App Settings
```
1. Login to Exabytes cPanel
2. Go to "Setup Python App"
3. Find your application
4. Verify all settings are correct
5. Click "Restart"
```

### Step 2: Verify File Locations
```bash
# SSH or Terminal
cd ~/public_html/hrms
pwd
# Should output: /home/yourusername/public_html/hrms

ls -la
# Should show: passenger_wsgi.py, web_app.py, .htaccess, etc.
```

### Step 3: Update .htaccess with Correct Paths
```bash
cd ~/public_html/hrms
nano .htaccess

# Replace $CPANEL_USER with your actual username
# Replace version number if different
# Save and exit (Ctrl+X, Y, Enter)
```

### Step 4: Create .env File
```bash
cd ~/public_html/hrms
cp .env.example .env
nano .env

# Add your Supabase credentials
# Save and exit
```

### Step 5: Install Dependencies
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Test Application Import
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
python3 -c "from web_app import app; print('✓ App loads successfully')"
python3 -c "import passenger_wsgi; print('✓ WSGI adapter works')"
```

### Step 7: Check Logs for Errors
```bash
cd ~/public_html/hrms
tail -n 50 log/passenger.log
```

### Step 8: Restart Application
```bash
cd ~/public_html/hrms
touch passenger_wsgi.py
```

### Step 9: Test in Browser
```
Visit: https://your-subdomain.yourdomain.com
```

---

## Detailed Error Diagnosis

### If You See: "Application Error" or Error Page

**Check Apache Error Logs**:
Via cPanel → **Metrics** → **Errors** → Look for recent errors

**Check Passenger Logs**:
```bash
cat ~/public_html/hrms/log/passenger.log
```

Common error patterns:

#### Error: "No such file or directory"
```
Fix: Check .htaccess paths are correct
Fix: Ensure passenger_wsgi.py exists in root directory
```

#### Error: "ModuleNotFoundError: No module named 'fastapi'"
```
Fix: Install dependencies in virtual environment:
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements-web.txt
```

#### Error: Module Installation Failed (PyQt5, tabula-py, etc.)
```
The full requirements.txt includes desktop packages that won't install on cPanel:
- PyQt5 requires system GUI libraries (not available on headless servers)
- tabula-py requires Java runtime (not usually installed on cPanel)

Fix: Use web-only requirements file instead:
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements-web.txt
touch passenger_wsgi.py
```

#### Error: "Permission denied"
```
Fix: Set correct permissions:
cd ~/public_html/hrms
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
```

#### Error: "Unable to connect to database" or Supabase errors
```
Fix: Check .env file has correct Supabase credentials
cd ~/public_html/hrms
cat .env
```

---

## Manual Verification Commands

Run these commands to verify everything:

```bash
# 1. Check you're in the right directory
cd ~/public_html/hrms && pwd

# 2. List all files
ls -la

# 3. Check .htaccess exists and has correct content
cat .htaccess | grep PassengerPython

# 4. Check .env exists
ls -la .env

# 5. Activate virtual environment
source ~/virtualenv/hrms/3.11/bin/activate

# 6. Check Python version
python3 --version

# 7. Test imports
python3 -c "from web_app import app; print('✓ FastAPI app works')"
python3 -c "import passenger_wsgi; print('✓ WSGI adapter works')"

# 8. List installed packages
pip list | grep -E "(fastapi|uvicorn|a2wsgi|supabase)"

# 9. Check logs
tail -n 50 log/passenger.log

# 10. Restart app
touch passenger_wsgi.py
```

---

## Getting Help

If you still can't get it working after trying everything above:

### 1. Collect Diagnostic Information

```bash
# Save diagnostic info to a file
cd ~/public_html/hrms
cat << 'EOF' > diagnostic.txt
=== Directory Contents ===
$(ls -la)

=== .htaccess Content ===
$(cat .htaccess)

=== Python Version ===
$(source ~/virtualenv/hrms/3.11/bin/activate && python3 --version)

=== Installed Packages ===
$(source ~/virtualenv/hrms/3.11/bin/activate && pip list)

=== Recent Logs ===
$(tail -n 50 log/passenger.log)

=== Virtual Environment Path ===
$(ls -la ~/virtualenv/hrms/)
EOF

cat diagnostic.txt
```

### 2. Contact Exabytes Support

**Phone**: +603-2182-0888 (24/7)  
**Email**: support@exabytes.com  
**Live Chat**: Available in your Exabytes account

Provide them with:
- Your subdomain URL
- The diagnostic.txt content
- Description of what you see (blank page, error message, etc.)

### 3. Common Questions to Ask Exabytes Support

- "Can you verify Python is enabled for my account?"
- "Can you check if Passenger is running for my subdomain?"
- "Can you see any errors in the server logs for my domain?"
- "Is the Python virtual environment created correctly?"

---

## Expected Working State

When everything is working correctly, you should see:

### 1. File Structure
```
~/public_html/hrms/
├── .env                   ✓ (with your credentials)
├── .htaccess              ✓ (with correct paths)
├── passenger_wsgi.py      ✓
├── web_app.py             ✓
├── requirements.txt       ✓
├── .cpanel.yml           ✓
├── log/                   ✓
│   └── passenger.log      ✓
└── [other files...]
```

### 2. .htaccess Content
```apache
PassengerPython /home/ACTUAL_USERNAME/virtualenv/hrms/3.11/bin/python
PassengerAppRoot /home/ACTUAL_USERNAME/public_html/hrms
PassengerStartupFile passenger_wsgi.py
```

### 3. .env Content
```env
SUPABASE_URL=https://your-actual-project.supabase.co
SUPABASE_KEY=your-actual-service-role-key
ENVIRONMENT=production
```

### 4. Test Commands Success
```bash
$ python3 -c "from web_app import app; print('OK')"
OK

$ python3 -c "import passenger_wsgi; print('OK')"
OK
```

### 5. Browser Access
- Visit: `https://your-subdomain.yourdomain.com`
- Should see: HRMS login page
- API docs: `https://your-subdomain.yourdomain.com/docs`
- Health check: `https://your-subdomain.yourdomain.com/health`

---

## Quick Fix Checklist

Try these in order, testing after each:

- [ ] Update .htaccess with YOUR actual cPanel username
- [ ] Create .env file with YOUR Supabase credentials
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Fix file permissions
- [ ] Restart application: `touch passenger_wsgi.py`
- [ ] Check subdomain points to correct directory
- [ ] Verify Python app configuration in cPanel
- [ ] Check logs: `tail -n 50 log/passenger.log`
- [ ] Test imports work correctly
- [ ] Clear browser cache and try again

---

**Still having issues?** 

Reply with:
1. What you see when you visit the subdomain (blank page, error message, etc.)
2. Content of your logs: `tail -n 50 ~/public_html/hrms/log/passenger.log`
3. Output of: `cat ~/public_html/hrms/.htaccess | grep Passenger`
4. Whether .env file exists: `ls -la ~/public_html/hrms/.env`

This will help diagnose the exact issue! 🔍
