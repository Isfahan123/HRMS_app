# HRMS Web Application - Quick Start Guide

This guide will help you quickly set up and run the HRMS web application.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- A Supabase account with database configured
- Modern web browser (Chrome, Firefox, Safari, or Edge)

## Quick Setup (5 minutes)

### Step 1: Install Dependencies

```bash
cd /path/to/HRMS_app
pip install -r requirements.txt
```

This will install all required packages including:
- Flask 3.0.0 (web framework)
- Supabase 2.8.1 (database client)
- python-dotenv (environment variables)
- And all other existing dependencies

### Step 2: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
```

Add your configuration to `.env`:

```env
# Supabase Configuration (required)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here

# Flask Configuration
FLASK_SECRET_KEY=your_random_secret_key_here
FLASK_ENV=development

# Optional: Port configuration (default is 5000)
FLASK_PORT=5000
```

**Important**: 
- Get `SUPABASE_URL` and `SUPABASE_KEY` from your Supabase project dashboard
- Generate `FLASK_SECRET_KEY` using: `python -c "import os; print(os.urandom(24).hex())"`

### Step 3: Run the Application

```bash
python app.py
```

You should see output like:
```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

### Step 4: Access the Application

Open your web browser and navigate to:
```
http://localhost:5000
```

You should see the HRMS login page.

## Default Login Credentials

Use the same credentials as the desktop application. If you don't have any:

**Employee Account:**
- Username: (your username)
- Password: (your password)

**Admin Account:**
- Username: (your admin username)
- Password: (your admin password)

## Troubleshooting

### Issue: "Module not found" errors

**Solution**: Make sure all dependencies are installed
```bash
pip install -r requirements.txt
```

### Issue: "Connection refused" or database errors

**Solution**: Check your Supabase configuration in `.env` file
```bash
# Verify your .env file exists and has correct values
cat .env
```

### Issue: "Secret key not set"

**Solution**: Generate and set a secret key
```bash
# Generate a secret key
python -c "import os; print('FLASK_SECRET_KEY=' + os.urandom(24).hex())"

# Add the output to your .env file
```

### Issue: Port already in use

**Solution**: Use a different port
```bash
# Option 1: Change port in .env
FLASK_PORT=8000

# Option 2: Specify port when running
python app.py --port 8000
```

### Issue: Templates not found

**Solution**: Make sure you're running from the correct directory
```bash
# Run from the project root where app.py is located
cd /path/to/HRMS_app
python app.py
```

## Project Structure

```
HRMS_app/
├── app.py                  # Flask application entry point (RUN THIS)
├── main.py                 # Old PyQt5 desktop app (don't use)
├── templates/              # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   └── ...
├── static/                 # CSS and JavaScript
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       └── dashboard.js
├── services/              # Backend services (Supabase, etc.)
├── core/                  # Core business logic
├── gui/                   # Old PyQt5 GUI files (not used by web app)
└── .env                   # Configuration (create this)
```

## Available Pages

### Employee Pages
- **Login**: http://localhost:5000/login
- **Dashboard**: http://localhost:5000/dashboard
- Profile, Attendance, Leave, Payroll, Engagements tabs

### Admin Pages
- **Admin Dashboard**: http://localhost:5000/admin
- Employee Management, Leave Approval, Payroll Processing, etc.

## Development Mode

For development with auto-reload:

```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python app.py
```

The server will automatically reload when you make changes to the code.

## Production Deployment

For production, use a proper WSGI server:

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

For HTTPS and better performance, use Nginx as a reverse proxy in front of Gunicorn.

## Features Overview

### Employee Features ✅
- View and edit profile
- Check-in/check-out attendance
- Submit leave requests
- View leave balance
- View payslips and salary
- View training courses
- View overseas trips

### Admin Features ✅
- Manage employees (add, edit, delete)
- Approve/reject leave requests
- Process payroll
- Generate payslips
- View attendance records
- Manage training courses
- Manage overseas trips
- Configure tax settings

## Browser Support

- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ❌ Internet Explorer (Not supported)

## Mobile Support

The web application is fully responsive and works on:
- 📱 Smartphones (iOS, Android)
- 📱 Tablets
- 💻 Desktops
- 🖥️ Large screens

## Security Notes

### Development
- Use HTTP for development
- Secret key can be simple
- Debug mode is OK

### Production
- **MUST** use HTTPS (SSL certificate)
- Use a strong, random secret key
- Disable debug mode
- Set up firewall rules
- Configure rate limiting
- Regular security updates

## Getting Help

### Documentation
- See `README_WEB.md` for comprehensive documentation
- See `CONVERSION_SUMMARY.md` for conversion details
- Check Flask documentation: https://flask.palletsprojects.com/

### Common Questions

**Q: Can I run both desktop and web versions?**  
A: Yes! They use the same database and can run simultaneously.

**Q: Will my data from the desktop app work?**  
A: Yes! They share the same Supabase database.

**Q: Can I access this from my phone?**  
A: Yes! The web interface is fully responsive and mobile-friendly.

**Q: How do I deploy this to the internet?**  
A: See the Production Deployment section above, or use platforms like Heroku, DigitalOcean, or AWS.

**Q: Is it secure?**  
A: For production, follow the security notes above and use HTTPS.

## Next Steps

1. ✅ Log in to the application
2. ✅ Explore the employee dashboard
3. ✅ Try admin features (if you have admin access)
4. 📚 Read the full documentation in `README_WEB.md`
5. 🚀 Deploy to production (when ready)

## Support

If you encounter issues:
1. Check the Troubleshooting section above
2. Review the logs in the terminal
3. Check your browser's console (F12 → Console tab)
4. Verify your `.env` configuration
5. Ensure Supabase database is accessible

## Version

- **Web Application Version**: 1.0.0
- **Flask Version**: 3.0.0
- **Python Version**: 3.8+
- **Last Updated**: 2025-11-12

---

**Happy coding! 🚀**
