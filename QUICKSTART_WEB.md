# HRMS Web Application - Quick Start Guide

## 🚀 Get Started in 4 Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
# Copy example environment file
cp .env.example .env

# Edit with your Supabase credentials (optional - defaults provided)
nano .env
```

**Note:** The application works out-of-the-box with default credentials. Only configure `.env` if you need custom Supabase credentials or deployment settings.

### 3. Start the Web Server
```bash
python start_web.py
```

### 4. Open Your Browser
Navigate to: **http://localhost:8000**

That's it! 🎉

---

## 📱 What You'll See

### Login Page
- Enter your username and password
- Click "Login"
- You'll be redirected based on your role:
  - **Admin** → Admin Dashboard
  - **Employee** → Employee Dashboard

### Employee Dashboard
Tabs available:
- 🏠 **Home** - Summary of attendance and leave
- 👤 **Profile** - Your personal information
- 📅 **Attendance** - Your attendance history
- 📬 **Leave Request** - Your leave requests
- 💸 **Payroll** - Coming soon
- 🗂 **Engagements** - Coming soon

### Admin Dashboard
Tabs available:
- 👥 **Employees** - List of all employees
- 📅 **Attendance** - Coming soon
- 📬 **Leave Management** - Coming soon
- 💸 **Payroll** - Coming soon
- 🎁 **Bonus** - Coming soon

---

## 🔧 Alternative Startup Methods

### Using Flask directly
```bash
python -c "from web_app import app; app.run(host='0.0.0.0', port=8000)"
```

### With debug mode (for development)
```bash
FLASK_DEBUG=true python start_web.py
```

### Using Python directly
```bash
python web_app.py
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file for custom configuration:

```bash
cp .env.example .env
```

Available settings:

| Variable | Description | Default |
|----------|-------------|---------|
| `SUPABASE_URL` | Your Supabase project URL | Default provided |
| `SUPABASE_KEY` | Your Supabase service role key | Default provided |
| `WEB_HOST` | Host to bind the server | `0.0.0.0` |
| `WEB_PORT` | Port for the server | `8000` |
| `FLASK_DEBUG` | Enable debug mode (dev mode) | `false` |
| `ENVIRONMENT` | Environment name | `production` |

### Change Port

Option 1 - Using `.env`:
```bash
# In .env file
WEB_PORT=8001
```

Option 2 - Command line:
```bash
python -c "from web_app import app; app.run(port=8001)"
```

### Development Mode

For auto-reload during development:
```bash
# In .env file
FLASK_DEBUG=true
ENVIRONMENT=development
```

**See `docs/DEPLOYMENT_GUIDE.md` for production deployment instructions.**

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use a different port
python -c "from web_app import app; app.run(port=8001)"
```

### Module Not Found
```bash
# Make sure you're in the correct directory
cd /path/to/HRMS_app

# Reinstall dependencies
pip install -r requirements.txt
```

### Cannot Connect to Database
- Check your `.env` file exists
- Verify Supabase URL and API key
- Test internet connection

---

## 🎯 Quick Test

### Test the Health Endpoint
```bash
curl http://localhost:8000/health
```

Should return:
```json
{"status": "healthy", "timestamp": "2024-11-14T..."}
```

### Test the Login Endpoint
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

---

## 📖 More Information

- **Full Documentation**: See `docs/WEB_APPLICATION_GUIDE.md`
- **Web vs Desktop**: See `docs/WEB_VS_DESKTOP.md`
- **Implementation Details**: See `docs/IMPLEMENTATION_SUMMARY.md`
- **Web README**: See `web/README.md`

---

## 🔐 Default Access

Use the same credentials as the desktop application. If you don't have credentials, contact your administrator.

---

## 🌐 Accessing from Other Devices

To access from other devices on the same network:

1. Find your IP address:
```bash
# macOS/Linux
ifconfig | grep "inet "
# Windows
ipconfig
```

2. Start server with `0.0.0.0`:
```bash
python start_web.py  # Already configured for 0.0.0.0
```

3. Access from other devices:
```
http://YOUR_IP_ADDRESS:8000
```

---

## 📝 Notes

- The web version and desktop version share the same database
- Changes made in one interface will be reflected in the other
- The desktop application (`python main.py`) still works independently
- No data migration is needed between versions

---

## 🎉 Enjoy!

You now have a modern web interface for HRMS that works alongside the desktop application!

For questions or issues, check the documentation in the `docs/` folder.
