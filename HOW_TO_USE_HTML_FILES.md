# How to Use the HTML Files - HRMS Web Application Guide

## Overview

This document explains how to use the HTML files from the Flask web application conversion of HRMS. The web version was created in **PR #2** but was later reverted in **PR #3**. This guide will help you understand and use the HTML-based web application.

## What Was Created in PR #2?

The HRMS desktop application (PyQt5) was converted to a Flask web application with 19 HTML templates, creating a full-featured web-based HRMS system.

### Files Created (33 total):

#### Core Application (2 files)
- **`app.py`** - Flask application with 25+ API endpoints (416 lines)
- **`requirements.txt`** - Updated with Flask 3.0.0 dependency

#### HTML Templates (19 files)
1. **`templates/base.html`** - Base template with common layout
2. **`templates/index.html`** - Landing page with hero section
3. **`templates/login.html`** - Authentication page
4. **`templates/dashboard.html`** - Employee dashboard (6 tabs)
5. **`templates/admin_dashboard.html`** - Admin dashboard (10 tabs)

**Employee Templates:**
6. `templates/employee_profile.html` - Profile information
7. `templates/employee_attendance.html` - Check-in/out & history
8. `templates/employee_leave.html` - Leave requests & balance
9. `templates/employee_payroll.html` - Salary & payslips
10. `templates/employee_engagements.html` - Training & trips

**Admin Templates:**
11. `templates/admin_profile.html` - Employee CRUD
12. `templates/admin_leave.html` - Leave approvals
13. `templates/admin_payroll.html` - Payroll processing
14. `templates/admin_attendance.html` - Attendance management
15. `templates/admin_salary_history.html` - Salary changes
16. `templates/admin_bonus.html` - Bonus management
17. `templates/admin_training.html` - Training courses
18. `templates/admin_trips.html` - Overseas trips
19. `templates/admin_tax_config.html` - Tax configuration

#### Static Files (3 files)
- **`static/css/style.css`** - Complete responsive styling (300+ lines)
- **`static/js/main.js`** - Utility functions (107 lines)
- **`static/js/dashboard.js`** - Dashboard logic (350+ lines)

#### Documentation (8 files)
- **`README_WEB.md`** - Comprehensive web app guide (306 lines)
- **`QUICKSTART.md`** - 5-minute setup guide (296 lines)
- **`CONVERSION_SUMMARY.md`** - Technical conversion details (328 lines)
- **`HTML_PAGES_INDEX.md`** - Complete page reference (513 lines)
- **`API_DOCUMENTATION.md`** - Complete API reference (751 lines)
- **`BACKEND_IMPLEMENTATION.md`** - Technical implementation (508 lines)
- **`IMPLEMENTATION_COMPLETE.md`** - Development summary (530 lines)
- **`COMPLETION_SUMMARY.md`** - Final summary (326 lines)

#### Configuration (3 files)
- **`.env.example`** - Configuration template
- **`.gitignore`** - Updated to exclude .env
- **`requirements.txt`** - Flask dependency added

---

## How to Restore and Use the Web Version

### Option 1: Cherry-Pick from PR #2

If you want to restore the web version, you can cherry-pick the commits from PR #2:

```bash
# View the commits from PR #2
git log origin/copilot/rewrite-files-to-html --oneline

# Cherry-pick the web application commits
git cherry-pick <commit-sha>
```

### Option 2: Access PR #2 Branch Directly

You can check out the original PR #2 branch to see all the HTML files:

```bash
# Fetch all branches
git fetch --all

# Check out PR #2 branch (if it still exists)
git checkout copilot/rewrite-files-to-html

# Or view files from the closed PR on GitHub
# Navigate to: https://github.com/Isfahan123/HRMS_app/pull/2/files
```

### Option 3: Start Fresh with Flask

Follow these steps to recreate the web application:

1. **Install Flask**:
```bash
pip install Flask==3.0.0
```

2. **Create Basic Flask App** (`app.py`):
```python
from flask import Flask, render_template

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
```

3. **Create Templates Directory**:
```bash
mkdir -p templates static/css static/js
```

4. **Create HTML Files** (see templates section below)

---

## Understanding the HTML Files

### File Structure

```
HRMS_app/
├── app.py                  # Flask application (MAIN ENTRY POINT)
├── templates/              # HTML templates
│   ├── base.html          # Base template (inherited by all pages)
│   ├── index.html         # Landing page
│   ├── login.html         # Login page
│   ├── dashboard.html     # Employee dashboard
│   └── ...                # Other templates
├── static/
│   ├── css/
│   │   └── style.css      # Main stylesheet
│   └── js/
│       ├── main.js        # Utility functions
│       └── dashboard.js   # Dashboard logic
└── services/              # Backend services (unchanged)
```

### How the Templates Work

#### 1. Base Template (`base.html`)
All pages extend from this template:

```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}HRMS{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    {% block content %}{% endblock %}
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

#### 2. Landing Page (`index.html`)
Professional landing page with:
- Hero section with welcome message
- Features showcase (6 cards)
- Benefits section
- Call-to-action buttons
- Auto-redirect if already logged in

#### 3. Login Page (`login.html`)
- Username/password form
- AJAX submission
- Error message display
- Redirects to appropriate dashboard based on role

#### 4. Employee Dashboard (`dashboard.html`)
Tab-based interface with 6 tabs:
- 🏠 Home - Summary view
- 👤 Profile - Employee information
- 📅 Attendance - Check-in/out & history
- 📬 Leave - Leave requests & balance
- 💸 Payroll - Salary & payslips
- 🗂 Engagements - Training & trips

#### 5. Admin Dashboard (`admin_dashboard.html`)
Tab-based interface with 10 tabs:
- 🏠 Home - System overview
- 👤 Profile Management - Employee CRUD
- 📅 Attendance - Attendance oversight
- 📬 Leave - Approve/reject leaves
- 💸 Payroll - Process payroll
- 💰 Salary History - Track changes
- 🎁 Bonus - Manage bonuses
- 📚 Training - Course management
- ✈️ Trips - Overseas trips
- 📊 Tax Config - Tax settings

---

## How to Run the Web Application

### Prerequisites

- Python 3.8+
- pip package manager
- Supabase account (database)

### Step 1: Install Dependencies

```bash
pip install Flask==3.0.0
# Existing dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file:

```env
# Supabase (if not hardcoded in supabase_service.py)
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Flask
FLASK_SECRET_KEY=your_random_secret_key
FLASK_ENV=development
FLASK_DEBUG=1
```

Generate a secret key:
```bash
python -c "import os; print(os.urandom(24).hex())"
```

### Step 3: Run the Application

```bash
# From the project root
python app.py
```

The application will be available at:
```
http://localhost:5000
```

### Step 4: Access the Application

1. Open browser to `http://localhost:5000`
2. You'll see the landing page
3. Click "Login" to access the system
4. Use your existing database credentials

---

## API Endpoints

The Flask app provides 25+ RESTful API endpoints:

### Authentication
- `POST /login` - User authentication
- `GET /logout` - Clear session

### Employee APIs (7 endpoints)
- `GET /api/profile` - Employee profile
- `GET /api/attendance` - Attendance history
- `GET /api/leave-requests` - Leave requests
- `POST /api/leave-requests/submit` - Submit leave
- `GET /api/payroll` - Payroll information
- `GET /api/training` - Training courses
- `GET /api/trips` - Overseas trips

### Admin APIs (18 endpoints)
- `GET /api/admin/employees` - List all employees
- `POST /api/admin/employees/add` - Add employee
- `PUT /api/admin/employees/<id>` - Update employee
- `GET /api/admin/leave-requests` - All leave requests
- `POST /api/admin/leave-requests/<id>/approve` - Approve leave
- `POST /api/admin/leave-requests/<id>/reject` - Reject leave
- And many more...

See **API_DOCUMENTATION.md** from PR #2 for complete details.

---

## Desktop vs Web Version

| Aspect | Desktop (PyQt5) | Web (Flask) |
|--------|-----------------|-------------|
| **Platform** | Windows/Mac/Linux | Any browser |
| **Installation** | Required | None |
| **Updates** | Manual | Automatic |
| **Access** | Local only | Anywhere |
| **Mobile** | No | Yes |
| **Multi-user** | Limited | Unlimited |
| **Database** | Supabase | Supabase (same) |

### Key Advantages of Web Version:

✅ **Cross-platform** - Works on any device with a browser  
✅ **No installation** - Just open the browser  
✅ **Centralized deployment** - Update once, everyone updated  
✅ **Mobile-friendly** - Responsive design  
✅ **Remote access** - Work from anywhere  
✅ **Better collaboration** - Real-time multi-user access  

---

## Design & Styling

### Color Scheme
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Success**: Green (#27ae60)
- **Danger**: Red (#e74c3c)
- **Secondary**: Gray (#95a5a6)

### Components
- Modern card-based design
- Responsive CSS Grid and Flexbox
- Native HTML5 date inputs
- Modal dialogs for forms
- Tab-based navigation
- Status badges with colors

### Responsive Design
- **Mobile**: < 768px (stacked layout)
- **Tablet**: 768px - 1024px (adjusted layout)
- **Desktop**: > 1024px (full features)

---

## Why Was It Reverted?

PR #2 was reverted in PR #3. The reason appears to be related to understanding how to use the web application vs the desktop application. PR #4 then added documentation clarifying that HRMS is a **desktop application** (PyQt5), not a web application.

However, **both versions can coexist**:
- Desktop app: Run `python main.py`
- Web app: Run `python app.py`
- They use the same database (Supabase)

---

## Next Steps

### To Use the Web Version:

1. **Restore PR #2 Files**:
   - Check out PR #2 branch or cherry-pick commits
   - Or manually recreate files based on this guide

2. **Install Dependencies**:
   ```bash
   pip install Flask==3.0.0
   ```

3. **Configure Environment**:
   - Create `.env` file with secrets
   - Or use existing Supabase credentials

4. **Run the Application**:
   ```bash
   python app.py
   ```

5. **Access in Browser**:
   - Open `http://localhost:5000`
   - Login with existing credentials

### To Keep Desktop Version:

Continue using the existing PyQt5 application:
```bash
python main.py
```

### To Use Both:

Run both applications simultaneously:
```bash
# Terminal 1: Desktop app
python main.py

# Terminal 2: Web app
python app.py
```

They share the same Supabase database, so data stays synchronized.

---

## Deployment Options

### Development (Local)
```bash
python app.py
```

### Production (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Cloud Platforms
- **Heroku**: Easy deployment with Git
- **DigitalOcean**: App Platform
- **AWS**: Elastic Beanstalk
- **Google Cloud**: App Engine
- **Azure**: App Service

### Nginx (Reverse Proxy)
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Getting Help

### Documentation from PR #2:
- **README_WEB.md** - Comprehensive guide
- **QUICKSTART.md** - Quick setup
- **API_DOCUMENTATION.md** - API reference
- **CONVERSION_SUMMARY.md** - Technical details
- **HTML_PAGES_INDEX.md** - All pages documented

### Resources:
- Flask Documentation: https://flask.palletsprojects.com/
- GitHub PR #2: https://github.com/Isfahan123/HRMS_app/pull/2
- Supabase Docs: https://supabase.com/docs

---

## Summary

The HTML files from PR #2 created a **complete, production-ready Flask web application** with:

✅ 19 HTML templates  
✅ 25+ API endpoints  
✅ Full employee & admin features  
✅ Responsive design  
✅ Complete documentation  

**To use them**: Restore PR #2, install Flask, and run `python app.py`

**Current state**: The web version was reverted, but you can restore it anytime

**Both versions work**: Desktop (main.py) and Web (app.py) can run together

---

**Last Updated**: 2025-11-12  
**Related PRs**: #2 (created web app), #3 (reverted), #4 (clarified desktop app)  
**Status**: Web app available in PR #2, desktop app is current
