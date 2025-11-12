# HRMS - Human Resources Management System

A comprehensive desktop application for managing human resources, payroll, leave requests, and employee records. Built with PyQt5 and Supabase.

## 🖥️ Desktop Application (Not Web-Based)

**Important:** This is a **desktop application**, not a web application. It runs as a native window on your computer using PyQt5, similar to Microsoft Word or Excel. There are no HTML files to open in a browser.

## 🚀 Quick Start

**Want to deploy to Render or web hosting?** → [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) ⚠️

**Confused about how to run this?** → [HOW_TO_RUN.md](HOW_TO_RUN.md) ⭐

**New to HRMS?** → [QUICKSTART.md](QUICKSTART.md)

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Supabase account (for database)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Isfahan123/HRMS_app.git
   cd HRMS_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   
   **Windows:**
   ```batch
   scripts\start_hrms.bat
   ```
   
   **Linux/Mac:**
   ```bash
   ./scripts/start_hrms.sh
   ```
   
   **Or directly with Python:**
   ```bash
   python main.py
   ```

## 📖 Documentation

- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Deployment options and web vs desktop architecture
- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)** - Detailed setup instructions
- **[docs/REPOSITORY_STRUCTURE.md](docs/REPOSITORY_STRUCTURE.md)** - Code organization
- **[docs/INTEGRATION_SUMMARY.md](docs/INTEGRATION_SUMMARY.md)** - Integration overview
- **[docs/LHDN_PCB_IMPLEMENTATION.md](docs/LHDN_PCB_IMPLEMENTATION.md)** - Tax calculation details

## 🎯 Key Features

- **Employee Management** - Add, edit, and manage employee records with comprehensive profiles
- **Leave Management** - Request, approve, and track leave with real-time balance updates
- **Payroll Processing** - Calculate salaries with Malaysian LHDN tax compliance
- **Attendance Tracking** - Monitor and manage employee attendance records
- **Payslip Generation** - Automatically generate PDF payslips for employees
- **Holiday Calendar** - Manage company holidays and public holidays
- **Bonus Management** - Process and track employee bonuses
- **Training Records** - Keep track of employee training and development
- **Overseas Trips** - Manage work-related overseas travel records

## 🏗️ Technology Stack

- **Frontend:** PyQt5 (Desktop GUI Framework)
- **Backend:** Python 3.x
- **Database:** Supabase (PostgreSQL)
- **PDF Generation:** ReportLab
- **Authentication:** bcrypt
- **Date/Time:** pytz

## 📁 Repository Structure

```
HRMS_app/
├── main.py                 # Application entry point (RUN THIS)
├── requirements.txt        # Python dependencies
├── QUICKSTART.md          # Quick start guide
├── core/                  # Core business logic (31 files)
│   ├── calculators/       # Payroll, tax, and leave calculators
│   └── utilities/         # Helper functions and utilities
├── gui/                   # User interface components (67 files)
│   ├── windows/           # Main application windows
│   ├── dialogs/           # Dialog boxes and forms
│   └── tabs/              # Tab components for different modules
├── services/              # External service integrations (9 files)
│   └── supabase_service.py  # Database integration
├── data/                  # Configuration and schemas (56 files)
│   ├── SQL schemas        # Database table definitions
│   └── JSON configs       # Configuration files
├── docs/                  # Documentation (16 files)
├── tests/                 # Test files (125 files)
├── scripts/               # Utility scripts
│   ├── start_hrms.bat     # Windows startup script
│   ├── start_hrms.ps1     # PowerShell startup script
│   └── start_hrms.sh      # Linux/Mac startup script
└── examples/              # Sample data and exports
```

## 🔧 System Requirements

### Minimum Requirements
- **OS:** Windows 7+, macOS 10.12+, or Linux
- **Python:** 3.8 or higher
- **RAM:** 2 GB
- **Display:** 1024x768 minimum resolution

### Recommended
- **OS:** Windows 10+, macOS 11+, or Ubuntu 20.04+
- **Python:** 3.10 or higher
- **RAM:** 4 GB or more
- **Display:** 1920x1080 or higher

## 🚦 First Time Setup

1. **Install Python** (if not already installed)
   - Download from https://python.org
   - Make sure to check "Add Python to PATH" during installation

2. **Set up the database**
   ```bash
   # See docs/SETUP_GUIDE.md for detailed instructions
   ```

3. **Configure Supabase credentials**
   - Create a Supabase project
   - Run the SQL scripts from `/data` directory
   - Update connection settings

4. **Launch the application**
   ```bash
   python main.py
   ```

5. **Log in or create an account**
   - Default admin credentials (if configured)
   - Or create a new user account

## 🎓 Usage Examples

### Running on Different Platforms

**Windows (Command Prompt):**
```batch
cd HRMS_app
scripts\start_hrms.bat
```

**Windows (PowerShell):**
```powershell
cd HRMS_app
.\scripts\start_hrms.ps1
```

**Linux/macOS:**
```bash
cd HRMS_app
./scripts/start_hrms.sh
```

**Using Virtual Environment (Recommended):**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install and run
pip install -r requirements.txt
python main.py
```

## 🔍 Troubleshooting

### Common Issues

**"Python is not recognized"**
- Install Python and ensure it's in your system PATH
- Restart your terminal/command prompt after installation

**"No module named 'PyQt5'"**
- Install dependencies: `pip install -r requirements.txt`
- If that fails, try: `pip install PyQt5`

**"Database connection failed"**
- Verify your Supabase credentials
- Check that database tables are created
- See [docs/SETUP_GUIDE.md](docs/SETUP_GUIDE.md)

**Application won't start**
- Check Python version: `python --version` (must be 3.8+)
- Verify all dependencies are installed
- Check console output for specific error messages

**Window is too small**
- The application window is fully resizable
- Drag the edges to resize or use the maximize button

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing documentation in `/docs`
- Review the QUICKSTART.md guide

## ❓ FAQ

**Q: Is this a web application?**  
A: No, HRMS is a desktop application built with PyQt5. It runs as a native window on your computer.

**Q: Do I need a web server to run it?**  
A: No, just Python and the required packages. Run it directly with `python main.py`.

**Q: Can I access it from a web browser?**  
A: No, this is not a web application. It's a desktop application like Microsoft Office or Adobe Acrobat.

**Q: Where is index.html?**  
A: There is no index.html. This application uses PyQt5 for its user interface, not HTML/CSS/JavaScript.

**Q: How do I deploy this to a server?**  
A: This is a desktop application, not designed for web deployment. Each user runs their own copy locally.

**Q: Can I deploy this to Render, Heroku, or other web hosting?**  
A: No, PyQt5 desktop applications cannot be deployed to web hosting platforms. See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for options.

**Q: Can multiple users access it simultaneously?**  
A: Multiple users can run their own instances, and they share the same Supabase database for data synchronization.

**Q: I see mentions of HTML files - where are they?**  
A: There are no HTML files in the current codebase. This is a PyQt5 desktop app. See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for clarification.

---

**Ready to get started?** → [Read the QUICKSTART.md](QUICKSTART.md)
