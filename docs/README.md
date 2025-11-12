# HRMS_app

Human Resources Management System - A comprehensive **desktop application** built with PyQt5 and Supabase.

## Important Note

**This is a desktop application, not a web application.** It runs as a native window on your computer, similar to Microsoft Word or Excel. There are no HTML files to open in a browser.

- ✅ **Desktop App** - Built with PyQt5
- ✅ **Run with Python** - Use `python main.py` or startup scripts
- ❌ **Not a Web App** - No HTML/browser interface
- ❌ **No index.html** - Uses PyQt5 GUI framework

**New users:** See [../QUICKSTART.md](../QUICKSTART.md) for how to run the application.

## Repository Structure

This repository is organized into logical directories for improved maintainability:

- **`/core`** - Core business logic, calculators, and utilities (31 files)
- **`/gui`** - User interface components, windows, dialogs, and tabs (67 files)
- **`/services`** - External service integrations (Supabase, APIs) (9 files)
- **`/data`** - Configuration files, SQL schemas, and migrations (56 files)
- **`/docs`** - Documentation and guides (16 files)
- **`/tests`** - Test files and diagnostic tools (125 files)
- **`/scripts`** - Build and utility scripts (6 files)
- **`/examples`** - Sample data and exports (11 files)

For detailed information about the repository structure, see [REPOSITORY_STRUCTURE.md](REPOSITORY_STRUCTURE.md).

## Getting Started

**Quick Start:** See [../QUICKSTART.md](../QUICKSTART.md) to get up and running in 5 minutes.

**Detailed Setup:** See [SETUP_GUIDE.md](SETUP_GUIDE.md) for complete installation and configuration instructions.

## Documentation

- [Quick Start Guide](../QUICKSTART.md) - Get started immediately
- [Setup Guide](SETUP_GUIDE.md) - Installation and configuration
- [Repository Structure](REPOSITORY_STRUCTURE.md) - Detailed directory organization
- [Integration Summary](INTEGRATION_SUMMARY.md) - Integration overview
- [PCB Implementation](LHDN_PCB_IMPLEMENTATION.md) - Tax calculation details

## Running the Application

### Windows (Batch)
```batch
scripts\start_hrms.bat
```

### Windows (PowerShell)
```powershell
scripts\start_hrms.ps1
```

### Linux/Mac
```bash
./scripts/start_hrms.sh
```

### Python Direct
```bash
python main.py
```

**Note:** Make sure you have installed all dependencies first: `pip install -r requirements.txt`

## Key Features

- Employee management and profiles
- Leave request and approval system
- Payroll processing with Malaysian tax calculations
- Attendance tracking
- Holiday calendar management
- Bonus management
- Training and overseas work trip tracking
- PDF payslip generation

## Technology Stack

- **Frontend**: PyQt5
- **Backend**: Python 3.x
- **Database**: Supabase (PostgreSQL)
- **PDF Generation**: ReportLab
- **Authentication**: bcrypt