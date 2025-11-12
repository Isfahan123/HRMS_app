# How to Run HRMS Application

## ⚠️ Important: This is NOT a Web Application

Many users ask about `index.html` or how to run this in a browser. **This application does NOT use HTML and cannot run in a web browser.**

### What Type of Application Is This?

```
❌ Web Application (HTML/CSS/JavaScript in browser)
✅ Desktop Application (Native window on your computer)
```

HRMS is built with **PyQt5**, which creates native desktop windows like:
- Microsoft Word
- Excel
- Adobe Acrobat
- Calculator

### Visual Comparison

**What You Might Be Looking For (Web App):**
```
Browser (Chrome/Firefox)
    ↓
http://localhost:8000/index.html
    ↓
Web Interface
```

**What HRMS Actually Is (Desktop App):**
```
Python Interpreter
    ↓
python main.py
    ↓
Native Desktop Window
```

## How to Actually Run HRMS

### Step 1: Install Prerequisites

1. **Install Python 3.8+**
   - Windows: Download from https://python.org
   - Mac: `brew install python3`
   - Linux: `sudo apt-get install python3 python3-pip`

2. **Verify Installation**
   ```bash
   python --version
   # Should show: Python 3.8 or higher
   ```

### Step 2: Install Dependencies

```bash
cd HRMS_app
pip install -r requirements.txt
```

This installs:
- PyQt5 (GUI framework)
- Supabase (database client)
- ReportLab (PDF generation)
- And other required packages

### Step 3: Run the Application

Choose the method for your operating system:

#### Option A: Use Startup Scripts (Recommended)

**Windows Users:**
```batch
# Double-click this file:
scripts\start_hrms.bat

# Or run in Command Prompt:
cd HRMS_app
scripts\start_hrms.bat
```

**Linux/Mac Users:**
```bash
# In terminal:
cd HRMS_app
./scripts/start_hrms.sh
```

**PowerShell Users (Windows):**
```powershell
cd HRMS_app
.\scripts\start_hrms.ps1
```

#### Option B: Direct Python Command

```bash
cd HRMS_app
python main.py
```

## What Happens When You Run It?

### 1. Splash Screen Appears
```
┌─────────────────────────┐
│   HRMS - Loading        │
│   ████████░░░░ 80%      │
│   Loading dashboard...  │
└─────────────────────────┘
```

### 2. Login Window Opens
```
┌─────────────────────────────┐
│      HRMS Login             │
│                             │
│  Username: [___________]    │
│  Password: [___________]    │
│                             │
│  [ Login ]  [ Register ]    │
└─────────────────────────────┘
```

### 3. Main Application Appears
```
┌──────────────────────────────────────┐
│ HRMS - Dashboard              [_][□][X]│
├──────────────────────────────────────┤
│ 📊 Dashboard | 👤 Employees | 📅 Leave│
├──────────────────────────────────────┤
│                                      │
│  Welcome to HRMS!                    │
│                                      │
│  Employee Count: 25                  │
│  Pending Leave Requests: 3           │
│  ...                                 │
│                                      │
└──────────────────────────────────────┘
```

## Troubleshooting

### "I double-clicked main.py and a black window flashed"

This is expected. Python files need to be run from a terminal/command prompt, not by double-clicking.

**Solution:**
1. Open Command Prompt/Terminal
2. Navigate to the folder: `cd HRMS_app`
3. Run: `python main.py`

### "No module named 'PyQt5'"

You haven't installed the dependencies yet.

**Solution:**
```bash
pip install -r requirements.txt
```

### "Python is not recognized"

Python is not installed or not in your PATH.

**Solution:**
1. Install Python from https://python.org
2. During installation, check "Add Python to PATH"
3. Restart your terminal

### "The application window is too small"

The window is resizable!

**Solution:**
- Drag the edges of the window to resize it
- Click the maximize button (□) in the title bar
- The minimum size is 400x300, but it can go much larger

### "Where's the web interface?"

There isn't one. This is a desktop application.

**If you need a web interface:**
- This codebase would need significant rewriting
- Consider using frameworks like Django, Flask, or FastAPI
- The current PyQt5 GUI cannot run in a browser

## Common Questions

### Q: Can I deploy this to a website?
**A:** No, this is a desktop application. It's designed to run on individual computers, not on a web server.

### Q: Can multiple users access it at the same time?
**A:** Yes, but each user runs their own copy of the application. They share data through the Supabase database.

### Q: Do I need a web server like Apache or Nginx?
**A:** No. This application doesn't need a web server because it's not a web application.

### Q: Can I access it from my phone?
**A:** Not directly. You would need to rewrite it as a mobile app or web app.

### Q: Why does the README mention scripts but no HTML?
**A:** "Scripts" refers to Python scripts and shell scripts, not JavaScript. The application uses Python code, not HTML/CSS/JavaScript.

## File Structure Explanation

```
HRMS_app/
├── main.py                    ← START HERE (run this file)
├── requirements.txt           ← Python packages needed
├── gui/                       ← User interface code (PyQt5, not HTML)
│   ├── login_window.py        ← Login screen
│   ├── dashboard_window.py    ← Main dashboard
│   └── ...
├── core/                      ← Business logic
├── services/                  ← Database connections
└── scripts/
    ├── start_hrms.bat         ← Windows startup script
    ├── start_hrms.ps1         ← PowerShell startup script
    └── start_hrms.sh          ← Linux/Mac startup script
```

### What Each File Does

- **main.py** - The entry point. This is what you run.
- **gui/*.py** - Python files that create windows and buttons using PyQt5
- **core/*.py** - Python files with business logic (calculations, etc.)
- **services/*.py** - Python files that connect to the database
- **requirements.txt** - List of Python packages to install
- **scripts/*.bat/.sh/.ps1** - Helper scripts to start the application easily

## Quick Reference Card

```
┌────────────────────────────────────────────┐
│         HRMS Quick Reference               │
├────────────────────────────────────────────┤
│ Install:  pip install -r requirements.txt  │
│                                            │
│ Run:      python main.py                   │
│  or:      scripts\start_hrms.bat (Windows) │
│  or:      ./scripts/start_hrms.sh (Linux)  │
│                                            │
│ Type:     Desktop Application (PyQt5)      │
│ Not:      Web Application (HTML)           │
│                                            │
│ Browser:  ❌ Not needed                    │
│ Python:   ✅ Required (3.8+)               │
└────────────────────────────────────────────┘
```

## Still Confused?

If you're still unsure about how to run the application:

1. **Read:** [QUICKSTART.md](QUICKSTART.md) - Step-by-step guide
2. **Check:** Do you have Python installed? Run `python --version`
3. **Verify:** Are you in the right folder? You should see `main.py`
4. **Install:** Have you run `pip install -r requirements.txt`?
5. **Run:** Execute `python main.py` from the terminal

Need more help? Check the `/docs` directory for detailed documentation.
