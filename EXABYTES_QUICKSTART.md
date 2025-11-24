# HRMS on Exabytes - Quick Start Guide 🇲🇾

## 🚀 Deploy in 5 Minutes

### Prerequisites
- ✅ Exabytes cPanel hosting with Python support
- ✅ Your Supabase credentials (URL and Key)
- ✅ SSH access (optional but helpful)

---

## Method 1: Git Auto-Deploy (Fastest - 2 minutes)

### Step 1: Create Python App
1. Login to **Exabytes cPanel**
2. Go to **Setup Python App**
3. Click **Create Application**:
   - Python Version: **3.11** (or latest)
   - App Root: `/home/yourusername/public_html/hrms`
   - App URL: `yourdomain.com` or `hrms.yourdomain.com`
   - Startup File: `passenger_wsgi.py`
   - Entry Point: `application`
4. Click **Create** and note the virtual environment path

### Step 2: Deploy Code
1. Go to **Git Version Control** → **Create**
2. Repository URL: `https://github.com/Isfahan123/HRMS_app.git`
3. Repository Path: `/home/yourusername/repositories/HRMS_app`
4. Click **Create** → **Pull or Deploy** → **Deploy HEAD Commit**

### Step 3: Link Application
Via cPanel Terminal or SSH:
```bash
cd ~/public_html
ln -s ~/repositories/HRMS_app hrms
cd hrms
```

### Step 4: Install Dependencies
```bash
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
```

### Step 5: Configure Environment
```bash
cp .env.example .env
nano .env  # Add your Supabase credentials
```

### Step 6: Update .htaccess
Open `.htaccess` and replace `$CPANEL_USER` with your actual username:
```apache
PassengerPython /home/YOURUSERNAME/virtualenv/hrms/3.11/bin/python
PassengerAppRoot /home/YOURUSERNAME/public_html/hrms
```

### Step 7: Restart
```bash
touch passenger_wsgi.py
```

### Step 8: Test
Visit: `https://yourdomain.com` ✅

---

## Method 2: Manual Upload (5 minutes)

### Step 1: Download
Download repository as ZIP from GitHub

### Step 2: Upload to Exabytes
1. Login to cPanel → **File Manager**
2. Navigate to `public_html`
3. Create folder `hrms` and enter it
4. Upload ZIP file
5. Right-click ZIP → **Extract**
6. Move files from extracted folder to `hrms`

### Step 3: Create Python App
Same as Method 1, Step 1

### Step 4: Install & Configure
Same as Method 1, Steps 4-8

---

## Quick Commands

### Restart Application
```bash
touch ~/public_html/hrms/passenger_wsgi.py
```

### View Logs
```bash
tail -f ~/public_html/hrms/log/passenger.log
```

### Update Application
```bash
cd ~/public_html/hrms
git pull origin main
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### Test Import
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
python3 -c "from web_app import app; print('OK')"
```

---

## Common Issues

### 503 Error
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### 500 Error
Check `.env` exists and has correct Supabase credentials:
```bash
cd ~/public_html/hrms
cat .env
```

### Module Not Found
```bash
cd ~/public_html/hrms
source ~/virtualenv/hrms/3.11/bin/activate
pip install -r requirements.txt --force-reinstall
```

---

## Verification Checklist

- [ ] Python app created in cPanel
- [ ] Code deployed to `~/public_html/hrms`
- [ ] Dependencies installed
- [ ] `.env` file configured with Supabase credentials
- [ ] `.htaccess` updated with your username
- [ ] Application restarted
- [ ] Login page loads at your domain
- [ ] Health check works: `https://yourdomain.com/health`

---

## Important URLs

- **Application**: `https://yourdomain.com`
- **API Docs**: `https://yourdomain.com/docs`
- **Health Check**: `https://yourdomain.com/health`

---

## Exabytes Support

- **24/7 Live Chat**: Available in your Exabytes account
- **Phone**: +603-2182-0888 (Malaysia)
- **Email**: support@exabytes.com
- **Portal**: https://my.exabytes.com

---

## Full Documentation

For detailed instructions and troubleshooting:
📚 [EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md)

---

## Need Help?

1. ✅ Check [EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md) for detailed guide
2. ✅ View logs: `cat ~/public_html/hrms/log/passenger.log`
3. ✅ Test locally: `python start_web.py`
4. ✅ Contact Exabytes support for hosting issues

---

**That's it!** Your HRMS is now running on Exabytes! 🎉
