# cPanel Deployment - Complete Requirements Checklist

This document answers: **"What do you need (or not need) for the deployment?"**

## ✅ What IS Included (Already Done)

### Core Deployment Files ✓
All essential files are included in the repository:

- ✅ **`.htaccess`** - Apache/Passenger configuration
- ✅ **`passenger_wsgi.py`** - WSGI entry point (FastAPI → WSGI adapter)
- ✅ **`.cpanel.yml`** - Automated Git deployment configuration
- ✅ **`requirements.txt`** - All Python dependencies listed
- ✅ **`runtime.txt`** - Python version specification (3.11.9)
- ✅ **`.env`** - Environment variables with Supabase credentials (included)
- ✅ **`setup_cpanel.sh`** - Automated setup script
- ✅ **`verify_packages.py`** - Package verification helper

### Documentation ✓
Comprehensive guides are provided:

- ✅ **`README.md`** - Project overview with deployment options
- ✅ **`CPANEL_DEPLOYMENT.md`** - Complete 12KB deployment guide
- ✅ **`CPANEL_QUICKSTART.md`** - Quick reference (fastest method)
- ✅ **`DEPLOYMENT_READINESS.md`** - Pre-deployment verification

### Application Code ✓
All application files are ready:

- ✅ **`web_app.py`** - FastAPI application (90 routes)
- ✅ **`start_web.py`** - Development server launcher
- ✅ **Web interface** - HTML templates and static files
- ✅ **Services** - Database and business logic
- ✅ **All dependencies** - Listed in requirements.txt

---

## 🔧 What YOU Need to Provide (Server Side)

### 1. Hosting Requirements ⚠️ REQUIRED

You need a cPanel hosting account with:

- **Python 3.8+** support (Python 3.11 recommended)
- **Passenger** support for Python applications
- **SSH access** (recommended, but optional)
- **Git support** (optional, for auto-deploy method)

**Check with your hosting provider:**
- Does cPanel have "Setup Python App" option?
- Is Passenger available for Python?
- Which Python versions are available?

### 2. Supabase Database ⚠️ REQUIRED

The application uses Supabase for the database.

**Already configured in `.env`:**
```env
SUPABASE_URL=https://wxaerkdmpxriveyknfov.supabase.co
SUPABASE_KEY=eyJhbGci...
```

**You can:**
- **Option A**: Use the included credentials (for testing/demo)
- **Option B**: Create your own Supabase project:
  1. Go to https://supabase.com (free tier available)
  2. Create a new project
  3. Get your Project URL and Service Role Key
  4. Update `.env` file with your credentials

**If using your own Supabase:**
- Run the SQL scripts in `CREATE_MISSING_TABLES.sql` to set up tables
- Follow instructions in `setup_database.md`

### 3. Domain/Subdomain ⚠️ REQUIRED

You need a domain or subdomain where the app will be accessible:
- **Example**: `hrms.yourdomain.com` or `yourdomain.com`
- Configure in cPanel when setting up Python App

---

## ❌ What You DO NOT Need

### Not Required for Deployment:

- ❌ **Desktop GUI dependencies** (PyQt5) - Only for desktop version, not web
- ❌ **PDF generation libraries** (reportlab, tabula-py) - Unless you use PDF features
- ❌ **Node.js** - Not needed (pure Python backend)
- ❌ **Docker** - Not needed for cPanel (alternative deployment method)
- ❌ **Nginx** - cPanel uses Apache with Passenger
- ❌ **Systemd services** - Passenger handles this
- ❌ **SSL certificate** - Optional (cPanel has AutoSSL, but recommended)
- ❌ **Custom domain registrar** - Can use existing domain
- ❌ **Email server** - Not required by the app
- ❌ **External API keys** - Only Supabase needed

### Optional (Can Install Later):

- 🔵 **SSL Certificate** - Strongly recommended for production
- 🔵 **Custom domain** - Can use subdomain initially
- 🔵 **Monitoring service** - Optional (UptimeRobot, etc.)
- 🔵 **Backup service** - Optional (cPanel has built-in)

---

## 📋 Pre-Deployment Checklist

Before you start deployment, verify you have:

### Hosting Infrastructure
- [ ] cPanel account active
- [ ] Python 3.8+ available in cPanel
- [ ] Passenger support confirmed
- [ ] SSH access working (optional but recommended)
- [ ] Domain/subdomain ready

### Application Files
- [ ] Repository cloned/downloaded (✅ Already in repo)
- [ ] All files present (✅ Already in repo)
- [ ] `.env` file exists (✅ Already in repo)

### Database
- [ ] Supabase credentials available (✅ Already in .env)
- [ ] OR your own Supabase project created
- [ ] Database tables set up (if using your own)

### Optional but Recommended
- [ ] SSL certificate (can enable via cPanel AutoSSL)
- [ ] Backup strategy planned
- [ ] Monitoring set up

---

## 🚀 Deployment Methods Available

You have 3 deployment options, all fully documented:

### Method 1: Git Auto-Deploy ⭐ (Recommended)
**Time**: 30 seconds  
**Requirements**:
- Git support in cPanel
- GitHub/GitLab repository access

**What you do**:
1. cPanel → Git Version Control → Create
2. cPanel → Setup Python App → Create
3. Done!

### Method 2: SSH Manual Deploy
**Time**: 5 minutes  
**Requirements**:
- SSH access to server

**What you do**:
1. SSH to server
2. Clone repository
3. Run `./setup_cpanel.sh`
4. Configure Python app in cPanel

### Method 3: File Upload
**Time**: 10 minutes  
**Requirements**:
- Just cPanel File Manager

**What you do**:
1. Download ZIP from GitHub
2. Upload via cPanel File Manager
3. Extract files
4. Configure Python app in cPanel

---

## 🔍 Detailed Requirements by Category

### Python Packages (Automatic Installation)

All packages are listed in `requirements.txt` and will be installed automatically:

**Core Web Framework:**
- ✅ fastapi==0.115.5
- ✅ uvicorn==0.32.1
- ✅ jinja2==3.1.4
- ✅ python-multipart==0.0.18
- ✅ a2wsgi==1.10.10 (CRITICAL for cPanel/Passenger - converts ASGI to WSGI)

**Database & Auth:**
- ✅ supabase==2.8.1
- ✅ bcrypt==4.2.0

**Utilities:**
- ✅ python-dotenv==1.0.1
- ✅ pytz==2024.1
- ✅ requests==2.32.3

**Optional (for specific features):**
- PyQt5 - Only if running desktop version
- reportlab, pandas, openpyxl - For reports/exports
- tabula-py, PyPDF2 - For PDF processing

**Installation**: These are installed automatically by `.cpanel.yml` or `setup_cpanel.sh`

### System Requirements

**Server Side:**
- Operating System: Linux (typically CentOS, Ubuntu, or similar)
- Web Server: Apache (managed by cPanel)
- Application Server: Passenger (must be available)
- Python: 3.8, 3.9, 3.10, or 3.11 (3.11 recommended)

**Client Side (Users):**
- Any modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript enabled
- Internet connection

---

## 💡 What Gets Installed Where

### On Your Server (cPanel):

1. **Python Virtual Environment**
   - Created by cPanel's "Setup Python App"
   - Location: `/home/yourusername/virtualenv/HRMS_app/3.11/`

2. **Python Packages**
   - Installed in virtual environment
   - Managed by pip from requirements.txt

3. **Application Files**
   - Location: `/home/yourusername/public_html/HRMS_app/`
   - All repository files copied here

4. **Configuration**
   - `.htaccess` → Apache configuration
   - `.env` → Environment variables
   - `passenger_wsgi.py` → Entry point

### On Supabase (Database):

- PostgreSQL database (cloud-hosted)
- All employee, payroll, attendance data
- Managed through Supabase dashboard

### Client Side (Users):

- Nothing! Just a web browser
- No installation required for end users

---

## ❓ Common Questions

### Q: Do I need to install Python locally?
**A**: No, not for deployment. Python is provided by your cPanel hosting.

### Q: Do I need a database server?
**A**: No, Supabase provides the database (cloud-hosted PostgreSQL).

### Q: Do I need root access?
**A**: No, regular cPanel account is sufficient.

### Q: What if my cPanel doesn't have Python 3.11?
**A**: Python 3.8+ works. Update `.htaccess` and `.cpanel.yml` with your version.

### Q: Do I need to buy an SSL certificate?
**A**: No, cPanel offers free AutoSSL (Let's Encrypt). Strongly recommended.

### Q: Can I use a different database?
**A**: Currently configured for Supabase only. Would require code changes.

### Q: Do I need Node.js?
**A**: No, this is a pure Python application.

### Q: What about the desktop version (PyQt5)?
**A**: Completely separate. The web version doesn't need PyQt5 or any GUI libraries.

---

## 🎯 Summary: What You Actually Need

### Absolutely Required:
1. ✅ cPanel hosting with Python 3.8+ and Passenger
2. ✅ Domain or subdomain
3. ✅ Supabase credentials (provided or create your own)

### Already Provided in Repository:
1. ✅ All deployment files (.htaccess, passenger_wsgi.py, .cpanel.yml)
2. ✅ Complete documentation
3. ✅ Automation scripts
4. ✅ Application code
5. ✅ Default environment configuration

### Strongly Recommended:
1. 🔵 SSH access (makes troubleshooting easier)
2. 🔵 SSL certificate (security)
3. 🔵 Git access (for auto-deploy)

### Optional:
1. 🔵 Custom Supabase project (can use provided one)
2. 🔵 Monitoring service
3. 🔵 Backup strategy
4. 🔵 Custom domain (can use subdomain)

---

## 📞 Need Help?

If you're unsure about any requirement:

1. **Check your hosting**: Contact your hosting provider to confirm:
   - Python version available
   - Passenger support
   - SSH access
   - Git support

2. **Review documentation**:
   - `CPANEL_QUICKSTART.md` - Fast setup guide
   - `CPANEL_DEPLOYMENT.md` - Detailed instructions
   - `DEPLOYMENT_READINESS.md` - Verification checklist

3. **Test locally first**:
   ```bash
   python start_web.py
   # Visit http://localhost:8000
   ```

---

## ✅ Final Answer

**What you need for deployment:**

**REQUIRED:**
- cPanel hosting (with Python 3.8+ and Passenger)
- Domain/subdomain
- Supabase database credentials (already provided in repo)

**PROVIDED:**
- All deployment files (✅ in repo)
- All application code (✅ in repo)
- Complete documentation (✅ in repo)
- Automation scripts (✅ in repo)

**NOT NEEDED:**
- Node.js, Docker, custom servers
- Desktop GUI dependencies (PyQt5)
- External API keys (except Supabase)
- Root/sudo access
- Manual database setup (Supabase is cloud)

**RECOMMENDED:**
- SSH access
- SSL certificate (free via AutoSSL)
- Git access (for auto-deploy)

---

**You're ready to deploy!** Everything you need is already in the repository. Just follow `CPANEL_QUICKSTART.md` to get started.

---

*For specific questions about your hosting environment, contact your hosting provider.*
*For deployment questions, see the comprehensive guides in the repository.*
