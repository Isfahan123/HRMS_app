# How to Connect to Exabytes cPanel Python Web Application

This guide shows you how to connect and deploy the HRMS Python web application to Exabytes cPanel hosting.

---

## ⚡ Quick Answer: 3 Steps

### Step 1: Create Python App in cPanel
1. Login to Exabytes cPanel (https://my.exabytes.com → Login to cPanel)
2. Go to **Setup Python App** → **Create Application**
3. Configure:
   - Python Version: `3.11`
   - Application Root: `/home/USERNAME/public_html/hrms`
   - Application URL: `yourdomain.com`
   - Startup File: `passenger_wsgi.py`
   - Entry Point: `application`

### Step 2: Upload Application Files
**Option A (Git - Recommended):**
```bash
# In cPanel Terminal or SSH
cd ~/public_html
git clone https://github.com/Isfahan123/HRMS_app.git hrms
cd hrms
```

**Option B (File Manager):**
- Download ZIP from GitHub → Upload to `public_html/hrms` → Extract

### Step 3: Install & Configure
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate

# Use web-only requirements (avoids PyQt5/Java errors on cPanel)
pip install -r requirements-web.txt

# Create environment file
cp .env.example .env
nano .env  # Add your Supabase credentials

# Update .htaccess with your username
nano .htaccess  # Replace $CPANEL_USER with your actual username

# Restart
touch passenger_wsgi.py
```

> ⚠️ **Important**: Use `requirements-web.txt` instead of `requirements.txt` on cPanel. The full `requirements.txt` includes PyQt5 and tabula-py which require system libraries not available on shared hosting.

**Done!** Visit `https://yourdomain.com` 🎉

---

## 📋 Prerequisites

Before connecting, ensure you have:
- ✅ Exabytes cPanel hosting account with Python support
- ✅ Python 3.8+ available in cPanel
- ✅ Supabase account (for database) - [Get one free](https://supabase.com)
- ✅ Domain name pointed to Exabytes hosting

---

## 🔧 Configuration Files Explained

### `passenger_wsgi.py` - WSGI Entry Point
- Already configured - **No changes needed**
- Converts FastAPI to WSGI for Passenger

### `.htaccess` - Apache Configuration
**You must update:**
```apache
# Replace $CPANEL_USER with your actual cPanel username
PassengerPython /home/YOUR_USERNAME/virtualenv/hrms/3.11/bin/python
PassengerAppRoot /home/YOUR_USERNAME/public_html/hrms
```

### `.env` - Environment Variables
**You must create and configure:**
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
ENVIRONMENT=production
```

---

## 🔍 How the Connection Works

```
User Browser
    ↓
Exabytes Server (Apache + Passenger)
    ↓
.htaccess (routes to Python app)
    ↓
passenger_wsgi.py (WSGI adapter)
    ↓
web_app.py (FastAPI application)
    ↓
Supabase (PostgreSQL database)
```

### Key Components:

1. **Apache + Passenger** - Web server that runs Python apps on cPanel
2. **passenger_wsgi.py** - Converts ASGI (FastAPI) to WSGI (Passenger)
3. **asgiref** - Python library that provides the ASGI-to-WSGI bridge
4. **FastAPI** - Modern Python web framework
5. **Supabase** - Cloud database (PostgreSQL)

---

## ✅ Verify Connection

### Test 1: Health Check
```bash
curl https://yourdomain.com/health
```
Expected: `{"status":"healthy","timestamp":"..."}`

### Test 2: API Documentation
Visit: `https://yourdomain.com/docs`

### Test 3: Login Page
Visit: `https://yourdomain.com`

---

## 🐛 Connection Issues?

### "503 Service Unavailable"
```bash
# Check dependencies are installed (use web-only requirements)
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements-web.txt
touch passenger_wsgi.py
```

> ⚠️ **Module Installation Error?** If `pip install -r requirements.txt` fails, use `requirements-web.txt` instead. The full requirements include PyQt5 and tabula-py which won't install on cPanel.

### "500 Internal Server Error"
```bash
# Check .env file exists and has credentials
cat ~/public_html/hrms/.env

# If missing, create it
cp .env.example .env
nano .env
```

### Blank Page
```bash
# Check .htaccess has YOUR username (not $CPANEL_USER)
cat ~/public_html/hrms/.htaccess | grep PassengerPython
# Should show: /home/YOUR_ACTUAL_USERNAME/...
```

### View Logs
```bash
tail -f ~/public_html/hrms/log/passenger.log
```

---

## 📞 Need Help?

### Exabytes Support
- **Phone**: +603-2182-0888 (24/7)
- **Email**: support@exabytes.com
- **Live Chat**: Available in your Exabytes account

### Documentation
- [EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md) - Complete guide
- [EXABYTES_QUICKSTART.md](EXABYTES_QUICKSTART.md) - Quick start
- [EXABYTES_TROUBLESHOOTING.md](EXABYTES_TROUBLESHOOTING.md) - Fix issues
- [CPANEL_DEPLOYMENT.md](CPANEL_DEPLOYMENT.md) - General cPanel guide

---

## 🔗 Quick Links

| Resource | URL |
|----------|-----|
| Exabytes Login | https://my.exabytes.com |
| Supabase | https://supabase.com |
| Application | https://yourdomain.com |
| API Docs | https://yourdomain.com/docs |
| Health Check | https://yourdomain.com/health |

---

**Summary:** The HRMS app connects to Exabytes cPanel using Passenger (Python WSGI server). Create a Python app in cPanel, upload files, install dependencies, configure `.env` and `.htaccess`, then restart. That's it!
