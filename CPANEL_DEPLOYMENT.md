# HRMS Web Application - cPanel Deployment Guide

This guide provides step-by-step instructions for deploying the HRMS web application on cPanel hosting with Python support.

## Prerequisites

✅ cPanel hosting account with:
- **Python 3.9 or higher support** (Python 3.11 recommended)
  - ⚠️ Python 3.8 is NOT compatible with this application
  - Required by: supabase>=2.8.1, holidays>=0.81, pandas>=2.2.2
- SSH access (recommended)
- Git access (recommended)
- Passenger support for Python applications

## Quick Start

### Option 1: Git Deployment (Recommended)

If your cPanel account has Git deployment enabled:

1. **Login to cPanel** and go to **Git Version Control**

2. **Create a repository**:
   - Repository URL: `https://github.com/Isfahan123/HRMS_app.git`
   - Repository Path: `/home/your-username/repositories/HRMS_app`
   - Branch: `main` (or your desired branch)

3. **Pull the repository** and it will automatically deploy to your domain using `.cpanel.yml`

4. **Configure Python environment** (see Configuration section below)

5. **Access your application** at your domain

### Option 2: Manual Deployment via SSH

1. **Connect to your server via SSH**:
   ```bash
   ssh your-username@your-domain.com
   ```

2. **Navigate to your public_html directory**:
   ```bash
   cd ~/public_html
   ```

3. **Clone the repository**:
   ```bash
   git clone https://github.com/Isfahan123/HRMS_app.git
   cd HRMS_app
   ```

4. **Set up Python virtual environment** (see Configuration section below)

5. **Configure the application** (see Configuration section below)

### Option 3: File Upload via cPanel File Manager

1. **Download the repository** as a ZIP file from GitHub

2. **Login to cPanel** → **File Manager**

3. **Navigate to** `public_html`

4. **Upload and extract** the ZIP file

5. **Continue with Configuration** section below

---

## Configuration

### Step 1: Set Up Python Virtual Environment

1. **Login to cPanel** → **Setup Python App**

2. **Create New Application**:
   - Python Version: `3.11` (or latest available)
   - Application Root: `/home/your-username/public_html/HRMS_app`
   - Application URL: `your-domain.com` or `subdomain.your-domain.com`
   - Application Startup File: `passenger_wsgi.py`
   - Application Entry Point: `application`

3. **Click "Create"** - cPanel will create a virtual environment

4. **Note the virtual environment path** (usually shown in the interface):
   ```
   /home/your-username/virtualenv/HRMS_app/3.11
   ```

### Step 2: Install Dependencies

**Via cPanel Terminal or SSH**:

```bash
# Navigate to your application directory
cd ~/public_html/HRMS_app

# Activate the virtual environment
source ~/virtualenv/HRMS_app/3.11/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Via cPanel Python App interface**:
- Some cPanel interfaces allow you to paste the contents of `requirements.txt`
- Or use the "Run pip install" button if available

### Step 3: Configure Environment Variables

1. **Create the `.env` file**:
   ```bash
   cd ~/public_html/HRMS_app
   cp .env.example .env
   nano .env
   ```

2. **Edit with your credentials**:
   ```env
   # Supabase Configuration
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_service_role_key
   
   # Web Application Configuration
   WEB_HOST=0.0.0.0
   WEB_PORT=8000
   WEB_RELOAD=false
   
   # Application Environment
   ENVIRONMENT=production
   ```

3. **Save and exit** (Ctrl+X, Y, Enter in nano)

### Step 4: Update .cpanel.yml (if using Git deployment)

Edit `.cpanel.yml` and update the Python version path if different:

```yaml
deployment:
  tasks:
    - echo "Starting deployment of HRMS_app..."
    
    # Update this path to match your actual virtual environment
    - source /home/$CPANEL_USER/virtualenv/HRMS_app/3.11/bin/activate
    
    - echo "Installing Python dependencies..."
    - pip install --upgrade pip
    - pip install -r requirements.txt
    
    - echo "Reloading Passenger..."
    - touch passenger_wsgi.py
    
    - echo "Deployment completed successfully."
```

### Step 5: Update .htaccess

The `.htaccess` file should already be configured, but verify the Python path:

```apache
PassengerPython /home/$CPANEL_USER/virtualenv/HRMS_app/3.11/bin/python
```

Replace `$CPANEL_USER` with your actual cPanel username if it doesn't auto-resolve.

### Step 6: Set Proper Permissions

```bash
cd ~/public_html/HRMS_app

# Set directory permissions
find . -type d -exec chmod 755 {} \;

# Set file permissions
find . -type f -exec chmod 644 {} \;

# Make scripts executable
chmod +x start_web.py
chmod 644 passenger_wsgi.py
```

### Step 7: Restart the Application

**Option A - Touch passenger_wsgi.py** (Quick):
```bash
cd ~/public_html/HRMS_app
touch passenger_wsgi.py
```

**Option B - Via cPanel**:
- Go to **Setup Python App**
- Find your application
- Click "Restart"

**Option C - Via tmp/restart.txt** (Passenger standard):
```bash
cd ~/public_html/HRMS_app
mkdir -p tmp
touch tmp/restart.txt
```

---

## Verification

### Check Application Status

1. **Visit your domain**:
   ```
   https://your-domain.com
   ```
   You should see the HRMS login page.

2. **Check API Documentation**:
   ```
   https://your-domain.com/docs
   ```
   FastAPI Swagger UI should load.

3. **Test Health Endpoint**:
   ```bash
   curl https://your-domain.com/health
   ```
   Should return: `{"status":"healthy","timestamp":"..."}`

### Check Logs

**Passenger logs**:
```bash
cd ~/public_html/HRMS_app
cat log/passenger.log
```

**Application logs** (if you set up logging):
```bash
cd ~/public_html/HRMS_app
tail -f logs/app.log
```

**cPanel error logs**:
- Via cPanel → **Metrics** → **Errors**

---

## Troubleshooting

### Issue: "503 Service Unavailable"

**Causes:**
- Virtual environment not activated
- Dependencies not installed
- Python version mismatch

**Solutions:**
```bash
# Reinstall dependencies
cd ~/public_html/HRMS_app
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### Issue: "An error occurred during installation of modules"

**Causes:**
- fpdf2 requires Pillow and fonttools which may fail to compile on restricted hosting
- Missing development headers for C compilation
- Python version incompatibility

**Solutions:**
```bash
# Use minimal requirements (excludes PDF generation but app will work)
cd ~/public_html/HRMS_app
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements-minimal.txt
touch passenger_wsgi.py
```

If you need PDF generation later:
```bash
pip install fpdf2
```

### Issue: "Internal Server Error (500)"

**Causes:**
- Missing or incorrect `.env` configuration
- Database connection issues
- Import errors

**Solutions:**
1. Check `.env` file exists and has correct credentials
2. Check error logs (see Logs section above)
3. Test imports:
   ```bash
   cd ~/public_html/HRMS_app
   source ~/virtualenv/HRMS_app/3.11/bin/activate
   python3 -c "from web_app import app; print('OK')"
   ```

### Issue: "Module not found" errors

**Solution:**
```bash
cd ~/public_html/HRMS_app
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements.txt --force-reinstall
touch passenger_wsgi.py
```

### Issue: Static files (CSS/JS) not loading

**Causes:**
- Incorrect `.htaccess` configuration
- File permissions issues

**Solutions:**
```bash
# Fix permissions
cd ~/public_html/HRMS_app
chmod -R 755 web/static

# Clear cache
rm -rf web/static/.cache

# Restart
touch passenger_wsgi.py
```

### Issue: "Permission Denied"

**Solution:**
```bash
cd ~/public_html/HRMS_app
find . -type d -exec chmod 755 {} \;
find . -type f -exec chmod 644 {} \;
```

### Issue: Application is slow or timing out

**Causes:**
- Database connection timeout
- Not enough resources

**Solutions:**
1. Check Supabase connection:
   ```bash
   python3 -c "from services.supabase_service import supabase; print(supabase.table('employees').select('*').limit(1).execute())"
   ```

2. Increase Passenger memory:
   - Add to `.htaccess`:
     ```apache
     PassengerMaxPoolSize 6
     PassengerMinInstances 2
     ```

3. Contact hosting provider for resource upgrades

---

## Updating the Application

### Via Git (if using Git deployment):

```bash
cd ~/public_html/HRMS_app
git pull origin main
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### Via cPanel Git Interface:

1. Go to **Git Version Control**
2. Find your repository
3. Click **Pull or Deploy**
4. Select **Deploy HEAD Commit**

### Manual Update:

1. Download new files
2. Upload to server (overwrite old files)
3. Install new dependencies if any
4. Restart application

---

## Performance Optimization

### 1. Enable Gzip Compression

Already configured in `.htaccess`:
```apache
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/css text/javascript application/javascript
</IfModule>
```

### 2. Enable Browser Caching

Already configured in `.htaccess`:
```apache
<IfModule mod_expires.c>
    ExpiresActive On
    # ... caching rules
</IfModule>
```

### 3. Optimize Passenger Settings

Add to `.htaccess`:
```apache
# Use more application instances
PassengerMinInstances 2
PassengerMaxPoolSize 6

# Increase request timeout
PassengerStartTimeout 600
```

### 4. Enable HTTP/2 (if SSL is installed)

Most cPanel servers enable this automatically with SSL.

---

## Security Best Practices

### 1. Protect Sensitive Files

Already configured in `.htaccess`:
```apache
<FilesMatch "\.(env|py|pyc|log|ini|md|txt)$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

### 2. Enable SSL/HTTPS

1. In cPanel → **SSL/TLS Status**
2. Enable AutoSSL or install Let's Encrypt
3. Uncomment in `.htaccess`:
   ```apache
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```

### 3. Regular Updates

```bash
# Update Python packages
cd ~/public_html/HRMS_app
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip list --outdated
pip install --upgrade package-name
```

### 4. Secure Database Credentials

- Never commit `.env` to version control
- Use strong Supabase service role keys
- Rotate keys periodically

---

## Backup Strategy

### 1. Database Backup

Supabase provides automatic backups. Check your Supabase dashboard.

### 2. Application Backup

**Via cPanel Backup**:
- cPanel → **Backup** → **Download a Home Directory Backup**

**Via SSH**:
```bash
cd ~
tar -czf hrms_backup_$(date +%Y%m%d).tar.gz public_html/HRMS_app
```

### 3. Automated Backups

Set up a cron job:
```bash
0 2 * * * cd ~ && tar -czf hrms_backup_$(date +\%Y\%m\%d).tar.gz public_html/HRMS_app
```

---

## Monitoring

### 1. Set Up Monitoring

Use services like:
- UptimeRobot (free)
- Pingdom
- StatusCake

Monitor: `https://your-domain.com/health`

### 2. Error Tracking

Check logs regularly:
```bash
tail -f ~/public_html/HRMS_app/log/passenger.log
```

### 3. Performance Monitoring

Use tools like:
- Google PageSpeed Insights
- GTmetrix
- WebPageTest

---

## Support

### Documentation

- **Quick Start**: See `QUICKSTART_WEB.md`
- **Full Deployment**: See `docs/DEPLOYMENT_GUIDE.md`
- **Web Interface**: See `WEB_INTERFACE_GUIDE.md`
- **Troubleshooting**: See `TROUBLESHOOTING_UI.md`

### Common Resources

- [cPanel Documentation](https://docs.cpanel.net/)
- [Passenger Documentation](https://www.phusionpassenger.com/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Supabase Documentation](https://supabase.com/docs)

### Getting Help

1. Check the documentation files in the repository
2. Review error logs
3. Test locally first: `python start_web.py`
4. Contact your hosting provider for cPanel-specific issues
5. Contact Supabase support for database issues

---

## Success Checklist

- [ ] Python virtual environment created
- [ ] Dependencies installed from requirements.txt
- [ ] `.env` file configured with credentials
- [ ] `.htaccess` updated with correct Python path
- [ ] File permissions set correctly
- [ ] Application accessible via domain
- [ ] Login page loads correctly
- [ ] API documentation accessible at /docs
- [ ] Health endpoint returns success
- [ ] SSL certificate installed (recommended)
- [ ] Backup strategy in place
- [ ] Monitoring set up

---

## Congratulations! 🎉

Your HRMS web application is now running on cPanel!

**Next Steps:**
1. Test login with your credentials
2. Configure leave types and settings
3. Add employees
4. Run initial payroll test
5. Train users on the interface

For questions, refer to the documentation or check the application logs.

---

**Application URL**: https://your-domain.com  
**API Docs**: https://your-domain.com/docs  
**Health Check**: https://your-domain.com/health

Enjoy your HRMS web application! 🚀
