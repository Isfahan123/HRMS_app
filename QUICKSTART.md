# HRMS Quick Start Guide

Welcome to the Human Resources Management System (HRMS)! This guide will help you get the application up and running.

## Important: This is a Desktop Application

**HRMS is a desktop application built with PyQt5, not a web application.** There are no HTML files to open in a browser. The application runs as a native desktop window on your computer.

## Prerequisites

Before running HRMS, ensure you have:

1. **Python 3.8 or higher** installed
   - Download from: https://www.python.org/downloads/
   - Verify installation: `python --version` or `python3 --version`

2. **pip** (Python package installer)
   - Usually comes with Python
   - Verify: `pip --version` or `pip3 --version`

3. **Supabase Account** (for database)
   - Sign up at: https://supabase.com/
   - You'll need your Supabase URL and API key

## Quick Start Steps

### Step 1: Install Dependencies

Open a terminal/command prompt in the HRMS_app directory and run:

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### Step 2: Configure Database Connection

1. Create a Supabase project at https://supabase.com/
2. Set up your database using the SQL scripts in the `/data` directory
3. Configure your database credentials in the application (see SETUP_GUIDE.md for details)

### Step 3: Run the Application

Choose one of the following methods:

#### Method 1: Using Startup Scripts (Recommended)

**On Windows (Command Prompt):**
```batch
scripts\start_hrms.bat
```

**On Windows (PowerShell):**
```powershell
scripts\start_hrms.ps1
```

**On Linux/Mac:**
```bash
./scripts/start_hrms.sh
```

#### Method 2: Direct Python Execution

```bash
python main.py
```

## What Happens When You Run It?

1. A splash screen appears showing "HRMS - Loading"
2. The application initializes all components
3. A login window opens where you can:
   - Log in with existing credentials
   - Create a new account (if enabled)

## First Time Setup

When you first run HRMS, you'll need to:

1. **Set up the database** (see `/docs/SETUP_GUIDE.md`)
2. **Configure tax rates and reliefs** (Admin panel)
3. **Add employee records**
4. **Set up holidays and leave policies**

## Troubleshooting

### "Python is not installed or not in PATH"
- Install Python from https://www.python.org/
- Make sure to check "Add Python to PATH" during installation

### "ModuleNotFoundError: No module named 'PyQt5'"
- Install dependencies: `pip install -r requirements.txt`

### "Database connection failed"
- Check your Supabase credentials
- Ensure your database tables are created
- See `/docs/SETUP_GUIDE.md` for database setup

### Application window is too small
- The main window is resizable - drag the edges to resize
- Or maximize using the window controls

### Import errors
```bash
# Try reinstalling all dependencies
pip install --upgrade -r requirements.txt
```

## Application Structure

```
HRMS_app/
├── main.py              # Application entry point - RUN THIS FILE
├── requirements.txt     # Python dependencies
├── scripts/             # Startup scripts
│   ├── start_hrms.bat   # Windows batch script
│   ├── start_hrms.ps1   # PowerShell script
│   └── start_hrms.sh    # Linux/Mac script
├── gui/                 # User interface components
├── core/                # Business logic
├── services/            # External integrations (Supabase, etc.)
├── data/                # Database schemas and configs
└── docs/                # Documentation
```

## Key Features

Once running, HRMS provides:

- **Employee Management**: Add, edit, and manage employee records
- **Leave Management**: Request and approve leave
- **Payroll Processing**: Calculate salaries with Malaysian tax compliance
- **Attendance Tracking**: Track employee attendance
- **Payslip Generation**: Generate PDF payslips
- **Holiday Calendar**: Manage company holidays
- **Bonus Management**: Process employee bonuses
- **Training Records**: Track employee training

## Next Steps

1. ✅ Run the application using one of the methods above
2. 📚 Read `/docs/SETUP_GUIDE.md` for detailed configuration
3. 🏗️ Set up your database schema
4. 👤 Create admin and employee accounts
5. ⚙️ Configure tax rates and company policies

## Getting Help

- Check `/docs/` directory for detailed documentation
- Review `/docs/SETUP_GUIDE.md` for database setup
- See `/docs/REPOSITORY_STRUCTURE.md` for code organization

## Common Misconceptions

❌ **This is NOT a web application** - You cannot open it in a browser  
❌ **There is NO index.html** - It's a desktop application  
✅ **This IS a PyQt5 desktop application** - It runs as a native desktop window  
✅ **Run with Python** - Use `python main.py` or the provided scripts  

---

**Ready to start?** Run `python main.py` or use the startup scripts!
