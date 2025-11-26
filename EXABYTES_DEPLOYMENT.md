# HRMS Web Application - Exabytes cPanel Deployment Guide

Complete guide for deploying the HRMS web application on **Exabytes** cPanel hosting with Python support.

## 📋 Prerequisites

### Exabytes Hosting Requirements
- ✅ Exabytes cPanel hosting account with Python support
- ✅ **Python 3.9 or higher available** (Python 3.11 recommended)
  - ⚠️ Python 3.8 is NOT compatible with this application
- ✅ SSH access (optional but recommended)
- ✅ Git access (for automated deployments)
- ✅ Passenger support (Exabytes provides this)
- ✅ Supabase account for database

### What You'll Need
- Your Exabytes cPanel login credentials
- Your domain name (e.g., yourdomain.com)
- Your Supabase project URL and service role key
- About 15-20 minutes for first-time setup

---

## 🚀 Quick Deployment (Recommended)

### Step 1: Access Exabytes cPanel

1. Login to your **Exabytes Account** at https://my.exabytes.com
2. Navigate to **My Services** → Select your hosting package
3. Click **Login to cPanel**
4. You'll be redirected to your cPanel dashboard

### Step 2: Set Up Python Application

1. In cPanel, scroll to **Software** section
2. Click on **Setup Python App** (or **Python Selector**)
3. Click **Create Application**
4. Configure:
   - **Python Version**: `3.11` (or highest available, minimum 3.9)
   - **Application Root**: `/home/yourusername/public_html/hrms`
   - **Application URL**: Your domain or subdomain
   - **Application Startup File**: `passenger_wsgi.py`
   - **Application Entry Point**: `application`
5. Click **Create**

> 📝 **Note**: Take note of the virtual environment path shown after creation.  
> Example: `/home/yourusername/virtualenv/hrms/3.11`

### Step 3: Deploy Application Files

#### Option A: Git Deployment (Recommended)

1. **Enable Git Version Control**:
   - In cPanel → **Git Version Control** → **Create**
   - Repository URL: `https://github.com/Isfahan123/HRMS_app.git`
   - Repository Path: `/home/yourusername/repositories/HRMS_app`
   - Click **Create**

2. **Pull and Deploy**:
   - Click **Manage** on your repository
   - Click **Pull or Deploy** → **Deploy HEAD Commit**
   - The `.cpanel.yml` file will automatically handle deployment

3. **Link to Application Directory**:
   ```bash
   # Via SSH or cPanel Terminal
   cd ~/public_html
   ln -s ~/repositories/HRMS_app hrms
   ```

#### Option B: Direct Upload via File Manager

1. Download the repository as ZIP from GitHub
2. In cPanel → **File Manager**
3. Navigate to `public_html`
4. Create folder `hrms` and enter it
5. Click **Upload** and upload the ZIP file
6. Right-click the ZIP → **Extract**
7. Move all files from extracted folder to `hrms` directory

#### Option C: SSH/Terminal

```bash
# Connect via SSH
ssh yourusername@yourdomain.com

# Navigate to public_html
cd ~/public_html

# Clone repository
git clone https://github.com/Isfahan123/HRMS_app.git hrms
cd hrms
```

### Step 4: Configure Environment Variables

1. **Create `.env` file**:
   - Via cPanel File Manager:
     - Navigate to `public_html/hrms`
     - Click **+ File** → Name it `.env`
     - Right-click → **Edit**
   
   - Via SSH/Terminal:
     ```bash
     cd ~/public_html/hrms
     cp .env.example .env
     nano .env
     ```

2. **Add your credentials**:
   ```env
   # Supabase Configuration
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-service-role-key-here
   
   # Web Application Configuration
   WEB_HOST=0.0.0.0
   WEB_PORT=8000
   WEB_RELOAD=false
   
   # Application Environment
   ENVIRONMENT=production
   ```

3. **Save the file**

### Step 5: Install Dependencies

#### Via cPanel Terminal (or SSH)

```bash
# Navigate to application directory
cd ~/public_html/hrms

# Activate virtual environment
# Replace 'yourusername' and '3.11' with your actual values
source ~/virtualenv/hrms/3.11/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies (both files are now web-compatible)
pip install -r requirements.txt
# Or use the web-specific file (identical):
# pip install -r requirements-web.txt

# Verify installation
python3 verify_packages.py
```

> ✅ **Note**: Both `requirements.txt` and `requirements-web.txt` are now web-compatible. Desktop-only dependencies (PyQt5, tabula-py) have been moved to `requirements-desktop.txt`.

#### Using Exabytes Python App Interface

Some Exabytes cPanel versions allow dependency installation via UI:
1. Go to **Setup Python App**
2. Find your application
3. Look for **Run pip install** or similar option
4. Upload or paste contents of `requirements-web.txt`

### Step 6: Update Configuration Files

1. **Update `.htaccess`**:
   - Open `.htaccess` in File Manager
   - Update Python path to match your environment:
   ```apache
   PassengerPython /home/yourusername/virtualenv/hrms/3.11/bin/python
   ```
   - Replace `yourusername` with your actual cPanel username
   - Save the file

2. **Verify `passenger_wsgi.py`**:
   - File should already be correct
   - No changes needed unless you have custom requirements

### Step 7: Set File Permissions

Via SSH/Terminal:
```bash
cd ~/public_html/hrms

# Set directory permissions
find . -type d -exec chmod 755 {} \;

# Set file permissions
find . -type f -exec chmod 644 {} \;

# Make scripts executable
chmod +x start_web.py setup_cpanel.sh
```

Or use the automated script:
```bash
cd ~/public_html/hrms
./setup_cpanel.sh
```

### Step 8: Restart Application

Choose one method:

**Method 1 - Via cPanel**:
- Go to **Setup Python App**
- Find your application
- Click **Restart**

**Method 2 - Via SSH/Terminal**:
```bash
cd ~/public_html/hrms
touch passenger_wsgi.py
```

**Method 3 - Using restart.txt**:
```bash
cd ~/public_html/hrms
mkdir -p tmp
touch tmp/restart.txt
```

---

## ✅ Verification

### 1. Test Application Access

Open your browser and visit:
- **Login Page**: `https://yourdomain.com`
- **API Documentation**: `https://yourdomain.com/docs`
- **Health Check**: `https://yourdomain.com/health`

Expected health check response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-24T12:00:00Z"
}
```

### 2. Check Logs

```bash
# Via SSH/Terminal
cd ~/public_html/hrms
cat log/passenger.log

# Check for errors
tail -n 50 log/passenger.log
```

Or via cPanel:
- **Metrics** → **Errors**
- Look for recent errors related to your application

### 3. Test Login

1. Visit your domain
2. Try logging in with your credentials
3. Verify dashboard loads correctly

---

## 🔧 Exabytes-Specific Configuration

### Subdomain Setup

If using a subdomain (e.g., hrms.yourdomain.com):

1. **Create Subdomain**:
   - cPanel → **Domains** → **Subdomains**
   - Subdomain: `hrms`
   - Document Root: `/home/yourusername/public_html/hrms`
   - Click **Create**

2. **Update Python App**:
   - Go to **Setup Python App**
   - Edit your application
   - Update **Application URL** to subdomain
   - Save and restart

### SSL Certificate (HTTPS)

Exabytes provides free SSL certificates:

1. **Enable AutoSSL**:
   - cPanel → **Security** → **SSL/TLS Status**
   - Find your domain
   - Click **Run AutoSSL**

2. **Force HTTPS**:
   - Uncomment in `.htaccess`:
   ```apache
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```

### Database Configuration

The application uses Supabase (cloud database), so no local database setup needed.
However, ensure `.env` has correct Supabase credentials.

### Email Configuration (Optional)

If your HRMS needs to send emails:

1. **Get SMTP Details from Exabytes**:
   - cPanel → **Email** → **Email Accounts**
   - Create email account
   - Note SMTP settings

2. **Add to `.env`**:
   ```env
   SMTP_HOST=mail.yourdomain.com
   SMTP_PORT=587
   SMTP_USER=noreply@yourdomain.com
   SMTP_PASSWORD=your-email-password
   SMTP_FROM=noreply@yourdomain.com
   ```

---

## 🐛 Troubleshooting Exabytes-Specific Issues

> **📚 For comprehensive troubleshooting, see [EXABYTES_TROUBLESHOOTING.md](EXABYTES_TROUBLESHOOTING.md)**

### Issue: "503 Service Unavailable" or Blank Page

**Cause**: Virtual environment or dependencies not properly set up, or incorrect paths in .htaccess

**Solution**:
```bash
cd ~/public_html/hrms
# 1. Check .htaccess has YOUR actual username (not $CPANEL_USER)
nano .htaccess
# 2. Install dependencies
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt --force-reinstall
touch passenger_wsgi.py
```

### Issue: "ModuleNotFoundError"

**Cause**: Dependencies installed in wrong Python environment

**Solution**:
```bash
# Verify you're in the correct virtual environment
which python
# Should show: /home/yourusername/virtualenv/hrms/3.11/bin/python

# Reinstall in correct environment
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
```

### Issue: "Permission Denied" Errors

**Cause**: Incorrect file permissions

**Solution**:
```bash
cd ~/public_html/hrms
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
```

### Issue: Application Shows Old Version

**Cause**: Passenger cache not cleared

**Solution**:
```bash
cd ~/public_html/hrms
touch passenger_wsgi.py
touch tmp/restart.txt
```

Or via cPanel:
- **Setup Python App** → Find app → **Restart**

### Issue: Cannot Connect to Database

**Cause**: Supabase credentials incorrect or missing

**Solution**:
1. Verify `.env` file exists in `~/public_html/hrms`
2. Check credentials are correct
3. Test connection:
   ```bash
   cd ~/public_html/hrms
   source ~/virtualenv/hrms/3.11/bin/activate
   python3 -c "from services.supabase_service import supabase; print(supabase.table('employees').select('*').limit(1).execute())"
   ```

### Issue: Slow Performance

**Exabytes-Specific Solutions**:

1. **Optimize Passenger**:
   Add to `.htaccess`:
   ```apache
   PassengerMinInstances 2
   PassengerMaxPoolSize 4
   PassengerStartTimeout 600
   ```

2. **Enable OPcache** (if available):
   - Contact Exabytes support to enable
   - Or check in **Select PHP Version** → **Options**

3. **Check Resource Usage**:
   - cPanel → **Metrics** → **CPU and Concurrent Connection Usage**
   - If high, consider upgrading plan

### Issue: Git Deployment Not Working

**Solution**:
```bash
# Via SSH
cd ~/repositories/HRMS_app
git pull origin main

# Re-run deployment
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

---

## 📈 Performance Optimization for Exabytes

### 1. Optimize Static Files

Already configured in `.htaccess`:
- Gzip compression
- Browser caching
- CDN-ready headers

### 2. Use Exabytes CDN (if available)

Contact Exabytes support to enable CDN for static files.

### 3. Enable HTTP/2

Automatically enabled with SSL on Exabytes servers.

### 4. Monitor Performance

Use these tools:
- Google PageSpeed Insights
- GTmetrix
- Exabytes cPanel metrics

---

## 🔒 Security Best Practices

### 1. Secure Your `.env` File

Already protected by `.htaccess`, but verify:
```bash
# Check .htaccess includes:
<FilesMatch "\.(env|py|pyc)$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

### 2. Enable Firewall Rules

In cPanel:
- **Security** → **ModSecurity** → Enable
- **Security** → **IP Blocker** → Block suspicious IPs

### 3. Regular Updates

```bash
cd ~/public_html/hrms
git pull origin main
source ~/virtualenv/hrms/3.11/bin/activate
pip install --upgrade -r requirements.txt
touch passenger_wsgi.py
```

### 4. Monitor Logs

Set up regular log monitoring:
```bash
# Create a simple monitoring script
cat > ~/check_hrms.sh << 'EOF'
#!/bin/bash
cd ~/public_html/hrms
if grep -q "ERROR" log/passenger.log; then
    echo "Errors found in HRMS application logs"
fi
EOF

chmod +x ~/check_hrms.sh
```

Add to cron (cPanel → **Advanced** → **Cron Jobs**):
```
0 * * * * ~/check_hrms.sh
```

---

## 🔄 Updating the Application

### Via Git (Recommended)

```bash
cd ~/public_html/hrms
git pull origin main
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### Manual Update

1. Download latest version from GitHub
2. Upload via File Manager
3. Extract and replace files
4. Restart application

---

## 💾 Backup Strategy

### 1. Automated cPanel Backups

Exabytes provides automatic backups. Verify in:
- cPanel → **Files** → **Backup** → Check schedule

### 2. Manual Backup

```bash
# Via SSH
cd ~
tar -czf hrms_backup_$(date +%Y%m%d).tar.gz public_html/hrms
```

### 3. Database Backup

Supabase provides automatic backups. Check your Supabase dashboard.

---

## 📞 Support Resources

### Exabytes Support

- **24/7 Live Chat**: Available in your Exabytes account
- **Phone**: +603-2182-0888 (Malaysia)
- **Email**: support@exabytes.com
- **Ticket System**: https://my.exabytes.com/submitticket.php

### Application Support

- **Documentation**: See `CPANEL_DEPLOYMENT.md`, `CPANEL_QUICKSTART.md`
- **Issues**: GitHub repository issues
- **General cPanel**: `CPANEL_DEPLOYMENT.md`

### Common Questions for Exabytes Support

If you need to contact Exabytes support, you can ask:
- "How do I access SSH on my hosting plan?"
- "What Python versions are available on my server?"
- "Can you help enable Passenger for Python applications?"
- "How do I increase PHP memory limit?" (if needed)
- "Can you enable Redis/Memcached?" (for caching)

---

## ✨ Success Checklist

- [ ] Exabytes cPanel access working
- [ ] Python app created in cPanel
- [ ] Application files deployed to `public_html/hrms`
- [ ] Virtual environment activated
- [ ] Dependencies installed successfully
- [ ] `.env` file created with correct credentials
- [ ] `.htaccess` updated with correct Python path
- [ ] File permissions set correctly
- [ ] Application restarted
- [ ] Login page loads at domain
- [ ] API docs accessible at `/docs`
- [ ] Health endpoint returns success
- [ ] SSL certificate installed (recommended)
- [ ] Git deployment configured (optional)
- [ ] Backup strategy in place

---

## 🎉 Congratulations!

Your HRMS web application is now running on **Exabytes cPanel**!

### Next Steps

1. ✅ Test all functionality
2. ✅ Configure leave types and settings
3. ✅ Add employees
4. ✅ Train users
5. ✅ Set up monitoring

### Important URLs

- **Application**: `https://yourdomain.com`
- **API Documentation**: `https://yourdomain.com/docs`
- **Health Check**: `https://yourdomain.com/health`
- **Exabytes Dashboard**: https://my.exabytes.com

---

## 📖 Additional Documentation

- **Quick Start**: `CPANEL_QUICKSTART.md`
- **Full Deployment Guide**: `CPANEL_DEPLOYMENT.md`
- **Web Interface Guide**: `WEB_INTERFACE_GUIDE.md`
- **Troubleshooting**: `TROUBLESHOOTING_UI.md`

---

**Deployment Platform**: Exabytes cPanel  
**Application**: HRMS Web Application  
**Status**: Production Ready  
**Support**: 24/7 via Exabytes

Enjoy your HRMS application! 🚀
