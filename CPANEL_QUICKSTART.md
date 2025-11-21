# HRMS cPanel Deployment - Quick Reference

## 🚀 Fastest Way to Deploy

### Method 1: Git Auto-Deploy (30 seconds)

1. **cPanel → Git Version Control → Create**
   - URL: `https://github.com/Isfahan123/HRMS_app.git`
   - Click "Create"
   
2. **cPanel → Setup Python App → Create**
   - Python: `3.11`
   - App Root: `/home/yourusername/public_html/HRMS_app`
   - App URL: `yourdomain.com`
   - Startup: `passenger_wsgi.py`
   - Entry: `application`
   
3. **Done!** ✨ Access at `https://yourdomain.com`

### Method 2: SSH Manual Deploy (5 minutes)

```bash
# 1. Connect
ssh you@yourdomain.com

# 2. Clone
cd ~/public_html
git clone https://github.com/Isfahan123/HRMS_app.git
cd HRMS_app

# 3. Setup (via cPanel Python App interface)
# - Then come back and run:

# 4. Install
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements.txt

# 5. Configure
cp .env.example .env
nano .env  # Add your Supabase credentials

# 6. Start
touch passenger_wsgi.py

# 7. Test
curl https://yourdomain.com/health
```

---

## ⚙️ Essential Files (Already Included)

✅ `passenger_wsgi.py` - WSGI entry point  
✅ `.htaccess` - Apache configuration  
✅ `.cpanel.yml` - Auto-deployment config  
✅ `requirements.txt` - Python dependencies  
✅ `.env.example` - Environment template  

---

## 🔧 Quick Commands

### Restart Application
```bash
touch passenger_wsgi.py
```

### Update Application
```bash
cd ~/public_html/HRMS_app
git pull
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### Check Status
```bash
# Test import
python3 -c "from web_app import app; print('OK')"

# Test health
curl https://yourdomain.com/health
```

### View Logs
```bash
tail -f ~/public_html/HRMS_app/log/passenger.log
```

---

## 🐛 Quick Troubleshooting

### 503 Error
```bash
source ~/virtualenv/HRMS_app/3.11/bin/activate
pip install -r requirements.txt
touch passenger_wsgi.py
```

### 500 Error
```bash
# Check .env exists and has Supabase credentials
cat .env

# Test imports
python3 -c "from web_app import app; print('OK')"
```

### Static Files Not Loading
```bash
chmod -R 755 web/static
touch passenger_wsgi.py
```

---

## 📝 Environment Variables (.env)

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key-here
WEB_HOST=0.0.0.0
WEB_PORT=8000
ENVIRONMENT=production
```

---

## ✅ Verification Checklist

- [ ] Python 3.8+ available in cPanel
- [ ] Git repository cloned/deployed
- [ ] Python app created in cPanel
- [ ] Virtual environment activated
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Application restarted
- [ ] Login page loads at domain
- [ ] `/docs` shows API documentation
- [ ] `/health` returns `{"status":"healthy"}`

---

## 🔗 Important URLs

- **Application**: `https://yourdomain.com`
- **API Docs**: `https://yourdomain.com/docs`
- **Health Check**: `https://yourdomain.com/health`

---

## 📚 Full Documentation

- **Complete Guide**: `CPANEL_DEPLOYMENT.md`
- **Web App Guide**: `QUICKSTART_WEB.md`
- **General Deployment**: `docs/DEPLOYMENT_GUIDE.md`
- **Troubleshooting**: Check logs and `CPANEL_DEPLOYMENT.md`

---

## 💡 Pro Tips

1. **Use Git deployment** - It auto-updates on git push
2. **Enable SSL** - cPanel → SSL/TLS Status → AutoSSL
3. **Monitor uptime** - Use UptimeRobot (free) on `/health` endpoint
4. **Backup regularly** - cPanel → Backup or use cron
5. **Check logs** - When issues occur, always check logs first

---

## 🆘 Need Help?

1. ✅ Read `CPANEL_DEPLOYMENT.md` (detailed guide)
2. ✅ Check Passenger logs: `cat log/passenger.log`
3. ✅ Test locally first: `python start_web.py`
4. ✅ Verify `.env` has correct credentials
5. ✅ Ensure virtual environment is activated

---

**That's it!** Your HRMS is now running on cPanel! 🎉

For detailed instructions, see: **CPANEL_DEPLOYMENT.md**
